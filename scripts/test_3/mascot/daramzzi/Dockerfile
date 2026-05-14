# make_mascot pipeline image — Daramzzi atlas generation
# Per docs/phase_0_v2/fsd/make_mascot.md §2.3
#
# Build:  docker build -t daramzzi-pipeline -f Dockerfile .
# Run:    docker run --rm --gpus all -v $(pwd):/work daramzzi-pipeline \
#             python pipeline.py <stage> --config daramzzi_config.yaml

FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/work/.hf_cache \
    TRANSFORMERS_CACHE=/work/.hf_cache \
    TORCH_HOME=/work/.torch_cache

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-dev python3-pip \
        git curl ca-certificates \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
        ffmpeg \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip wheel setuptools

# PyTorch (CUDA 12.4 build)
RUN pip install --index-url https://download.pytorch.org/whl/cu124 \
        torch==2.4.1 torchvision==0.19.1

# Image-gen / training stack
RUN pip install \
        "diffusers>=0.30,<0.32" \
        "transformers>=4.45,<4.50" \
        "accelerate>=0.34" \
        "peft>=0.13" \
        "safetensors>=0.4" \
        "huggingface_hub>=0.25" \
        sentencepiece \
        protobuf

# Vision / utility deps
RUN pip install \
        "Pillow>=10.4" \
        "numpy<2" \
        opencv-python-headless \
        mediapipe \
        "click>=8.1" \
        pyyaml \
        einops \
        scipy \
        tqdm

# BiRefNet — load from HF transformers (model code in trust_remote_code repo)
RUN pip install timm kornia

# AI-Toolkit (Ostris) — installed from source; pinned tag set in build args.
# Not pip-installable (no setup.py/pyproject.toml); we invoke run.py directly.
ARG AI_TOOLKIT_REF=main
RUN git clone https://github.com/ostris/ai-toolkit.git /opt/ai-toolkit \
    && cd /opt/ai-toolkit \
    && git checkout "${AI_TOOLKIT_REF}" \
    && pip install -r requirements.txt || true

ENV PATH="/opt/ai-toolkit:${PATH}" \
    AI_TOOLKIT_ROOT="/opt/ai-toolkit"

WORKDIR /work
COPY . /work/

CMD ["python", "pipeline.py", "--help"]
