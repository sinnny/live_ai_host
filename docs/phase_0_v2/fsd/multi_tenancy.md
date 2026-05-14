# Function Spec — Multi-tenancy

| | |
|---|---|
| Status | Spec v1 (Phase 2) |
| Phase | Phase 2 |
| Component | Tenant isolation strategy — Postgres RLS + per-tenant Qdrant collections + RBAC |
| Source documents | [`../../prd.md`](../../prd.md) §2, §5.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

PRD §2 defines two tenant types (brand + platform). This FSD specifies how tenant data is isolated across the stack at the row + collection + auth level.

---

## 2. Technology stack

| Stage | Tool | License |
|---|---|---|
| Row-level isolation | Postgres RLS | PostgreSQL |
| Vector isolation | Qdrant per-tenant collection | Apache 2.0 |
| Auth | OAuth + JWT (Naver/Kakao SSO for platform-tier) | – |
| Authorization | role-based via Postgres `current_setting('app.user_role')` | – |

---

## 3. Isolation layers

### 3.1 Database (Postgres)

- Every multi-tenant table has `tenant_id` column.
- RLS policy: `USING (tenant_id = current_setting('app.tenant_id')::uuid)`.
- Connection-pool session sets `app.tenant_id` per request.

### 3.2 Vector store (Qdrant)

- Per-broadcast collection: `broadcast_<broadcast_id>_products`.
- Per-tenant doesn't need separate Qdrant collections at MVP — broadcast scope is sufficient.

### 3.3 Object storage

- S3 path prefix: `<tenant_id>/...` enforced by IAM policy.

### 3.4 Auth / RBAC

| Role | Capabilities |
|---|---|
| platform_admin | manage sub-accounts, allocate mascots, view all tenant data |
| account_admin | manage own users, broadcasts, products |
| broadcast_author | create/edit/launch broadcasts |
| broadcast_reviewer | approve broadcasts |
| viewer_only | read-only analytics |

---

## 4. Platform tenancy specifics

A platform tenant (e.g. Naver 쇼핑라이브) has child brand tenants. Architecturally: same `tenant` table, with `parent_tenant_id` column for child rows.

Platform admin role can `current_setting('app.tenant_id')` to any child tenant's ID for cross-child operations.

---

## 5. Quality criteria

| Criterion | Test |
|---|---|
| Tenant A cannot read Tenant B data via Postgres | RLS bypass test |
| Tenant A cannot read Tenant B's Qdrant data | API access test |
| Tenant A cannot read Tenant B's S3 assets | IAM test |
| Platform admin can see child tenants only | role test |

---

## 6. References

- [`../../prd.md`](../../prd.md) §2
- [`data_model.md`](data_model.md) — table schema
- [`storage.md`](storage.md) — S3 isolation
- Postgres RLS docs
