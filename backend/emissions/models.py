from django.db import models


class Company(models.Model):
    """
    Multi-tenancy root. Every record belongs to a company so the same
    database can serve multiple organisations without data leaking across them.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DataSource(models.Model):
    """
    Represents a repeating data feed — e.g. 'SAP monthly fuel export'.
    Separating this from RawUpload lets us track which feed a file came from
    and build per-source quality metrics over time.
    """
    SOURCE_TYPES = [
        ("SAP_FUEL", "SAP Fuel / Procurement"),
        ("UTILITY", "Utility Electricity"),
        ("TRAVEL", "Corporate Travel"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="data_sources")
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.slug} — {self.name}"


class RawUpload(models.Model):
    """
    Represents a single CSV file upload. We keep the original file so we can
    re-process it if ingestion logic changes, and track overall status.
    """
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="uploads")
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField(upload_to="uploads/")
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.CharField(max_length=255)  # analyst name / email
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    row_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class NormalizedEmissionRecord(models.Model):
    """
    The canonical emissions table. All CSVs — regardless of source format —
    are parsed into this unified schema so analysts work with a single view.

    Design decisions:
    - raw_data (JSONField) stores the original CSV row verbatim. This is
      the 'source of truth' anchor; if calculation logic changes we can
      re-derive co2e_kg from the raw snapshot without re-uploading.
    - is_locked prevents edits after approval, enforcing data integrity for
      downstream reporting.
    - scope follows the GHG Protocol categories used in corporate reporting.
    """
    SCOPE_CHOICES = [
        ("SCOPE1", "Scope 1 — Direct (fuel combustion)"),
        ("SCOPE2", "Scope 2 — Indirect (purchased electricity)"),
        ("SCOPE3", "Scope 3 — Value chain (travel, supply chain)"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="emission_records")
    raw_upload = models.ForeignKey(RawUpload, on_delete=models.CASCADE, related_name="records")
    source_type = models.CharField(max_length=20)  # mirrors DataSource.SOURCE_TYPES

    # --- Source-of-truth snapshot ---
    raw_data = models.JSONField()  # original CSV row as a dict

    # --- Normalised fields ---
    activity_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=500, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)          # as reported in CSV
    normalized_quantity = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)
    normalized_unit = models.CharField(max_length=50, blank=True)  # liters | kWh | km

    # --- Emissions calculation ---
    emission_factor = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    co2e_kg = models.DecimalField(max_digits=15, decimal_places=4, null=True, blank=True)

    # --- GHG Protocol scope classification ---
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)

    # --- Analyst review workflow ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    is_suspicious = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True)

    # Record is locked once approved — prevents accidental mutation of audited data
    is_locked = models.BooleanField(default=False)

    # --- Tracking ---
    reviewed_by = models.CharField(max_length=255, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_type} | {self.activity_date} | {self.co2e_kg} kg CO₂e"


class AuditLog(models.Model):
    """
    Immutable append-only log. We never update or delete rows here.
    Captures who did what to which record and when — required for ESG audit trails.
    """
    ACTION_CHOICES = [
        ("UPLOAD", "File Uploaded"),
        ("APPROVE", "Record Approved"),
        ("REJECT", "Record Rejected"),
        ("EDIT", "Record Edited"),
        ("FLAG", "Record Flagged as Suspicious"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="audit_logs")
    record = models.ForeignKey(
        NormalizedEmissionRecord,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    raw_upload = models.ForeignKey(
        RawUpload,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)  # e.g. {"previous_status": "PENDING"}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} by {self.performed_by} @ {self.created_at:%Y-%m-%d %H:%M}"
