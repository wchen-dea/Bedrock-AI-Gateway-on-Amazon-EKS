FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --compile-bytecode
COPY app ./app
USER app
EXPOSE 8080
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
