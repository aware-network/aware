from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class NetworkDirectory(ORMModel):
    # Attributes
    name: str = Field(default="default")
