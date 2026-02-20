# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Async bot worker that evaluates rules against incoming events.

The worker consumes from a module-level :class:`asyncio.Queue` populated
by the ingest router.  It runs as an ``asyncio.Task`` created during
FastAPI startup.
"""

import asyncio
import logging

from .actions import ActionExecutor
from .rules import RuleEngine

logger = logging.getLogger(__name__)

event_queue: asyncio.Queue = asyncio.Queue()
"""Module-level queue shared with the ingest router."""


async def start_bot_worker() -> None:
    """Run the bot event loop indefinitely.

    Pulls events from :data:`event_queue`, evaluates them against all
    enabled :class:`~server.models.BotRule` records, and dispatches
    matching actions via :class:`ActionExecutor`.
    """
    engine = RuleEngine()
    executor = ActionExecutor()
    logger.info("Bot worker started")

    while True:
        try:
            event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
            await engine.evaluate(event, executor)
        except asyncio.TimeoutError:
            pass  # Normal — no events in the last second
        except Exception:
            logger.exception("Bot worker error")
