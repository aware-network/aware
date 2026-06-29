from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.function.function_config_enums import FunctionKind
from aware_meta_ontology.class_.class_config_function_config import ClassConfigFunctionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta.graph.config.model_bootstrap import get_class_config_fqn
from aware_meta.graph.config.stable_ids import stable_class_config_function_config_id
from aware_meta.handlers.impl.function import function_config as function_config_handler

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def update_config(
    class_config_function_config: ClassConfigFunctionConfig,
    is_public: bool = True,
    is_constructor: bool = False,
    position: int = 0,
) -> None:
    """
    Update mutable class-function membership metadata.

    Contract:
    - `class_config_id` and `function_config_id` are identity keys and are not mutable here.
    - Function scalar metadata lives on FunctionConfig.update_config.
    - This full-payload update treats booleans and position as current semantic truth.
    """

    # --- AWARE: LOGIC START update_config
    if position < 0:
        raise RuntimeError("ClassConfigFunctionConfig.update_config requires position >= 0")

    class_config_function_config.is_public = is_public
    class_config_function_config.is_constructor = is_constructor
    class_config_function_config.position = position
    return None
    # --- AWARE: LOGIC END update_config


async def create_via_class_config(
    class_config_id: UUID,
    owner_key: str,
    name: str,
    description: str | None = None,
    verb: str | None = None,
    is_async: bool = False,
    kind: FunctionKind = FunctionKind.instance,
    is_public: bool = True,
    is_constructor: bool = False,
    position: int = 0,
) -> ClassConfigFunctionConfig:
    """
    Create deterministic ClassConfigFunctionConfig link.

    Contract:
    - Parent `ClassConfig` scope is propagated by traversal lowering.
    - FunctionConfig is ensured via semantic standalone keys (`owner_key`, `name`, `kind`).
    - Deterministic edge identity derives from parent scope + `function_config_id`.
    """

    # --- AWARE: LOGIC START create_via_class_config
    if position < 0:
        raise RuntimeError("ClassConfigFunctionConfig.create_via_class_config requires position >= 0")

    session = current_handler_session()
    class_config = session.imap_get(ClassConfig, class_config_id)
    if class_config is None:
        raise RuntimeError(
            "ClassConfigFunctionConfig.create_via_class_config requires existing ClassConfig: "
            f"class_config_id={class_config_id}"
        )

    normalized_owner_key = (owner_key or "").strip()
    normalized_name = (name or "").strip()
    if not normalized_owner_key:
        raise RuntimeError("ClassConfigFunctionConfig.create_via_class_config requires non-empty owner_key")
    if not normalized_name:
        raise RuntimeError("ClassConfigFunctionConfig.create_via_class_config requires non-empty name")

    expected_owner_key = (get_class_config_fqn(class_config) or "").strip()
    if not expected_owner_key:
        raise RuntimeError("ClassConfigFunctionConfig.create_via_class_config requires ClassConfig.class_fqn")
    if normalized_owner_key != expected_owner_key:
        raise RuntimeError(
            "ClassConfigFunctionConfig.create_via_class_config owner_key mismatch for parent ClassConfig: "
            f"owner_key={normalized_owner_key!r} expected={expected_owner_key!r}"
        )

    function_config = await function_config_handler.create(
        owner_key=normalized_owner_key,
        name=normalized_name,
        description=description,
        verb=verb,
        is_async=is_async,
        kind=kind,
    )
    if function_config.id is None:
        raise RuntimeError("ClassConfigFunctionConfig.create_via_class_config requires FunctionConfig.id after ensure")

    class_config_function_config_id = stable_class_config_function_config_id(
        class_config_id=class_config_id,
        function_config_id=function_config.id,
    )
    existing = session.imap_get(
        ClassConfigFunctionConfig,
        class_config_function_config_id,
    )
    if existing is not None:
        if (
            existing.class_config_id != class_config_id
            or existing.function_config_id != function_config.id
            or existing.is_public != is_public
            or existing.is_constructor != is_constructor
            or existing.position != position
        ):
            raise RuntimeError(
                "ClassConfigFunctionConfig.create_via_class_config payload mismatch for existing edge: "
                f"class_config_function_config_id={class_config_function_config_id}"
            )
        return existing

    return ClassConfigFunctionConfig(
        id=class_config_function_config_id,
        class_config_id=class_config_id,
        function_config=function_config,
        function_config_id=function_config.id,
        is_public=is_public,
        is_constructor=is_constructor,
        position=position,
    )
    # --- AWARE: LOGIC END create_via_class_config
