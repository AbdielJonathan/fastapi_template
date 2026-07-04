# Comandos de uv (y su equivalencia con pip)

Este proyecto usa [**uv**](https://docs.astral.sh/uv/) para gestionar dependencias
y el entorno virtual, en lugar de `pip` + `requirements.txt`. La diferencia clave:

- Con **pip** instalabas paquetes sueltos y mantenías un `requirements.txt` a mano.
- Con **uv** hay un solo comando (`uv add`) que **edita `pyproject.toml`,
  actualiza `uv.lock` e instala en `.venv`** de forma atómica. El estado del
  proyecto vive en `pyproject.toml` (lo que pides) + `uv.lock` (las versiones
  exactas resueltas).

No necesitas activar el `.venv`: los comandos se corren con `uv run ...`.

## Tabla de equivalencias

| Antes (pip)                       | Ahora (uv)                        |
| --------------------------------- | --------------------------------- |
| `pip install requests`            | `uv add requests`                 |
| `pip install "requests>=2.30"`    | `uv add "requests>=2.30"`         |
| `pip install -r requirements.txt` | `uv sync` (instala desde el lock) |
| `pip uninstall requests`          | `uv remove requests`              |
| `pip freeze`                      | `uv pip freeze`                   |
| `python -m venv .venv`            | `uv venv` (o automático en `sync`)|
| `python script.py`                | `uv run python script.py`         |

## Gestionar dependencias

```bash
# Añadir una dependencia de producción
uv add httpx

# Fijar/limitar versión
uv add "httpx>=0.27"

# Dependencia SOLO de desarrollo (tests, linters, etc.)
uv add --dev pytest-cov

# Quitar una dependencia
uv remove httpx
```

Cada `uv add` hace tres cosas de una vez:

1. La escribe en `[project.dependencies]` (o en `[dependency-groups] dev` si usas
   `--dev`) dentro de `pyproject.toml`.
2. Resuelve versiones compatibles y actualiza `uv.lock`.
3. La instala en el `.venv`.

## Instalar / sincronizar el entorno

```bash
# Instala TODO lo del lockfile (equivale a pip install -r requirements.txt)
uv sync

# Solo dependencias de producción (sin el grupo dev) — es lo que usa el Dockerfile
uv sync --no-dev

# Falla si pyproject.toml y uv.lock no coinciden (lo que corre CI)
uv sync --frozen
```

## Ejecutar cosas en el entorno

No hace falta `source .venv/bin/activate`; usa `uv run`:

```bash
uv run fastapi dev app/main.py         # levantar la API sin Docker (FastAPI CLI)
uv run uvicorn app.main:app --reload   # alternativa: uvicorn directo
uv run pytest                          # tests
uv run ruff check .                    # linter
uv run python script.py                # cualquier script
```

> Para probar la API sin Docker, `uv run fastapi dev app/main.py` recarga en
> caliente. Necesita un MySQL alcanzable (puedes usar el de Docker en el puerto
> `3307`); ver detalles en el README.

## Importar un requirements.txt existente

Si te pasan un `requirements.txt`, uv puede volcarlo al proyecto de golpe:

```bash
uv add -r requirements.txt
```

## El lockfile (`uv.lock`)

- Registra las versiones **exactas** de todas las dependencias (directas y
  transitivas), garantizando instalaciones reproducibles.
- **Commitea siempre `pyproject.toml` y `uv.lock` juntos.** CI corre
  `uv sync --frozen`, que falla si el lock está desactualizado respecto al
  `pyproject.toml`.
- Para regenerarlo manualmente (raro, `uv add` ya lo hace): `uv lock`.
- Para subir dependencias a versiones nuevas dentro de los rangos permitidos:
  `uv lock --upgrade`.

## Ojo con Docker

Las dependencias se "hornean" en la imagen (`uv sync --frozen --no-dev` en el
`Dockerfile`). Tras un `uv add`/`uv remove` hay que reconstruir la imagen:

```bash
docker compose up -d --build app
```
