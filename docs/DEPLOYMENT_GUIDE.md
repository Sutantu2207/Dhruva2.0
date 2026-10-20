# DHRUVA.AI (V2) — PRODUCTION DEPLOYMENT & OPERATIONS BLUEPRINT

> **Document Version:** 2.0.0 (Phase 10 Hardened)  
> **Target Cloud Platforms:** Render (Backend + Database + Cache) & Vercel (Frontend Next.js 15)  
> **Vendor Isolation:** Standard vendor-neutral Docker containerization. **Zero Railway dependencies.**  
> **Database:** Managed PostgreSQL 16 with `pgvector` & `uuid-ossp` extensions.

---

## 1. High-Level Architecture & Component Topology

```mermaid
flowchart LR
    subgraph Client ["Client Devices (Students / Faculty / Admins)"]
        Browser["Modern Web Browser / Mobile (WCAG 2.1 AA)"]
    end

    subgraph Edge ["Global Edge Tier (Vercel)"]
        VercelCDN["Vercel Edge Network / Asset Cache"]
        NextApp["Next.js 15 SSR & Static Shell (/workspace)"]
    end

    subgraph Core ["Application Tier (Render)"]
        WAF["Render Managed HTTPS / Proxy"]
        Backend["FastAPI ASGI App (2 Uvicorn Workers / Non-Root UID 10001)"]
        Redis["Managed Redis 7 (Rate Limiting & Token Blacklist)"]
    end

    subgraph Persistence ["Persistence Tier (PostgreSQL 16)"]
        Postgres["Managed PostgreSQL 16 (pgvector / RLS Enabled)"]
    end

    Browser -->|HTTPS / WSS| VercelCDN
    VercelCDN --> NextApp
    NextApp -->|API Requests with JWT / Credentials| WAF
    WAF --> Backend
    Backend -->|Async Sessions / Connection Pool| Postgres
    Backend -->|Token Buckets / Sessions| Redis
```

---

## 2. Infrastructure Inventory & Provisioning

### 2.1 Managed Services (Render)
Render is defined via `render.yaml` infrastructure-as-code at the repository root.

| Service Name | Type | Environment | Plan | Health Check Path | Region |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `dhruva-backend` | Web Service | Docker (`backend/Dockerfile`) | Standard | `/health/live` | Oregon (`us-west`) |
| `dhruva-postgres` | Managed Database | PostgreSQL 16 | Standard | Managed | Oregon (`us-west`) |
| `dhruva-redis` | Managed Cache | Redis 7 | Starter | Managed (Private) | Oregon (`us-west`) |

### 2.2 Frontend Edge Hosting (Vercel)
Configured via `frontend/vercel.json` and Next.js 15 App Router.

- **Framework Preset**: Next.js
- **Build Command**: `next build`
- **Output Directory**: `.next`
- **Node.js Version**: 20.x or 22.x LTS
- **Security Headers**: HSTS (63072000s), Frame-Options (DENY), Content-Type-Options (nosniff), Referrer-Policy, Strict CSP.

---

## 3. Environment Variable Specifications

> [!CAUTION]
> **Zero Secret Leaks**: Never commit `.env` or production credentials to git. Set secrets exclusively via the Render and Vercel management dashboards.

### 3.1 Backend Service Environment Variables (`dhruva-backend`)

| Variable Name | Required | Example Safe Value | Purpose |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | Yes | `production` | Enables fail-fast checks, strict security headers, and disables Swagger UI. |
| `DEBUG` | Yes | `false` | Disables debug mode and tracebacks. Enforced by fail-fast validator. |
| `SERVICE_NAME` | Yes | `dhruva-backend` | Structured JSON log tag and OpenTelemetry service identifier. |
| `PORT` | Yes | `8000` | Port for ASGI Uvicorn binding inside container. |
| `SECRET_KEY` | Yes | *(Min 32 characters random hexadecimal)* | Cryptographic HMAC signing key for JWT session access tokens. |
| `JWT_ALGORITHM` | Yes | `HS256` | Token signature algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | `15` | Short-lived access token expiry. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Yes | `7` | Refresh token lifecycle. |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://dhruva_admin:...@dpg-...:5432/dhruva_db` | Async SQLAlchemy 2.0 PostgreSQL connection string. |
| `DATABASE_POOL_SIZE` | No | `15` | Persistent connection pool size per worker. |
| `DATABASE_MAX_OVERFLOW` | No | `25` | Burst connection capacity. |
| `REDIS_ENABLED` | Yes | `true` | Enables token-bucket rate limiting and session invalidation. |
| `REDIS_URL` | Yes | `redis://red-...:6379` | Internal Render private Redis connection URL. |
| `CORS_ORIGINS` | Yes | `https://dhruva.vercel.app,https://*.vercel.app` | Allowed origins for cross-site browser requests. |
| `COOKIE_SECURE` | Yes | `true` | Mandates `Secure` flag on all cookies (HTTPS only). |
| `COOKIE_SAMESITE` | Yes | `none` | Cross-site cookie posture between Vercel and Render. |
| `ARGON2_TIME_COST` | Yes | `3` | OWASP-recommended password hash time cost. |
| `ARGON2_MEMORY_COST` | Yes | `65536` | 64 MB memory cost per password verification. |
| `ARGON2_PARALLELISM` | Yes | `4` | Parallel threads per hash evaluation. |

### 3.2 Frontend Edge Environment Variables (Vercel)

| Variable Name | Required | Example Safe Value | Purpose |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Yes | `https://dhruva-backend.onrender.com/api/v1` | Public API gateway base URL. |
| `NEXT_PUBLIC_APP_ENV` | Yes | `production` | Environment flag for client error reporting. |

---

## 4. Database Migrations & Startup Execution Order

### 4.1 Deployment Sequence
When rolling out a new release, execute operations in this exact order:

```mermaid
sequenceDiagram
    autonumber
    participant CI as CI Pipeline / Release Engineer
    participant DB as Managed PostgreSQL 16
    participant Render as Render API (dhruva-backend)
    participant Vercel as Vercel Edge (dhruva-frontend)

    CI->>DB: 1. Run Alembic Migrations (alembic upgrade head)
    Note over DB: Applies 0001 through 0009 schema changes<br/>with atomic transactions and RLS policies
    CI->>Render: 2. Deploy Backend Docker Image
    Render->>Render: 3. Healthcheck Verification (/health/live)
    Render-->>CI: Backend Healthy (HTTP 200)
    CI->>Vercel: 4. Deploy Frontend Edge Bundle (next build)
    Vercel-->>CI: Frontend Live on Global CDN
    CI->>Render: 5. Execute Automated Smoke Test Suite
```

### 4.2 Migration Execution
Run migrations from a one-off task or CI job targeting the production database:

```bash
# Set production DATABASE_URL
export DATABASE_URL="postgresql+asyncpg://dhruva_admin:<SECURE_PASSWORD>@<HOST>:5432/dhruva_db"
export ENVIRONMENT="production"
export SECRET_KEY="<PROD_SECRET_KEY_MIN_32_CHARS>"

# Execute linear migration chain to latest revision
alembic upgrade head
```

### 4.3 Database Rollback Procedure
If a migration or deployment encounters an irrecoverable issue:

```bash
# Downgrade by 1 revision
alembic downgrade -1

# Or downgrade to specific stable target
alembic downgrade 0008_interventions_notifications_analytics
```

---

## 5. Backup, Disaster Recovery & High Availability

### 5.1 Continuous Archiving & Point-in-Time Recovery (PITR)
- **Continuous WAL Archiving**: Managed PostgreSQL continuously streams Write-Ahead Logs (WAL) to durable object storage.
- **Recovery Point Objective (RPO)**: **< 15 minutes**. In the event of a catastrophic regional failure, data loss is strictly bounded to the latest uncommitted WAL chunk.
- **Recovery Time Objective (RTO)**: **< 1 hour**. Automated failover promotes standby replicas within minutes; manual disaster recovery executes container rebuilds within 60 minutes.

### 5.2 Manual Backup Creation
Prior to applying major institutional schema migrations:

```bash
# Create immediate point-in-time snapshot
pg_dump -h <HOST> -U dhruva_admin -d dhruva_db -F c -b -v -f "dhruva_backup_$(date +%Y%m%d_%H%M%S).dump"
```

### 5.3 Backup Restore Drill
```bash
# Verify backup integrity into isolated staging instance
pg_restore -h <STAGING_HOST> -U dhruva_admin -d dhruva_staging_db -v "dhruva_backup_latest.dump"
```

---

## 6. Post-Deployment Smoke Test & Verification Checklist

Immediately following deployment to Render and Vercel, execute the following verification checklist:

- [ ] **Liveness Probe**: `GET https://dhruva-backend.onrender.com/health/live` returns `{"success": true, "data": {"status": "UP"}}`.
- [ ] **Readiness Probe**: `GET https://dhruva-backend.onrender.com/health/ready` returns `{"success": true, "data": {"status": "READY"}}`.
- [ ] **Platform Health**: `GET https://dhruva-backend.onrender.com/api/v1/platform/health` returns status `UP` with database latency < 50ms.
- [ ] **Security Headers**: Verify `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, and `Referrer-Policy` are present on all API and frontend responses.
- [ ] **CORS Preflight**: Verify `OPTIONS /api/v1/auth/login` returns `Access-Control-Allow-Origin: https://dhruva.vercel.app` with `Access-Control-Allow-Credentials: true`.
- [ ] **Tenant Isolation Guard**: Attempt cross-tenant query with tenant-A credentials querying tenant-B slug; verify server responds with `403 Permission Denied` or `404 Resource Not Found`.
- [ ] **Frontend Login Journey**: Navigate to `https://dhruva.vercel.app/login`, perform sign-in with staff credentials, confirm workspace loads and top header displays tenant badge.
- [ ] **AI Gateway Pre-flight**: Open `/workspace/ai`, send test query containing student roll number, verify client redaction preview appears and answer includes verified syllabus citations.
- [ ] **Accessibility Check**: Navigate full workspace using only keyboard (`Tab`, `Shift+Tab`, `Enter`, `Escape`), verify visible focus ring, and verify skip link functions.

---

## 7. Known Platform-Specific Considerations & Manual Steps

1. **Local Docker CLI Limitation**: Docker CLI is not installed on this local Windows development machine. The multi-stage `backend/Dockerfile` has been designed and verified using standard Docker best practices (minimal `python:3.12-slim` base, unprivileged user `UID 10001`, explicit healthchecks), but container builds occur in the Render CI/CD pipeline upon git commit.
2. **PostgreSQL pgvector Extension**: In Render Managed PostgreSQL, run `CREATE EXTENSION IF NOT EXISTS vector;` and `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";` via the Render database console prior to first migration run.
3. **Vercel Custom Domain DNS**: When binding an institutional domain (e.g. `learn.iitb.ac.in`), configure CNAME pointing to `cname.vercel-dns.com` and generate Let's Encrypt SSL certificate through Vercel Dashboard.
