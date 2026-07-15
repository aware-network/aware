from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class ActorFocusRequestResponse(ORMModel):
    """Separate from ActorFocusRequest to ensure provenance on result standalone."""

    # Attributes
    key: str = Field(default="default")
    success: bool
    message: str | None = Field(default=None)


FUNCTIONS = {
    "ActorFocusRequestResponse": {},
}

__all__ = [
    "ActorFocusRequestResponse",
    "FUNCTIONS",
]
