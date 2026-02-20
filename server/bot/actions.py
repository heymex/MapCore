# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Action executor — dispatches side-effects for triggered bot rules.

Supports ``log``, ``send_message``, ``webhook``, and ``telemetry_request``
action types.  The ``send_message`` action requires a working
pyMC_Repeater send endpoint (placeholder until the API is mapped).
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ..models import BotRule

logger = logging.getLogger(__name__)

REPEATER_URL: str = os.getenv("REPEATER_URL", "http://localhost:8000")


class ActionExecutor:
    """Dispatches rule actions based on :attr:`BotRule.action_type`."""

    async def execute(self, rule: BotRule, event: dict) -> None:
        """Run the action defined by *rule* in response to *event*.

        Args:
            rule: The triggered bot rule.
            event: The event that matched the rule.
        """
        config: dict = json.loads(rule.action_config)
        action = rule.action_type

        if action == "log":
            logger.info("[BOT] Rule '%s' triggered: %s", rule.name, event)

        elif action == "send_message":
            await self._send_message(
                destination=config.get("destination", "flood"),
                message=config["message"],
            )

        elif action == "webhook":
            await self._call_webhook(config["url"], event)

        elif action == "telemetry_request":
            await self._request_telemetry(config.get("node_hash"))

        else:
            logger.warning("[BOT] Unknown action type '%s'", action)

    async def _send_message(self, destination: str, message: str) -> None:
        """Send a message through pyMC_Repeater's command API.

        .. note::
           The Repeater send endpoint is a placeholder — verify the
           actual route before deploying.

        Args:
            destination: Target node hash or ``"flood"``.
            message: Text payload to transmit.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{REPEATER_URL}/api/send",  # PLACEHOLDER — verify endpoint
                    json={"destination": destination, "message": message},
                    timeout=5.0,
                )
                resp.raise_for_status()
                logger.info("[BOT] Sent message to %s: %s", destination, message)
        except Exception as exc:
            logger.warning("[BOT] Failed to send message: %s", exc)

    async def _call_webhook(self, url: str, event: dict) -> None:
        """POST the event payload to an external webhook URL.

        Args:
            url: Webhook endpoint.
            event: Event dict to forward.
        """
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=event, timeout=5.0)
                logger.info("[BOT] Webhook delivered to %s", url)
        except Exception as exc:
            logger.warning("[BOT] Webhook failed for %s: %s", url, exc)

    async def _request_telemetry(self, node_hash: str | None) -> None:
        """Request telemetry from a specific node.

        .. note::
           Endpoint TBD — currently logs the intent only.

        Args:
            node_hash: Target node hash, or ``None`` for the local node.
        """
        logger.info(
            "[BOT] Telemetry request for %s — endpoint TBD",
            node_hash or "local",
        )
