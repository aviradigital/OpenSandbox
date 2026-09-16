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

FROM python:3.10-slim AS builder

ARG SETUPTOOLS_SCM_PRETEND_VERSION
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$SETUPTOOLS_SCM_PRETEND_VERSION

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=/app/.venv \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

# Keep build tooling current enough to avoid shipping the vulnerable
# setuptools-vendored jaraco.context/wheel versions detected by Trivy.
RUN uv pip install --python /app/.venv/bin/python --upgrade \
    "setuptools>=82.0.1" \
    "wheel>=0.46.2" \
    "jaraco.context>=6.1.0"

COPY opensandbox_server ./opensandbox_server
COPY LICENSE README.md ./

RUN uv pip install --python /app/.venv/bin/python --no-deps --editable .

FROM python:3.10-slim AS runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    SANDBOX_CONFIG_PATH=/etc/opensandbox/config.toml

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/opensandbox_server /app/opensandbox_server
COPY --from=builder /app/opensandbox_server/examples/example.config.k8s.toml /etc/opensandbox/config.toml
COPY --from=builder /app/opensandbox_server/examples/example.config.k8s.zh.toml /etc/opensandbox/config.zh.toml
COPY --from=builder /app/opensandbox_server/examples/example.batchsandbox-template.yaml /etc/opensandbox/example.batchsandbox-template.yaml
COPY --from=builder /app/opensandbox_server/examples/e2e.batchsandbox-template.yaml /etc/opensandbox/e2e.batchsandbox-template.yaml

EXPOSE 8080

ENTRYPOINT ["opensandbox-server"]
CMD ["--config", "/etc/opensandbox/config.toml"]
