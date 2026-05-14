# Checklist — Multi-tenancy

| | |
|---|---|
| Purpose | Enforce tenant isolation at DB, vector DB, storage, and auth layers |
| FSD | [`../../fsd/multi_tenancy.md`](../../fsd/multi_tenancy.md) |
| Phase | Phase 2 |
| Language | English source — KO at [`../ko/multi_tenancy.md`](../ko/multi_tenancy.md) |

---

## Tech stack (at a glance)

- **Postgres RLS** — row-level isolation
- **Qdrant** per-broadcast collections (already)
- **S3 IAM** — bucket prefix isolation
- **OAuth + JWT** — auth with role claim
- **Infra**: same as `data_model.md` and `storage.md`

Full table: [`../../fsd/multi_tenancy.md`](../../fsd/multi_tenancy.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/multi_tenancy.md`](../../fsd/multi_tenancy.md) read
- [ ] [`data_model.md`](data_model.md) DB ready
- [ ] [`storage.md`](storage.md) S3 ready

## §2. Postgres RLS

- [ ] RLS enabled per [`data_model.md`](data_model.md) checklist §3
- [ ] Cross-tenant read test passes (tenant A can't read tenant B)

## §3. Qdrant isolation

- [ ] Per-broadcast collection naming verified (`broadcast_<id>_products`)
- [ ] Cross-broadcast query test: querying wrong collection returns empty

## §4. S3 IAM

- [ ] Per-tenant prefix IAM policy applied
- [ ] Cross-tenant access test: tenant A can't read `s3://.../tenant_b/...`

## §5. Auth + RBAC

- [ ] JWT contains `tenant_id` + `role` claims
- [ ] Role-permission matrix tested per FSD §3.4

## §6. Status board

| Step | Status |
|---|---|
| §1 Prerequisites | ⬜ |
| §2 Postgres RLS | ⬜ |
| §3 Qdrant isolation | ⬜ |
| §4 S3 IAM | ⬜ |
| §5 Auth + RBAC | ⬜ |

## §7. Troubleshooting

| Issue | Response |
|---|---|
| RLS bypass succeeded | check policy enabled + connection sets setting |
| Cross-tenant Qdrant leak | check collection naming consistent |
| JWT missing claim | check IDP custom claim configuration |
