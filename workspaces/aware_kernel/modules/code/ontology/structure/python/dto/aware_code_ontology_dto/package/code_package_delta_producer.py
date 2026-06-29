from __future__ import annotations

# Standard
from typing import TYPE_CHECKING

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package_code import CodePackageCode
    from aware_code_ontology_dto.package.code_package_delta_producer_code import CodePackageDeltaProducerCode


class CodePackageDeltaProducer(BaseModel):
    # Attributes
    provider_key: str
    producer_key: str
    producer_kind: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)
