# Dhruva.AI V2 — Institutional Data Center & Provenance Explorer Frontend Specification

> **Classification:** Engineering & Architecture Documentation  
> **Route:** `/workspace/datacenter`  
> **Underlying Backend Commit:** `d42ed33` (`feat: implement institutional data center, 9-stage ingestion pipeline, and provenance tracking`)  
> **Core Principle:** `NO SOURCE → NO DATA` (Zero Hallucination / Zero Synthetic Institutional Truth)  

---

## 1. Overview & Architecture Purpose

The **Institutional Data Center & Provenance Explorer** is the central nervous system for institutional data ingestion and provenance in Dhruva.AI V2. In accordance with the platform's core tenet—**"NO SOURCE → NO DATA"**—no student record, faculty assignment, course catalog item, or official grade may enter the authoritative production schema without an unbroken, cryptographically verified chain of custody.

The frontend interface at `/workspace/datacenter` connects directly to the 9-stage asynchronous ingestion pipeline implemented in the FastAPI backend:
```
Upload ➔ Extract ➔ Normalize ➔ Validate ➔ Stage ➔ Review ➔ Approve ➔ Publish ➔ Audit
```

---

## 2. Workspace Tabs & Screen Architecture

The Data Center interface is divided into five dedicated operational views:

### 2.1 Telemetry Overview Bar
Renders institutional metrics queried directly from `GET /institutions/{tenant_slug}/data-center/overview`:
- **Total Batches**: Count of all ingestion packages processed or pending.
- **Pending Approvals**: Batches currently quarantined in `STAGED` state requiring human review.
- **Published Batches**: Batches successfully committed to live authoritative tables.
- **Staged Records Breakdown**: Total records with granular valid vs. error counts.
- **Provenance Chains**: Count of immutable provenance traces recorded across all authoritative tables.

### 2.2 Tab 1: Ingestion Batches & Lifecycle Manager
- Real-time tabular listing of all institutional import batches via `GET /institutions/{tenant_slug}/ingestion/batches`.
- **Filtering**: By lifecycle status (`STAGED`, `APPROVED`, `PUBLISHED`, `REJECTED`, `ROLLED_BACK`) and target academic domain (`STUDENTS`, `COURSES`, `FACULTY`).
- **Cryptographic Transparency**: Shows SHA-256 file checksums computed at ingestion time.
- **Lifecycle Actions**:
  - *Inspect*: Transitions to the Staged Record review queue for deep row-level inspection.
  - *Review & Sign*: Opens the Human Review and Digital Sign-Off modal (privileged roles).
  - *Publish*: Commits approved staged records into authoritative live tables (`POST /institutions/{tenant_slug}/ingestion/batches/{id}/publish`).
  - *Rollback*: Reverts published/approved batches (`POST /institutions/{tenant_slug}/ingestion/batches/{id}/rollback`).

### 2.3 Tab 2: Upload & Stage
- An accessible document dropzone allowing authorized officers to upload source files.
- **Format Disclosure**: Only accepts CSV and delimited text formats (`.csv`, `.tsv`, `.txt`) with comma, tab, semicolon, or pipe delimiters.
- **Size Limit**: 50 MB maximum (server-enforced via `MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024`).
- **Client-Side Cryptography**: Computes SHA-256 checksums locally via the Web Crypto API (`crypto.subtle.digest`) prior to transmission for immediate audit visibility.
- **Normalization Preview**: Documents how synonym normalization transforms raw column headers into canonical DTO schemas (e.g., `student_email` → `email`, `roll_no` → `roll_number`).

### 2.4 Tab 3: Staged Records Review Queue & Rule Inspector
- Quarantined record inspector connected to `GET /institutions/{tenant_slug}/ingestion/batches/{batch_id}/staged-records`.
- **Row-Level Coordinates**: Tracks the exact row/cell location within the uploaded document (e.g., `Row 2`, `Row 3`).
- **Deterministic Validation Findings**: Highlights rule violations without synthesizing corrections:
  - `REQUIRED_FIELD_MISSING`: Missing required columns (e.g., `first_name`, `email`, `code`).
  - `INVALID_EMAIL_FORMAT`: Regex syntax failures on institutional email addresses.
  - `DUPLICATE_IDENTIFIER`: Cross-row duplicate collisions within the batch.
  - `MISSING_ROLL_NUMBER`: Non-blocking warning conditions.
- **Dual Payload Inspector Modal**: Side-by-side inspection of the raw extracted row payload vs. the normalized canonical JSON structure.

### 2.5 Tab 4: Institutional Data Sources
- Catalog of external feeds, ERP exports, and SIS sync configurations via `GET /institutions/{tenant_slug}/data-center/sources`.
- Modal dialog for registering new institutional sources (`POST /institutions/{tenant_slug}/data-center/sources`) with JSON connection configurations.

### 2.6 Tab 5: Immutable Provenance Explorer
- Genesis trace lookup engine via `GET /institutions/{tenant_slug}/ingestion/provenance/{authoritative_table}/{record_id}`.
- Allows auditing any authoritative record (e.g., in `students`, `courses`, `users`) to reveal:
  - Original source filename and cryptographic SHA-256 hash.
  - Ingestion batch number and import timestamp.
  - Extraction coordinate (row/line).
  - Reviewing officer user ID and digital approval signature.
  - Complete snapshot of values at the exact instant of publication.

---

## 3. Real Backend API Contracts & Schema Bindings

All endpoints reside under `/api/v1/institutions/{institution_slug}/`:

| HTTP Method | Route | Description | Required Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/data-center/overview` | Telemetry statistics and aggregate health metrics | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `GET` | `/data-center/sources` | List registered data sources | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `POST` | `/data-center/sources` | Register a new institutional data source | `SUPER_ADMIN`, `INSTITUTION_ADMIN` |
| `POST` | `/ingestion/upload` | Upload and stage a raw delimited document (`multipart/form-data`) | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `GET` | `/ingestion/batches` | List import batches with status and domain filters | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `GET` | `/ingestion/batches/{id}` | Retrieve individual batch metadata | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `GET` | `/ingestion/batches/{id}/staged-records` | List quarantined staged rows with validation results | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `POST` | `/ingestion/batches/{id}/approve` | Record human review decision (`APPROVED` or `REJECTED`) | `SUPER_ADMIN`, `INSTITUTION_ADMIN`, `HOD` |
| `POST` | `/ingestion/batches/{id}/publish` | Promote approved batch into authoritative tables | `SUPER_ADMIN`, `INSTITUTION_ADMIN` |
| `POST` | `/ingestion/batches/{id}/rollback` | Roll back batch records | `SUPER_ADMIN`, `INSTITUTION_ADMIN` |
| `GET` | `/ingestion/provenance/{table}/{id}` | Retrieve immutable provenance trail for authoritative record | Authenticated (`get_current_user`) |

---

## 4. Role-Based Access Control (RBAC) Enforcement

| Capability | SUPER_ADMIN | INSTITUTION_ADMIN | HOD | FACULTY | STUDENT |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **View Ingestion Batches & Telemetry** | Full | Full | Department/Catalog | Denied | Denied |
| **Upload Delimited Batch** | Yes | Yes | Yes | Denied | Denied |
| **Inspect Quarantined Rows & Rules** | Yes | Yes | Yes | Denied | Denied |
| **Human Review & Sign-Off (Approve/Reject)** | Yes | Yes | Yes | Denied | Denied |
| **Publish to Authoritative Live Tables** | Yes | Yes | Denied | Denied | Denied |
| **Rollback Batch** | Yes | Yes | Denied | Denied | Denied |
| **Register Data Sources** | Yes | Yes | Denied | Denied | Denied |
| **Inspect Record Provenance Trail** | Yes | Yes | Yes | Yes | Yes (Own) |

*All authorization gates are enforced on the backend by FastAPI dependency guards (`require_roles(...)`). The frontend reflects these permissions gracefully by hiding or disabling mutating actions and rendering empty/no-permission states.*

---

## 5. Supported Upload Formats & Security Rules

1. **Delimited Formats**: CSV (`.csv`), TSV (`.tsv`), TXT (`.txt`).
2. **Character Encodings**: UTF-8, UTF-8-SIG (BOM stripped), Latin-1 fallback.
3. **Delimiter Detection**: Automatic sniffing supporting comma (`,`), tab (`\t`), semicolon (`;`), and pipe (`|`).
4. **File Size Enforcement**: Strict ceiling of 50 MB (`52,428,800` bytes). Client validates size before transmission; backend validates size on raw stream before disk write.
5. **Dangerous Extensions Prohibited**: `.exe`, `.sh`, `.bat`, `.cmd`, `.py`, `.bin`, `.dll`, `.so`, `.ps1`.
6. **No Phantom Formats**: The UI explicitly disclaims PDF, DOCX, or Excel `.xlsx` ingestion until dedicated server parsers and worker pools are deployed.

---

## 6. Verification & Test Suite

### 6.1 Frontend Test Suite (`frontend/src/__tests__/datacenter.test.ts`)
Run via `npm test` (using Node 24 native `--experimental-strip-types --test`):
```text
▶ Data Center Ingestion Guardrails
  ✔ accepts valid CSV files under 50 MB
  ✔ accepts valid TSV and TXT delimited files
  ✔ rejects files exceeding 50 MB limit
  ✔ strictly blocks dangerous executable extensions
  ✔ rejects unsupported spreadsheet formats until server parsers are deployed
▶ Data Center RBAC Permission Guardrails
  ✔ grants full lifecycle control to SUPER_ADMIN
  ✔ grants administrative management to INSTITUTION_ADMIN
  ✔ allows HOD to upload and review/approve, but prevents publishing to authoritative live tables
  ✔ strictly denies FACULTY and STUDENT from modifying Data Center staging or approvals
▶ Batch Lifecycle Permissible Actions
  ✔ allows review only when batch is in STAGED status
  ✔ allows publication only when batch is in APPROVED status
  ✔ allows rollback only for APPROVED and PUBLISHED batches
▶ Deterministic Validation Formatting
  ✔ correctly classifies errors preventing promotion
  ✔ handles clean records with zero validation errors
ℹ tests 14, pass 14, fail 0
```

### 6.2 Frontend Type-Check & Build
- `npm run typecheck` (`tsc --noEmit`): **0 errors**
- `npm run build` (`next build`): **0 errors** (all 9 pages statically optimized, `/workspace/datacenter` rendered at 9.38 kB)

### 6.3 Backend Regression Test Suite
- `pytest tests`: **52 passed in 35.50s** across all 8 modules (Academic Hierarchy, Auth, Platform, Curriculum, Ingestion Data Center, RBAC, Security, Tenant Isolation).

---

## 7. Known Limitations & Roadmap

1. **Spreadsheet Binary Parsers (XLSX / ODS)**: Requires `openpyxl` / worker daemon in background worker layer before enabling `.xlsx` uploads.
2. **Unstructured Document OCR / Layout Extraction (PDF / DOCX)**: Planned for background worker integration with bounding box coordinate capture.
3. **Automated Dual-Key Sign-Off**: The current approval workflow records single-signature digital sign-off. High-stakes graduation cohorts will support two-man cryptographic co-signatures in Phase 7 production hardening.
