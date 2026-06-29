from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Orm
from aware_orm.models.orm_model import ORMModel

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_orm_models.package.code_package_code import CodePackageCode


class CodePackageDeltaProducerCode(ORMModel):
    # Relationships
    code_package_code: CodePackageCode = Field(description="Association target reference to CodePackageCode")

    # Attributes
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_digest: str | None = Field(default=None)
    output_digest: str | None = Field(default=None)
    emission_payload: JsonObject | None = Field(default=None)

    # Foreign Keys
    code_package_code_id: UUID | None = Field(default=None, description="Join FK to CodePackageCode")
    code_package_delta_producer_id: UUID = Field(description="Join FK to CodePackageDeltaProducer")
