# Checklist — Bilingual extension (EN / JP)

| | |
|---|---|
| FSD | [`../../fsd/bilingual_extension.md`](../../fsd/bilingual_extension.md) |
| Phase | Phase 3 — v2 product release |
| Language | English source — KO at [`../ko/bilingual_extension.md`](../ko/bilingual_extension.md) |

---

## Tech stack
- Language-aware TTS / LLM / RAG / compliance per FSD §2

---

## §1. Prerequisites (pre-activation)
- [ ] Market validation: are sellers asking for EN or JP audiences?
- [ ] Priority decision: EN-first vs JP-first
- [ ] Re-bible decision (single localized mascot vs separate per language)

## §2. Cultural adaptation
- [ ] Re-bible per language (not direct translate — culturally specific 사장님 frame needs rework)
- [ ] Per-language voice ref
- [ ] Per-language compliance rules (US FTC for EN, Japan 景品表示法 for JP)

## §3. Component updates
- [ ] TTS: multi-language voice profiles
- [ ] LLM Host: persona prompts per language
- [ ] LLM Moderator: language-aware rules
- [ ] Script schema: `language` field already supports en/ja — runtime honors it
- [ ] RAG: BGE-M3 multilingual already; verify quality on EN/JP

## §4. Pilot
- [ ] 1 broadcast in chosen language
- [ ] Native-speaker review
- [ ] Iterate
