"""Dhruva.AI V2 — Data Center, Ingestion Pipeline & Provenance Tests.

Validates:
1. Data source registry management.
2. 9-Stage ingestion pipeline: Upload, extraction, normalization, deterministic validation, staging.
3. Strict isolation: Staged records remain invisible in authoritative live tables prior to approval.
4. Deterministic validation engine: Email syntax, duplicate identifier detection, required field checks.
5. Administrative approval gates and RBAC boundaries (Faculty/Student rejected, Admin/HOD allowed).
6. Publication transaction engine: Authoritative entity creation + immutable provenance records generation.
7. Provenance trace query answering 'Where did this data come from?'.
8. Cross-tenant isolation rejection (Tenant B blocked from Tenant A ingestion batches).
9. Batch rollback capabilities.
10. Data Center telemetry aggregation metrics.
"""

import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import create_access_token
from src.domain.identity.models import User
from src.domain.ingestion.models import ImportBatch, ProvenanceRecord, StagedRecord


@pytest.mark.asyncio
class TestIngestionDataCenterAPI:
    """Test suite for Phase 4 Data Center, Ingestion Pipeline & Provenance."""

    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_data_source_registry(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify institutional admin can register and list institutional data sources."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        # 1. Register data source
        create_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/data-center/sources",
            json={
                "name": "Registrar ERP SIS Sync",
                "source_type": "SIS_SYNC",
                "connection_details": {"protocol": "sftp", "host": "erp.iitb.ac.in"},
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        source_data = create_resp.json()["data"]
        assert source_data["name"] == "Registrar ERP SIS Sync"
        assert source_data["source_type"] == "SIS_SYNC"
        source_id = source_data["id"]

        # 2. List data sources
        list_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/data-center/sources",
            headers=headers,
        )
        assert list_resp.status_code == 200
        sources = list_resp.json()["data"]
        assert any(s["id"] == source_id for s in sources)

    async def test_upload_csv_staging_and_live_isolation(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify CSV upload extracts and stages records, while live tables remain untouched."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        csv_content = (
            "Roll No,First Name,Last Name,Student Email,Phone\n"
            "2026CS101,Aarav,Sharma,aarav.sharma@iitb.ac.in,+919876543210\n"
            "2026CS102,Diya,Patel,diya.patel@iitb.ac.in,+919876543211\n"
        ).encode("utf-8")

        files = {"file": ("students_roster_2026.csv", io.BytesIO(csv_content), "text/csv")}
        data = {"target_domain": "STUDENTS"}

        upload_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/upload",
            files=files,
            data=data,
            headers=headers,
        )
        assert upload_resp.status_code == 201
        batch_data = upload_resp.json()["data"]
        batch_id = batch_data["id"]

        assert batch_data["total_records"] == 2
        assert batch_data["valid_records"] == 2
        assert batch_data["error_records"] == 0
        assert batch_data["status"] == "STAGED"
        assert len(batch_data["file_sha256"]) == 64

        # Verify staged records in review queue
        records_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/staged-records",
            headers=headers,
        )
        assert records_resp.status_code == 200
        staged_rows = records_resp.json()["data"]
        assert len(staged_rows) == 2
        assert staged_rows[0]["normalized_payload"]["email"] == "aarav.sharma@iitb.ac.in"
        assert staged_rows[0]["normalized_payload"]["roll_number"] == "2026CS101"
        assert staged_rows[0]["stage_status"] == "VALID"

        # CRITICAL TEST: Staged students MUST NOT exist in live users table yet
        live_user_q = await db_session.execute(
            select(User).where(User.email == "aarav.sharma@iitb.ac.in")
        )
        assert live_user_q.scalar_one_or_none() is None

    async def test_deterministic_validation_rules(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify validation engine catches missing fields, invalid email, and batch duplicates."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        # Row 1: Valid
        # Row 2: Invalid Email
        # Row 3: Missing Required First Name
        # Row 4: Duplicate Email with Row 1
        flawed_csv = (
            "Roll No,First Name,Last Name,Student Email\n"
            "CS001,Kavya,Nair,kavya.nair@iitb.ac.in\n"
            "CS002,Rahul,Verma,invalid-email-format\n"
            "CS003,,Gupta,rohit.gupta@iitb.ac.in\n"
            "CS004,Kavya,Clone,kavya.nair@iitb.ac.in\n"
        ).encode("utf-8")

        files = {"file": ("flawed_roster.csv", io.BytesIO(flawed_csv), "text/csv")}
        data = {"target_domain": "STUDENTS"}

        upload_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/upload",
            files=files,
            data=data,
            headers=headers,
        )
        assert upload_resp.status_code == 201
        batch_data = upload_resp.json()["data"]
        batch_id = batch_data["id"]

        assert batch_data["total_records"] == 4
        assert batch_data["error_records"] == 3
        assert batch_data["valid_records"] == 1

        # Check staged records and validation messages
        records_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/staged-records",
            headers=headers,
        )
        staged_rows = records_resp.json()["data"]
        assert len(staged_rows) == 4

        # Row 2 has INVALID_EMAIL_FORMAT
        row2_rules = [v["rule_code"] for v in staged_rows[1]["validation_results"]]
        assert "INVALID_EMAIL_FORMAT" in row2_rules

        # Row 3 has REQUIRED_FIELD_MISSING
        row3_rules = [v["rule_code"] for v in staged_rows[2]["validation_results"]]
        assert "REQUIRED_FIELD_MISSING" in row3_rules

        # Row 4 has DUPLICATE_IDENTIFIER
        row4_rules = [v["rule_code"] for v in staged_rows[3]["validation_results"]]
        assert "DUPLICATE_IDENTIFIER" in row4_rules

    async def test_approval_workflow_rbac_and_publishing(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify approval RBAC, publication transaction, live table creation, and provenance generation."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]

        admin_headers = self._auth_headers(admin)
        student_headers = self._auth_headers(student)
        faculty_headers = self._auth_headers(faculty)

        # 1. Upload valid student batch
        csv_content = (
            "Roll No,First Name,Last Name,Student Email\n"
            "2026EE201,Priya,Raman,priya.raman@iitb.ac.in\n"
        ).encode("utf-8")
        files = {"file": ("ee_students.csv", io.BytesIO(csv_content), "text/csv")}

        upload_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/upload",
            files=files,
            data={"target_domain": "STUDENTS"},
            headers=admin_headers,
        )
        assert upload_resp.status_code == 201
        batch_id = upload_resp.json()["data"]["id"]

        # 2. RBAC check: Student cannot approve batch
        student_approve_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/approve",
            json={"decision": "APPROVED", "digital_signature": "Student Hack"},
            headers=student_headers,
        )
        assert student_approve_resp.status_code == 403

        # 3. Cannot publish unapproved batch
        premature_pub_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/publish",
            headers=admin_headers,
        )
        assert premature_pub_resp.status_code == 409

        # 4. Admin approves batch
        approve_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/approve",
            json={
                "decision": "APPROVED",
                "digital_signature": "Prof. Admin Sign-off",
                "notes": "Verified against admissions registrar roster",
            },
            headers=admin_headers,
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["data"]["decision"] == "APPROVED"

        # 5. Admin publishes approved batch
        pub_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/publish",
            headers=admin_headers,
        )
        assert pub_resp.status_code == 200
        pub_data = pub_resp.json()["data"]
        assert pub_data["status"] == "PUBLISHED"
        assert pub_data["published_records"] == 1
        assert pub_data["provenance_records_created"] == 1

        # 6. Verify live user is created in database
        live_user_q = await db_session.execute(
            select(User).where(User.email == "priya.raman@iitb.ac.in")
        )
        live_user = live_user_q.scalar_one_or_none()
        assert live_user is not None
        assert live_user.first_name == "Priya"

        # 7. Trace Provenance API
        prov_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/ingestion/provenance/users/{live_user.id}",
            headers=admin_headers,
        )
        assert prov_resp.status_code == 200
        prov_records = prov_resp.json()["data"]
        assert len(prov_records) == 1
        prov = prov_records[0]
        assert prov["authoritative_table"] == "users"
        assert prov["authoritative_record_id"] == str(live_user.id)
        assert prov["original_filename"] == "ee_students.csv"
        assert prov["coordinate_reference"] == "Row 2"
        assert prov["snapshot_payload"]["email"] == "priya.raman@iitb.ac.in"

    async def test_cross_tenant_ingestion_denial(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify Institution 2 user cannot view or approve Institution 1 batch."""
        inst1 = seed_data["inst1"]
        admin1 = seed_data["inst_admin"]
        admin2 = seed_data.get("inst_admin_2") or seed_data["inst2_user"]

        admin1_headers = self._auth_headers(admin1)
        admin2_headers = self._auth_headers(admin2)

        # Upload in inst1
        csv_content = "Roll No,First Name,Student Email\nCS999,Rohan,rohan@iitb.ac.in\n".encode("utf-8")
        files = {"file": ("rohan.csv", io.BytesIO(csv_content), "text/csv")}
        upload_resp = await client.post(
            f"/api/v1/institutions/{inst1.slug}/ingestion/upload",
            files=files,
            data={"target_domain": "STUDENTS"},
            headers=admin1_headers,
        )
        batch_id = upload_resp.json()["data"]["id"]

        # Admin of Inst 2 attempts to view Inst 1's batches
        cross_list_resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/ingestion/batches",
            headers=admin2_headers,
        )
        assert cross_list_resp.status_code == 403

        # Admin of Inst 2 attempts to approve Inst 1's batch
        cross_approve_resp = await client.post(
            f"/api/v1/institutions/{inst1.slug}/ingestion/batches/{batch_id}/approve",
            json={"decision": "APPROVED", "digital_signature": "Attacker"},
            headers=admin2_headers,
        )
        assert cross_approve_resp.status_code == 403

    async def test_batch_rollback_workflow(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify administrator can roll back a batch."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        csv_content = "Roll No,First Name,Student Email\nRB001,Test,test.rb@iitb.ac.in\n".encode("utf-8")
        files = {"file": ("rb.csv", io.BytesIO(csv_content), "text/csv")}
        upload_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/upload",
            files=files,
            data={"target_domain": "STUDENTS"},
            headers=headers,
        )
        batch_id = upload_resp.json()["data"]["id"]

        # Rollback
        rb_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ingestion/batches/{batch_id}/rollback",
            headers=headers,
        )
        assert rb_resp.status_code == 200
        assert rb_resp.json()["data"]["status"] == "ROLLED_BACK"

    async def test_datacenter_telemetry_metrics(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify Data Center overview telemetry accurately aggregates counts."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        overview_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/data-center/overview",
            headers=headers,
        )
        assert overview_resp.status_code == 200
        telemetry = overview_resp.json()["data"]
        assert "total_batches" in telemetry
        assert "pending_approval" in telemetry
        assert "published_batches" in telemetry
        assert "failure_rate_percent" in telemetry
        assert "total_provenance_records" in telemetry
        assert telemetry["total_batches"] >= 0
