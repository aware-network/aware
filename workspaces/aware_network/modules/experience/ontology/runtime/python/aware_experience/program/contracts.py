from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProgramRunIdentity:
    """Experience-owned identity for one program run lifecycle."""

    program_run_id: UUID
    mailbox_key: str
    program_id: UUID | None = None
