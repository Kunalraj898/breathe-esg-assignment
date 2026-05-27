"""
Suspicious row detection rules.

Each rule is a function that takes a row dict and returns (is_suspicious, reason).
We collect all triggered reasons and join them so analysts see the full picture.
"""

from decimal import Decimal

# Threshold above which a single fuel record is flagged (litres)
FUEL_HIGH_THRESHOLD = 50_000


def check_negative_value(quantity) -> str | None:
    try:
        if quantity is not None and Decimal(str(quantity)) < 0:
            return "Negative quantity value"
    except Exception:
        return "Non-numeric quantity value"
    return None


def check_missing_unit(unit: str) -> str | None:
    if not unit or str(unit).strip() in ("", "nan", "null", "None"):
        return "Missing unit"
    return None


def check_missing_quantity(quantity) -> str | None:
    if quantity is None or str(quantity).strip() in ("", "nan", "null", "None"):
        return "Missing quantity"
    return None


def check_high_fuel_usage(source_type: str, quantity) -> str | None:
    if source_type == "SAP_FUEL":
        try:
            if Decimal(str(quantity)) > FUEL_HIGH_THRESHOLD:
                return f"Abnormally high fuel usage: {quantity} litres (threshold {FUEL_HIGH_THRESHOLD})"
        except Exception:
            pass
    return None


def check_missing_date(activity_date) -> str | None:
    if not activity_date or str(activity_date).strip() in ("", "nan", "null", "None"):
        return "Missing activity date"
    return None


def evaluate(source_type: str, quantity, unit: str, activity_date) -> tuple[bool, str]:
    """
    Run all rules and return (is_suspicious, comma-joined reasons).
    """
    checks = [
        check_missing_quantity(quantity),
        check_negative_value(quantity),
        check_missing_unit(unit),
        check_missing_date(activity_date),
        check_high_fuel_usage(source_type, quantity),
    ]
    reasons = [r for r in checks if r]
    return bool(reasons), "; ".join(reasons)
