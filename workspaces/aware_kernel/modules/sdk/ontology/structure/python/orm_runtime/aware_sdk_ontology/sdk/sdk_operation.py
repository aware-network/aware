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

if TYPE_CHECKING:
    from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint
    from aware_sdk_ontology.sdk.sdk_operation_call import SdkOperationCall
    from aware_sdk_ontology.sdk.sdk_operation_dependency import SdkOperationDependency


class SdkOperation(ORMModel):
    """
    SDK-local operation truth.
    One operation may coordinate one or more API capability endpoints. The API
    endpoint remains the canonical ingress contract for request/response/stream
    payloads.
    """

    # Relationships
    api_capability_endpoints: list[SdkOperationApiCapabilityEndpoint] = Field(default_factory=list)
    sdk_operation_dependencies: list[SdkOperationDependency] = Field(default_factory=list)
    sdk_operation_calls: list[SdkOperationCall] = Field(default_factory=list)

    # Attributes
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    implementation_ref: str | None = Field(default=None)

    # Foreign Keys
    sdk_config_id: UUID = Field(description="Foreign key for SdkConfig.operations")

    async def bind_api_capability_endpoint(
        self,
        name: str,
        api_capability_endpoint_id: UUID,
        endpoint_ref: str | None = None,
        discriminant: str | None = None,
        role: str = "primary",
        order: int = 1,
        required: bool = True,
    ) -> SdkOperationApiCapabilityEndpoint:
        """
        Bind this SDK operation to one API capability endpoint.

        Contract:
        - `api_capability_endpoint_id` points at API-owned invocation truth.
        - `endpoint_ref` preserves authored `api.capability.endpoint` syntax when available.
        - `role`, `order`, and `required` are SDK orchestration metadata only.
        """

        payload = {
            "name": name,
            "api_capability_endpoint_id": api_capability_endpoint_id,
            "endpoint_ref": endpoint_ref,
            "discriminant": discriminant,
            "role": role,
            "order": order,
            "required": required,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_api_capability_endpoint", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint

        if isinstance(value, SdkOperationApiCapabilityEndpoint):
            return value
        return SdkOperationApiCapabilityEndpoint.validate_invocation_value(value)

    async def bind_sdk_operation_dependency(
        self,
        target_sdk_operation_id: UUID,
        target_operation_ref: str,
        target_sdk_name: str,
        target_operation_name: str,
        target_package_name: str | None = None,
        role: str = "dependency",
        order: int = 1,
        required: bool = True,
        description: str | None = None,
    ) -> SdkOperationDependency:
        """
        Bind this SDK operation to another SDK operation.

        Contract:
        - This is SDK operation composition truth, not API endpoint ingress truth.
        - Local operation refs target the same `SdkConfig`; external refs must come from
          the package dependency closure declared by `SdkPackageDependency`.
        - `target_operation_ref` preserves authored `sdk_name.operation_name` syntax.
        """

        payload = {
            "target_sdk_operation_id": target_sdk_operation_id,
            "target_operation_ref": target_operation_ref,
            "target_sdk_name": target_sdk_name,
            "target_operation_name": target_operation_name,
            "target_package_name": target_package_name,
            "role": role,
            "order": order,
            "required": required,
            "description": description,
        }
        result = await invoke_instance(orm_model=self, function_name="bind_sdk_operation_dependency", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_operation_dependency import SdkOperationDependency

        if isinstance(value, SdkOperationDependency):
            return value
        return SdkOperationDependency.validate_invocation_value(value)

    async def create_call(
        self,
        call_key: UUID,
        request_hash: str,
        description: str | None = None,
        context_hash: str | None = None,
        status: str = "pending",
        api_call_id: UUID | None = None,
    ) -> SdkOperationCall:
        """
        Create one SDK operation invocation receipt anchored on this operation.

        Contract:
        - `SdkOperation` is the configuration rail; `SdkOperationCall` is the actual invocation.
        - `call_key` must be stable for one client dispatch attempt.
        - `api_call_id` optionally links the SDK call to the API ingress receipt it produced.
        """

        payload = {
            "call_key": call_key,
            "request_hash": request_hash,
            "description": description,
            "context_hash": context_hash,
            "status": status,
            "api_call_id": api_call_id,
        }
        result = await invoke_instance(orm_model=self, function_name="create_call", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_sdk_ontology.sdk.sdk_operation_call import SdkOperationCall

        if isinstance(value, SdkOperationCall):
            return value
        return SdkOperationCall.validate_invocation_value(value)

    @classmethod
    async def build_via_sdk_config(
        cls,
        sdk_config_id: UUID,
        name: str,
        title: str | None = None,
        description: str | None = None,
        implementation_ref: str | None = None,
    ) -> SdkOperation:
        """
        Create one SDK-owned operation.

        Contract:
        - Identity is scoped by parent `SdkConfig` and operation `name`.
        - `implementation_ref` is a local adapter hint, not API contract truth.
        - Endpoint binding remains explicit through `bind_api_capability_endpoint`.
        """

        payload = {
            "sdk_config_id": sdk_config_id,
            "name": name,
            "title": title,
            "description": description,
            "implementation_ref": implementation_ref,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_sdk_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, SdkOperation):
            return value
        return SdkOperation.validate_invocation_value(value)


class SdkOperationBindApiCapabilityEndpointInput(BaseModel):
    name: str
    api_capability_endpoint_id: UUID
    endpoint_ref: str | None = Field(default=None)
    discriminant: str | None = Field(default=None)
    role: str = Field(default="primary")
    order: int = Field(default=1)
    required: bool = Field(default=True)


class SdkOperationBindApiCapabilityEndpointOutput(BaseModel):
    value: SdkOperationApiCapabilityEndpoint


class SdkOperationBindSdkOperationDependencyInput(BaseModel):
    target_sdk_operation_id: UUID
    target_operation_ref: str
    target_sdk_name: str
    target_operation_name: str
    target_package_name: str | None = Field(default=None)
    role: str = Field(default="dependency")
    order: int = Field(default=1)
    required: bool = Field(default=True)
    description: str | None = Field(default=None)


class SdkOperationBindSdkOperationDependencyOutput(BaseModel):
    value: SdkOperationDependency


class SdkOperationCreateCallInput(BaseModel):
    call_key: UUID
    request_hash: str
    description: str | None = Field(default=None)
    context_hash: str | None = Field(default=None)
    status: str = Field(default="pending")
    api_call_id: UUID | None = Field(default=None)


class SdkOperationCreateCallOutput(BaseModel):
    value: SdkOperationCall


class SdkOperationBuildViaSdkConfigInput(BaseModel):
    sdk_config_id: UUID = Field(description="Foreign key for SdkConfig.operations")
    name: str
    title: str | None = Field(default=None)
    description: str | None = Field(default=None)
    implementation_ref: str | None = Field(default=None)


class SdkOperationBuildViaSdkConfigOutput(BaseModel):
    value: SdkOperation


FUNCTIONS = {
    "SdkOperation": {
        "bind_api_capability_endpoint": {
            "canonical": {
                "name": "bind_api_capability_endpoint",
                "description": "Bind this SDK operation to one API capability endpoint.\n\nContract:\n- `api_capability_endpoint_id` points at API-owned invocation truth.\n- `endpoint_ref` preserves authored `api.capability.endpoint` syntax when available.\n- `role`, `order`, and `required` are SDK orchestration metadata only.",
                "is_constructor": False,
            },
            "input": SdkOperationBindApiCapabilityEndpointInput,
            "output": SdkOperationBindApiCapabilityEndpointOutput,
        },
        "bind_sdk_operation_dependency": {
            "canonical": {
                "name": "bind_sdk_operation_dependency",
                "description": "Bind this SDK operation to another SDK operation.\n\nContract:\n- This is SDK operation composition truth, not API endpoint ingress truth.\n- Local operation refs target the same `SdkConfig`; external refs must come from\n  the package dependency closure declared by `SdkPackageDependency`.\n- `target_operation_ref` preserves authored `sdk_name.operation_name` syntax.",
                "is_constructor": False,
            },
            "input": SdkOperationBindSdkOperationDependencyInput,
            "output": SdkOperationBindSdkOperationDependencyOutput,
        },
        "create_call": {
            "canonical": {
                "name": "create_call",
                "description": "Create one SDK operation invocation receipt anchored on this operation.\n\nContract:\n- `SdkOperation` is the configuration rail; `SdkOperationCall` is the actual invocation.\n- `call_key` must be stable for one client dispatch attempt.\n- `api_call_id` optionally links the SDK call to the API ingress receipt it produced.",
                "is_constructor": False,
            },
            "input": SdkOperationCreateCallInput,
            "output": SdkOperationCreateCallOutput,
        },
        "build_via_sdk_config": {
            "canonical": {
                "name": "build_via_sdk_config",
                "description": "Create one SDK-owned operation.\n\nContract:\n- Identity is scoped by parent `SdkConfig` and operation `name`.\n- `implementation_ref` is a local adapter hint, not API contract truth.\n- Endpoint binding remains explicit through `bind_api_capability_endpoint`.",
                "is_constructor": True,
            },
            "input": SdkOperationBuildViaSdkConfigInput,
            "output": SdkOperationBuildViaSdkConfigOutput,
        },
    },
}

__all__ = [
    "SdkOperation",
    "SdkOperationBindApiCapabilityEndpointInput",
    "SdkOperationBindApiCapabilityEndpointOutput",
    "SdkOperationBindSdkOperationDependencyInput",
    "SdkOperationBindSdkOperationDependencyOutput",
    "SdkOperationCreateCallInput",
    "SdkOperationCreateCallOutput",
    "SdkOperationBuildViaSdkConfigInput",
    "SdkOperationBuildViaSdkConfigOutput",
    "FUNCTIONS",
]
