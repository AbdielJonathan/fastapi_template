# Comandos de uv (y su equivalencia con pip)

Este proyecto usa [**uv**](https://docs.astral.sh/uv/) para gestionar dependencias
y el entorno virtual, en lugar de `pip` + `requirements.txt`. La diferencia clave:

- Con **pip** instalabas paquetes sueltos y mantenías un `requirements.txt` a mano.
- Con **uv** hay un solo comando (`uv add`) que **edita `pyproject.toml`,
  actualiza `uv.lock` e instala en `.venv`** de forma atómica. El estado del
  proyecto vive en `pyproject.toml` (lo que pides) + `uv.lock` (las versiones
  exactas resueltas).

No necesitas activar el `.venv`: los comandos se corren con `uv run ...`.

## Crear y activar el entorno virtual (paso a paso)

`uv` puede gestionar el entorno por ti (`uv run` / `uv sync` crean y usan el
`.venv` automáticamente), pero si prefieres el flujo clásico de crear y activar
el venv a mano, aquí lo tienes de principio a fin.

```bash
# 1. Crear el entorno virtual (crea la carpeta .venv/ con Python 3.12)
uv venv

# 2. Activarlo
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows (PowerShell/CMD)

# 3. Instalar las dependencias del proyecto dentro del venv
uv sync

# 4. Ya con el venv activo, corres los comandos SIN el prefijo `uv run`:
fastapi dev app/main.py            # levantar la API (recarga automática)
uvicorn app.main:app --reload      # alternativa
pytest                             # tests
ruff check .                       # linter

# 5. Salir del entorno cuando termines
deactivate
```

Con el venv activado el ejecutable `python` y todos los comandos (`fastapi`,
`uvicorn`, `pytest`, `ruff`) resuelven al del `.venv`, así que ya no hace falta
`uv run` delante.

> **Recomendación:** con uv normalmente puedes saltarte los pasos 1 y 2 y usar
> directamente `uv run <comando>` (p. ej. `uv run fastapi dev app/main.py`), que
> crea/usa el `.venv` solo. Activar el entorno es útil sobre todo si tu editor o
> herramientas esperan un venv activo.

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
