from django.contrib import admin
from .models import Company, DataSource, RawUpload, NormalizedEmissionRecord, AuditLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "source_type", "created_at"]
    list_filter = ["source_type", "company"]


@admin.register(RawUpload)
class RawUploadAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "company", "data_source", "status", "uploaded_by", "uploaded_at"]
    list_filter = ["status", "company"]
    readonly_fields = ["uploaded_at"]


@admin.register(NormalizedEmissionRecord)
class NormalizedEmissionRecordAdmin(admin.ModelAdmin):
    list_display = ["id", "source_type", "scope", "activity_date", "co2e_kg", "status", "is_suspicious", "is_locked"]
    list_filter = ["status", "scope", "source_type", "is_suspicious", "company"]
    readonly_fields = ["created_at", "updated_at", "raw_data"]
    search_fields = ["description"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "performed_by", "company", "created_at"]
    list_filter = ["action", "company"]
    readonly_fields = ["created_at"]

    def has_change_permission(self, request, obj=None):
        return False  # audit logs are immutable

    def has_delete_permission(self, request, obj=None):
        return False
