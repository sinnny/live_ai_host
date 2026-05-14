# Function Spec — Analytics dashboard

| | |
|---|---|
| Status | Skeleton v1 (Phase 3 — depends on platform analytics access) |
| Phase | Phase 3 |
| Component | Per-broadcast viewer/conversion analytics for sellers |
| Source documents | [`../../prd.md`](../../prd.md) §3.2 |
| Open dependencies | Platform partnerships provide viewer + conversion data; conversion-attribution model |
| Last updated | 2026-05-13 |

---

## 1. Purpose

Once broadcasts run on Naver / Kakao / Coupang, sellers want to see: viewers, engagement (comments, likes), conversions (clicks, purchases), AOV. This dashboard surfaces it.

---

## 2. Tech stack

| Stage | Tool |
|---|---|
| Source data | platform APIs (Naver Analytics, etc.); also our own audit log |
| Warehouse | ClickHouse (extends [`audit_log.md`](audit_log.md)) |
| Visualization | Grafana (extends [`observability.md`](observability.md)) or custom React |
| Backend | FastAPI extension on [`operator_dashboard.md`](operator_dashboard.md) |

---

## 3. Metrics to surface (v1)

- Viewer count peak / avg
- Comments per minute
- Conversion: comment-to-click (when CTA-clicks tracked)
- Conversion: click-to-purchase (when checkout-tracked)
- Cost-per-broadcast vs revenue (when finance-tied)
- Top products by engagement

---

## 4. Open dependencies

- Platform-specific analytics APIs (Naver / Kakao / Coupang — partnership-gated)
- Conversion attribution: cross-platform tracking pixel? In-stream click tracking?
- Privacy: how much viewer-level data do we have vs aggregate?

---

## 5. References

- [`../../prd.md`](../../prd.md) §3.2
- [`audit_log.md`](audit_log.md), [`observability.md`](observability.md)
- Platform analytics docs (partnership-gated)
