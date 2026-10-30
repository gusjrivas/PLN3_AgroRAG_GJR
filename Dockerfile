# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337

FROM ${PYTHON_IMAGE} AS builder

COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /build

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

FROM ${PYTHON_IMAGE} AS runtime

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
    HOME=/tmp \
    XDG_CONFIG_HOME=/tmp/.config
WORKDIR /app
COPY --from=builder --chown=10001:10001 /opt/venv /opt/venv

FROM runtime AS api

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "agro_rag.bootstrap.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS ui

COPY --chown=10001:10001 src/agro_rag_ui/app.py /app/ui.py
USER 10001:10001
EXPOSE 8501
CMD ["streamlit", "run", "/app/ui.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--browser.gatherUsageStats", "false"]
