from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_operation import SdkOperation
from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import SdkOperationApiCapabilityEndpoint
from aware_sdk_ontology.sdk.sdk_operation_call import SdkOperationCall
from aware_sdk_ontology.sdk.sdk_operation_dependency import SdkOperationDependency

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_operation_id

# --- AWARE: USER_IMPORTS END


async def bind_api_capability_endpoint(
    sdk_operation: SdkOperation,
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

    # --- AWARE: LOGIC START bind_api_capability_endpoint
    endpoint = await SdkOperationApiCapabilityEndpoint.create_via_sdk_operation(
        sdk_operation_id=sdk_operation.id,
        name=name,
        api_capability_endpoint_id=api_capability_endpoint_id,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
        role=role,
        order=order,
        required=required,
    )
    if all(existing.id != endpoint.id for existing in sdk_operation.api_capability_endpoints):
        sdk_operation.api_capability_endpoints.append(endpoint)
    return endpoint
    # --- AWARE: LOGIC END bind_api_capability_endpoint


async def bind_sdk_operation_dependency(
    sdk_operation: SdkOperation,
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

    # --- AWARE: LOGIC START bind_sdk_operation_dependency
    dependency = await SdkOperationDependency.create_via_sdk_operation(
        sdk_operation_id=sdk_operation.id,
        target_sdk_operation_id=target_sdk_operation_id,
        target_operation_ref=target_operation_ref,
        target_sdk_name=target_sdk_name,
        target_operation_name=target_operation_name,
        target_package_name=target_package_name,
        role=role,
        order=order,
        required=required,
        description=description,
    )
    if all(existing.id != dependency.id for existing in sdk_operation.sdk_operation_dependencies):
        sdk_operation.sdk_operation_dependencies.append(dependency)
    return dependency
    # --- AWARE: LOGIC END bind_sdk_operation_dependency


async def create_call(
    sdk_operation: SdkOperation,
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

    # --- AWARE: LOGIC START create_call
    call = await SdkOperationCall.create_via_sdk_operation(
        sdk_operation_id=sdk_operation.id,
        call_key=call_key,
        request_hash=request_hash,
        description=description,
        context_hash=context_hash,
        status=status,
        api_call_id=api_call_id,
    )
    for existing in sdk_operation.sdk_operation_calls:
        if existing.id == call.id:
            if (
                existing.sdk_operation_id != call.sdk_operation_id
                or existing.call_key != call.call_key
                or existing.request_hash != call.request_hash
                or existing.description != call.description
                or existing.context_hash != call.context_hash
                or existing.status != call.status
                or existing.api_call_id != call.api_call_id
            ):
                raise RuntimeError(
                    "SdkOperation already has a mismatched operation call: " + f"sdk_operation_call_id={call.id}"
                )
            return existing
    sdk_operation.sdk_operation_calls.append(call)
    return call
    # --- AWARE: LOGIC END create_call


async def build_via_sdk_config(
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

    # --- AWARE: LOGIC START build_via_sdk_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkOperation.build_via_sdk_config requires non-empty name")
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_implementation_ref = (implementation_ref or "").strip() or None
    return SdkOperation(
        id=stable_sdk_operation_id(sdk_config_id=sdk_config_id, name=normalized_name),
        sdk_config_id=sdk_config_id,
        name=normalized_name,
        title=normalized_title,
        description=normalized_description,
        implementation_ref=normalized_implementation_ref,
    )
    # --- AWARE: LOGIC END build_via_sdk_config
