# Checklist — Pricing + billing

| | |
|---|---|
| Purpose | Track per-broadcast costs and generate tenant invoices |
| FSD | [`../../fsd/pricing_billing.md`](../../fsd/pricing_billing.md) |
| Phase | Phase 2 (depends on pricing-model decision) |
| Language | English source — KO at [`../ko/pricing_billing.md`](../ko/pricing_billing.md) |

---

## Tech stack (at a glance)

- Own Python — cost aggregator
- **Stripe Invoicing** (managed) or **Toss Payments** (KR-native)
- Reads from `observability.md` + `audit_log.md`
- **Infra**: cron job on backend host

Full table: [`../../fsd/pricing_billing.md`](../../fsd/pricing_billing.md) §2

---

## §1. Prerequisites

- [ ] [`../../fsd/pricing_billing.md`](../../fsd/pricing_billing.md) read
- [ ] **Pricing model locked** (founder decision per PRD §8 OQ #5)
- [ ] Stripe or Toss account set up
- [ ] Webhook endpoint configured

## §2. Cost attribution

- [ ] Daily cron aggregates per-broadcast costs from observability + audit log
- [ ] Per-tenant rollup
- [ ] Manual reconciliation with cloud bills (target: ±5% accuracy)

## §3. Invoice generation

- [ ] Monthly cron emits invoices via Stripe/Toss
- [ ] Email delivery to tenant billing contact
- [ ] Payment webhook updates `billing_state`

## §4. Status board

| Step | Status |
|---|---|
| §1 Prerequisites (incl. pricing decision) | ⬜ |
| §2 Cost attribution | ⬜ |
| §3 Invoice generation | ⬜ |

## §5. Troubleshooting

| Issue | Response |
|---|---|
| Cost attribution drift > 5% | reconcile per-line costs; check missing GPU-hour tracking |
| Invoice email bounces | maintain backup billing contact |
| Payment webhook misses | implement webhook retry + manual reconciliation script |
