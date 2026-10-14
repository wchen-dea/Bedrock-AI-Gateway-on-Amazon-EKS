FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system --gid 10001 app && adduser --system --uid 10001 --gid 10001 app
COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --compile-bytecode
COPY app ./app
USER 10001:10001
EXPOSE 8080
ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
