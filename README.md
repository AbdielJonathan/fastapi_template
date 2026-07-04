# fastapi_template

Template de API REST con **FastAPI** (async-first), listo para desplegar en
**Google Cloud Run**. Expone un CRUD simple de **Usuarios** como punto de
partida limpio.

## Stack

- **FastAPI** async-first (todos los handlers son `async def`).
- **SQLAlchemy 2.0 async** con driver **`asyncmy`** (MySQL).
- **Uvicorn** como servidor ASGI.
- **uv** para gestión de dependencias (`pyproject.toml` + `uv.lock`).
- **pydantic-settings** para configuración por entorno.
- Tests con **pytest** + **pytest-asyncio** (contra SQLite en memoria por
  defecto).

## Estructura

```
app/
├── main.py            # App FastAPI, lifespan, routers, /health, CORS
├── core/settings.py   # Configuración de entorno (pydantic-settings)
├── db.py              # SOLO infra de DB: engine async, sesión, Base, get_session
├── models.py          # Modelos SQLAlchemy (ORM): User
├── store.py           # Lógica de negocio: CRUD async sobre AsyncSession
├── utils.py           # Ejemplo del patrón CPU-bound + run_in_threadpool
├── dtos/user.py       # Schemas Pydantic (contratos de la API)
└── routers/
    ├── users.py       # CRUD /usuarios
    └── tasks.py       # Placeholder /tareas (uso futuro)
tests/                 # conftest + unit (store) + integración (API)
```

Separación estricta: `core/settings.py` = configuración de entorno; `db.py` =
solo infraestructura de DB; `models.py` = modelos ORM; `dtos/` = schemas
Pydantic. **Los modelos ORM y los DTOs nunca se mezclan.**

## Puesta en marcha (local)

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.12.

```bash
# 1. Instalar dependencias (crea el .venv)
uv sync

# 2. Configurar entorno
cp .env.template .env   # edita las credenciales de tu MySQL

# 3. Levantar la API en local
uv run uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs OpenAPI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

> Nota: `--reload` usa el puerto 8000 de Uvicorn por defecto en local. En
> contenedor/Cloud Run se escucha en `$PORT` (default 8080).

### Base de datos

`db.py` arma la URL async de MySQL a partir de campos discretos de `settings`
(`DB_HOSTNAME`, `DB_PORT`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME`):

```
mysql+asyncmy://USER:PASSWORD@HOST:PORT/NAME
```

Al arranque, el `lifespan` crea las tablas con `Base.metadata.create_all`.

> **TODO (producción):** usar **Alembic** para migraciones versionadas en lugar
> de `create_all`, que no gestiona cambios de esquema.

## Tests

```bash
uv run pytest
```

Por defecto corren contra **SQLite en memoria** (`sqlite+aiosqlite://`): sin
infra, rápido y portable. `conftest.py` crea un engine de test propio y hace
override de `get_session`.

Para probar contra **MySQL real** (motor de producción):

```bash
TEST_DATABASE_URL="mysql+asyncmy://user:pass@127.0.0.1:3306/test" uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Docker

```bash
# Build
docker build -t fastapi_template .

# Run (mapea el puerto y pasa las variables de entorno)
docker run --rm -p 8080:8080 --env-file .env fastapi_template
```

El `Dockerfile` es multi-stage con uv: un *builder* que crea el `.venv` con
`uv sync --frozen --no-dev` y una imagen *final* mínima con usuario no-root.
Escucha en `0.0.0.0:$PORT` (default 8080).

## Deploy a Cloud Run

```bash
# Build + deploy directo desde el fuente
gcloud run deploy fastapi_template \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars APP_NAME=fastapi_template,DB_NAME=buholegal,DB_USERNAME=buholegal \
  --set-secrets DB_PASSWORD=db-password:latest \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE
```

Para **Cloud SQL** por unix socket, pon como hostname el socket de la instancia:

```
DB_HOSTNAME=/cloudsql/PROJECT:REGION:INSTANCE
```

`db.py` detecta un hostname que empieza por `/` y construye la URL con el
parámetro `unix_socket`. Cloud Run inyecta `PORT` automáticamente; el contenedor
ya lo respeta.

## Patrón async + threadpool

La API es **I/O-bound**, así que se usa async de punta a punta (SQLAlchemy async,
Uvicorn) para maximizar la concurrencia por instancia en Cloud Run.

Para trabajo **CPU-bound** (o librerías síncronas y bloqueantes) hay que
delegarlo a un threadpool para no bloquear el event loop. `app/utils.py` incluye
el molde de referencia:

```python
from starlette.concurrency import run_in_threadpool

def heavy_cpu_task(payload: str) -> str:
    ...  # trabajo CPU-bound síncrono

async def run_heavy_cpu_task(payload: str) -> str:
    # Corre en el threadpool; el event loop sigue atendiendo otras requests.
    return await run_in_threadpool(heavy_cpu_task, payload)
```

Regla: I/O → async; CPU-bound → `run_in_threadpool` (o
`anyio.to_thread.run_sync`). El CRUD actual no lo necesita; es solo la plantilla.

## Notas de diseño

- **Settings**: los campos de DB tienen valores por defecto para que el template
  importe y los tests corran sin un `.env`. En producción se sobreescriben con
  variables de entorno. Se usa `SettingsConfigDict` (idioma de pydantic-settings
  v2) en lugar de la antigua `class Config`.
- `routers/tasks.py` es un placeholder sin endpoints; su `include_router` está
  comentado en `main.py` a la espera de implementación.
