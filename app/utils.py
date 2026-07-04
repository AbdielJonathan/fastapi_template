"""Utilidades: patrón de referencia para trabajo CPU-bound + threadpool.

Este módulo es un *molde* demostrativo. El CRUD actual es I/O-bound (async con
SQLAlchemy) y no lo necesita, pero cuando aparezca trabajo síncrono y
CPU-intensivo (hashing costoso, procesamiento de imágenes, cálculo pesado,
serialización grande...), este es el patrón a seguir para NO bloquear el event
loop de Uvicorn.

Regla de oro:
- I/O-bound (DB, HTTP, ficheros)  -> usa librerías async (ya no bloquean).
- CPU-bound o librerías síncronas  -> delégalo al threadpool con
  `run_in_threadpool` (o `anyio.to_thread.run_sync`).
"""

import hashlib

from starlette.concurrency import run_in_threadpool


def heavy_cpu_task(payload: str, rounds: int = 200_000) -> str:
    """Función SÍNCRONA claramente CPU-bound (ejemplo).

    Aplica SHA-256 en muchas iteraciones encadenadas para simular un cálculo
    intensivo. Al ser síncrona y pesada, llamarla directamente dentro de un
    handler async bloquearía el event loop y frenaría toda la instancia.
    """
    digest = payload.encode("utf-8")
    for _ in range(rounds):
        digest = hashlib.sha256(digest).digest()
    return digest.hex()


async def run_heavy_cpu_task(payload: str, rounds: int = 200_000) -> str:
    """Ejecuta `heavy_cpu_task` en el threadpool para no bloquear el event loop.

    `run_in_threadpool` corre la función síncrona en un hilo aparte y devuelve
    el control al event loop mientras tanto, de modo que otras requests async
    siguen atendiéndose. Este es el patrón a copiar para cualquier trabajo
    CPU-bound, NO para I/O (que ya se hace con librerías async).
    """
    return await run_in_threadpool(heavy_cpu_task, payload, rounds)
