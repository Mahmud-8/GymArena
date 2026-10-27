ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE} AS dependencies
WORKDIR /build
COPY infra/requirements.lock ./requirements.lock
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --only-binary=:all: --require-hashes -r requirements.lock

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=10001:10001 packages/runtime/gymarena_runtime ./gymarena_runtime
COPY --chown=10001:10001 services/challenge-service/api ./api
ARG VCS_REF=working-tree
LABEL org.opencontainers.image.source="https://github.com/Mahmud-8/GymArena" \
      org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.title="GymArena challenge-service foundation"
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=4).close()"]
CMD ["python", "-m", "uvicorn", "api.routes:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
