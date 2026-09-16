# Copyright 2026 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Security-validation variant:
# - Keep the upstream build context as server/
# - Pin the Python base image by digest
# - Apply Debian security updates explicitly
# - Update Python packaging tooling
# - Keep the existing application/runtime layout unchanged

ARG PYTHON_BASE=python:3.10-slim@sha256:8c97ebedc32fd60935cdf5992e935753e2a0f98231830028050e1e04bd3c13c2


# ============================================================
# Builder
# ============================================================

FROM ${PYTHON_BASE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=/app/.venv \
    UV_LINK_MODE=copy

WORKDIR /app


# ------------------------------------------------------------
# Debian security updates
# ------------------------------------------------------------

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && apt-get install -y --only-upgrade \
        gzip \
        libpcre2-8-0 \
        libsqlite3-0 \
        perl-base \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Install uv
# ------------------------------------------------------------

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"


# ------------------------------------------------------------
# Install application dependencies
# ------------------------------------------------------------

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project


# ------------------------------------------------------------
# Copy application source
# ------------------------------------------------------------

COPY opensandbox_server ./opensandbox_server

COPY LICENSE README.md ./


# ------------------------------------------------------------
# Install OpenSandbox server
# ------------------------------------------------------------

RUN uv pip install --no-deps --editable .


# ------------------------------------------------------------
# Update Python packaging dependencies
# ------------------------------------------------------------

RUN uv pip install \
        --python /app/.venv/bin/python \
        --upgrade \
        "setuptools>=82.0.1" \
        "wheel>=0.46.2"



# ============================================================
# Runtime
# ============================================================

FROM ${PYTHON_BASE} AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    SANDBOX_CONFIG_PATH=/etc/opensandbox/config.toml

WORKDIR /app


# ------------------------------------------------------------
# Debian security updates in FINAL runtime image
# ------------------------------------------------------------

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && apt-get install -y --only-upgrade \
        gzip \
        libpcre2-8-0 \
        libsqlite3-0 \
        perl-base \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Update system Python packaging tools
#
# Trivy previously detected:
#   CVE-2026-23949 -> jaraco.context
#   CVE-2026-24049 -> wheel
#
# These were associated with Python packaging tooling in the
# base image.
# ------------------------------------------------------------

RUN python -m pip install \
        --no-cache-dir \
        --upgrade \
        "setuptools>=82.0.1" \
        "wheel>=0.46.2"


# ------------------------------------------------------------
# Copy application from builder
# ------------------------------------------------------------

COPY --from=builder /app/.venv /app/.venv

COPY --from=builder /app/opensandbox_server /app/opensandbox_server


# ------------------------------------------------------------
# Preserve existing OpenSandbox runtime files
#
# NOTE:
# The current upstream Dockerfile uses the Kubernetes example
# configuration. We are deliberately NOT changing that in this
# vulnerability-remediation change.
#
# Docker-vs-Kubernetes configuration will be reviewed separately.
# ------------------------------------------------------------

COPY --from=builder /app/opensandbox_server/examples/example.config.k8s.toml /etc/opensandbox/config.toml

COPY --from=builder /app/opensandbox_server/examples/example.config.k8s.zh.toml /etc/opensandbox/config.zh.toml

COPY --from=builder /app/opensandbox_server/examples/example.batchsandbox-template.yaml /etc/opensandbox/example.batchsandbox-template.yaml

COPY --from=builder /app/opensandbox_server/examples/e2e.batchsandbox-template.yaml /etc/opensandbox/e2e.batchsandbox-template.yaml


# ============================================================
# Security verification
# ============================================================
#
# IMPORTANT:
# This section is diagnostic only.
#
# It prints the installed package versions but does NOT fail
# the Docker build if a package is absent.
#
# Trivy remains the actual security gate in GitHub Actions.
# ============================================================

RUN echo "===== Debian package versions =====" \
    && for pkg in perl-base gzip libpcre2-8-0 libsqlite3-0; do \
        echo "--- $pkg ---"; \
        dpkg-query -W \
            -f='${Package} ${Version}\n' \
            "$pkg" 2>/dev/null \
            || echo "$pkg: NOT INSTALLED"; \
    done \
    && echo "===== Python packaging versions =====" \
    && python -m pip show setuptools 2>/dev/null \
        || echo "setuptools: NOT FOUND" \
    && python -m pip show wheel 2>/dev/null \
        || echo "wheel: NOT FOUND" \
    && echo "===== Python packaging metadata =====" \
    && python -c 'import importlib.metadata as md; [print(f"{name}: {md.version(name)}") for name in ("setuptools", "wheel")]' \
    && echo "===== Vendored packaging metadata =====" \
    && find /usr/local/lib/python3.10/site-packages \
        -maxdepth 4 \
        \( \
            -name "jaraco.context-*.dist-info" \
            -o -name "wheel-*.dist-info" \
        \) \
        -print || true


# ------------------------------------------------------------
# Application port
# ------------------------------------------------------------

EXPOSE 8080


# ------------------------------------------------------------
# OpenSandbox startup
# ------------------------------------------------------------

ENTRYPOINT ["opensandbox-server"]

CMD ["--config", "/etc/opensandbox/config.toml"]
