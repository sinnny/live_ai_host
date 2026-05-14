# Checklist — Analytics dashboard

| | |
|---|---|
| FSD | [`../../fsd/analytics_dashboard.md`](../../fsd/analytics_dashboard.md) |
| Phase | Phase 3 (platform-analytics-API-dependent) |
| Language | English source — KO at [`../ko/analytics_dashboard.md`](../ko/analytics_dashboard.md) |

---

## Tech stack
- Platform analytics APIs + ClickHouse warehouse + Grafana/React viz

---

## §1. Pre-activation
- [ ] Platform partnerships provide viewer + conversion data access
- [ ] Conversion-attribution model decided (in-stream click-tracking + checkout pixel)

## §2. Implementation
- [ ] Platform analytics API connectors (per platform)
- [ ] Extend ClickHouse schema for analytics events
- [ ] Build dashboard panels (FSD §3 metric list)
- [ ] Per-tenant access controls

## §3. Privacy
- [ ] Per-platform PII handling reviewed
- [ ] Aggregation defaults (vs viewer-level data)
- [ ] Retention policy aligned with `audit_log.md`

## §4. Acceptance
- [ ] Seller can see at least: viewer peak/avg, comment rate, conversion rate per broadcast
- [ ] Data latency from broadcast end to dashboard ≤ 24 hours
