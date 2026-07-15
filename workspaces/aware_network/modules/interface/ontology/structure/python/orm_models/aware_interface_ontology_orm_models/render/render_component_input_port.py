from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel


class RenderComponentInputPort(ORMModel):
    # Attributes
    port_key: str
    value_kind: str
    is_required: bool = Field(default=True)
    description: str | None = Field(default=None)

    # Foreign Keys
    render_component_contract_id: UUID = Field(description="Foreign key for RenderComponentContract.input_ports")
