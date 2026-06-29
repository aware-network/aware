from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package_code import CodePackageCode


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

    @classmethod
    async def build_via_code_package_delta_producer(
        cls,
        code_package_delta_producer_id: UUID,
        code_package_code_id: UUID,
        input_code_package_id: UUID | None = None,
        input_object_instance_graph_commit_id: UUID | None = None,
        input_digest: str | None = None,
        output_digest: str | None = None,
        emission_payload: JsonObject | None = None,
    ) -> CodePackageDeltaProducerCode:
        """Attach one producer emission to package-owned Code."""

        payload = {
            "code_package_delta_producer_id": code_package_delta_producer_id,
            "code_package_code_id": code_package_code_id,
            "input_code_package_id": input_code_package_id,
            "input_object_instance_graph_commit_id": input_object_instance_graph_commit_id,
            "input_digest": input_digest,
            "output_digest": output_digest,
            "emission_payload": emission_payload,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_code_package_delta_producer", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageDeltaProducerCode):
            return value
        return CodePackageDeltaProducerCode.validate_invocation_value(value)


class CodePackageDeltaProducerCodeBuildViaCodePackageDeltaProducerInput(BaseModel):
    code_package_delta_producer_id: UUID = Field(description="Join FK to CodePackageDeltaProducer")
    code_package_code_id: UUID
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_digest: str | None = Field(default=None)
    output_digest: str | None = Field(default=None)
    emission_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaProducerCodeBuildViaCodePackageDeltaProducerOutput(BaseModel):
    value: CodePackageDeltaProducerCode


FUNCTIONS = {
    "CodePackageDeltaProducerCode": {
        "build_via_code_package_delta_producer": {
            "canonical": {
                "name": "build_via_code_package_delta_producer",
                "description": "Attach one producer emission to package-owned Code.",
                "is_constructor": True,
            },
            "input": CodePackageDeltaProducerCodeBuildViaCodePackageDeltaProducerInput,
            "output": CodePackageDeltaProducerCodeBuildViaCodePackageDeltaProducerOutput,
        },
    },
}

__all__ = [
    "CodePackageDeltaProducerCode",
    "CodePackageDeltaProducerCodeBuildViaCodePackageDeltaProducerInput",
    "CodePackageDeltaProducerCodeBuildViaCodePackageDeltaProducerOutput",
    "FUNCTIONS",
]
