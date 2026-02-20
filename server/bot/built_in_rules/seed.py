# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Seed the database with default bot rules if they don't exist yet."""

import json
import logging

from sqlmodel import select

from ...database import get_session
from ...models import BotRule

logger = logging.getLogger(__name__)

BUILTIN_RULES: list[dict] = [
    {
        "name": "Log all ADVERT packets",
        "enabled": False,
        "trigger_type": "packet_type",
        "trigger_value": "ADVERT",
        "action_type": "log",
        "action_config": "{}",
    },
    {
        "name": "Ping reply",
        "enabled": False,
        "trigger_type": "keyword",
        "trigger_value": "ping",
        "action_type": "send_message",
        "action_config": json.dumps({"destination": "flood", "message": "pong"}),
    },
    {
        "name": "New node alert webhook",
        "enabled": False,
        "trigger_type": "node_seen",
        "trigger_value": "",  # fill in a specific node_hash to watch
        "action_type": "webhook",
        "action_config": json.dumps({"url": "https://hooks.example.com/meshcore"}),
    },
]


def seed_builtin_rules() -> None:
    """Insert built-in rules that are not yet present in the database.

    Matching is done by rule name — existing rules with the same name
    are left untouched so user edits are preserved.
    """
    with get_session() as session:
        for rule_data in BUILTIN_RULES:
            existing = session.exec(
                select(BotRule).where(BotRule.name == rule_data["name"])
            ).first()
            if existing:
                continue
            rule = BotRule(**rule_data)
            session.add(rule)
            logger.info("Seeded built-in rule: %s", rule.name)
        session.commit()
