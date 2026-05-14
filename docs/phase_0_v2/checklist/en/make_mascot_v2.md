# Checklist — `make_mascot_v2` (seller self-service)

| | |
|---|---|
| FSD | [`../../fsd/make_mascot_v2.md`](../../fsd/make_mascot_v2.md) |
| Phase | Phase 3 (speculative) |
| Language | English source — KO at [`../ko/make_mascot_v2.md`](../ko/make_mascot_v2.md) |

---

## Tech stack
- Inherits from [`make_mascot.md`](make_mascot.md) + Next.js UI + tenant-scoped queue

---

## §1. Prerequisites (pre-activation)
- [ ] First 10 broadcasts on system mascot complete
- [ ] Customer feedback shows demand for per-seller mascots
- [ ] Legal: AI-generated character IP ownership clarified
- [ ] Cost model: per-mascot bill vs bundled

## §2. Implementation (when activated)
- [ ] Generalize `make_mascot` config — parameterize from CLI to API input
- [ ] Build seller-facing UI (mascot wizard)
- [ ] Approval-gate workflow surfaces to seller dashboard
- [ ] Tenant-scoped storage prefixes

## §3. Quality gate
- [ ] Brand-cohesion review (manual)
- [ ] Publication gate before mascot usable in live broadcasts

## §4. Troubleshooting
- Seller-defined brief produces off-brand mascot → coach via brief examples; manual override
