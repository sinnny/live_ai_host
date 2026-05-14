# Function Spec — `make_mascot_v2` (seller self-service mascot creation)

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — speculative; requires post-MVP customer data) |
| Phase | Phase 3 |
| Component | Generalization of `make_mascot.md` exposed as a seller-facing self-service workflow |
| Source documents | [`../../prd.md`](../../prd.md) §1.4, §7 (post-MVP) |
| Open dependencies | Customer feedback after first 10 broadcasts on whether per-seller mascot is wanted; legal review on AI-generated character IP ownership when seller defines the brief |
| Last updated | 2026-05-13 |

---

## 1. Purpose

After MVP launch, sellers may want their own mascot rather than using the system-owned Daramzzi. This FSD generalizes the existing `make_mascot.md` pipeline into a parameterized API + seller-facing UI flow.

---

## 2. Tech stack

Inherits from [`make_mascot.md`](make_mascot.md) §2. Adds:

- Web UI (Next.js, same stack as [`operator_dashboard.md`](operator_dashboard.md))
- Tenant-scoped job queue
- Approval-gate workflow (seller reviews seed before LoRA trains)

---

## 3. Key changes from base FSD

- `daramzzi_config.yaml` becomes parameterized: seller submits `{character_brief, base_visual_descriptor, layer_count_overrides}` via UI.
- Bible markdown becomes optional; if absent, Claude generates a minimal bible from brief.
- Approval gates surface to seller UI (instead of founder CLI).
- Output goes to tenant-scoped storage prefix.

---

## 4. Open design questions

- Per-seller cost cap (mascot generation is ~$5-15; do sellers pay separately or bundled into broadcast pricing?)
- IP ownership: who owns the seller-defined mascot? Per [`compliance_runbook.md`](compliance_runbook.md) — legal review required.
- Quality bar: seller-defined mascots may not meet brand-cohesion standards we'd enforce ourselves. Do we gate publication on review?

---

## 5. References

- [`make_mascot.md`](make_mascot.md) — base pipeline
- [`../../prd.md`](../../prd.md) §1.4, §7
- [`operator_dashboard.md`](operator_dashboard.md) — UI stack
