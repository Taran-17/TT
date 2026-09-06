from __future__ import annotations

"""
Persistence layer.

Uses Postgres via SQLAlchemy when DATABASE_URL is set (recommended for any real
deployment - Render's free/managed Postgres works well here, and it's what
survives a redeploy/restart, unlike a SQLite file sitting in an ephemeral
container filesystem). Falls back to a local SQLite file with zero config so
the app still runs out of the box for local dev / quick demos.
"""

import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USING_POSTGRES = bool(DATABASE_URL)

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'techtailor_agent.db')}"

# Render (and some other providers) hand out `postgres://` URLs; SQLAlchemy's
# psycopg2 dialect wants `postgresql://`.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionRow(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    workflow_id = Column(String, nullable=True)
    workflow_title = Column(String, nullable=True)
    intent_bucket = Column(String, nullable=True)
    workflow_summary = Column(Text, nullable=True)
    branch = Column(String, nullable=True)
    turn_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class MessageRow(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    workflow_id = Column(String, nullable=True)
    intent_bucket = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)


class EventRow(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utc_now)


class StockRow(Base):
    __tablename__ = "stock"

    product_id = Column(String, primary_key=True)
    quantity = Column(Integer, nullable=False, default=25)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class CustomerProfileRow(Base):
    """One row per browser/session_id (the closest thing this prototype has
    to a stable customer identity - see redis_layer/app.js: session_id is
    persisted in the browser's localStorage, so it survives across visits on
    the same device even though there's no login). Captures whatever
    measurement/fit details the customer has given so a *future* visit can
    reuse them instead of asking again - the "doesn't remember previous
    ... for future recommendations" gap.
    """

    __tablename__ = "customer_profiles"

    session_id = Column(String, primary_key=True)
    body_type = Column(String, nullable=True)
    height = Column(String, nullable=True)
    fitting = Column(String, nullable=True)
    size_method = Column(String, nullable=True)
    measurements_json = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


class OrderRow(Base):
    """A line item recorded whenever the agent issues an `add_to_bag`
    action. This is what lets a later session say "reuse what you bought
    last time" with an actual fact instead of the model inferring it from
    chat text alone.
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    product_id = Column(String, nullable=False)
    product_name = Column(String, nullable=True)
    price = Column(Integer, nullable=True)
    workflow_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)


@contextmanager
def _session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_store() -> None:
    Base.metadata.create_all(engine)


def upsert_session(
    session_id: str,
    workflow_id: Optional[str] = None,
    workflow_title: Optional[str] = None,
    intent_bucket: Optional[str] = None,
    workflow_summary: Optional[str] = None,
    branch: Optional[str] = None,
) -> None:
    with _session() as db:
        row = db.get(SessionRow, session_id)
        if row:
            row.workflow_id = workflow_id or row.workflow_id
            row.workflow_title = workflow_title or row.workflow_title
            row.intent_bucket = intent_bucket or row.intent_bucket
            row.workflow_summary = workflow_summary or row.workflow_summary
            row.branch = branch or row.branch
            row.turn_count = (row.turn_count or 0) + 1
            row.updated_at = _utc_now()
        else:
            row = SessionRow(
                session_id=session_id,
                workflow_id=workflow_id,
                workflow_title=workflow_title,
                intent_bucket=intent_bucket,
                workflow_summary=workflow_summary,
                branch=branch,
                turn_count=1,
            )
            db.add(row)


def record_message(
    session_id: str,
    role: str,
    content: str,
    workflow_id: Optional[str] = None,
    intent_bucket: Optional[str] = None,
    branch: Optional[str] = None,
) -> None:
    with _session() as db:
        db.add(
            MessageRow(
                session_id=session_id,
                role=role,
                content=content,
                workflow_id=workflow_id,
                intent_bucket=intent_bucket,
                branch=branch,
            )
        )


def record_event(session_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    with _session() as db:
        db.add(
            EventRow(
                session_id=session_id,
                event_type=event_type,
                payload_json=json.dumps(payload, ensure_ascii=True, default=str),
            )
        )


def get_session_snapshot(session_id: str) -> Optional[Dict[str, Any]]:
    with _session() as db:
        row = db.get(SessionRow, session_id)
        if not row:
            return None
        return {
            "session_id": row.session_id,
            "workflow_id": row.workflow_id,
            "workflow_title": row.workflow_title,
            "intent_bucket": row.intent_bucket,
            "workflow_summary": row.workflow_summary,
            "branch": row.branch,
            "turn_count": row.turn_count,
        }


def get_recent_messages(session_id: str, limit: int = 12) -> List[Dict[str, Any]]:
    with _session() as db:
        rows = (
            db.query(MessageRow)
            .filter(MessageRow.session_id == session_id)
            .order_by(MessageRow.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "role": row.role,
                "content": row.content,
                "workflow_id": row.workflow_id,
                "intent_bucket": row.intent_bucket,
                "branch": row.branch,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in reversed(rows)
        ]


def get_analytics() -> Dict[str, Any]:
    with _session() as db:
        session_count = db.query(func.count(SessionRow.session_id)).scalar() or 0
        message_count = db.query(func.count(MessageRow.id)).scalar() or 0
        event_count = db.query(func.count(EventRow.id)).scalar() or 0

        bucket_rows = (
            db.query(
                func.coalesce(SessionRow.intent_bucket, "unknown").label("bucket"),
                func.count(SessionRow.session_id).label("count"),
            )
            .group_by(text("bucket"))
            .order_by(text("count DESC"))
            .all()
        )
        event_rows = (
            db.query(EventRow.event_type, func.count(EventRow.id).label("count"))
            .group_by(EventRow.event_type)
            .order_by(text("count DESC"))
            .all()
        )
        return {
            "sessions": session_count,
            "messages": message_count,
            "events": event_count,
            "intent_buckets": [{"bucket": b, "count": c} for b, c in bucket_rows],
            "event_types": [{"event_type": e, "count": c} for e, c in event_rows],
            "backend": "postgres" if USING_POSTGRES else "sqlite",
        }


# --- Stock / inventory -------------------------------------------------------
# Nothing in the original app tracked inventory at all (the storefront catalog
# is static frontend data). This adds a minimal per-product counter so the
# "does everyone see the same stock" concern has something real behind it.

DEFAULT_STOCK = 25


def ensure_stock_seeded(product_ids: List[str]) -> None:
    with _session() as db:
        existing = {pid for (pid,) in db.query(StockRow.product_id).all()}
        for pid in product_ids:
            if pid not in existing:
                db.add(StockRow(product_id=pid, quantity=DEFAULT_STOCK))


def get_stock(product_id: str) -> int:
    with _session() as db:
        row = db.get(StockRow, product_id)
        return row.quantity if row else DEFAULT_STOCK


def get_all_stock() -> Dict[str, int]:
    with _session() as db:
        rows = db.query(StockRow).all()
        return {row.product_id: row.quantity for row in rows}


def decrement_stock(product_id: str, amount: int = 1) -> Optional[int]:
    """Returns the new quantity, or None if the product is unknown/out of stock."""
    with _session() as db:
        row = db.get(StockRow, product_id)
        if not row:
            row = StockRow(product_id=product_id, quantity=DEFAULT_STOCK)
            db.add(row)
            db.flush()
        if row.quantity <= 0:
            return None
        row.quantity = max(0, row.quantity - amount)
        db.flush()
        return row.quantity


# --- Customer profile (measurements/body type persisted across visits) -----

def upsert_customer_profile(
    session_id: str,
    body_type: Optional[str] = None,
    height: Optional[str] = None,
    fitting: Optional[str] = None,
    size_method: Optional[str] = None,
    measurements: Optional[Dict[str, Any]] = None,
) -> None:
    with _session() as db:
        row = db.get(CustomerProfileRow, session_id)
        if not row:
            row = CustomerProfileRow(session_id=session_id)
            db.add(row)
        if body_type:
            row.body_type = body_type
        if height:
            row.height = height
        if fitting:
            row.fitting = fitting
        if size_method:
            row.size_method = size_method
        if measurements:
            row.measurements_json = json.dumps(measurements, default=str)
        row.updated_at = _utc_now()


def get_customer_profile(session_id: str) -> Optional[Dict[str, Any]]:
    with _session() as db:
        row = db.get(CustomerProfileRow, session_id)
        if not row:
            return None
        return {
            "session_id": row.session_id,
            "body_type": row.body_type,
            "height": row.height,
            "fitting": row.fitting,
            "size_method": row.size_method,
            "measurements": json.loads(row.measurements_json) if row.measurements_json else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }


# --- Order history (so a future visit can reference what was actually bought) -

def record_order(
    session_id: str,
    product_id: str,
    product_name: Optional[str] = None,
    price: Optional[int] = None,
    workflow_id: Optional[str] = None,
) -> None:
    with _session() as db:
        db.add(
            OrderRow(
                session_id=session_id,
                product_id=product_id,
                product_name=product_name,
                price=price,
                workflow_id=workflow_id,
            )
        )


def get_order_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    with _session() as db:
        rows = (
            db.query(OrderRow)
            .filter(OrderRow.session_id == session_id)
            .order_by(OrderRow.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "price": row.price,
                "workflow_id": row.workflow_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]


init_store()
