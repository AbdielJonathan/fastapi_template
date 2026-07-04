"""Placeholder para el futuro recurso ``/tareas``.

De momento el router no expone endpoints; existe para reservar el prefijo y los
tags. Cuando se implemente, se añaden aquí las rutas y se descomenta el
`include_router` correspondiente en `app/main.py`.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/tareas", tags=["tareas"])
