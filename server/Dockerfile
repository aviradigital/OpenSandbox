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

# Security-validation variant
# - Keep server/ as the Docker build context
# - Keep the existing pinned Python base image
# - Apply Debian security updates
# - Update Python packaging tools
# - Keep the existing OpenSandbox runtime layout unchanged

ARG PYTHON_BASE=python:3.10-slim@sha256:8c97ebedc32fd60935cdf5992e935753e2a0f98231830028050e1e04bd3c13c2

FROM ${PYTHON_BASE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=/app/.venv \
    UV_LINK_MODE=copy

WORKDIR /app

# Update Debian packages and explicitly update packages reported by Trivy.
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

# Install uv.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

COPY pyproject.toml uv.lock ./

# Install application dependencies.
RUN uv sync --frozen --no-dev --no-install-project

COPY opensandbox_server ./opensandbox_server

COPY LICENSE README.md ./

# Install the OpenSandbox server itself.
RUN uv pip install --no-deps --editable .

# Update application Python packaging tools.
RUN uv pip install \
        --python /app/.venv/bin/python \
        --upgrade \
        "setuptools>=82.0.1" \
        "wheel>=0.46.2"


# ============================================================
# Runtime image
# ============================================================

FROM ${PYTHON_BASE} AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    SANDBOX_CONFIG_PATH=/etc/opensandbox/config.toml

WORKDIR /app

# Apply Debian security updates in the final runtime image.
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

# Update system Python packaging tools.
#
# Trivy previously detected vulnerable vendored versions of
# jaraco.context and wheel through setuptools.
RUN python -m pip install \
        --no-cache-dir \
        --upgrade \
        "setuptools>=82.0.1" \
        "wheel>=0.46.2"

COPY --from=builder /app/.venv /app/.venv

COPY --from=builder /app/opensandbox_server /app/opensandbox_server

# Keep the existing runtime configuration unchanged for this
# vulnerability-remediation change.
#
# We will review Docker vs Kubernetes configuration separately.
COPY --from=builder /app/opensandbox_server/examples/example.config.k8s.toml /etc/opensandbox/config.toml

COPY --from=builder /app/opensandbox_server/examples/example.config.k8s.zh.toml /etc/opensandbox/config.zh.toml

COPY --from=builder /app/opensandbox_server/examples/example.batchsandbox-template.yaml /etc/opensandbox/example.batchsandbox-template.yaml

COPY --from=builder /app/opensandbox_server/examples/e2e.batchsandbox-template.yaml /etc/opensandbox/e2e.batchsandbox-template.yaml


# ============================================================
# Security verification during image build
# ============================================================

RUN echo "===== Debian package versions =====" \
    && dpkg-query -W \
        -f='${Package} ${Version}\n' \
        perl-base \
        gzip \
        libpcre2-8-0 \
        libsqlite3-0 \
    && echo "===== Python packaging versions =====" \
    && python -m pip show setuptools wheel \
    && echo "===== Python packaging metadata =====" \
    && python - <<'PY'
import importlib.metadata as md

for name in ("setuptools", "wheel"):
    try:
        print(f"{name}: {md.version(name)}")
    except Exception as exc:
        print(f"{name}: NOT FOUND ({exc})")
PY


EXPOSE 8080

ENTRYPOINT ["opensandbox-server"]

CMD ["--config", "/etc/opensandbox/config.toml"]
