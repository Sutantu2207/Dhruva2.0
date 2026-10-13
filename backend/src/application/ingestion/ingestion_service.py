"""Dhruva.AI V2 — Ingestion Application Service.

Encapsulates the complete 9-stage data ingestion lifecycle:
Upload -> Extract -> Normalize -> Validate -> Stage -> Review -> Approve -> Publish -> Audit
with strict tenant boundaries, deterministic validation, and end-to-end provenance.
"""

import csv
import hashlib
import io
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.audit.audit_service import AuditService
from src.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from src.domain.academic.models import Course, Department, StudentProfile
from src.domain.identity.models import Role, User, UserRole
from src.domain.ingestion.models import (
    Approval,
    DataSource,
    ImportBatch,
    ProvenanceRecord,
    StagedRecord,
    ValidationResult,
)
from src.infrastructure.persistence.postgres.base import utc_now
from src.infrastructure.repositories.academic_repository import AcademicRepository
from src.infrastructure.repositories.ingestion_repository import IngestionRepository
from src.infrastructure.repositories.user_repository import UserRepository


DANGEROUS_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".py", ".bin", ".dll", ".so", ".ps1"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

# Canonical field synonym mappings
SYNONYMS_STUDENT = {
    "email": "email",
    "student_email": "email",
    "mail": "email",
    "first_name": "first_name",
    "name": "first_name",
    "student_name": "first_name",
    "first": "first_name",
    "last_name": "last_name",
    "surname": "last_name",
    "last": "last_name",
    "roll_number": "roll_number",
    "roll_no": "roll_number",
    "roll": "roll_number",
    "reg_no": "roll_number",
    "registration_no": "roll_number",
    "enrollment_no": "roll_number",
    "department_code": "department_code",
    "dept_code": "department_code",
    "dept": "department_code",
    "department": "department_code",
    "batch_name": "batch_name",
    "batch": "batch_name",
    "cohort": "batch_name",
    "phone": "phone",
    "mobile": "phone",
    "contact": "phone",
}

SYNONYMS_COURSE = {
    "code": "code",
    "course_code": "code",
    "course_id": "code",
    "title": "title",
    "name": "title",
    "course_title": "title",
    "course_name": "title",
    "credits": "credits",
    "credit": "credits",
    "credit_hours": "credits",
    "course_type": "course_type",
    "type": "course_type",
    "department_code": "department_code",
    "dept_code": "department_code",
    "dept": "department_code",
    "department": "department_code",
}

SYNONYMS_FACULTY = {
    "email": "email",
    "faculty_email": "email",
    "mail": "email",
    "first_name": "first_name",
    "name": "first_name",
    "faculty_name": "first_name",
    "last_name": "last_name",
    "surname": "last_name",
    "employee_id": "employee_id",
    "emp_id": "employee_id",
    "staff_id": "employee_id",
    "designation": "designation",
    "role": "designation",
    "department_code": "department_code",
    "dept_code": "department_code",
    "dept": "department_code",
    "department": "department_code",
    "phone": "phone",
    "mobile": "phone",
}


class IngestionService:
    """Service orchestrating ingestion, staging, human approvals, and live publication."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = IngestionRepository(session)
        self.academic_repo = AcademicRepository(session)
        self.user_repo = UserRepository(session)
        self.audit = AuditService(session)

    # -------------------------------------------------------------------------
    # 1. DATA SOURCES
    # -------------------------------------------------------------------------
    async def create_data_source(
        self,
        institution_id: uuid.UUID,
        name: str,
        source_type: str = "CSV_UPLOAD",
        connection_details: Optional[Dict[str, Any]] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> DataSource:
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("Data source name cannot be empty.")

        source = DataSource(
            institution_id=institution_id,
            name=clean_name,
            source_type=source_type.upper().strip(),
            connection_details=connection_details or {},
            status="ACTIVE",
        )
        saved = await self.repo.create_data_source(source)

        await self.audit.log_event(
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            action="DATA_SOURCE_CREATED",
            entity_name="DataSource",
            entity_id=saved.id,
            new_values={"name": saved.name, "source_type": saved.source_type},
        )
        return saved

    async def list_data_sources(self, institution_id: uuid.UUID) -> List[DataSource]:
        return await self.repo.list_data_sources(institution_id)

    # -------------------------------------------------------------------------
    # 2. UPLOAD, EXTRACT, NORMALIZE, VALIDATE & STAGE
    # -------------------------------------------------------------------------
    async def upload_and_stage_file(
        self,
        institution_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        target_domain: str,
        uploader_user_id: Optional[uuid.UUID],
        data_source_id: Optional[uuid.UUID] = None,
    ) -> ImportBatch:
        """Process file upload: compute SHA-256, parse tabular rows, normalize headers, run validation rules, and stage."""
        # 1. Security & MIME validation
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ValidationError(f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.")

        lower_filename = filename.lower()
        for dangerous_ext in DANGEROUS_EXTENSIONS:
            if lower_filename.endswith(dangerous_ext):
                raise ValidationError(f"Prohibited file format detected: {dangerous_ext}. Only CSV and spreadsheet documents allowed.")

        # 2. Compute SHA-256 checksum
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()

        # 3. Generate unique batch number
        now = datetime.now()
        batch_number = f"BATCH-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 4. Extract rows
        raw_rows = self._extract_csv_rows(file_bytes)
        if not raw_rows:
            raise ValidationError("The uploaded document contains 0 valid data rows.")

        # 5. Normalize & Validate
        normalized_target_domain = target_domain.upper().strip()
        staged_entities: List[StagedRecord] = []
        all_validation_results: List[ValidationResult] = []

        valid_count = 0
        warning_count = 0
        error_count = 0

        # Create batch container first
        batch = ImportBatch(
            institution_id=institution_id,
            data_source_id=data_source_id,
            batch_number=batch_number,
            original_file_name=filename,
            file_sha256=file_sha256,
            storage_uri=f"quarantine/{institution_id}/{batch_number}/{filename}",
            file_size_bytes=len(file_bytes),
            mime_type=mime_type or "text/csv",
            total_records=len(raw_rows),
            status="STAGED",
            target_domain=normalized_target_domain,
            uploaded_by=uploader_user_id,
            error_summary={},
        )
        saved_batch = await self.repo.create_import_batch(batch)

        seen_identifiers = set()

        for idx, raw_row in enumerate(raw_rows, start=1):
            normalized_payload = self._normalize_row(raw_row, normalized_target_domain)
            row_validations = self._validate_row(
                normalized_payload,
                normalized_target_domain,
                seen_identifiers,
                institution_id,
            )

            has_error = any(v.severity == "ERROR" for v in row_validations)
            has_warning = any(v.severity == "WARNING" for v in row_validations)

            if has_error:
                stage_status = "ERROR"
                error_count += 1
            elif has_warning:
                stage_status = "WARNING"
                warning_count += 1
            else:
                stage_status = "VALID"
                valid_count += 1

            rec_id = uuid.uuid4()
            staged_rec = StagedRecord(
                id=rec_id,
                institution_id=institution_id,
                import_batch_id=saved_batch.id,
                row_index=idx,
                target_entity_type=self._domain_to_entity_type(normalized_target_domain),
                raw_payload=raw_row,
                normalized_payload=normalized_payload,
                extraction_coordinate=f"Row {idx + 1}",
                stage_status=stage_status,
            )
            staged_entities.append(staged_rec)

            for val in row_validations:
                val.staged_record_id = rec_id
                val.institution_id = institution_id
                all_validation_results.append(val)

        # Bulk persist staged records & validations
        await self.repo.create_staged_records(staged_entities)
        if all_validation_results:
            await self.repo.create_validation_results(all_validation_results)

        # Update batch summary counts
        saved_batch.valid_records = valid_count
        saved_batch.warning_records = warning_count
        saved_batch.error_records = error_count
        saved_batch.status = "STAGED"
        await self.session.flush()

        await self.audit.log_event(
            institution_id=institution_id,
            actor_user_id=uploader_user_id,
            action="DATA_BATCH_UPLOADED_AND_STAGED",
            entity_name="ImportBatch",
            entity_id=saved_batch.id,
            new_values={
                "batch_number": saved_batch.batch_number,
                "total_records": len(raw_rows),
                "valid_records": valid_count,
                "warning_records": warning_count,
                "error_records": error_count,
            },
        )

        return saved_batch

    # -------------------------------------------------------------------------
    # 3. REVIEW & APPROVAL GATE
    # -------------------------------------------------------------------------
    async def approve_or_reject_batch(
        self,
        institution_id: uuid.UUID,
        batch_id: uuid.UUID,
        reviewer_user: User,
        decision: str,
        digital_signature: str,
        notes: str = "",
    ) -> Approval:
        """Grant formal administrative approval or rejection for staged data batch."""
        clean_decision = decision.upper().strip()
        if clean_decision not in ("APPROVED", "REJECTED"):
            raise ValidationError("Decision must be either 'APPROVED' or 'REJECTED'.")

        batch = await self.repo.get_import_batch_by_id(institution_id, batch_id)
        if not batch:
            raise NotFoundError(f"Import batch {batch_id} not found.")

        if batch.status in ("PUBLISHED", "ROLLED_BACK"):
            raise ConflictError(f"Cannot alter approval for batch in '{batch.status}' status.")

        # Record Approval
        approval = Approval(
            institution_id=institution_id,
            import_batch_id=batch.id,
            reviewer_user_id=reviewer_user.id,
            decision=clean_decision,
            digital_signature=digital_signature.strip() or f"{reviewer_user.first_name} {reviewer_user.last_name}",
            notes=notes.strip(),
        )
        saved_approval = await self.repo.create_approval(approval)

        # Update batch and staged record states
        if clean_decision == "APPROVED":
            batch.status = "APPROVED"
            # Update staged records: VALID and WARNING become APPROVED, ERROR remain REJECTED
            staged_records = await self.repo.list_staged_records(institution_id, batch.id, limit=10000)
            for rec in staged_records:
                if rec.stage_status in ("VALID", "WARNING"):
                    rec.stage_status = "APPROVED"
                else:
                    rec.stage_status = "REJECTED"
        else:
            batch.status = "REJECTED"
            staged_records = await self.repo.list_staged_records(institution_id, batch.id, limit=10000)
            for rec in staged_records:
                rec.stage_status = "REJECTED"

        await self.session.flush()

        await self.audit.log_event(
            institution_id=institution_id,
            actor_user_id=reviewer_user.id,
            action=f"DATA_BATCH_{clean_decision}",
            entity_name="ImportBatch",
            entity_id=batch.id,
            new_values={"decision": clean_decision, "batch_number": batch.batch_number},
        )

        return saved_approval

    # -------------------------------------------------------------------------
    # 4. PUBLICATION & PROVENANCE GENERATION
    # -------------------------------------------------------------------------
    async def publish_batch(
        self,
        institution_id: uuid.UUID,
        batch_id: uuid.UUID,
        publisher_user: User,
    ) -> Dict[str, Any]:
        """Move approved staged records into authoritative live tables and generate immutable provenance records."""
        batch = await self.repo.get_import_batch_by_id(institution_id, batch_id)
        if not batch:
            raise NotFoundError(f"Import batch {batch_id} not found.")

        if batch.status != "APPROVED":
            raise ConflictError(f"Batch must be in 'APPROVED' status before publication. Current: '{batch.status}'.")

        staged_records = await self.repo.list_staged_records(
            institution_id, batch.id, stage_status="APPROVED", limit=10000
        )
        if not staged_records:
            raise ValidationError("No approved staged records available to publish in this batch.")

        provenance_records_to_create: List[ProvenanceRecord] = []
        published_count = 0

        # Execute publication per domain
        for rec in staged_records:
            payload = rec.normalized_payload
            authoritative_table = ""
            authoritative_id: Optional[uuid.UUID] = None

            if batch.target_domain == "STUDENTS":
                authoritative_table = "users"
                user = await self._publish_student_record(institution_id, payload, publisher_user.id)
                authoritative_id = user.id

            elif batch.target_domain == "COURSES":
                authoritative_table = "courses"
                course = await self._publish_course_record(institution_id, payload)
                authoritative_id = course.id

            elif batch.target_domain == "FACULTY":
                authoritative_table = "users"
                user = await self._publish_faculty_record(institution_id, payload, publisher_user.id)
                authoritative_id = user.id

            else:
                authoritative_table = "users"
                user = await self._publish_student_record(institution_id, payload, publisher_user.id)
                authoritative_id = user.id

            # Create immutable ProvenanceRecord
            prov = ProvenanceRecord(
                institution_id=institution_id,
                authoritative_table=authoritative_table,
                authoritative_record_id=authoritative_id,
                import_batch_id=batch.id,
                staged_record_id=rec.id,
                approved_by=publisher_user.id,
                source_type=batch.mime_type,
                original_filename=batch.original_file_name,
                file_sha256=batch.file_sha256,
                coordinate_reference=rec.extraction_coordinate,
                snapshot_payload=payload,
            )
            provenance_records_to_create.append(prov)

            rec.stage_status = "PUBLISHED"
            published_count += 1

        # Bulk persist provenance
        await self.repo.create_provenance_records(provenance_records_to_create)

        batch.status = "PUBLISHED"
        await self.session.flush()

        await self.audit.log_event(
            institution_id=institution_id,
            actor_user_id=publisher_user.id,
            action="DATA_BATCH_PUBLISHED_TO_AUTHORITATIVE",
            entity_name="ImportBatch",
            entity_id=batch.id,
            new_values={
                "batch_number": batch.batch_number,
                "published_count": published_count,
            },
        )

        return {
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "status": "PUBLISHED",
            "published_records": published_count,
            "provenance_records_created": len(provenance_records_to_create),
        }

    # -------------------------------------------------------------------------
    # 5. ROLLBACK
    # -------------------------------------------------------------------------
    async def rollback_batch(
        self,
        institution_id: uuid.UUID,
        batch_id: uuid.UUID,
        actor_user: User,
    ) -> ImportBatch:
        """Rollback a published or approved batch and set status to ROLLED_BACK."""
        batch = await self.repo.get_import_batch_by_id(institution_id, batch_id)
        if not batch:
            raise NotFoundError(f"Import batch {batch_id} not found.")

        if batch.status == "ROLLED_BACK":
            raise ConflictError("Batch has already been rolled back.")

        batch.status = "ROLLED_BACK"
        staged_records = await self.repo.list_staged_records(institution_id, batch.id, limit=10000)
        for rec in staged_records:
            if rec.stage_status == "PUBLISHED":
                rec.stage_status = "ROLLED_BACK"

        await self.session.flush()

        await self.audit.log_event(
            institution_id=institution_id,
            actor_user_id=actor_user.id,
            action="DATA_BATCH_ROLLED_BACK",
            entity_name="ImportBatch",
            entity_id=batch.id,
            new_values={"batch_number": batch.batch_number},
        )

        return batch

    # -------------------------------------------------------------------------
    # 6. PROVENANCE TRACE & TELEMETRY
    # -------------------------------------------------------------------------
    async def get_provenance_trace(
        self,
        institution_id: uuid.UUID,
        authoritative_table: str,
        record_id: uuid.UUID,
    ) -> List[ProvenanceRecord]:
        """Trace data genesis answering 'Where did this data come from?'."""
        return await self.repo.list_provenance_for_record(
            institution_id, authoritative_table, record_id
        )

    async def get_telemetry_overview(self, institution_id: uuid.UUID) -> Dict[str, Any]:
        """Provide telemetry overview metrics for the Data Center dashboard."""
        return await self.repo.get_telemetry_metrics(institution_id)

    # -------------------------------------------------------------------------
    # HELPER PARSERS & ENGINES
    # -------------------------------------------------------------------------
    def _extract_csv_rows(self, file_bytes: bytes) -> List[Dict[str, str]]:
        """Safely decode and parse CSV bytes with auto-delimiter detection and BOM removal."""
        try:
            # Handle UTF-8 with BOM or standard UTF-8
            decoded_text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                decoded_text = file_bytes.decode("latin-1")
            except Exception as e:
                raise ValidationError(f"Failed to decode document: {str(e)}")

        lines = [line.strip() for line in decoded_text.splitlines() if line.strip()]
        if not lines:
            return []

        # Sniff delimiter
        first_few_lines = "\n".join(lines[:5])
        try:
            dialect = csv.Sniffer().sniff(first_few_lines, delimiters=",\t;|")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(decoded_text), delimiter=delimiter)
        rows: List[Dict[str, str]] = []
        for row in reader:
            cleaned_row = {
                str(k).strip(): str(v).strip() if v is not None else ""
                for k, v in row.items()
                if k is not None
            }
            if any(cleaned_row.values()):
                rows.append(cleaned_row)

        return rows

    def _normalize_row(self, raw_row: Dict[str, str], domain: str) -> Dict[str, Any]:
        """Map raw header synonyms to Canonical DTO schemas."""
        synonym_map = (
            SYNONYMS_STUDENT if domain == "STUDENTS"
            else SYNONYMS_COURSE if domain == "COURSES"
            else SYNONYMS_FACULTY if domain == "FACULTY"
            else SYNONYMS_STUDENT
        )

        normalized: Dict[str, Any] = {}
        for raw_key, raw_val in raw_row.items():
            clean_key = raw_key.lower().replace(" ", "_").replace("-", "_")
            canonical_key = synonym_map.get(clean_key, clean_key)
            normalized[canonical_key] = raw_val

        return normalized

    def _validate_row(
        self,
        payload: Dict[str, Any],
        domain: str,
        seen_identifiers: set,
        institution_id: uuid.UUID,
    ) -> List[ValidationResult]:
        """Deterministic validation rules enforcing required fields, syntax, and batch uniqueness."""
        results: List[ValidationResult] = []

        if domain in ("STUDENTS", "FACULTY"):
            email = payload.get("email", "").strip().lower()
            first_name = payload.get("first_name", "").strip()

            if not email:
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="REQUIRED_FIELD_MISSING",
                        severity="ERROR",
                        field_name="email",
                        message="Email address is required.",
                        context={"provided": payload},
                    )
                )
            elif not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="INVALID_EMAIL_FORMAT",
                        severity="ERROR",
                        field_name="email",
                        message=f"'{email}' is not a valid email address.",
                        context={"email": email},
                    )
                )
            elif email in seen_identifiers:
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="DUPLICATE_IDENTIFIER",
                        severity="ERROR",
                        field_name="email",
                        message=f"Duplicate email '{email}' detected within this batch.",
                        context={"email": email},
                    )
                )
            else:
                seen_identifiers.add(email)

            if not first_name:
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="REQUIRED_FIELD_MISSING",
                        severity="ERROR",
                        field_name="first_name",
                        message="First name is required.",
                        context={"provided": payload},
                    )
                )

            # Optional warnings
            if domain == "STUDENTS" and not payload.get("roll_number"):
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="MISSING_ROLL_NUMBER",
                        severity="WARNING",
                        field_name="roll_number",
                        message="Roll number not provided; default academic profile will be empty.",
                        context={},
                    )
                )

        elif domain == "COURSES":
            code = payload.get("code", "").strip().upper()
            title = payload.get("title", "").strip()

            if not code:
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="REQUIRED_FIELD_MISSING",
                        severity="ERROR",
                        field_name="code",
                        message="Course code is required.",
                        context={},
                    )
                )
            elif code in seen_identifiers:
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="DUPLICATE_IDENTIFIER",
                        severity="ERROR",
                        field_name="code",
                        message=f"Duplicate course code '{code}' in batch.",
                        context={"code": code},
                    )
                )
            else:
                seen_identifiers.add(code)

            if not title:
                results.append(
                    ValidationResult(
                        institution_id=institution_id,
                        staged_record_id=uuid.uuid4(),
                        rule_code="REQUIRED_FIELD_MISSING",
                        severity="ERROR",
                        field_name="title",
                        message="Course title is required.",
                        context={},
                    )
                )

        return results

    def _domain_to_entity_type(self, domain: str) -> str:
        if domain == "STUDENTS":
            return "STUDENT"
        elif domain == "COURSES":
            return "COURSE"
        elif domain == "FACULTY":
            return "FACULTY"
        return "GENERIC"

    async def _publish_student_record(
        self, institution_id: uuid.UUID, payload: Dict[str, Any], publisher_id: uuid.UUID
    ) -> User:
        """Create or update authoritative student user and profile."""
        email = payload["email"].lower().strip()
        first_name = payload.get("first_name", "Student")
        last_name = payload.get("last_name", "")
        phone = payload.get("phone", "")
        roll_number = payload.get("roll_number", "").strip()

        user = await self.user_repo.get_by_email(email)
        if not user:
            user = User(
                institution_id=institution_id,
                email=email,
                password_hash="!INGESTED_UNINITIALIZED_AUTH",
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                status="ACTIVE",
            )
            user = await self.user_repo.create(user)

            student_role = await self.user_repo.get_or_create_system_role(
                code="STUDENT", name="Student", permissions=["view_own_curriculum"]
            )
            await self.user_repo.assign_role(
                user_id=user.id,
                role_id=student_role.id,
                institution_id=institution_id,
                granted_by=publisher_id,
            )

        # Create StudentProfile if roll number provided and department exists
        if roll_number:
            depts = await self.academic_repo.list_departments(institution_id)
            dept_id = depts[0].id if depts else None
            if dept_id:
                existing_profile = await self.academic_repo.get_student_by_roll(institution_id, roll_number)
                if not existing_profile:
                    prof = StudentProfile(
                        user_id=user.id,
                        institution_id=institution_id,
                        department_id=dept_id,
                        roll_number=roll_number,
                        academic_status="ACTIVE",
                    )
                    await self.academic_repo.create_student_profile(prof)

        return user

    async def _publish_faculty_record(
        self, institution_id: uuid.UUID, payload: Dict[str, Any], publisher_id: uuid.UUID
    ) -> User:
        """Create or update authoritative faculty user."""
        email = payload["email"].lower().strip()
        first_name = payload.get("first_name", "Faculty")
        last_name = payload.get("last_name", "")
        phone = payload.get("phone", "")

        user = await self.user_repo.get_by_email(email)
        if not user:
            user = User(
                institution_id=institution_id,
                email=email,
                password_hash="!INGESTED_UNINITIALIZED_AUTH",
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                status="ACTIVE",
            )
            user = await self.user_repo.create(user)

            faculty_role = await self.user_repo.get_or_create_system_role(
                code="FACULTY", name="Faculty", permissions=["view_curriculum", "create_curriculum"]
            )
            await self.user_repo.assign_role(
                user_id=user.id,
                role_id=faculty_role.id,
                institution_id=institution_id,
                granted_by=publisher_id,
            )

        return user

    async def _publish_course_record(
        self, institution_id: uuid.UUID, payload: Dict[str, Any]
    ) -> Course:
        """Create or update authoritative course catalog entry."""
        code = payload["code"].strip().upper()
        title = payload.get("title", f"Course {code}")
        credits_val = float(payload.get("credits", 3.0) or 3.0)
        course_type = payload.get("course_type", "THEORY").upper()

        depts = await self.academic_repo.list_departments(institution_id)
        if not depts:
            # Create a default academic department if none exists
            dept = Department(
                institution_id=institution_id,
                code="GEN",
                name="General Academic Department",
            )
            saved_dept = await self.academic_repo.create_department(dept)
            dept_id = saved_dept.id
        else:
            dept_id = depts[0].id

        existing = await self.academic_repo.get_course_by_code(institution_id, code)
        if existing:
            return existing

        course = Course(
            institution_id=institution_id,
            department_id=dept_id,
            code=code,
            title=title,
            credits=credits_val,
            course_type=course_type,
            metadata_info={"ingested_via": "INGESTION_PIPELINE"},
        )
        return await self.academic_repo.create_course(course)
