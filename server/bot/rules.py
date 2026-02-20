# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Rule engine — matches incoming events against stored bot rules."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import select

from ..database import get_session
from ..models import BotRule

if TYPE_CHECKING:
    from .actions import ActionExecutor

logger = logging.getLogger(__name__)


class RuleEngine:
    """Evaluates events against all enabled :class:`BotRule` records.

    Each rule specifies a ``trigger_type`` and ``trigger_value``.  When an
    incoming event matches, the corresponding action is dispatched through
    an :class:`ActionExecutor`.
    """

    async def evaluate(self, event: dict, executor: ActionExecutor) -> None:
        """Check *event* against every enabled rule and fire matches.

        Args:
            event: Dict with ``"type"`` and ``"data"`` keys.
            executor: Action executor used to dispatch triggered rules.
        """
        with get_session() as session:
            rules = list(
                session.exec(
                    select(BotRule).where(BotRule.enabled == True)
                ).all()  # noqa: E712
            )

        for rule in rules:
            if await self._matches(rule, event):
                logger.info("Rule '%s' matched event", rule.name)
                await executor.execute(rule, event)
                # Update trigger statistics
                with get_session() as session:
                    db_rule = session.get(BotRule, rule.id)
                    if db_rule:
                        db_rule.last_triggered = datetime.now(UTC)
                        db_rule.trigger_count += 1
                        session.add(db_rule)
                        session.commit()

    async def _matches(self, rule: BotRule, event: dict) -> bool:
        """Determine whether *rule* matches *event*.

        Args:
            rule: The bot rule to test.
            event: The incoming event dict.

        Returns:
            ``True`` if the rule's trigger conditions are satisfied.
        """
        trigger = rule.trigger_type
        value = rule.trigger_value
        data = event.get("data", {})

        if trigger == "packet_type":
            return data.get("packet_type") == value

        if trigger == "keyword":
            # Only works on decrypted / cleartext payloads
            payload = data.get("payload_hex", "")
            if not payload:
                return False
            try:
                text = bytes.fromhex(payload).decode("utf-8", errors="ignore")
                return value.lower() in text.lower()
            except (ValueError, UnicodeDecodeError):
                return False

        if trigger == "node_seen":
            return data.get("source_hash") == value

        return False
