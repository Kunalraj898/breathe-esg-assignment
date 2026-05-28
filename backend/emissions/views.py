from django.utils import timezone
from django.db.models import Sum, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Company, DataSource, RawUpload, NormalizedEmissionRecord, AuditLog
from .serializers import (
    CompanySerializer, DataSourceSerializer, RawUploadSerializer,
    NormalizedEmissionRecordSerializer, RecordReviewSerializer,
    AuditLogSerializer, DashboardStatsSerializer,
)
from .services import ingestion


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.select_related("company").all()
    serializer_class = DataSourceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get("company")
        if company_id and company_id not in ("undefined", "null", ""):
            try:
                qs = qs.filter(company_id=int(company_id))
            except ValueError:
                qs = qs.none()
        return qs


class RawUploadViewSet(viewsets.ModelViewSet):
    queryset = RawUpload.objects.select_related("company", "data_source").all()
    serializer_class = RawUploadSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = super().get_queryset()
        company_id = self.request.query_params.get("company")
        if company_id and company_id not in ("undefined", "null", ""):
            try:
                qs = qs.filter(company_id=int(company_id))
            except ValueError:
                qs = qs.none()
        return qs

    def create(self, request, *args, **kwargs):
        """
        Upload a CSV file. After saving the RawUpload record we immediately
        trigger ingestion synchronously. In production you'd push this to a
        Celery task queue so large files don't block the HTTP response.
        """
        file_obj = request.FILES.get("file")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = serializer.save(
            original_filename=file_obj.name if file_obj else "",
            status="PROCESSING",
        )

        try:
            row_count = ingestion.ingest(upload)
            upload.status = "COMPLETED"
            upload.row_count = row_count
            upload.save(update_fields=["status", "row_count"])
        except Exception as exc:
            upload.status = "FAILED"
            upload.error_message = str(exc)
            upload.save(update_fields=["status", "error_message"])
            return Response(
                {"error": f"Ingestion failed: {exc}"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return Response(RawUploadSerializer(upload).data, status=status.HTTP_201_CREATED)


class NormalizedEmissionRecordViewSet(viewsets.ModelViewSet):
    queryset = NormalizedEmissionRecord.objects.select_related("company", "raw_upload").all()
    serializer_class = NormalizedEmissionRecordSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        if company_id := params.get("company"):
            if company_id not in ("undefined", "null", ""):
                try:
                    qs = qs.filter(company_id=int(company_id))
                except ValueError:
                    qs = qs.none()
        if status_filter := params.get("status"):
            qs = qs.filter(status=status_filter)
        if scope := params.get("scope"):
            qs = qs.filter(scope=scope)
        if suspicious := params.get("suspicious"):
            qs = qs.filter(is_suspicious=suspicious.lower() == "true")
        if source_type := params.get("source_type"):
            qs = qs.filter(source_type=source_type)

        return qs

    def update(self, request, *args, **kwargs):
        """Prevent edits on locked (approved) records."""
        record = self.get_object()
        if record.is_locked:
            return Response(
                {"error": "This record is locked after approval and cannot be edited."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        """
        POST /api/records/<id>/review/
        Body: { "action": "approve"|"reject", "reviewed_by": "name", "notes": "..." }
        """
        record = self.get_object()
        if record.is_locked:
            return Response(
                {"error": "Record is already locked."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = RecordReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if data["action"] == "approve":
            record.status = "APPROVED"
            record.is_locked = True
            audit_action = "APPROVE"
        else:
            record.status = "REJECTED"
            audit_action = "REJECT"

        record.reviewed_by = data["reviewed_by"]
        record.reviewed_at = timezone.now()
        record.save(update_fields=["status", "is_locked", "reviewed_by", "reviewed_at"])

        AuditLog.objects.create(
            company=record.company,
            record=record,
            action=audit_action,
            performed_by=data["reviewed_by"],
            notes=data.get("notes", ""),
            metadata={"previous_status": "PENDING"},
        )

        return Response(NormalizedEmissionRecordSerializer(record).data)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """
        GET /api/records/dashboard/?company=<id>
        Returns summary counts for the analyst dashboard.
        """
        qs = self.get_queryset()
        stats = {
            "total": qs.count(),
            "pending": qs.filter(status="PENDING").count(),
            "approved": qs.filter(status="APPROVED").count(),
            "rejected": qs.filter(status="REJECTED").count(),
            "suspicious": qs.filter(is_suspicious=True).count(),
            "total_co2e_kg": qs.aggregate(total=Sum("co2e_kg"))["total"],
        }
        return Response(DashboardStatsSerializer(stats).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit logs are read-only — no create/update/delete via API."""
    queryset = AuditLog.objects.select_related("company", "record", "raw_upload").all()
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if company_id := self.request.query_params.get("company"):
            if company_id not in ("undefined", "null", ""):
                try:
                    qs = qs.filter(company_id=int(company_id))
                except ValueError:
                    qs = qs.none()
        if record_id := self.request.query_params.get("record"):
            if record_id not in ("undefined", "null", ""):
                try:
                    qs = qs.filter(record_id=int(record_id))
                except ValueError:
                    qs = qs.none()
        return qs
