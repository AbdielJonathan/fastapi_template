"""DTOs Pydantic para User: contratos de entrada/salida de la API.

Nunca se mezclan con los modelos ORM (`app/models.py`). `from_attributes=True`
permite construir estos schemas directamente desde una instancia ORM.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    """Datos para crear un usuario."""


class UserUpdate(BaseModel):
    """Actualización parcial: todos los campos son opcionales."""

    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    """Representación de salida de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
