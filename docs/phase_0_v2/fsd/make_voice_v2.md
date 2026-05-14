# Function Spec — `make_voice_v2` (per-seller voice cloning)

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — speculative; requires legal framework) |
| Phase | Phase 3 |
| Component | Per-seller voice cloning workflow with consent + legal framework |
| Source documents | [`../../prd.md`](../../prd.md) §7 |
| Open dependencies | Korean PIPA (개인정보보호법) consultation on biometric voice data; consent workflow design |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Allow sellers to clone a specific human voice (e.g. a brand spokesperson) into the system. Distinct from `make_voice.md` v1, which generates synthetic voices only.

---

## 2. Tech stack

- **CosyVoice 2** voice cloning (Apache 2.0) — same as base FSD
- Audio uploader (Next.js)
- Consent capture (signed agreement, archived per PIPA)
- Quality gate (manual review of cloned output)

---

## 3. Workflow

1. Seller uploads ~30 sec of clean voice recording + signed consent.
2. System extracts voice reference; clones via CosyVoice 2.
3. Generates 5 test samples; seller approves.
4. Quality gate: founder/admin reviews for hallucinations.
5. Voice committed to tenant scope.

---

## 4. Legal requirements (TBD via counsel)

- Korean PIPA: voice is biometric data, requires explicit consent + retention policy.
- Right to delete: must support 1-day deletion of voice profile + derived audio.
- Liability: who is responsible if cloned voice misrepresents the original speaker? Indemnification clauses in seller contract.

---

## 5. References

- [`make_voice.md`](make_voice.md) — base FSD
- [`tts.md`](tts.md) — consumer
- [`compliance_runbook.md`](compliance_runbook.md)
- Korean PIPA + biometric data guidelines
