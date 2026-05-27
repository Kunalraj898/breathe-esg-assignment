from rest_framework import serializers
from .models import Company, DataSource, RawUpload, NormalizedEmissionRecord, AuditLog


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "name", "slug", "created_at"]


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ["id", "company", "name", "source_type", "created_at"]


class RawUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawUpload
        fields = [
            "id", "company", "data_source", "file", "original_filename",
            "uploaded_by", "status", "row_count", "error_message", "uploaded_at",
        ]
        read_only_fields = ["status", "row_count", "error_message", "uploaded_at"]


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            "id", "company", "raw_upload", "source_type",
            "activity_date", "description", "quantity", "unit",
            "normalized_quantity", "normalized_unit",
            "emission_factor", "co2e_kg",
            "scope", "status", "is_suspicious", "suspicious_reason",
            "is_locked", "reviewed_by", "reviewed_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["is_locked", "created_at", "updated_at"]


class RecordReviewSerializer(serializers.Serializer):
    """Used for approve / reject actions — captures who performed the action."""
    action = serializers.ChoiceField(choices=["approve", "reject"])
    reviewed_by = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ["id", "company", "record", "raw_upload", "action", "performed_by", "notes", "metadata", "created_at"]


class DashboardStatsSerializer(serializers.Serializer):
    """Summary counts for the analyst dashboard."""
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    suspicious = serializers.IntegerField()
    total_co2e_kg = serializers.DecimalField(max_digits=20, decimal_places=2, allow_null=True)
