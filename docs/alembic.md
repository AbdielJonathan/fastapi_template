# Migraciones con Alembic

Guía práctica de cómo se gestiona el esquema de la base de datos en este
proyecto. **El esquema lo gestiona exclusivamente Alembic**. Antes de levantar la
API por primera vez —o en cada deploy— hay que aplicar las migraciones.

> Todos los comandos van con el prefijo `uv run` (usa el `.venv` del proyecto sin
> activarlo). Si activaste el entorno (`source .venv/bin/activate`), puedes
> omitir `uv run`.

## Cómo está configurado aquí

- **Modo async**: Alembic se inicializó con el template `async`, así reutiliza el
  mismo driver `asyncmy` que la app.
- **`alembic.ini`**: config general. La `sqlalchemy.url` **no** se fija aquí; la
  provee `env.py`.
- **`alembic/env.py`**: el "pegamento" con la app. En concreto:
  - `target_metadata = Base.metadata` → Alembic conoce tus modelos
    (paquete `app/models/`), necesario para el `--autogenerate`.
  - La URL de conexión sale de `app.core.settings` (la misma que la app), y se
    puede sobreescribir con la variable de entorno `DATABASE_URL`.
  - `include_name` → filtro que limita el `--autogenerate` a **las tablas de tus
    modelos** (+ `alembic_version`). Es imprescindible porque la DB es compartida
    con la app legacy y tiene cientos de tablas ajenas. Ver
    [Trabajar con una DB compartida](#trabajar-con-una-db-compartida-el-filtro-include_name).
- **`alembic/versions/`**: aquí viven los archivos de migración. Ya hay uno
  inicial, `create users table`.

## Conceptos en 30 segundos

- **Revisión (revision)**: un archivo de migración en `alembic/versions/`, con un
  `revision` (id único) y un `down_revision` (a quién sigue). Encadenadas forman
  un historial lineal.
- **`head`**: la última revisión de la cadena. `base`: el estado vacío (antes de
  cualquier migración).
- **`alembic_version`**: tabla que Alembic crea en tu DB para recordar en qué
  revisión está el esquema.
- **`upgrade` / `downgrade`**: aplicar o revertir migraciones.

## Comandos del día a día

```bash
# Aplicar TODAS las migraciones pendientes (lo más habitual)
uv run alembic upgrade head

# Ver en qué revisión está la base de datos ahora mismo
uv run alembic current

# Ver el historial de migraciones (encadenado)
uv run alembic history --verbose

# Ver cuál es la última revisión disponible en el código
uv run alembic heads

# Revertir la última migración
uv run alembic downgrade -1

# Volver al estado vacío (revierte todo)
uv run alembic downgrade base

# Aplicar/revertir hasta una revisión concreta (por su id)
uv run alembic upgrade fdd812fef97f
uv run alembic downgrade fdd812fef97f

# Ver el SQL sin ejecutarlo (modo offline), útil para revisar o para DBAs
uv run alembic upgrade head --sql
```

## El flujo con `--autogenerate` (lo importante)

`--autogenerate` compara **tus modelos** (`Base.metadata`, lo que *debería*
existir) contra el **estado real de la base de datos** (lo que *existe*) y
escribe una migración con las diferencias. Es la forma normal de crear
migraciones cuando cambias los modelos.

### Receta paso a paso

```bash
# 1. Asegúrate de que la DB está al día ANTES de autogenerar
uv run alembic upgrade head

# 2. Cambia tus modelos en app/models/ (p. ej. app/models/user.py)
#    (p. ej. añades una columna `telefono` a User)

# 3. Genera la migración comparando modelos vs DB
uv run alembic revision --autogenerate -m "add telefono a user"

# 4. ABRE el archivo generado en alembic/versions/ y REVÍSALO (ver abajo)

# 5. Aplícala
uv run alembic upgrade head
```

> **El paso 1 importa:** autogenerate compara contra la DB conectada. Si la DB no
> está en `head`, las diferencias que detecte estarán mezcladas con migraciones
> que aún no aplicaste y saldrá basura.

### ⚠️ SIEMPRE revisa la migración autogenerada

Autogenerate es una ayuda, **no** es infalible. Detecta bien:

- tablas y columnas nuevas o eliminadas,
- cambios de nulabilidad,
- índices y unique constraints,
- (con `compare_type=True`, ya activado aquí) cambios de tipo de columna.

Pero **NO detecta ni acierta** en:

- **renombrar** una tabla o columna → lo ve como "borra la vieja + crea la
  nueva" (perderías datos). Hay que editarlo a mano con `op.alter_column(...,
  new_column_name=...)`.
- **cambios de `server_default`** y algunos defaults, según el caso.
- **datos**: autogenerate solo toca el esquema. Si necesitas migrar/backfillear
  datos, se escribe a mano en el `upgrade()`.
- objetos que no están en la metadata: **vistas, triggers, procedimientos y
  functions** son invisibles para autogenerate (nunca los compara ni genera
  `DROP` sobre ellos). Si los quieres versionar, se hace a mano con
  `op.execute("CREATE VIEW ...")`.
- **tablas ajenas** (de la app legacy que comparte la DB): sin protección,
  Alembic las vería en la DB pero no en la metadata y querría **borrarlas**. Por
  eso este proyecto usa el filtro `include_name` (ver
  [abajo](#trabajar-con-una-db-compartida-el-filtro-include_name)). Aun así,
  **nunca apliques a ciegas**: lee el `upgrade()` generado.

Regla de oro: lee siempre el `upgrade()`/`downgrade()` generado antes de
aplicarlo y ajusta lo que haga falta.

### Crear una migración vacía (sin autogenerate)

Cuando quieres escribir los cambios a mano (renombrados, migración de datos,
DDL que autogenerate no cubre):

```bash
uv run alembic revision -m "descripcion del cambio"
```

Esto crea el archivo sin conectarse a la DB; rellenas tú `upgrade()` y
`downgrade()` con operaciones `op.*` (`op.create_table`, `op.add_column`,
`op.alter_column`, `op.drop_column`, `op.execute("SQL...")`, etc.).

## ¿Contra qué base de datos corre?

Por defecto, `env.py` usa la misma URL que la app (desde `settings`, es decir tu
`.env`). Para apuntar a otra DB sin tocar el `.env`, exporta `DATABASE_URL`:

```bash
# Contra el MySQL de test que corre en Docker (puerto 3307)
DATABASE_URL="mysql+asyncmy://root:pearsonhardman@127.0.0.1:3307/buholegal" \
  uv run alembic upgrade head

# Contra un SQLite local de prueba (rápido, sin infra)
DATABASE_URL="sqlite+aiosqlite:///./prueba.db" \
  uv run alembic upgrade head
```

## El `__init__.py` de `app/models/` es obligatorio

`app/models/__init__.py` **no es un archivo de relleno**: es el registro central
de modelos. `env.py` hace `from app import models` para que **todos** los modelos
queden registrados en `Base.metadata`, y eso solo ocurre si el `__init__.py`
importa cada uno.

Si borras o dejas incompleto ese `__init__.py`:

- Python trata `app/models` como *namespace package*: el import no falla, pero
  **no ejecuta nada** que importe tus archivos de modelo.
- Ningún modelo se registra en `Base.metadata` (queda vacía).
- Autogenerate no ve ninguna tabla → **genera migraciones vacías** (`pass`).

Por eso, **al añadir un modelo nuevo** hay que registrarlo:

```python
# app/models/__init__.py
from app.models.mascota import Mascota
from app.models.superheroes import SuperHeroe
from app.models.user import User

__all__ = ["Mascota", "SuperHeroe", "User"]
```

Regla: un archivo por modelo en `app/models/<nombre>.py`, y añádelo tanto al
`import` como a `__all__` de `__init__.py`. Si la migración autogenerada sale
vacía cuando esperabas una tabla nueva, lo primero que debes revisar es esto.

## Trabajar con una DB compartida: el filtro `include_name`

La base de datos de este proyecto es **compartida con la app legacy** y contiene
cientos de tablas, vistas y triggers que **no** son modelos de esta app. El
`--autogenerate` compara en ambos sentidos: cualquier tabla que exista en la DB
pero no en `Base.metadata` la interpreta como "hay que borrarla" y genera un
`op.drop_table(...)`. Sin protección, una simple migración generaría **miles de
`drop_table`** sobre datos que no gestiona esta app.

La solución en `env.py` es un filtro que limita la comparación a tus tablas:

```python
def include_name(name, type_, parent_names):
    if type_ == "table":
        return name in target_metadata.tables or name == "alembic_version"
    return True
```

Se pasa a `context.configure(..., include_name=include_name)` en los dos modos
(online y offline).

Puntos clave:

- **Solo aplica a tablas.** `include_name` se llama con `type_` de `"table"`,
  `"column"`, `"index"`, etc., nunca para vistas/triggers.
- **Vistas, triggers, procedures y functions ya están a salvo** aunque no exista
  este filtro: el autogenerate no los refleja ni los compara. El filtro protege
  únicamente contra el borrado de **tablas** ajenas.
- **Al añadir un modelo nuevo**, su tabla entra automáticamente en
  `target_metadata.tables`, así que el filtro la incluye sin tener que tocar
  nada.

## ¿Puedo editar a mano un archivo de revisión?

Sí, y a veces es necesario (el `# please adjust!` del autogenerate lo invita). La
clave es **cuándo**:

- **✅ Seguro** si la revisión **aún no se aplicó** a ninguna DB (`alembic
  current` está por debajo de ella) y **no se ha compartido** en el repo. Puedes
  editarla libremente antes de correr `upgrade`.
- **⚠️ No la edites** (o hazlo con mucho cuidado) si **ya se aplicó** en alguna DB
  (test, staging, prod) o **ya está en el repo** y otros la aplicaron.

Por qué: Alembic solo mira el `version_num` de la tabla `alembic_version`. Una DB
que ya aplicó una revisión **no la vuelve a ejecutar**, así que tu edición nunca
corre ahí → esquemas desincronizados entre entornos.

Qué es válido editar (en una revisión no aplicada):

- ajustar tipos que autogenerate detectó mal;
- añadir lo que autogenerate no cubre: `op.execute("CREATE VIEW ...")`, triggers,
  migración de datos (`op.execute("UPDATE ...")`), `server_default`, orden de
  operaciones, `batch_alter_table`…

Qué **no** tocar: `revision` y `down_revision` (forman la cadena; cambiarlos a
mano rompe el historial o crea múltiples heads).

**Si necesitas cambiar algo ya aplicado o compartido:** no edites la vieja, crea
una **migración nueva** encima que haga el ajuste. El historial es append-only,
igual que git.

## Situaciones frecuentes

- **"Target database is not up to date"** al autogenerar → te falta aplicar
  migraciones: `uv run alembic upgrade head` y reintenta.
- **La migración autogenerada sale vacía** → no hay diferencias entre modelos y
  DB (todo está sincronizado). Puedes borrar ese archivo.
- **Adoptar Alembic en una DB que ya tiene las tablas** (creadas antes por
  `create_all`, por ejemplo): marca la revisión como aplicada sin ejecutar el
  DDL con `stamp`:
  ```bash
  uv run alembic stamp head
  ```
- **Múltiples "heads"** (dos ramas de migraciones, típico tras un merge de git)
  → se resuelve fusionándolas:
  ```bash
  uv run alembic merge -m "merge heads" <head1> <head2>
  ```

## Relación con los tests

Los tests **no** usan Alembic: crean el esquema con `Base.metadata.create_all`
sobre SQLite en memoria (ver `tests/conftest.py`). Es a propósito —así los tests
son rápidos e independientes del historial de migraciones. Alembic es para las
DB reales (dev, test en Docker, producción).
