from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package_code import CodePackageCode


class CodePackageDeltaProducerCode(BaseModel):
    # Relationships
    code_package_code: CodePackageCode = Field(description="Association target reference to CodePackageCode")

    # Attributes
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_digest: str | None = Field(default=None)
    output_digest: str | None = Field(default=None)
    emission_payload: JsonObject | None = Field(default=None)
