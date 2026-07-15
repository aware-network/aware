from __future__ import annotations

# Standard
from uuid import UUID

# Third-party
from pydantic import Field

# Api Ontology Orm Models
from aware_api_ontology_orm_models.api.api_view_stream_enums import ApiViewStreamMode

# Orm
from aware_orm.models.orm_model import ORMModel


class ApiViewStreamPolicy(ORMModel):
    """Optional stream policy for one readable API view contract."""

    # Attributes
    stream_mode: ApiViewStreamMode
    description: str | None = Field(default=None)

    # Foreign Keys
    api_view_id: UUID | None = Field(default=None, description="Foreign key for ApiView.stream_policy")
