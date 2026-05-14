# Prototype pipeline image — TTS, phoneme alignment, renderer, encoder.
# Per docs/phase_0_v2/fsd/{orchestrator,tts,phoneme_alignment,renderer}.md

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/work/.hf_cache \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-dev python3-pip \
        git curl ca-certificates xz-utils \
        ffmpeg \
        libsndfile1 sox \
        libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
        libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
        libcairo2 libasound2 libatspi2.0-0 \
        fonts-noto fonts-noto-cjk \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip wheel setuptools

# PyTorch CUDA 12.4
RUN pip install --index-url https://download.pytorch.org/whl/cu124 \
        torch==2.4.1 torchaudio==2.4.1

# CosyVoice 2 — installed from source (no PyPI release). FunAudioLLM repo.
ARG COSYVOICE_REF=main
RUN git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git /opt/cosyvoice \
    && cd /opt/cosyvoice \
    && git checkout "${COSYVOICE_REF}" \
    && pip install -r requirements.txt || true

ENV PYTHONPATH="/opt/cosyvoice:/opt/cosyvoice/third_party/Matcha-TTS:${PYTHONPATH}" \
    COSYVOICE_ROOT="/opt/cosyvoice"

# Rhubarb Lip Sync — prebuilt release binary
ARG RHUBARB_VERSION=1.13.0
RUN curl -L -o /tmp/rhubarb.zip \
        "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v${RHUBARB_VERSION}/Rhubarb-Lip-Sync-${RHUBARB_VERSION}-Linux.zip" \
    && apt-get update && apt-get install -y --no-install-recommends unzip \
    && unzip /tmp/rhubarb.zip -d /opt/ \
    && mv "/opt/Rhubarb-Lip-Sync-${RHUBARB_VERSION}-Linux" /opt/rhubarb \
    && chmod +x /opt/rhubarb/rhubarb \
    && ln -sf /opt/rhubarb/rhubarb /usr/local/bin/rhubarb \
    && rm /tmp/rhubarb.zip \
    && apt-get remove -y unzip && rm -rf /var/lib/apt/lists/*

# Python pipeline deps
RUN pip install \
        click \
        pyyaml \
        jsonschema \
        librosa \
        soundfile \
        numpy \
        scipy \
        Pillow \
        playwright

RUN playwright install --with-deps chromium

WORKDIR /work
COPY . /work/

CMD ["python", "prototype.py", "--help"]
