# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""Tests for the bot rule engine trigger matching logic."""

import asyncio

import pytest

from server.bot.rules import RuleEngine
from server.models import BotRule


class TestRuleMatching:
    """Tests for :meth:`RuleEngine._matches`."""

    @pytest.fixture()
    def engine(self) -> RuleEngine:
        """Return a fresh :class:`RuleEngine` instance."""
        return RuleEngine()

    def _run(self, coro):
        """Helper to run a coroutine synchronously."""
        return asyncio.run(coro)

    def test_packet_type_match(self, engine: RuleEngine):
        """packet_type trigger should match on exact type string."""
        rule = BotRule(
            name="test",
            trigger_type="packet_type",
            trigger_value="ADVERT",
            action_type="log",
        )
        event = {"data": {"packet_type": "ADVERT"}}
        assert self._run(engine._matches(rule, event)) is True

    def test_packet_type_no_match(self, engine: RuleEngine):
        """packet_type trigger should not match a different type."""
        rule = BotRule(
            name="test",
            trigger_type="packet_type",
            trigger_value="ADVERT",
            action_type="log",
        )
        event = {"data": {"packet_type": "TXT_MSG"}}
        assert self._run(engine._matches(rule, event)) is False

    def test_keyword_match(self, engine: RuleEngine):
        """keyword trigger should match when payload contains the keyword."""
        rule = BotRule(
            name="test",
            trigger_type="keyword",
            trigger_value="ping",
            action_type="log",
        )
        # "ping" as hex
        payload_hex = "70696e67"
        event = {"data": {"payload_hex": payload_hex}}
        assert self._run(engine._matches(rule, event)) is True

    def test_keyword_no_payload(self, engine: RuleEngine):
        """keyword trigger should not match when there is no payload."""
        rule = BotRule(
            name="test",
            trigger_type="keyword",
            trigger_value="ping",
            action_type="log",
        )
        event = {"data": {}}
        assert self._run(engine._matches(rule, event)) is False

    def test_node_seen_match(self, engine: RuleEngine):
        """node_seen trigger should match on exact source_hash."""
        rule = BotRule(
            name="test",
            trigger_type="node_seen",
            trigger_value="FA",
            action_type="log",
        )
        event = {"data": {"source_hash": "FA"}}
        assert self._run(engine._matches(rule, event)) is True

    def test_node_seen_no_match(self, engine: RuleEngine):
        """node_seen trigger should not match a different source_hash."""
        rule = BotRule(
            name="test",
            trigger_type="node_seen",
            trigger_value="FA",
            action_type="log",
        )
        event = {"data": {"source_hash": "BB"}}
        assert self._run(engine._matches(rule, event)) is False

    def test_unknown_trigger_returns_false(self, engine: RuleEngine):
        """An unrecognised trigger type should not match."""
        rule = BotRule(
            name="test",
            trigger_type="unknown_trigger",
            trigger_value="anything",
            action_type="log",
        )
        event = {"data": {}}
        assert self._run(engine._matches(rule, event)) is False


class TestBotRulesAPI:
    """Tests for the ``/api/bot/rules`` CRUD endpoints."""

    def test_list_rules_empty(self, client):
        """Empty database should return an empty list."""
        resp = client.get("/api/bot/rules")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_rule(self, client):
        """Creating a rule should return the new rule with an ID."""
        resp = client.post(
            "/api/bot/rules",
            json={
                "name": "Test Rule",
                "trigger_type": "packet_type",
                "trigger_value": "ADVERT",
                "action_type": "log",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Rule"
        assert data["id"] is not None
        assert data["enabled"] is True

    def test_update_rule(self, client):
        """Updating a rule should persist the changes."""
        create_resp = client.post(
            "/api/bot/rules",
            json={
                "name": "Before",
                "trigger_type": "packet_type",
                "trigger_value": "ADVERT",
                "action_type": "log",
            },
        )
        rule_id = create_resp.json()["id"]

        update_resp = client.put(
            f"/api/bot/rules/{rule_id}",
            json={
                "name": "After",
                "trigger_type": "keyword",
                "trigger_value": "ping",
                "action_type": "send_message",
                "action_config": '{"message":"pong"}',
            },
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "After"

    def test_delete_rule(self, client):
        """Deleting a rule should remove it from the database."""
        create_resp = client.post(
            "/api/bot/rules",
            json={
                "name": "Doomed",
                "trigger_type": "packet_type",
                "trigger_value": "ACK",
                "action_type": "log",
            },
        )
        rule_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/bot/rules/{rule_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/api/bot/rules/{rule_id}")
        assert get_resp.status_code == 404

    def test_get_nonexistent_rule(self, client):
        """Requesting a non-existent rule should return 404."""
        resp = client.get("/api/bot/rules/9999")
        assert resp.status_code == 404
