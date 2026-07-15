from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_config import SdkConfig
from aware_sdk_ontology.sdk.sdk_operation import SdkOperation
from aware_sdk_ontology.sdk.sdk_surface import SdkSurface

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_config_id

# --- AWARE: USER_IMPORTS END


async def build(name: str, title: str | None = None, description: str | None = None) -> SdkConfig:
    """
    Create one canonical reusable SDK definition.

    Contract:
    - `SdkConfig` is the semantic orchestration root for generated/handwritten SDK surfaces.
    - `SdkOperation` is SDK-owned local operation truth.
    - `SdkOperationApiCapabilityEndpoint` binds each SDK operation to API-owned endpoint truth.
    - Runtime language adapters consume this config; they do not invent SDK/API contracts.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkConfig.build requires non-empty name")
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    return SdkConfig(
        id=stable_sdk_config_id(name=normalized_name),
        name=normalized_name,
        title=normalized_title,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build


async def add_operation(
    sdk_config: SdkConfig,
    name: str,
    title: str | None = None,
    description: str | None = None,
    implementation_ref: str | None = None,
) -> SdkOperation:
    """
    Add one SDK-owned operation under this SDK config.
    """

    # --- AWARE: LOGIC START add_operation
    operation = await SdkOperation.build_via_sdk_config(
        sdk_config_id=sdk_config.id,
        name=name,
        title=title,
        description=description,
        implementation_ref=implementation_ref,
    )
    if all(existing.id != operation.id for existing in sdk_config.operations):
        sdk_config.operations.append(operation)
    return operation
    # --- AWARE: LOGIC END add_operation


async def add_surface(
    sdk_config: SdkConfig, name: str, title: str | None = None, description: str | None = None
) -> SdkSurface:
    """
    Add one SDK-owned conceptual surface under this SDK config.
    """

    # --- AWARE: LOGIC START add_surface
    surface = await SdkSurface.build_via_sdk_config(
        sdk_config_id=sdk_config.id,
        name=name,
        title=title,
        description=description,
    )
    if all(existing.id != surface.id for existing in sdk_config.surfaces):
        sdk_config.surfaces.append(surface)
    return surface
    # --- AWARE: LOGIC END add_surface
