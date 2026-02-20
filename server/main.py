# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""MeshCore Monitor — FastAPI application entrypoint.

Run in development with::

    uvicorn server.main:app --reload --port 8001
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .bot.built_in_rules.seed import seed_builtin_rules
from .bot.worker import start_bot_worker
from .database import create_db
from .routers import bot_rules, ingest, nodes, packets, telemetry, ws

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialise database, seed rules, and launch the bot worker."""
    create_db()
    seed_builtin_rules()
    bot_enabled = os.getenv("BOT_ENABLED", "true").lower() in ("1", "true", "yes")
    bot_task = None
    if bot_enabled:
        bot_task = asyncio.create_task(start_bot_worker())
        logger.info("Bot worker task created")
    else:
        logger.info("Bot worker disabled via BOT_ENABLED")
    yield
    if bot_task:
        bot_task.cancel()


app = FastAPI(
    title="MeshCore Monitor",
    version="0.1.0",
    description="A MeshMonitor-equivalent web platform for MeshCore networks.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(ingest.router)
app.include_router(nodes.router, prefix="/api")
app.include_router(packets.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(bot_rules.router, prefix="/api")
app.include_router(ws.router)

# ---------------------------------------------------------------------------
# Static frontend (production build)
# ---------------------------------------------------------------------------
_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
