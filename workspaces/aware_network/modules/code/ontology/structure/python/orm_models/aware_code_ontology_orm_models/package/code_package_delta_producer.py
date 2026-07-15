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
    from aware_code_ontology_orm_models.package.code_package_delta_producer_code import CodePackageDeltaProducerCode


class CodePackageDeltaProducer(ORMModel):
    # Attributes
    provider_key: str
    producer_key: str
    producer_kind: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)

    # Foreign Keys
    code_package_id: UUID = Field(description="Foreign key for CodePackage.delta_producers")

    # Edges
    code_package_delta_producer_codes: list[CodePackageDeltaProducerCode] = Field(
        default_factory=list, description="Edge association helper for code_package_codes"
    )

    @property
    def code_package_codes(self) -> list[CodePackageCode]:
        return [
            edge.code_package_code
            for edge in self.code_package_delta_producer_codes
            if edge.code_package_code is not None
        ]
