from __future__ import annotations

import os
import random
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import AbstractAsyncContextManager, AbstractContextManager, contextmanager
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
    PendingWrite,
    get_checkpoint_id,
    get_checkpoint_metadata,
)
from langgraph.checkpoint.memory import WRITES_IDX_MAP


class SqliteSaver(BaseCheckpointSaver[str], AbstractContextManager, AbstractAsyncContextManager):
    """A small SQLite-backed checkpoint saver for TechTailor."""

    def __init__(self, db_path: str, *, serde: Any | None = None) -> None:
        super().__init__(serde=serde)
        self.db_path = db_path
        self._ensure_schema()

    @classmethod
    def from_conn_string(cls, conn_string: str, *, serde: Any | None = None) -> "SqliteSaver":
        path = conn_string
        if conn_string.startswith("sqlite:///"):
            path = conn_string.removeprefix("sqlite:///")
        return cls(path, serde=serde)

    def __enter__(self) -> "SqliteSaver":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool | None:
        return None

    async def __aenter__(self) -> "SqliteSaver":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool | None:
        return None

    @contextmanager
    def _connect(self):
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    checkpoint_type TEXT NOT NULL,
                    checkpoint_blob BLOB NOT NULL,
                    metadata_type TEXT NOT NULL,
                    metadata_blob BLOB NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    write_idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    value_type TEXT NOT NULL,
                    value_blob BLOB NOT NULL,
                    task_path TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, write_idx)
                )
                """
            )

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = get_checkpoint_id(config)

        with self._connect() as conn:
            if checkpoint_id:
                row = conn.execute(
                    """
                    SELECT *
                    FROM checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    """,
                    (thread_id, checkpoint_ns, checkpoint_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT *
                    FROM checkpoints
                    WHERE thread_id = ? AND checkpoint_ns = ?
                    ORDER BY created_at DESC, checkpoint_id DESC
                    LIMIT 1
                    """,
                    (thread_id, checkpoint_ns),
                ).fetchone()

            if not row:
                return None

            checkpoint = self.serde.loads_typed((row["checkpoint_type"], row["checkpoint_blob"]))
            metadata = self.serde.loads_typed((row["metadata_type"], row["metadata_blob"]))
            writes_rows = conn.execute(
                """
                SELECT task_id, write_idx, channel, value_type, value_blob, task_path
                FROM writes
                WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                ORDER BY task_id, write_idx
                """,
                (thread_id, checkpoint_ns, row["checkpoint_id"]),
            ).fetchall()

            pending_writes: list[PendingWrite] = [
                (
                    write_row["task_id"],
                    write_row["channel"],
                    self.serde.loads_typed((write_row["value_type"], write_row["value_blob"])),
                )
                for write_row in writes_rows
            ]

            parent_config = (
                {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": row["parent_checkpoint_id"],
                    }
                }
                if row["parent_checkpoint_id"]
                else None
            )

            return CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": row["checkpoint_id"],
                    }
                },
                checkpoint=checkpoint,
                metadata=metadata,
                parent_config=parent_config,
                pending_writes=pending_writes or None,
            )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        with self._connect() as conn:
            query = "SELECT * FROM checkpoints"
            params: list[Any] = []
            clauses: list[str] = []

            if config:
                clauses.append("thread_id = ?")
                params.append(config["configurable"]["thread_id"])
                checkpoint_ns = config["configurable"].get("checkpoint_ns")
                if checkpoint_ns is not None:
                    clauses.append("checkpoint_ns = ?")
                    params.append(checkpoint_ns)
                checkpoint_id = get_checkpoint_id(config)
                if checkpoint_id:
                    clauses.append("checkpoint_id = ?")
                    params.append(checkpoint_id)

            if before and (before_checkpoint_id := get_checkpoint_id(before)):
                clauses.append("checkpoint_id < ?")
                params.append(before_checkpoint_id)

            if clauses:
                query += " WHERE " + " AND ".join(clauses)

            query += " ORDER BY created_at DESC, checkpoint_id DESC"
            rows = conn.execute(query, params).fetchall()

            for row in rows:
                metadata = self.serde.loads_typed((row["metadata_type"], row["metadata_blob"]))
                if filter and not all(metadata.get(key) == value for key, value in filter.items()):
                    continue
                checkpoint = self.serde.loads_typed((row["checkpoint_type"], row["checkpoint_blob"]))
                writes_rows = conn.execute(
                    """
                    SELECT task_id, write_idx, channel, value_type, value_blob, task_path
                    FROM writes
                    WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ?
                    ORDER BY task_id, write_idx
                    """,
                    (row["thread_id"], row["checkpoint_ns"], row["checkpoint_id"]),
                ).fetchall()
                pending_writes = [
                    (
                        write_row["task_id"],
                        write_row["channel"],
                        self.serde.loads_typed((write_row["value_type"], write_row["value_blob"])),
                    )
                    for write_row in writes_rows
                ]
                yield CheckpointTuple(
                    config={
                        "configurable": {
                            "thread_id": row["thread_id"],
                            "checkpoint_ns": row["checkpoint_ns"],
                            "checkpoint_id": row["checkpoint_id"],
                        }
                    },
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=(
                        {
                            "configurable": {
                                "thread_id": row["thread_id"],
                                "checkpoint_ns": row["checkpoint_ns"],
                                "checkpoint_id": row["parent_checkpoint_id"],
                            }
                        }
                        if row["parent_checkpoint_id"]
                        else None
                    ),
                    pending_writes=pending_writes or None,
                )

                if limit is not None:
                    limit -= 1
                    if limit <= 0:
                        break

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")
        now = datetime.now(timezone.utc).isoformat()
        serialized_checkpoint = self.serde.dumps_typed(checkpoint)
        serialized_metadata = self.serde.dumps_typed(get_checkpoint_metadata(config, metadata))

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints (
                    thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id,
                    checkpoint_type, checkpoint_blob, metadata_type, metadata_blob, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    checkpoint_ns,
                    checkpoint["id"],
                    parent_checkpoint_id,
                    serialized_checkpoint[0],
                    serialized_checkpoint[1],
                    serialized_metadata[0],
                    serialized_metadata[1],
                    now,
                ),
            )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            for idx, (channel, value) in enumerate(writes):
                write_idx = WRITES_IDX_MAP.get(channel, idx)
                value_type, value_blob = self.serde.dumps_typed(value)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO writes (
                        thread_id, checkpoint_ns, checkpoint_id, task_id, write_idx,
                        channel, value_type, value_blob, task_path, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id,
                        checkpoint_ns,
                        checkpoint_id,
                        task_id,
                        write_idx,
                        channel,
                        value_type,
                        value_blob,
                        task_path,
                        now,
                    ),
                )

    def delete_thread(self, thread_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return self.get_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self.put(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self.put_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return self.delete_thread(thread_id)

    def get_next_version(self, current: str | None, channel: None) -> str:
        if current is None:
            current_v = 0
        elif isinstance(current, int):
            current_v = current
        else:
            current_v = int(str(current).split(".")[0])
        next_v = current_v + 1
        next_h = random.random()
        return f"{next_v:032}.{next_h:016}"
