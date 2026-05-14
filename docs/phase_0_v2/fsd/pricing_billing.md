# Function Spec — Pricing + billing

| | |
|---|---|
| Status | Spec v1 (Phase 2 — pricing model not yet locked) |
| Phase | Phase 2 |
| Component | Per-broadcast cost attribution + tenant invoicing |
| Source documents | [`../../prd.md`](../../prd.md) §5 (TBD section), §8 OQ #5 |
| Open dependencies | Pricing model decision (founder + customer development in Sprint 4) |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Attribute cost (LLM tokens, GPU time, storage, bandwidth) to broadcasts and tenants; generate invoices.

---

## 2. Open: pricing model

Per PRD §8 OQ #5, the pricing model is not yet locked. Candidates:

| Model | Pros | Cons |
|---|---|---|
| Per-broadcast flat | predictable for seller | doesn't capture variable costs |
| Per-broadcast + per-comment | tracks engagement | complex |
| Per-minute streamed | aligns with broadcast length | low for short broadcasts |
| Monthly subscription | predictable revenue | low engagement = high cost-per-broadcast |

**Locked after customer development in Sprint 4.** This FSD currently assumes per-broadcast flat fee + bandwidth overage as the default until decided.

---

## 3. Technology stack

| Stage | Tool | License |
|---|---|---|
| Cost calculation | own Python; reads from `observability.md` token counters + cloud bills | – |
| Invoice generation | Stripe Invoicing (managed) or Toss Payments (KR-native) | – |
| Payment | Stripe or Toss | – |

---

## 4. Cost attribution sources

Per broadcast:
- LLM tokens (from `audit_log.md` event sums × per-model rate)
- GPU hours (per renderer/TTS GPU time tracked in observability)
- Bandwidth (RTMP egress from cloud monitoring)
- Storage (recorded broadcasts in `storage.md`)

---

## 5. Invoicing flow

1. Cron daily: aggregate previous-day broadcast costs per tenant.
2. Monthly: generate invoice for tenant with line items.
3. Payment via Stripe/Toss; webhook updates tenant `billing_state`.

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Cost attribution accuracy | ± 5% vs actual cloud bills |
| Invoice latency | ≤ 1 day after period close |

---

## 7. References

- [`../../prd.md`](../../prd.md) §5, §8 OQ #5
- [`observability.md`](observability.md) — cost metric source
- [`audit_log.md`](audit_log.md) — token usage source
- Stripe / Toss API docs
