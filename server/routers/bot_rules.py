# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""CRUD endpoints for bot automation rules."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session_dep
from ..models import BotRule
from ..schemas import BotRuleCreate, BotRuleResponse

router = APIRouter(tags=["bot"])


@router.get("/bot/rules", response_model=list[BotRuleResponse])
def list_rules(session: Session = Depends(get_session_dep)) -> list[BotRule]:
    """Return all bot rules.

    Args:
        session: Injected database session.

    Returns:
        List of :class:`BotRule` records.
    """
    return list(session.exec(select(BotRule)).all())


@router.get("/bot/rules/{rule_id}", response_model=BotRuleResponse)
def get_rule(
    rule_id: int,
    session: Session = Depends(get_session_dep),
) -> BotRule:
    """Return a single bot rule by ID.

    Args:
        rule_id: Primary key of the rule.
        session: Injected database session.

    Returns:
        The matching :class:`BotRule`.

    Raises:
        HTTPException: 404 if the rule is not found.
    """
    rule = session.get(BotRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/bot/rules", response_model=BotRuleResponse)
def create_rule(
    body: BotRuleCreate,
    session: Session = Depends(get_session_dep),
) -> BotRule:
    """Create a new bot rule.

    Args:
        body: Rule creation payload.
        session: Injected database session.

    Returns:
        The newly created :class:`BotRule`.
    """
    rule = BotRule(**body.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.put("/bot/rules/{rule_id}", response_model=BotRuleResponse)
def update_rule(
    rule_id: int,
    body: BotRuleCreate,
    session: Session = Depends(get_session_dep),
) -> BotRule:
    """Update an existing bot rule.

    Args:
        rule_id: Primary key of the rule to update.
        body: Updated fields.
        session: Injected database session.

    Returns:
        The updated :class:`BotRule`.

    Raises:
        HTTPException: 404 if the rule is not found.
    """
    rule = session.get(BotRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, val in body.model_dump().items():
        setattr(rule, key, val)
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.delete("/bot/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    session: Session = Depends(get_session_dep),
) -> dict:
    """Delete a bot rule.

    Args:
        rule_id: Primary key of the rule to delete.
        session: Injected database session.

    Returns:
        Simple ``{"ok": True}`` acknowledgement.

    Raises:
        HTTPException: 404 if the rule is not found.
    """
    rule = session.get(BotRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(rule)
    session.commit()
    return {"ok": True}
