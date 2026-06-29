from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class EnumOption(ORMModel):
    # Attributes
    value: str
    label: str | None = Field(default=None)
    description: str | None = Field(default=None)
    position: int = Field(default=0)

    # Foreign Keys
    enum_config_id: UUID = Field(description="Foreign key for EnumConfig.enum_options")
