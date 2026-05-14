# Checklist — Data model (Postgres)

| | |
|---|---|
| Purpose | Implement Postgres schema with Alembic migrations |
| FSD | [`../../fsd/data_model.md`](../../fsd/data_model.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/data_model.md`](../ko/data_model.md) |

---

## Tech stack (at a glance)

- **Postgres 16+** (PostgreSQL)
- **SQLAlchemy 2.x** (MIT) — ORM
- **Alembic** (MIT) — migrations
- **pgbouncer** (BSD-3) — connection pooling
- **Infra**: managed Postgres (AWS RDS / Render / Supabase) or self-hosted

Full table: [`../../fsd/data_model.md`](../../fsd/data_model.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/data_model.md`](../../fsd/data_model.md) read
- [ ] [`multi_tenancy.md`](multi_tenancy.md) read (RLS strategy)
- [ ] Postgres 16+ instance provisioned
- [ ] Database connection string in env

## §2. Schema implementation

- [ ] Define SQLAlchemy models per FSD §3
- [ ] Generate Alembic baseline migration: `alembic revision --autogenerate -m "baseline"`
- [ ] Review SQL — verify indexes per FSD §4
- [ ] Apply: `alembic upgrade head`

## §3. RLS setup

- [ ] Enable RLS on every multi-tenant table
- [ ] Add RLS policy using `app.tenant_id` setting (per [`multi_tenancy.md`](multi_tenancy.md) §3.1)
- [ ] Test: connect as tenant A, attempt to read tenant B row → blocked

## §4. Seed data

- [ ] Insert system mascot (Daramzzi)
- [ ] Insert test tenants for dev
- [ ] Insert test products

## §5. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Schema | ⬜ |
| §3 RLS | ⬜ |
| §4 Seed | ⬜ |

## §6. Troubleshooting

| Issue | Response |
|---|---|
| Migration conflict | resolve manually; never auto-merge revisions |
| RLS not enforced | check `current_setting('app.tenant_id')` is set on every connection |
| Slow query on broadcast list | check index on `(tenant_id, scheduled_start)` |
