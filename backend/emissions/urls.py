from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, DataSourceViewSet, RawUploadViewSet,
    NormalizedEmissionRecordViewSet, AuditLogViewSet,
)

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("data-sources", DataSourceViewSet, basename="datasource")
router.register("uploads", RawUploadViewSet, basename="upload")
router.register("records", NormalizedEmissionRecordViewSet, basename="record")
router.register("audit-logs", AuditLogViewSet, basename="auditlog")

urlpatterns = router.urls
