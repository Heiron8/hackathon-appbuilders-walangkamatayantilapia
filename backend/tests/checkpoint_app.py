"""Loopback-only verification app using SYNTHETIC vocabulary plus REAL Ollama.

Not a production entry point or shared-vocabulary substitute. Heiron8 owns main.py.
Run from backend: python -m uvicorn tests.checkpoint_app:app --host 127.0.0.1 --port 8000 --no-access-log
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.ai.ollama import OllamaRuntime
from app.api.communication import create_router
from app.api.errors import install_error_handlers
from tests.fixtures import VOCABULARY

runtime = OllamaRuntime()


@asynccontextmanager
async def lifespan(app):
    yield
    await runtime.aclose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
install_error_handlers(app)
app.include_router(create_router(VOCABULARY, runtime))
