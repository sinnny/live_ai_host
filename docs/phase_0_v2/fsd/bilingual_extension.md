# Function Spec — Bilingual extension (EN / JP)

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — pulled back to v2 product release) |
| Phase | Phase 3 |
| Component | Add English + Japanese support across runtime + assets |
| Source documents | [`../../prd.md`](../../prd.md) §1.3, §1.4 |
| Open dependencies | Market validation (are KR-first sellers asking for EN/JP audiences?) |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Per PRD §1.3, v1 launches Korean-only. EN/JP deferred. This FSD documents what changes when bilingual is added.

---

## 2. Affected components

| Component | Change |
|---|---|
| [`tts.md`](tts.md), [`tts_streaming.md`](tts_streaming.md) | Multi-language voice refs; language tag per segment |
| [`llm_host.md`](llm_host.md) | Persona prompts for EN + JP (cultural re-bible per [`../../characters/daramzzi.md`](../../characters/daramzzi.md) §8 OQ #6) |
| [`llm_director.md`](llm_director.md), [`llm_moderator.md`](llm_moderator.md) | Language-aware rule sets |
| [`rag.md`](rag.md) | BGE-M3 already multilingual; KURE remains KR-primary |
| [`compliance_pre_check.md`](compliance_pre_check.md) | Per-region rule sets (US FTC, Japan 景品表示法) |
| Script schema | `language` field already supports "en", "ja" — runtime needs to honor it |

---

## 3. Cultural adaptation

Bible §8 OQ #6 notes: the "사장님" workplace tension is culturally specific. EN/JP versions need re-bible, not direct translation.

---

## 4. Open questions

- Market priority: EN first (Hedra/US influencer overlap) or JP first (VTuber-adjacent audience)?
- Single mascot localized vs separate mascots per language?
- Compliance regime: which jurisdictions matter?

---

## 5. References

- [`../../prd.md`](../../prd.md) §1.3
- [`../../characters/daramzzi.md`](../../characters/daramzzi.md) §8 OQ #6
