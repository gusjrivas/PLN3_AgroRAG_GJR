# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12.16-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ARG CADDY_IMAGE=caddy:2.11.9-alpine@sha256:0bbb055bda6793c999bde78b1b5ce3e89f829fb031af2cf50056ea1246559fee
ARG CADDY_BUILDER_IMAGE=caddy:2.11.9-builder-alpine@sha256:646fee578e680989ca5c7fd1ce6f1de574d19fd71ef2221810cc0510a9f40c86

FROM ${PYTHON_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM builder AS observability-builder

RUN uv sync --frozen --no-dev --no-editable --extra tracing

FROM ${PYTHON_IMAGE} AS runtime-base

ARG APP_VERSION=0.1.0
ARG VCS_REF=unknown
ARG SOURCE_URL=https://github.com/gusjrivas/PLN3_AgroRAG_GJR

LABEL org.opencontainers.image.title="AgroRAG" \
      org.opencontainers.image.description="Asistente documental verificable para horticultura" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}"

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /var/lib/agrorag/catalogue \
    && chown -R 10001:10001 /var/lib/agrorag

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGRO_RELEASE_VERSION=${APP_VERSION} \
    AGRO_COMMIT_SHA=${VCS_REF} \
    HOME=/tmp \
    XDG_CONFIG_HOME=/tmp/.config
WORKDIR /app

FROM runtime-base AS api-base

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "agro_rag.bootstrap.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM api-base AS api

COPY --from=builder --chown=10001:10001 /opt/venv /opt/venv

FROM api-base AS api-observability

COPY --from=observability-builder --chown=10001:10001 /opt/venv /opt/venv

FROM runtime-base AS runtime

COPY --from=builder --chown=10001:10001 /opt/venv /opt/venv

FROM runtime AS ui

COPY --chown=10001:10001 src/agro_rag_ui/app.py /app/ui.py
USER 10001:10001
EXPOSE 8501
CMD ["streamlit", "run", "/app/ui.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--browser.gatherUsageStats", "false"]

FROM ${CADDY_BUILDER_IMAGE} AS gateway-builder

ENV CGO_ENABLED=0 GOTOOLCHAIN=local
WORKDIR /build/caddy
# Caddy 2.11.9 predates the x/net fix for CVE-2026-78661.
RUN go mod download github.com/caddyserver/caddy/v2@v2.11.9 \
    && cp -R "$(go env GOMODCACHE)/github.com/caddyserver/caddy/v2@v2.11.9/." . \
    && chmod u+w go.mod go.sum \
    && go get golang.org/x/net@v0.62.0 \
    && go build -mod=readonly -trimpath -ldflags "-s -w -X github.com/caddyserver/caddy/v2.CustomVersion=v2.11.9" -o /out/caddy ./cmd/caddy \
    && go version -m /out/caddy | grep -E '^[[:space:]]+dep[[:space:]]+golang\.org/x/net[[:space:]]+v0\.62\.0[[:space:]]'

FROM ${CADDY_IMAGE} AS gateway

ARG APP_VERSION=0.1.0
ARG VCS_REF=unknown
ARG SOURCE_URL=https://github.com/gusjrivas/PLN3_AgroRAG_GJR

LABEL org.opencontainers.image.title="AgroRAG gateway" \
      org.opencontainers.image.description="Gateway TLS de AgroRAG" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}"

COPY --from=gateway-builder /out/caddy /usr/bin/caddy
RUN apk upgrade --no-cache \
    && setcap cap_net_bind_service=+p /usr/bin/caddy \
    && addgroup -g 10002 -S gateway \
    && adduser -u 10002 -S -D -H -G gateway gateway \
    && mkdir -p /data/caddy /config/caddy \
    && chown -R 10002:10002 /data /config
COPY --chown=10002:10002 infra/gateway/Caddyfile /etc/caddy/Caddyfile
USER 10002:10002
EXPOSE 80 443
