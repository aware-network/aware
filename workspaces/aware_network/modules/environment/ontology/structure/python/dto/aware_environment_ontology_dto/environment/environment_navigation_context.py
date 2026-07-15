from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

if TYPE_CHECKING:
    from aware_environment_ontology_dto.environment.environment_session_thread import EnvironmentSessionThread


class EnvironmentNavigationContext(BaseModel):
    """
    Shared Environment navigation surface under an EnvironmentSession.
    Contract:
    - Parent constructor is EnvironmentSession.
    - This is the durable shared OS pointer that Interface windows/tabs follow.
    - One EnvironmentSession may own many navigation contexts.
    - SessionThread target changes are committed state; history is derived by
    commit replay and no EnvironmentNavigationEvent object exists in v0.
    - Attention layout/section focus and Experience lens/action resolution are
    later rails.
    """

    # Relationships
    session_thread: EnvironmentSessionThread | None = Field(default=None)

    # Attributes
    key: str
    status: str = Field(default="active")
    title: str | None = Field(default=None)
    is_default: bool = Field(
        default=False, description="Marks the EnvironmentSession-owned default navigation entrypoint."
    )
