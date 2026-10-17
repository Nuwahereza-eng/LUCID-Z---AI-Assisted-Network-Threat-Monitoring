# Multi-architecture Dockerfile for LUCID-DDoS
# Supports both x86_64 (standard) and s390x (IBM Z / LinuxONE)
#
# On IBM Z, pip needs build tools because some packages have no pre-built wheels.
# We detect the architecture at build time and select the appropriate requirements file.

FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies:
#   build-essential + gfortran: required to compile numpy/scipy/scikit-learn on s390x
#   tshark: required by pyshark for PCAP parsing
#   ca-certificates: HTTPS
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gfortran \
       tshark \
       ca-certificates \
       pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy both requirements files
COPY requirements.txt requirements-hosted.txt requirements-s390x.txt /app/

# Select requirements file based on CPU architecture:
#   s390x (IBM Z)  → requirements-s390x.txt  (flexible pins, compiles from source if needed)
#   everything else → requirements-hosted.txt (pre-built CPU wheels)
RUN ARCH=$(uname -m) && \
    echo "Building for architecture: $ARCH" && \
    if [ "$ARCH" = "s390x" ]; then \
        echo "IBM Z detected — using s390x requirements"; \
        pip install --upgrade pip && \
        pip install -r /app/requirements-s390x.txt; \
    else \
        echo "x86_64 detected — using hosted requirements"; \
        pip install --upgrade pip && \
        pip install -r /app/requirements-hosted.txt; \
    fi

# Copy application source
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
