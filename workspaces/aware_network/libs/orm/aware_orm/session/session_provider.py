from typing import Protocol, runtime_checkable
from uuid import UUID

# ORM
from aware_orm.session.session import Session
from aware_orm.session.session_enums import SessionType


@runtime_checkable
class SessionProvider(Protocol):
    """Resolve branch-scoped sessions for the executor."""

    def get(self, branch_id: UUID, session_type: SessionType) -> Session: ...
