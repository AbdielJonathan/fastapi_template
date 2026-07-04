# ---- Builder: instala dependencias con uv en un venv aislado ----
FROM python:3.12-slim AS builder

# uv oficial (binario estático).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Build deps por si asyncmy necesita compilar extensiones nativas.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Bytecode compilado + copia (no symlink) para poder mover el venv a la imagen final.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Capa cacheable: solo manifiestos primero.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Ahora el código y la instalación final del proyecto.
COPY app ./app
RUN uv sync --frozen --no-dev

# ---- Final: imagen mínima, usuario no-root ----
FROM python:3.12-slim AS final

# libgcc para runtimes compilados; sin toolchain de compilación.
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Copia el venv y el código desde el builder.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app

# El venv al frente del PATH: `uvicorn` resuelve al del venv.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

# Cloud Run inyecta PORT (default 8080). Escuchamos en 0.0.0.0.
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
