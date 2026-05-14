# Function Spec — Object storage

| | |
|---|---|
| Status | Spec v1 (Phase 2) |
| Phase | Phase 2 |
| Component | S3-compatible storage for mascot atlases, voices, backgrounds, B-roll clips, broadcast recordings |
| Source documents | [`../../prd.md`](../../prd.md) §5.4 |
| Last updated | 2026-05-13 |

---

## 1. Purpose

All large binary assets live here. Postgres references by path. Per-tenant prefix enforces isolation.

---

## 2. Technology stack

| Provider | Self-hosted | Managed |
|---|---|---|
| MVP self-host | **MinIO** (AGPL) | – |
| Production option | – | **Cloudflare R2** (free egress, S3-compatible) |
| Alternative | – | AWS S3 |

Decision: start with MinIO on RunPod / dedicated VM for cost; migrate to R2 if egress-heavy or scale demands.

---

## 3. Bucket layout

```
s3://daramzzi-prod/
├── <tenant_id>/
│   ├── mascots/<mascot_id>/atlas.png, config.json, lora.safetensors
│   ├── voices/<voice_id>/ref.wav, ref_text.txt
│   ├── backgrounds/<vibe>/<n>.png|.mp4
│   ├── broadcasts/<broadcast_id>/
│   │   ├── broll/<product_id>/final.mp4
│   │   ├── recordings/full.mp4
│   │   └── thumbnails/<n>.jpg
```

---

## 4. Access patterns

- Read: signed URLs (15-min expiry) for browser previews, direct access for runtime services.
- Write: only orchestrator + asset pipelines have write credentials.
- Lifecycle: broadcast recordings auto-tier to cold storage after 30 days, deleted after 1 year (configurable per tenant).

---

## 5. Per-tenant isolation

IAM policy enforces `s3://<bucket>/<tenant_id>/*` access. Cross-tenant reads rejected.

---

## 6. Quality criteria

| Criterion | Threshold |
|---|---|
| Read latency (cold) | ≤ 200ms |
| Write throughput (mascot upload) | ≥ 50 MB/s |
| Durability | 99.99% (MinIO with erasure coding; R2 native) |

---

## 7. References

- [`../../prd.md`](../../prd.md) §5.4
- [`multi_tenancy.md`](multi_tenancy.md) — IAM policy
- [`data_model.md`](data_model.md) — Postgres path references
