"""
Branch-scoped Session registry.

Provides an op-scoped registry that hands out exactly one Session per branch_id
and coordinates committing/rolling back all of them together.

Intended usage: create a registry for the lifetime of a high-level dispatch,
acquire sessions via for_branch(branch_id), and finally commit_all() or
rollback_all().
"""

from __future__ import annotations

import os
from typing import Iterable
from uuid import UUID

from aware_orm._support import logger
from aware_orm.session.session import Session
from aware_orm.session.session_enums import SessionType


class BranchSessionRegistry:
    """Simple per-branch session registry (operation-scoped)."""

    def __init__(self, *, skip_db: bool | None = None) -> None:
        """
        Initialize registry.

        Args:
            skip_db: Optional override. If None, Session decides based on env.
        """
        self._skip_db = skip_db
        self._sessions: dict[UUID, Session] = {}
        self._session_types: dict[UUID, SessionType] = {}

    def for_branch(self, branch_id: UUID, *, session_type: SessionType = SessionType.DOMAIN) -> Session:
        """Get or create a Session bound to branch_id with an explicit session type."""
        if branch_id in self._sessions:
            # Update type if provided and different
            prev_type = self._session_types.get(branch_id)
            if prev_type is None or prev_type != session_type:
                self._session_types[branch_id] = session_type
            return self._sessions[branch_id]

        # Prefer an already-scoped SessionContext when available (tests/tools/in-process runtimes).
        # This keeps "in-memory state" coherent for skip_db/noop backends.
        try:
            from aware_orm.session.current_session_ctx import current_session_context

            ctx = current_session_context()
            if ctx is not None and ctx.branch_id == branch_id:
                scoped_session = ctx.session
                self._sessions[branch_id] = scoped_session
                self._session_types[branch_id] = session_type
                return scoped_session
        except Exception:
            # Fall through to creating a new Session.
            pass

        # Default policy: if persistence is not configured, run in offline mode (skip_db=True).
        # This keeps v0 runtime tests and local tooling deterministic without requiring a DB.
        effective_skip_db: bool
        if self._skip_db is not None:
            effective_skip_db = self._skip_db
        else:
            backend = (os.getenv("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
            if backend:
                effective_skip_db = backend == "noop"
            elif os.getenv("DATABASE_URL"):
                effective_skip_db = False
            else:
                effective_skip_db = True
        sess = Session(branch_id=branch_id, skip_db=effective_skip_db)
        self._sessions[branch_id] = sess
        self._session_types[branch_id] = session_type
        logger.debug(f"Created branch session: branch={branch_id} session={id(sess)}")
        return sess

    def sessions(self) -> Iterable[Session]:
        """Iterate over managed sessions."""
        return self._sessions.values()

    async def commit_all(self) -> None:
        """Commit all managed sessions."""
        # Deterministic ordering by explicit session type
        sessions = list(self._sessions.values())
        domain_sessions = [s for s in sessions if self._session_types.get(s.branch_id) == SessionType.DOMAIN]
        os_sessions = [s for s in sessions if self._session_types.get(s.branch_id) == SessionType.OS]

        for sess in domain_sessions + os_sessions:
            try:
                await sess.commit()
            except Exception as e:
                logger.error(f"Commit failed for session {id(sess)} (branch {sess.branch_id}): {e}")
                raise

    async def rollback_all(self) -> None:
        """Rollback all managed sessions and clear state."""
        for sess in list(self._sessions.values()):
            try:
                await sess.rollback()
            except Exception as e:
                logger.warning(f"Rollback failed for session {id(sess)} (branch {sess.branch_id}): {e}")

    def clear(self) -> None:
        """Drop all references (used after commit/rollback)."""
        self._sessions.clear()
        self._session_types.clear()
