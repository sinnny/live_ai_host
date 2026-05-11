# Phase 0 체크리스트
## `Phase0 execution plan final.md` 작업용 동반 문서

이 문서는 **실행(do)** 문서입니다. 계획서는 **이유(why)** 문서입니다. 이유나 탈출 조건(escape triggers)에 대해 의문이 생기면 계획서를 읽으세요. "다음은 무엇인가?"만 알아야 할 때는 여기서 항목을 체크하세요.

**규칙:**
- `[ ]` = 미완료, `[x]` = 완료. 진행하면서 표시하세요.
- 각 단계는 탈출 조건을 위해 계획서 섹션을 참조합니다 — 한 단계가 두 번 실패하면 그곳으로 가세요.
- 하단의 누계(running totals)에서 진행 중인 fal.ai 지출을 추적하세요.

---

## 사전 준비 (1일차 저녁 전 실행)

- [ ] https://fal.ai 에서 **fal.ai 계정 생성**
- [ ] **fal.ai에 $50 충전** (대시보드에서 지출 한도를 $50로 설정 — 절대 상한선)
- [ ] fal.ai 대시보드에서 **`FAL_KEY` 발급**, `.env`에 붙여넣을 준비
- [ ] **1~5장의 한국인 레퍼런스 사진 수집**하여 폴더에 저장, `inputs/photos/`에 복사할 준비
  - 최소 1장은 정면, 조명이 좋고 해상도 ≥1024×1024
  - 사진이 많을수록 PuLID의 정체성 보존이 더 잘 됨; 있는 대로 모두 수집
- [ ] 오늘 밤 다운로드를 위해 **30분 확보** (Flux schnell 가중치 ~24 GB + PuLID 가중치 — 자기 전에 시작)
- [ ] **디스크 공간 확인**: 프로젝트 디렉토리가 있는 디스크에 최소 60GB 여유 공간 필요

---

## 0단계 — 환경 설정 (1일차 저녁, 약 2시간 + 밤샘 다운로드)
*계획서: §0단계 — 환경 설정*

### 0.1 Conda 환경 + 핵심 종속성
- [ ] `conda create -n live-ai-host python=3.11 -y && conda activate live-ai-host`
- [ ] `cd /Users/shinheehwang/Desktop/projects/00_live_ai_host/`
- [ ] **`numpy<2` 고정(pin)을 추가하여** pip install 명령어 실행:
  ```bash
  pip install \
    diffusers transformers accelerate \
    "numpy<2" torch torchvision torchaudio \
    pillow pandas \
    jupyterlab ipykernel \
    fal-client python-dotenv \
    requests pyyaml