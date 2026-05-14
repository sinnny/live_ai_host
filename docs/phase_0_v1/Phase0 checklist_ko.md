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
  
```
- [ ] `python -c "import numpy; print(numpy.__version__)"` → `1.`로 시작함
- [ ] `python -c "import torch; print(torch.__version__, torch.backends.mps.is_available())"` → 버전 + `True`
- [ ] `python -c "import fal_client, diffusers, transformers, PIL; print('ok')"` → `ok`

### 0.2 프로젝트 스켈레톤(뼈대)
- [ ] 디렉토리 구조 생성 (`inputs/`, `outputs/stage{1..5}_*/`, `notebooks/`, `comfy_workflows/`, `scripts/`, `logs/`)
- [ ] `FAL_KEY=...` 및 `ANTHROPIC_API_KEY=...`가 포함된 `.env` 생성
- [ ] `.env`, `outputs/`, `models/`, `logs/`, `__pycache__/`, `*.ipynb_checkpoints/`를 제외하는 `.gitignore` 생성
- [ ] 아직 안 했다면 `git init` 실행

### 0.3 ComfyUI 설치
- [ ] ComfyUI를 `tools/ComfyUI/`에 클론 (ComfyUI 자체 모델 디렉토리를 위한 것이므로 `models/`는 **아님**)
- [ ] `cd tools/ComfyUI && pip install -r requirements.txt`
- [ ] `PYTORCH_ENABLE_MPS_FALLBACK=1 python main.py --force-fp16` 오류 없이 실행됨
- [ ] 브라우저에서 `http://localhost:8188`이 열리고 ComfyUI 작업 공간이 로드됨
- [ ] Ctrl+C로 중지

### 0.4 PuLID-Flux + 가중치
- [ ] (번들로 제공되지 않은 경우) ComfyUI-Manager 커스텀 노드 설치
- [ ] ComfyUI Manager를 통해 **ComfyUI-PuLID-Flux** 커스텀 노드 설치
- [ ] ComfyUI 재시작; 우클릭 메뉴에 PuLID-Flux 노드들이 나타남
- [ ] **다운로드 시작 (시간이 오래 걸림, 시작해 두고 내버려 두기):**
  - [ ] Flux schnell 체크포인트 → `tools/ComfyUI/models/checkpoints/`
  - [ ] PuLID 가중치 → 커스텀 노드 README에 지정된 위치
  - [ ] PuLID-Flux 워크플로우에 필요한 CLIP / VAE / 인코더 (노드의 README에 목록이 있음)
- [ ] 모든 다운로드 완료; ComfyUI 재시작; 콘솔에 가중치 누락(missing-weights) 오류가 없음

### 0.5 fal.ai 인증 스모크 테스트
- [ ] `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(bool(os.getenv('FAL_KEY')))"` → `True`
- [ ] 한 줄 fal.ai 테스트 실행 (가장 저렴한 방법 — 단일 Flux schnell 이미지, 약 $0.003):
  ```python
  import fal_client
  result = fal_client.subscribe(
      "fal-ai/flux/schnell",
      arguments={"prompt": "a red apple", "image_size": "square_hd"},
  )
  print(result["images"][0]["url"])
  ```
- [ ] 반환된 URL이 브라우저에서 열리며 붉은 사과 이미지를 보여줌
- [ ] fal.ai 대시보드 확인: 지출이 약 $0.003 증가함

### 0.6 환경 고정(Lock)
- [ ] `pip freeze > requirements-lock.txt`
- [ ] `requirements-lock.txt`가 비어 있지 않으며 git에 커밋됨
- [ ] 계획서의 0단계 상태 업데이트: ✅ 완료(Done)

**현재까지 0단계 지출: 약 $0.003**

---

## 1단계 — 히어로 샷 (1일차 또는 2일차 저녁, 약 1시간)
*계획서: §1단계 — 히어로 샷 준비*

### 1.1 경로 선택
- [ ] 결정: A 경로 (기존 사진 사용) 또는 B 경로 (ComfyUI에서 새로 생성)
- 가지고 있는 사진이 방송 수준 품질이라면 → A 경로. 그렇지 않다면 → B 경로.

### 1.2 A 경로 — 기존 사진 사용 (해당하는 경우)
- [ ] 가장 깨끗하고, 조명이 좋으며, 정면을 향한 사진 선택
- [ ] 정사각형으로 자르고, 해상도 ≥1024×1024로 크기 조정
- [ ] `inputs/photos/hero.png`로 저장
- [ ] 1.3을 건너뛰고 1.4로 이동

### 1.3 B 경로 — 새로 생성 (해당하는 경우)
- [ ] `notebooks/01_hero_shot.ipynb` 열기
- [ ] 계획서 §1단계의 프롬프트 + 네거티브 프롬프트를 사용하여 Flux schnell ComfyUI 워크플로우 구축
- [ ] 로컬에서 약 20개의 변형 생성
- [ ] 얼굴이 너무 서구적으로 보일 경우: fal의 Hunyuan Image 3.0으로 전환 (`fal-ai/hunyuan-image/v3/text-to-image`, 약 $0.04/장 × 10 = $0.40)
- [ ] 가장 좋은 것을 골라 `inputs/photos/hero.png`로 저장

### 1.4 히어로 샷 품질 체크리스트 (모두 통과해야 함)
- [ ] 얼굴이 프레임의 40–60%를 차지함
- [ ] 카메라를 응시하며, 무표정이거나 살짝 미소 지음
- [ ] 균일한 조명, 거친 그림자가 없음
- [ ] 손이나 물체가 얼굴을 가리지 않음
- [ ] 머리카락 가장자리가 깔끔함 (흐려지거나 이상하지 않음)
- [ ] 배경이 단순함
- [ ] **이 사람을 방송 진행자로 인정할 수 있음** (직감적 확인)
- [ ] 해상도 ≥ 1024×1024
- [ ] 파일이 `inputs/photos/hero.png`에 저장됨
- [ ] 계획서의 1단계 상태 업데이트: ✅ 완료(Done)

**품질 검사 중 하나라도 실패할 경우: 다시 하세요. 2단계에서 잘못된 히어로 샷을 수정할 수 없습니다.**

---

## 2단계 — 정체성 변형 (2일차 저녁, 작업 약 3시간 + 밤샘)
*계획서: §2단계 — 정체성 변형*

### 2.1 워크플로우 설정
- [ ] `notebooks/02_identity_variants.ipynb` 열기
- [ ] ComfyUI에서 PuLID-Flux 커뮤니티 워크플로우 로드 (또는 PuLID 노드를 사용하여 처음부터 구축)
- [ ] 워크플로우 JSON을 `comfy_workflows/pulid_flux.json`에 저장

### 2.2 레퍼런스 이미지
- [ ] hero.png + 1~3장의 추가 한국인 레퍼런스 사진을 PuLID 입력 슬롯에 복사
- [ ] **가진 레퍼런스를 최대한 사용** (PuLID는 최대 4장까지 허용) — 정체성 보존을 실질적으로 향상시킴

### 2.3 생성 단계 — 4 스텝과 8 스텝 모두 시도
- [ ] **4 스텝**(schnell 기본값)에서 프롬프트 5개 × 변형 5개 생성 → 이미지 25장
- [ ] `outputs/stage2_variants/4steps/`에 저장
- [ ] **8 스텝**에서 동일한 세트 생성 → 이미지 추가 25장
- [ ] `outputs/stage2_variants/8steps/`에 저장
- [ ] 시각적 비교: 정체성이 가장 잘 유지되는 스텝 수 선택
- [ ] 선택된 25장을 `outputs/stage2_variants/final/`로 이동

### 2.4 정체성 채점
- [ ] 미리보기/이미지 그리드에서 25개의 변형 모두와 hero.png를 나란히 열기
- [ ] 계획서 §2단계 루브릭을 사용하여 솔직하게 채점 (5/5 ↔ 1/5)
- [ ] **한국인 특화 실패 여부 확인:**
  - [ ] 무쌍/홑꺼풀이 쌍꺼풀로 "교정"되지 않았음
  - [ ] 피부톤이 핑크빛/서구적으로 변하지 않았음
  - [ ] 얼굴 구조(턱 너비, 광대뼈)가 일관됨
  - [ ] 측면 샷에서 머리카락 가장자리가 깔끔함
  - [ ] 몽고주름이 보존됨
- [ ] 점수가 4/5 미만인 경우: 계획서 §2단계 탈출 조건 참조 (더 많은 레퍼런스 → InstantID → 유료 Flux Kontext Pro)
- [ ] **말하는 포즈 변형**(입이 살짝 벌려져 있고, 카메라를 응시)을 구체적으로 식별 — 이는 4단계 테스트 3에 필요함
- [ ] 계획서의 2단계 상태 업데이트: ✅ 완료(Done)

**잘못된 변형 결과물로 4단계에 진행하지 마세요.**

---

## 3단계 — 구동 오디오 (3일차 저녁, 약 1시간)
*계획서: §3단계 — 구동 오디오*

- [ ] 약 30초 길이의 깔끔한 한국어 음성 녹음 (휴대폰 음성 메모 가능)
- [ ] 다양하게 발음: ㄱ/ㅋ 거센소리, ㅡ 모음, 받침이 많은 음절 포함
- [ ] 24kHz 모노 WAV로 변환 (ffmpeg 한 줄 명령어: `ffmpeg -i input.m4a -ar 24000 -ac 1 inputs/audio/reference_korean_30s.wav`)
- [ ] 다시 듣기: 선명하고, 배경 잡음이 없으며, 정상적인 속도임
- [ ] 파일이 `inputs/audio/reference_korean_30s.wav`에 있으며, 약 30초, 24kHz 모노 확인됨
- [ ] 계획서의 3단계 상태 업데이트: ✅ 완료(Done)

---

## 4단계 — 토킹 헤드 생성 (3~4일차 저녁, 약 $27)
*계획서: §4단계 — 토킹 헤드 생성*

### 4.0 사전 준비 (첫 API 호출 전 실행)
- [ ] https://fal.ai/models 에서 **5개의 fal 슬러그(slug)가 여전히 최신인지 확인** — 가격도 확인. 변경되었다면 스크립트의 `MODELS` 딕셔너리 업데이트.
- [ ] **`scripts/fal_call.py` 구현** — 계획서의 버전은 플레이스홀더입니다. 각 모델은 다른 입력/출력 스키마를 가집니다:
  - [ ] EchoMimic v3: 필수 필드에 대한 fal 문서 확인
  - [ ] p-video-avatar: fal 문서 확인
  - [ ] Omnihuman v1.5: fal 문서 확인
  - [ ] Kling Avatar v2 Pro: fal 문서 확인
  - [ ] 모델별 `INPUT_ADAPTERS` 및 `OUTPUT_PARSERS` 딕셔너리 추가
- [ ] `notebooks/04_talking_head.ipynb`를 열고 스크립트 가져오기(import)

### 4.1 3일차 저녁 — 첫 세 개의 비디오 (저렴함 → 관문 → 프리미엄)
*비싼 실행을 하기 전, 파이프라인 검증을 위해 저렴한 것 먼저 실행.*

- [ ] **테스트 4** — `p-video-avatar` × hero.png × 한국어 오디오 (약 $0.75)
  - [ ] 성공적으로 생성됨
  - [ ] `outputs/stage4_videos/test4_hero_kor_pvideo.mp4`로 저장됨
  - [ ] QuickTime에서 재생됨
  - [ ] 생성 시간 + 비용 기록됨
- [ ] **계속하기 전에 멈추고 테스트 4 결과를 확인하세요.** 파이프라인이 조금이라도 일관성 있는 비디오를 생성했다면 연결은 작동하는 것입니다. 쓰레기 결과가 나왔다면 다음 테스트에 $6를 쓰기 전에 디버그하세요.
- [ ] **테스트 1** — `EchoMimic v3` × hero.png × 한국어 오디오 (약 $6.00)
  - [ ] 성공적으로 생성됨
  - [ ] `outputs/stage4_videos/test1_hero_kor_echomimic.mp4`로 저장됨
  - [ ] QuickTime에서 재생됨
  - [ ] 생성 시간 + 비용 기록됨
- [ ] **테스트 6** — `Kling Avatar v2 Pro` × hero.png × 한국어 오디오 (약 $3.45)
  - [ ] 성공적으로 생성됨
  - [ ] `outputs/stage4_videos/test6_hero_kor_kling.mp4`로 저장됨
  - [ ] QuickTime에서 재생됨
  - [ ] 생성 시간 + 비용 기록됨

**현재까지 3일차 저녁 지출: 약 $10.20. 자기 전에 fal 대시보드 확인.**

### 4.2 4일차 저녁 — 남은 세 개의 비디오
- [ ] **테스트 2** — `EchoMimic v3` × 3-4 각도 변형 × 한국어 오디오 (약 $6.00)
  - [ ] `outputs/stage4_videos/test2_variant34_kor_echomimic.mp4`로 저장됨
- [ ] **테스트 3** — `EchoMimic v3` × **말하는 포즈 변형** × 한국어 오디오 (약 $6.00)
  - [ ] `outputs/stage4_videos/test3_speakingpose_kor_echomimic.mp4`로 저장됨
- [ ] **테스트 5** — `Omnihuman v1.5` × hero.png × 한국어 오디오 (약 $4.80)
  - [ ] `outputs/stage4_videos/test5_hero_kor_omnihuman.mp4`로 저장됨

**4단계 총 지출: 약 $27. fal 대시보드를 확인하세요. 절대 상한선 $50 — 접근하면 중지하세요.**

- [ ] 6개의 비디오 모두 `outputs/stage4_videos/`에 저장됨
- [ ] 6개 모두 깨짐 없이 QuickTime에서 재생됨
- [ ] 계획서의 4단계 상태 업데이트: ✅ 완료(Done)

---

## 5단계 — 평가 + 결정 (4~5일차 저녁, 약 3시간)
*계획서: §5단계 — 평가 및 결정*

### 5.1 비디오별 채점 (6개 비디오 모두)
각 비디오마다 2번씩 시청하고 6개 축에 대해 1~5점으로 채점하세요:

- [ ] **테스트 1** 채점됨 — `outputs/stage5_evaluation/test1_notes.yaml` 저장됨
- [ ] **테스트 2** 채점됨 — `test2_notes.yaml` 저장됨
- [ ] **테스트 3** 채점됨 — `test3_notes.yaml` 저장됨
- [ ] **테스트 4** 채점됨 — `test4_notes.yaml` 저장됨
- [ ] **테스트 5** 채점됨 — `test5_notes.yaml` 저장됨
- [ ] **테스트 6** 채점됨 — `test6_notes.yaml` 저장됨

### 5.2 다중 평가자 (강력히 권장)
- [ ] 1명 이상의 한국어 원어민 평가자 모집
- [ ] 비디오 링크 공유 (Google Drive / WeTransfer)
- [ ] 6개의 비디오 중 최소 3개에 대한 평가 점수 회신 받기
- [ ] 본인의 YAML 파일과 함께 그들의 YAML 파일 저장

### 5.3 DECISION.md
- [ ] `notebooks/05_evaluation.ipynb` 열기
- [ ] 모든 평가자에 걸친 모델별 평균 점수 계산
- [ ] 계획서 §5단계의 DECISION.md 템플릿 채우기
- [ ] 다음 4개의 최종 결정 체크박스 중 정확히 **하나**에 체크:
  - [ ] 오픈소스 사용 가능 (EchoMimic v3 평균 ≥ 4.0)
  - [ ] 보급형으로 충분함 (p-video-avatar ≥ 3.5 이며 최고 유료 모델과 0.5점 이내 차이)
  - [ ] 프리미엄 유료 모델 필요
  - [ ] 한국어에 적합하지 않음 (준비 안 됨)
- [ ] 구체적인 발견 사항, 실패 모드, 한국어 특화 문제점 문서화
- [ ] 선택한 경로의 60분 방송당 비용 추산
- [ ] 다음 주 실행 항목(action items) 작성
- [ ] `outputs/stage5_evaluation/DECISION.md`로 저장
- [ ] DECISION.md를 git에 커밋
- [ ] 계획서의 5단계 상태 업데이트: ✅ 완료(Done)

---

## 진행 지출 추적기

각 fal.ai 호출 후 업데이트. 절대 상한선 $50.

| 단계 | 항목                                     | 예상 비용  | 실제 비용 | 누계 |
| ---- | ---------------------------------------- | ---------- | --------- | ---- |
| 0.5  | 스모크 테스트 (Flux schnell × 1)         | $0.003     |           |      |
| 1.3  | 히어로 샷 생성 (B 경로 + Hunyuan인 경우) | $0–$0.40   |           |      |
| 4.1  | 테스트 4 (p-video-avatar)                | $0.75      |           |      |
| 4.1  | 테스트 1 (EchoMimic v3)                  | $6.00      |           |      |
| 4.1  | 테스트 6 (Kling Avatar v2 Pro)           | $3.45      |           |      |
| 4.2  | 테스트 2 (EchoMimic v3)                  | $6.00      |           |      |
| 4.2  | 테스트 3 (EchoMimic v3)                  | $6.00      |           |      |
| 4.2  | 테스트 5 (Omnihuman v1.5)                | $4.80      |           |      |
|      | **기본 총액**                            | **약 $27** |           |      |
|      | 재시도 여유분(Buffer)                    | 약 $10     |           |      |
|      | **작업 예산**                            | **$40**    |           |      |
|      | **절대 상한선**                          | **$50**    |           |      |

---

## 마스터 탈출 조건 (빠른 참조)
*전체 탈출 조건은 계획서 §마스터 탈출 조건에 있음*

1. 단계가 반복적으로 실패함 → 해당 단계의 탈출 조건 확인
2. 여러 단계가 실패함 → 환경 문제, 한 가지를 집중 디버깅
3. 작동하는 파이프라인 없이 $50에 도달해감 → 중지, 문서화, 다음 날 다시 생각하기(sleep on it)
4. DECISION.md 없이 5일차 저녁이 끝남 → 기한 연장, 일정보다 결과물이 더 중요함
5. fal.ai 서비스 중단 >24시간 → Eachlabs 또는 RunPod (최후의 수단)