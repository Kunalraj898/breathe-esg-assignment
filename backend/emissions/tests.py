from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

from emissions.models import Company, DataSource, RawUpload, NormalizedEmissionRecord, AuditLog
from emissions.services import ingestion


class EmissionsBackendTests(APITestCase):
    def setUp(self):
        # Create a test company
        self.company = Company.objects.create(name="Acme Corp", slug="acme-corp")
        
        # Create test data sources
        self.fuel_source = DataSource.objects.create(
            company=self.company,
            name="SAP Fuel Logs",
            source_type="SAP_FUEL"
        )
        self.utility_source = DataSource.objects.create(
            company=self.company,
            name="Electricity Bills",
            source_type="UTILITY"
        )
        self.travel_source = DataSource.objects.create(
            company=self.company,
            name="Flight Bookings",
            source_type="TRAVEL"
        )

    def test_sap_fuel_ingestion(self):
        csv_content = (
            "posting date,material description,qty,uom\n"
            "2026-01-15,Diesel Fuel Purchase,1000,liters\n"
            "2026-01-20,High Usage Fuel,60000,liters\n"
            "2026-01-25,Negative Fuel,-100,liters\n"
        )
        csv_file = SimpleUploadedFile("fuel.csv", csv_content.encode("utf-8"), content_type="text/csv")
        
        raw_upload = RawUpload.objects.create(
            company=self.company,
            data_source=self.fuel_source,
            file=csv_file,
            original_filename="fuel.csv",
            uploaded_by="test_analyst@acme.com"
        )
        
        row_count = ingestion.ingest(raw_upload)
        self.assertEqual(row_count, 3)
        
        # Verify records
        records = NormalizedEmissionRecord.objects.filter(raw_upload=raw_upload).order_by("id")
        self.assertEqual(records.count(), 3)
        
        # Row 1 check
        r1 = records[0]
        self.assertEqual(r1.quantity, Decimal("1000"))
        self.assertEqual(r1.unit, "liters")
        self.assertEqual(r1.scope, "SCOPE1")
        self.assertFalse(r1.is_suspicious)
        # Factor is 2.68, co2e = 1000 * 2.68 = 2680
        self.assertEqual(r1.co2e_kg, Decimal("2680.0000"))
        
        # Row 2 check (suspicious due to high usage > 50,000 litres)
        r2 = records[1]
        self.assertEqual(r2.quantity, Decimal("60000"))
        self.assertTrue(r2.is_suspicious)
        self.assertIn("Abnormally high fuel usage", r2.suspicious_reason)
        
        # Row 3 check (suspicious due to negative value)
        r3 = records[2]
        self.assertEqual(r3.quantity, Decimal("-100"))
        self.assertTrue(r3.is_suspicious)
        self.assertIn("Negative quantity value", r3.suspicious_reason)

    def test_utility_ingestion(self):
        csv_content = (
            "billing date,description,consumption,unit\n"
            "2026-02-01,HQ Office Electricity,1200,kWh\n"
            "2026-02-15,Warehouse Electricity,,kWh\n"
        )
        csv_file = SimpleUploadedFile("utility.csv", csv_content.encode("utf-8"), content_type="text/csv")
        
        raw_upload = RawUpload.objects.create(
            company=self.company,
            data_source=self.utility_source,
            file=csv_file,
            original_filename="utility.csv",
            uploaded_by="test_analyst@acme.com"
        )
        
        row_count = ingestion.ingest(raw_upload)
        self.assertEqual(row_count, 2)
        
        records = NormalizedEmissionRecord.objects.filter(raw_upload=raw_upload).order_by("id")
        self.assertEqual(records.count(), 2)
        
        r1 = records[0]
        self.assertEqual(r1.quantity, Decimal("1200"))
        self.assertEqual(r1.scope, "SCOPE2")
        self.assertFalse(r1.is_suspicious)
        # Factor is 0.85, co2e = 1200 * 0.85 = 1020
        self.assertEqual(r1.co2e_kg, Decimal("1020.0000"))
        
        r2 = records[1]
        self.assertIsNone(r2.quantity)
        self.assertTrue(r2.is_suspicious)
        self.assertIn("Missing quantity", r2.suspicious_reason)

    def test_travel_ingestion(self):
        csv_content = (
            "travel date,trip,distance,unit\n"
            "2026-03-01,London to New York,5570,km\n"
        )
        csv_file = SimpleUploadedFile("travel.csv", csv_content.encode("utf-8"), content_type="text/csv")
        
        raw_upload = RawUpload.objects.create(
            company=self.company,
            data_source=self.travel_source,
            file=csv_file,
            original_filename="travel.csv",
            uploaded_by="test_analyst@acme.com"
        )
        
        row_count = ingestion.ingest(raw_upload)
        self.assertEqual(row_count, 1)
        
        r = NormalizedEmissionRecord.objects.get(raw_upload=raw_upload)
        self.assertEqual(r.quantity, Decimal("5570"))
        self.assertEqual(r.scope, "SCOPE3")
        # Factor is 0.115, co2e = 5570 * 0.115 = 640.55
        self.assertEqual(r.co2e_kg, Decimal("640.5500"))

    def test_dashboard_endpoint_valid_company(self):
        # Create some emission records
        csv_content = "posting date,material description,qty,uom\n2026-01-15,Diesel Fuel Purchase,100,liters\n"
        csv_file = SimpleUploadedFile("fuel.csv", csv_content.encode("utf-8"), content_type="text/csv")
        raw_upload = RawUpload.objects.create(
            company=self.company,
            data_source=self.fuel_source,
            file=csv_file,
            uploaded_by="tester"
        )
        ingestion.ingest(raw_upload)

        # Query dashboard for valid company ID
        url = reverse("record-dashboard")
        response = self.client.get(url, {"company": self.company.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(float(data["total_co2e_kg"]), 268.0)

    def test_dashboard_endpoint_no_company(self):
        # Create some emission records
        csv_content = "posting date,material description,qty,uom\n2026-01-15,Diesel Fuel Purchase,100,liters\n"
        csv_file = SimpleUploadedFile("fuel.csv", csv_content.encode("utf-8"), content_type="text/csv")
        raw_upload = RawUpload.objects.create(
            company=self.company,
            data_source=self.fuel_source,
            file=csv_file,
            uploaded_by="tester"
        )
        ingestion.ingest(raw_upload)

        # Query dashboard with no company param (should fetch all)
        url = reverse("record-dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["total"], 1)

    def test_dashboard_endpoint_undefined_company_does_not_crash(self):
        url = reverse("record-dashboard")
        
        # Test company=undefined
        response = self.client.get(url, {"company": "undefined"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test company=null
        response2 = self.client.get(url, {"company": "null"})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Test company=invalid_non_numeric
        response3 = self.client.get(url, {"company": "invalid_abc"})
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

    def test_record_review_workflow(self):
        # Create a record
        csv_content = "posting date,material description,qty,uom\n2026-01-15,Diesel Fuel Purchase,100,liters\n"
        csv_file = SimpleUploadedFile("fuel.csv", csv_content.encode("utf-8"), content_type="text/csv")
        raw_upload = RawUpload.objects.create(
            company=self.company,
            data_source=self.fuel_source,
            file=csv_file,
            uploaded_by="tester"
        )
        ingestion.ingest(raw_upload)
        record = NormalizedEmissionRecord.objects.filter(raw_upload=raw_upload).first()
        
        # Approve the record
        review_url = reverse("record-review", kwargs={"pk": record.id})
        response = self.client.post(review_url, {
            "action": "approve",
            "reviewed_by": "analyst@breathe.com",
            "notes": "Looks good"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Re-fetch and check locked
        record.refresh_from_db()
        self.assertEqual(record.status, "APPROVED")
        self.assertTrue(record.is_locked)
        self.assertEqual(record.reviewed_by, "analyst@breathe.com")
        
        # Check audit log creation
        audit_log = AuditLog.objects.filter(record=record, action="APPROVE").first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.performed_by, "analyst@breathe.com")
        
        # Attempt to edit or review locked record should fail (403)
        response2 = self.client.post(review_url, {
            "action": "reject",
            "reviewed_by": "another_analyst@breathe.com"
        })
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)
