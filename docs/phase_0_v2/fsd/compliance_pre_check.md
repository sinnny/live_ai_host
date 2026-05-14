# Function Spec — Pre-broadcast compliance check

| | |
|---|---|
| Status | Spec v1 (Phase 2 — requires legal consultation to finalize rules) |
| Phase | Phase 2 |
| Component | Audits the full scripted portion of a broadcast against Korean 표시광고법 + vertical-specific rules before broadcast goes live |
| Source documents | [`../../prd.md`](../../prd.md) §4.5 |
| Open dependencies | Legal consultation on 식품위생법 + 표시광고법 enforcement nuances (target: Sprint 4) |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Two-layer compliance:
- **Pre-broadcast**: this FSD — full script audit before "approve to go live"
- **Live**: [`llm_moderator.md`](llm_moderator.md) — per-line audit during broadcast

This is the gate that catches systemic issues (e.g. "this entire script makes superlative claims forbidden by law") before they ever go on air.

---

## 2. Technology stack

| Stage | Tool | License |
|---|---|---|
| Audit LLM | Claude Sonnet 4.6 | proprietary, paid |
| Rules corpus | inline in prompt | – |
| (Optional) regex rules | inline pre-LLM filter for trivial violations | – |

---

## 3. Inputs

```json
{
  "broadcast_id": "...",
  "vertical": "food",
  "script_segments": [...],
  "products": [...]
}
```

---

## 4. Outputs

```json
{
  "verdict": "approved|requires_revision",
  "issues": [
    {
      "segment_idx": 3,
      "category": "unsubstantiated_health_claim",
      "rule": "표시광고법 §3 — health benefit claims without evidence",
      "excerpt": "이거 먹으면 살 빠져요...",
      "suggested_fix": "Drop the health claim; rephrase as taste-focused"
    }
  ],
  "summary": "Found 2 high-severity issues; revision required."
}
```

---

## 5. Rules corpus (to be finalized with legal counsel)

Categories (skeleton — full corpus in dedicated `compliance_runbook.md`, deferred to Phase 3):

- **Unsubstantiated effectiveness claims** — diet, health, beauty effects without authorized basis
- **Forbidden superlatives** — "최고", "유일", "제일" without evidence
- **Forbidden comparatives** — direct comparison to competitor products
- **Origin / certification falsehoods** — claiming HACCP/유기농 status not held
- **Profanity / abuse** — even mild
- **Sexually suggestive content** — not applicable for food but blanket rule
- **Vertical-specific** (food): 식품위생법 packaging and labeling rules

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Latency | acceptable up to ~1 min per script (offline run) |
| Catch rate on labeled violation set | 100% on high-severity, ≥ 90% on medium |
| False positive rate | ≤ 15% (acceptable; founder reviews flagged segments) |

---

## 7. Open questions

- **Rule corpus depth** — needs legal consultation. Target: complete rule set by Sprint 4.
- **Liability** — does the AI-driven compliance check satisfy any "good faith effort" defense? Legal opinion needed.

---

## 8. References

- [`../../prd.md`](../../prd.md) §4.5
- [`llm_moderator.md`](llm_moderator.md) — runtime sibling
- 표시광고법 / 식품위생법 (legal consultation pending)
