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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_code_ontology.package.code_package_code import CodePackageCode
    from aware_code_ontology.package.code_package_delta_producer_code import CodePackageDeltaProducerCode


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

    async def link_code(
        self,
        code_package_code_id: UUID,
        input_code_package_id: UUID | None = None,
        input_object_instance_graph_commit_id: UUID | None = None,
        input_digest: str | None = None,
        output_digest: str | None = None,
        emission_payload: JsonObject | None = None,
    ) -> CodePackageDeltaProducerCode:
        """Link one producer emission to package-owned Code."""

        payload = {
            "code_package_code_id": code_package_code_id,
            "input_code_package_id": input_code_package_id,
            "input_object_instance_graph_commit_id": input_object_instance_graph_commit_id,
            "input_digest": input_digest,
            "output_digest": output_digest,
            "emission_payload": emission_payload,
        }
        result = await invoke_instance(orm_model=self, function_name="link_code", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_code_ontology.package.code_package_delta_producer_code import CodePackageDeltaProducerCode

        if isinstance(value, CodePackageDeltaProducerCode):
            return value
        return CodePackageDeltaProducerCode.validate_invocation_value(value)

    @classmethod
    async def build_via_code_package(
        cls,
        code_package_id: UUID,
        provider_key: str,
        producer_key: str,
        producer_kind: str | None = None,
        provider_payload: JsonObject | None = None,
    ) -> CodePackageDeltaProducer:
        """Create one package-local raw delta producer identity."""

        payload = {
            "code_package_id": code_package_id,
            "provider_key": provider_key,
            "producer_key": producer_key,
            "producer_kind": producer_kind,
            "provider_payload": provider_payload,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_code_package", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, CodePackageDeltaProducer):
            return value
        return CodePackageDeltaProducer.validate_invocation_value(value)


class CodePackageDeltaProducerLinkCodeInput(BaseModel):
    code_package_code_id: UUID
    input_code_package_id: UUID | None = Field(default=None)
    input_object_instance_graph_commit_id: UUID | None = Field(default=None)
    input_digest: str | None = Field(default=None)
    output_digest: str | None = Field(default=None)
    emission_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaProducerLinkCodeOutput(BaseModel):
    value: CodePackageDeltaProducerCode


class CodePackageDeltaProducerBuildViaCodePackageInput(BaseModel):
    code_package_id: UUID = Field(description="Foreign key for CodePackage.delta_producers")
    provider_key: str
    producer_key: str
    producer_kind: str | None = Field(default=None)
    provider_payload: JsonObject | None = Field(default=None)


class CodePackageDeltaProducerBuildViaCodePackageOutput(BaseModel):
    value: CodePackageDeltaProducer


FUNCTIONS = {
    "CodePackageDeltaProducer": {
        "link_code": {
            "canonical": {
                "name": "link_code",
                "description": "Link one producer emission to package-owned Code.",
                "is_constructor": False,
            },
            "input": CodePackageDeltaProducerLinkCodeInput,
            "output": CodePackageDeltaProducerLinkCodeOutput,
        },
        "build_via_code_package": {
            "canonical": {
                "name": "build_via_code_package",
                "description": "Create one package-local raw delta producer identity.",
                "is_constructor": True,
            },
            "input": CodePackageDeltaProducerBuildViaCodePackageInput,
            "output": CodePackageDeltaProducerBuildViaCodePackageOutput,
        },
    },
}

__all__ = [
    "CodePackageDeltaProducer",
    "CodePackageDeltaProducerLinkCodeInput",
    "CodePackageDeltaProducerLinkCodeOutput",
    "CodePackageDeltaProducerBuildViaCodePackageInput",
    "CodePackageDeltaProducerBuildViaCodePackageOutput",
    "FUNCTIONS",
]
