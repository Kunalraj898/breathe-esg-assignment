"""
CSV ingestion service.

Reads a RawUpload file, dispatches to the correct parser based on source_type,
creates NormalizedEmissionRecord rows, and writes one AuditLog entry per upload.

Parsers return a list of dicts with these normalised keys:
  activity_date, description, quantity, unit

The ingestion layer then applies emission factors, suspicious checks,
and bulk-creates NormalizedEmissionRecord rows.
"""

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from emissions.models import NormalizedEmissionRecord, AuditLog
from emissions.utils.emission_factors import get_factor, calculate_co2e
from emissions.services import suspicious as sus_svc


# ---------------------------------------------------------------------------
# Column mappings — maps our canonical names to the CSV column headers we expect
# ---------------------------------------------------------------------------

SAP_COLUMNS = {
    "date": ["date", "posting_date", "posting date", "document date"],
    "description": ["material", "material description", "description", "text"],
    "quantity": ["quantity", "qty", "volume", "amount"],
    "unit": ["unit", "uom", "unit of measure"],
}

UTILITY_COLUMNS = {
    "date": ["date", "billing_date", "billing date", "period"],
    "description": ["site", "location", "meter", "description", "account"],
    "quantity": ["kwh", "consumption", "quantity", "units"],
    "unit": ["unit", "uom"],
}

TRAVEL_COLUMNS = {
    "date": ["date", "travel_date", "travel date", "departure date"],
    "description": ["route", "destination", "description", "trip"],
    "quantity": ["distance_km", "distance", "km", "miles", "quantity"],
    "unit": ["unit", "uom"],
}

COLUMN_MAP = {
    "SAP_FUEL": SAP_COLUMNS,
    "UTILITY": UTILITY_COLUMNS,
    "TRAVEL": TRAVEL_COLUMNS,
}


def _find_column(headers: list[str], candidates: list[str]) -> str | None:
    """Case-insensitive column lookup — returns the first matching header."""
    lowered = {h.lower().strip(): h for h in headers}
    for c in candidates:
        if c.lower() in lowered:
            return lowered[c.lower()]
    return None


def _parse_date(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            from datetime import datetime
            return datetime.strptime(value.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _parse_decimal(value: str) -> Decimal | None:
    try:
        cleaned = str(value).replace(",", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, AttributeError):
        return None


def _parse_csv(file_obj, source_type: str) -> list[dict]:
    """Parse CSV bytes into a list of normalised row dicts."""
    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig", errors="replace")

    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or []
    mapping = COLUMN_MAP.get(source_type, {})

    date_col = _find_column(headers, mapping.get("date", []))
    desc_col = _find_column(headers, mapping.get("description", []))
    qty_col = _find_column(headers, mapping.get("quantity", []))
    unit_col = _find_column(headers, mapping.get("unit", []))

    rows = []
    for raw_row in reader:
        rows.append({
            "raw": dict(raw_row),
            "activity_date": _parse_date(raw_row.get(date_col, "") or "") if date_col else None,
            "description": str(raw_row.get(desc_col, "") or "").strip() if desc_col else "",
            "quantity": _parse_decimal(raw_row.get(qty_col, "")) if qty_col else None,
            "unit": str(raw_row.get(unit_col, "") or "").strip() if unit_col else "",
        })
    return rows


def ingest(raw_upload) -> int:
    """
    Main entry point. Parses the upload, creates NormalizedEmissionRecord rows,
    and writes an AuditLog entry. Returns number of rows created.
    """
    source_type = raw_upload.data_source.source_type
    factor_cfg = get_factor(source_type)

    raw_upload.file.open("rb")
    parsed_rows = _parse_csv(raw_upload.file, source_type)
    raw_upload.file.close()

    records_to_create = []
    for row in parsed_rows:
        qty = row["quantity"]
        unit = row["unit"]
        activity_date = row["activity_date"]

        is_suspicious, suspicious_reason = sus_svc.evaluate(source_type, qty, unit, activity_date)

        co2e = calculate_co2e(source_type, float(qty)) if qty is not None else None

        records_to_create.append(
            NormalizedEmissionRecord(
                company=raw_upload.company,
                raw_upload=raw_upload,
                source_type=source_type,
                raw_data=row["raw"],
                activity_date=activity_date,
                description=row["description"],
                quantity=qty,
                unit=unit,
                normalized_quantity=qty,
                normalized_unit=factor_cfg.get("normalized_unit", ""),
                emission_factor=Decimal(str(factor_cfg["factor"])) if factor_cfg.get("factor") else None,
                co2e_kg=Decimal(str(co2e)) if co2e is not None else None,
                scope=factor_cfg.get("scope", "SCOPE3"),
                is_suspicious=is_suspicious,
                suspicious_reason=suspicious_reason,
            )
        )

    NormalizedEmissionRecord.objects.bulk_create(records_to_create)

    AuditLog.objects.create(
        company=raw_upload.company,
        raw_upload=raw_upload,
        action="UPLOAD",
        performed_by=raw_upload.uploaded_by,
        notes=f"Ingested {len(records_to_create)} rows from {raw_upload.original_filename}",
        metadata={"row_count": len(records_to_create), "source_type": source_type},
    )

    return len(records_to_create)
