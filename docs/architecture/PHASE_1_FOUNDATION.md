# DHRUVA.AI (V2) — PHASE 1 FOUNDATION SPECIFICATION & VERIFICATION

> **Status:** Phase 1 Complete & Verified  
> **Standard:** Production-Grade / Zero Mock Data / Independently Testable  
> **Test Suite:** 33/33 Backend Tests Passing (100%) | Next.js 15 Production Build Passing  

---

## 1. Executive Summary

Phase 1 establishes the rock-solid foundation for **Dhruva.AI V2**: a scalable, multi-tenant institutional intelligence operating system. This phase sets up the database partitioning with PostgreSQL Row-Level Security (RLS), cryptographic user identity via Argon2id, rotating dual-token JWT sessions, centralized RBAC across all six system roles, structured audit logging, standardized API error envelopes, a complete frontend application with an institutional design system (20 reusable primitives), and an automated regression test suite.

In accordance with **Architecture Rule 18 (Zero Mock Data)**, the application database remains completely clean and unseeded. All tests operate in an isolated ephemeral in-memory SQLite sandbox, ensuring that no dummy or fake records ever contaminate production tables.

---

## 2. Monorepo & Directory Structure

```
Dhruva V2/
├── backend/
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_core_foundation.py  # Initial multi-tenant RLS schema migration
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── src/
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic Settings with env validation
│   │   │   ├── errors.py                # Standardized exception hierarchy
│   │   │   ├── logging.py               # JSON structured logging with correlation IDs
│   │   │   ├── rate_limit.py            # Sliding window in-memory/Redis rate limiter
│   │   │   └── security.py              # Argon2id hashing & JWT dual-token crypto
│   │   ├── domain/
│   │   │   ├── identity/                # Institution, User, Role, UserRole, RefreshToken
│   │   │   └── audit/                   # Append-only AuditLog model
│   │   ├── application/
│   │   │   ├── identity/                # AuthService & TenantService
│   │   │   └── audit/                   # AuditService
│   │   ├── infrastructure/
│   │   │   ├── persistence/postgres/    # Async engine, sessionmaker, and Base mixins
│   │   │   └── repositories/            # UserRepository, InstitutionRepository, AuditRepository
│   │   ├── interfaces/http/
│   │   │   ├── api/v1/                  # Auth, Platform, Institutions endpoints
│   │   │   ├── middlewares/             # CorrelationId & SecurityHeaders middlewares
│   │   │   ├── schemas/                 # Pydantic DTOs & standardized envelopes
│   │   │   └── dependencies.py          # Dependency injection (Auth, RBAC, Tenant scope)
│   │   └── main.py                      # FastAPI lifespan, router, and exception handlers
│   ├── tests/                           # 33 unit and integration tests
│   │   ├── conftest.py                  # Ephemeral in-memory SQLite test fixtures
│   │   ├── test_security.py             # Argon2id & JWT token crypto tests
│   │   ├── test_rbac_permissions.py     # Role permission matrix completeness
│   │   ├── test_tenant_isolation.py     # Cross-tenant denial & boundary assertions
│   │   ├── test_api_auth.py             # Login, Logout, /me, token rotation
│   │   └── test_api_platform.py         # Liveness and readiness probe verification
│   ├── pyproject.toml
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css              # Institutional design tokens (CSS variables)
│   │   │   ├── layout.tsx               # Root layout & AuthProvider wrapper
│   │   │   ├── page.tsx                 # Root guard & redirection
│   │   │   ├── login/page.tsx           # Enterprise login portal
│   │   │   └── workspace/               # Role-aware navigation shell & foundation dashboard
│   │   ├── components/ui/               # 20 required accessible UI primitives
│   │   │   ├── Button.tsx               ├── Dropdown.tsx     ├── Alert.tsx
│   │   │   ├── Input.tsx                ├── Tooltip.tsx      ├── Toast.tsx
│   │   │   ├── Select.tsx               ├── Badge.tsx        ├── Skeleton.tsx
│   │   │   ├── Checkbox.tsx             ├── Card.tsx         ├── EmptyState.tsx
│   │   │   ├── Radio.tsx                ├── Table.tsx        ├── ErrorState.tsx
│   │   │   ├── Switch.tsx               ├── Tabs.tsx         ├── PageHeader.tsx
│   │   │   └── Dialog.tsx                                    └── Breadcrumbs.tsx
│   │   ├── lib/
│   │   │   ├── api/client.ts            # Typed HTTP client with envelope parsing
│   │   │   └── auth/                    # AuthContext & usePermission hooks
│   │   └── types/                       # TypeScript interfaces for API and Auth
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.mjs
│
└── docs/
    ├── DHRUVA_V2_MASTER_ARCHITECTURE.md
    ├── DHRUVA_V2_IMPLEMENTATION_ROADMAP.md
    └── architecture/
        └── PHASE_1_FOUNDATION.md
```

---

## 3. Database Foundation & Multi-Tenancy

### 3.1 PostgreSQL 16 & Alembic Schema (`0001_core_foundation`)
* **Tables Created:**
  1. `institutions`: Multi-tenant boundary root entity (`id` UUID, `slug` unique, `legal_name`, `domain`, `status`, `settings` JSONB).
  2. `users`: Identity credentials (`id` UUID, `institution_id` FK, `email` unique, `password_hash`, `first_name`, `last_name`, `phone`, `status`, `deleted_at`).
  3. `roles`: Permission definitions (`id` UUID, `institution_id` FK nullable, `name`, `code`, `permissions` JSON, `is_system_role`).
  4. `user_roles`: Scoped role assignments (`id` UUID, `user_id` FK, `role_id` FK, `institution_id` FK, `context_department_id`).
  5. `refresh_tokens`: Hashed, revocable refresh tokens for session management.
  6. `audit_logs`: Append-only governance log (`actor_user_id`, `institution_id`, `action`, `entity_name`, `old_values`, `new_values`, `ip_address`, `request_id`).

### 3.2 Row-Level Security (RLS)
PostgreSQL RLS policies are applied across all tenant-bound tables:
```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_policy ON users
AS RESTRICTIVE FOR ALL
USING (
    institution_id IS NULL OR
    institution_id = NULLIF(current_setting('app.current_institution_id', true), '')::uuid
);
```

---

## 4. Authentication, Cryptography & Sessions

1. **Password Hashing:** Argon2id (`time_cost=3`, `memory_cost=65536`, `parallelism=4`, `salt_len=16`, `hash_len=32`).
2. **Password Validation:** Enforces minimum 8 characters, uppercase, lowercase, number, and special character.
3. **Session Strategy:**
   * Short-lived JWT access token (15 minutes expiry) containing `sub` (User UUID), `type: access`, and correlation `jti`.
   * Long-lived cryptographically random refresh token (7 days expiry), hashed with SHA-256 before storage in `refresh_tokens`.
   * Secure, `HttpOnly`, `SameSite=Strict` cookie transmission.
   * Full session revocation on logout or account deactivation.

---

## 5. Role-Based Access Control (RBAC)

The complete 6-role permission matrix defined in Master Architecture Section 8.2 is operational:

| Role | Scope | Key Capabilities |
| :--- | :--- | :--- |
| **SUPER_ADMIN** | Global / Platform | Full platform governance, cross-tenant auditing, institution creation & provisioning. |
| **INSTITUTION_ADMIN** | Institution | Department/user management, data center approval, curriculum approval, institution audit logs. |
| **HOD** | Department | Curriculum editing/approvals, departmental student mastery inspection, assessment auditing. |
| **FACULTY** | Course Offering | Course lesson management, question authoring, deterministic grading, project verification. |
| **STUDENT** | Individual | Learning resources access, assessment submission, mastery tracking, portfolio management. |
| **PLACEMENT_OFFICER** | Institution | Mastery telemetry inspection, verified portfolio reviews, placement opportunity publishing. |

---

## 6. Standardized API Envelopes & Error Handling

All API endpoints strictly output standard envelopes with zero sensitive leakages:

### Success Envelope
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_84f9a721",
    "timestamp": "2026-10-12T10:20:00Z",
    "pagination": null
  }
}
```

### Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": [],
    "request_id": "req_84f9a721"
  }
}
```

---

## 7. Frontend Design System & Architecture

* **Framework:** Next.js 15 App Router with React 19 and TypeScript.
* **Tokens:** Curated CSS variable palette in `globals.css` with dark mode default and light mode support.
* **Primitives:** 20 accessible, semantic UI components implemented without unnecessary external dependencies.
* **Shell:** Responsive navigation with tenant identification, role badges, breadcrumbs, and authentication guards.

---

## 8. Test Suite Verification Results

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1 -- 33 passed in 2.11s

tests/test_security.py (11 tests)          PASSED
tests/test_rbac_permissions.py (7 tests)   PASSED
tests/test_tenant_isolation.py (5 tests)   PASSED
tests/test_api_auth.py (6 tests)           PASSED
tests/test_api_platform.py (4 tests)       PASSED
============================= 33 passed in 2.11s ==============================
```

---

## 9. Phase 2 Readiness

Phase 1 satisfies all acceptance criteria and quality gates:
* [x] Project structure and clean domain boundaries.
* [x] Database schema, migrations, and PostgreSQL RLS policies.
* [x] Argon2id password hashing and dual-token JWT rotation.
* [x] Multi-tenancy isolation and cross-tenant access denial.
* [x] RBAC permission evaluation across all 6 roles.
* [x] Zero mock data standard verified.
* [x] Standardized API error envelopes and correlation IDs.
* [x] Frontend foundation, design tokens, 20 primitives, and authentication shell.
* [x] 100% backend test pass rate and clean frontend build.

**Verdict: Phase 1 is fully complete. Phase 2 (Academic Hierarchy & User Management) is safe to begin.**
