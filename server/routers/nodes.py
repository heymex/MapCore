# Copyright © 2025-26 l5yth & contributors
# Licensed under BSD 3-Clause License

"""REST endpoints for querying mesh nodes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session_dep
from ..models import Node

router = APIRouter(tags=["nodes"])


@router.get("/nodes")
def get_nodes(
    limit: int = 100,
    session: Session = Depends(get_session_dep),
) -> list[Node]:
    """Return mesh nodes ordered by most recently seen.

    Args:
        limit: Maximum number of nodes to return (default 100).
        session: Injected database session.

    Returns:
        List of :class:`Node` records.
    """
    return list(
        session.exec(
            select(Node).order_by(Node.last_seen.desc()).limit(limit)
        ).all()
    )


@router.get("/nodes/{node_hash}")
def get_node(
    node_hash: str,
    session: Session = Depends(get_session_dep),
) -> Node:
    """Return a single node by its hash prefix.

    Args:
        node_hash: 2-char hex prefix to look up.
        session: Injected database session.

    Returns:
        The matching :class:`Node`.

    Raises:
        HTTPException: 404 if the node is not found.
    """
    node = session.exec(
        select(Node).where(Node.node_hash == node_hash)
    ).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node
