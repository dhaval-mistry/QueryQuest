# syntax=docker/dockerfile:1
# Build from the repository root. Select QueryQuest_GPT with --build-arg.
FROM python:3.12-slim-bookworm AS dependencies
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv
ARG APP_VARIANT=QueryQuest_AWS
ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1
WORKDIR /app
COPY ${APP_VARIANT}/pyproject.toml ${APP_VARIANT}/uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

FROM python:3.12-slim-bookworm AS runtime
ARG APP_VARIANT=QueryQuest_AWS
ENV PATH="/app/.venv/bin:$PATH" \
    HOME=/home/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860 \
    GRADIO_ANALYTICS_ENABLED=False
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=dependencies /app/.venv /app/.venv
COPY --chown=app:app ${APP_VARIANT}/ ./
USER app
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os,urllib.request; port=os.getenv('PORT') or os.getenv('GRADIO_SERVER_PORT','7860'); urllib.request.urlopen('http://127.0.0.1:'+port+'/',timeout=4).close()"
CMD ["python", "app.py"]
