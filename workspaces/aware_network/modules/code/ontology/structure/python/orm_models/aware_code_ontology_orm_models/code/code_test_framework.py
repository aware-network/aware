from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class CodeTestFramework(ORMModel):
    """
    Canonical test framework identity.
    Framework is intentionally an object instead of an enum so languages and
    installations can later attach compatibility/capability contracts.
    """

    # Attributes
    name: str
    title: str | None = Field(default=None)
