from __future__ import annotations

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class NetworkNodeValidator(ORMModel):
    # Attributes
    public_key: str
    reliability: float = Field(default=1.0)
    stake: float = Field(default=0)
