# Function Spec — Data model (Postgres)

| | |
|---|---|
| Status | Spec v1 (Phase 2) |
| Phase | Phase 2 |
| Component | Primary data model — tenants, accounts, broadcasts, beats, products, mascots, voices |
| Source documents | [`../../prd.md`](../../prd.md) §5.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Defines the relational data model for the MVP. High-cardinality event log (per-line audit) lives in ClickHouse — see [`audit_log.md`](audit_log.md).

---

## 2. Technology stack

| Stage | Tool | License |
|---|---|---|
| Primary DB | **Postgres 16+** | PostgreSQL |
| Migrations | Alembic | MIT |
| ORM | SQLAlchemy 2.x | MIT |
| Connection pooling | pgbouncer | BSD-3 |

---

## 3. Tables (essential)

```
tenant
  id, name, tier (brand|platform), created_at, billing_plan_id, ...

account
  id, tenant_id (fk), email, role (admin|author|reviewer|viewer), sso_provider, ...

mascot
  id, tenant_id (fk, nullable for system-owned), name_display, character_bible_path,
  atlas_path, lora_path, voice_id (fk), created_at, version, ...

voice
  id, tenant_id (fk, nullable), name, ref_wav_path, ref_text, created_at, ...

product
  id, tenant_id (fk), name_kr, name_en, price, currency, weight_g, origin,
  ingredients (jsonb), is_hero (bool), image_urls (jsonb), pdp_url, ...

broadcast
  id, tenant_id (fk), title, mascot_id (fk), voice_id (fk),
  scheduled_start, scheduled_end, actual_start, actual_end,
  status (draft|scheduled|live|done|aborted),
  rtmp_dest_url, ...

broadcast_beat
  id, broadcast_id (fk), beat_idx, mode (FULL_MASCOT|PIP|SCRIPTED_CLIP),
  product_id (fk, nullable), scripted_clip_path, duration_sec, ...

broadcast_product (junction)
  broadcast_id, product_id, display_order, is_hero

audit_decision (Phase 1+ summary; full log in ClickHouse)
  broadcast_id, decision_id, timestamp, agent (director|moderator|host),
  verdict, reason
```

---

## 4. Indexing

- `broadcast(tenant_id, scheduled_start)` — calendar queries
- `product(tenant_id, is_hero)` — hero filter
- `audit_decision(broadcast_id, timestamp)` — replay queries

---

## 5. Multi-tenancy isolation

Decided in [`multi_tenancy.md`](multi_tenancy.md). v1 default: row-level tenancy with `tenant_id` foreign key on every multi-tenant table + RLS policies in Postgres.

---

## 6. Migrations strategy

- Alembic, one revision per change
- All migrations forward-only after MVP launch
- Pre-MVP: free to squash for cleanliness

---

## 7. References

- [`../../prd.md`](../../prd.md) §5.4
- [`multi_tenancy.md`](multi_tenancy.md) — isolation strategy
- [`audit_log.md`](audit_log.md) — high-cardinality event store
