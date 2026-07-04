"""Paquete de modelos ORM.

Un archivo por modelo. Se re-exportan aquí para que:
- `from app.models import User` siga funcionando, y
- `import app.models` registre TODOS los modelos en `Base.metadata`
  (necesario para el autogenerate de Alembic y el create_all de los tests).

Al añadir un modelo nuevo, crea su archivo `app/models/<nombre>.py` y añádelo
tanto al import como a `__all__` de aquí abajo.
"""

from app.models.user import User

__all__ = ["User"]
