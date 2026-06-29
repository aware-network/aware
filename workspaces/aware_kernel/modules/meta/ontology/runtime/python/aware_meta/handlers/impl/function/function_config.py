from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.function.function_config_enums import (
    FunctionAttributeType,
    FunctionKind,
)
from aware_meta_ontology.function.function_config_invocation_enums import (
    FunctionInvocationKind,
    FunctionInvocationRootKind,
)
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import FunctionConfigAttributeConfig
from aware_meta_ontology.function.function_config_invocation import FunctionConfigInvocation
from aware_meta_ontology.function.function_impl import FunctionImpl

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Ontology
from aware_meta.graph.config.stable_ids import stable_function_config_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create(
    owner_key: str,
    name: str,
    description: str | None = None,
    verb: str | None = None,
    is_async: bool = False,
    kind: FunctionKind = FunctionKind.instance,
) -> FunctionConfig:
    """
    Create deterministic FunctionConfig.

    Contract:
    - Function identity is semantic and standalone on `(owner_key, name, kind)`.
    - Traversal may still materialize this function through membership edges such as
      `ClassConfigFunctionConfig`, but parent propagation must not enter the function stable-id formula.
    """

    # --- AWARE: LOGIC START create
    normalized_owner_key = (owner_key or "").strip()
    if not normalized_owner_key:
        raise RuntimeError("FunctionConfig.create requires non-empty owner_key")

    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("FunctionConfig.create requires non-empty name")

    function_config_id = stable_function_config_id(
        owner_key=normalized_owner_key,
        name=normalized_name,
        kind=str(getattr(kind, "value", kind)),
    )

    session = current_handler_session()
    existing = session.imap_get(FunctionConfig, function_config_id)
    if existing is not None:
        if (
            (existing.owner_key or "").strip() != normalized_owner_key
            or (existing.name or "").strip() != normalized_name
            or existing.kind != kind
            or (existing.description or None) != (description or None)
            or (existing.verb or None) != (verb or None)
            or existing.is_async != is_async
        ):
            raise RuntimeError(
                "FunctionConfig.create payload mismatch for existing FunctionConfig: "
                f"function_config_id={function_config_id}"
            )
        return existing

    return FunctionConfig(
        id=function_config_id,
        owner_key=normalized_owner_key,
        name=normalized_name,
        description=description,
        verb=verb,
        is_async=is_async,
        kind=kind,
    )
    # --- AWARE: LOGIC END create


async def update_config(
    function_config: FunctionConfig, description: str | None = None, verb: str | None = None, is_async: bool = False
) -> None:
    """
    Update mutable FunctionConfig metadata for an existing function.

    Contract:
    - `owner_key`, `name`, and `kind` are identity keys and are not mutable here.
    - Class membership metadata (`is_public`, `is_constructor`, `position`) lives on
      ClassConfigFunctionConfig and requires its own edge-level function.
    - This full-payload update treats nullable arguments as current semantic truth.
    """

    # --- AWARE: LOGIC START update_config
    function_config.description = description
    function_config.verb = verb
    function_config.is_async = is_async
    return None
    # --- AWARE: LOGIC END update_config


async def add_primitive_attribute_config(
    function_config: FunctionConfig,
    name: str,
    primitive_base_type: CodePrimitiveBaseType = CodePrimitiveBaseType.any,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    type: FunctionAttributeType = FunctionAttributeType.input,
    position: int = 0,
    is_identity_key: bool = False,
) -> FunctionConfigAttributeConfig:
    """
    Attach one pre-existing typed AttributeConfig contract edge under this FunctionConfig.

    Contract:
    - Represents canonical function I/O schema intent.
    - Materializes/ensures a reusable primitive AttributeConfig via semantic standalone keys.
    - Idempotent per `(function_config_id, name, type)`.
    """

    # --- AWARE: LOGIC START add_primitive_attribute_config
    if position < 0:
        raise RuntimeError("FunctionConfig.add_primitive_attribute_config requires position >= 0")

    function_config_id = function_config.id
    if function_config_id is None:
        raise RuntimeError("FunctionConfig.add_primitive_attribute_config requires FunctionConfig.id")

    created = await FunctionConfigAttributeConfig.create_primitive_via_function_config(
        function_config_id=function_config_id,
        owner_key=function_config.owner_key,
        name=name,
        primitive_base_type=primitive_base_type,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        type=type,
        position=position,
        is_identity_key=is_identity_key,
    )
    if all(existing.id != created.id for existing in function_config.function_config_attribute_configs):
        function_config.function_config_attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_primitive_attribute_config


async def add_enum_attribute_config(
    function_config: FunctionConfig,
    name: str,
    enum_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    type: FunctionAttributeType = FunctionAttributeType.input,
    position: int = 0,
    is_identity_key: bool = False,
) -> FunctionConfigAttributeConfig:
    """
    Attach one pre-existing typed enum AttributeConfig contract edge under this FunctionConfig.
    """

    # --- AWARE: LOGIC START add_enum_attribute_config
    if position < 0:
        raise RuntimeError("FunctionConfig.add_enum_attribute_config requires position >= 0")

    function_config_id = function_config.id
    if function_config_id is None:
        raise RuntimeError("FunctionConfig.add_enum_attribute_config requires FunctionConfig.id")

    created = await FunctionConfigAttributeConfig.create_enum_via_function_config(
        function_config_id=function_config_id,
        owner_key=function_config.owner_key,
        name=name,
        enum_config_id=enum_config_id,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        type=type,
        position=position,
        is_identity_key=is_identity_key,
    )
    if all(existing.id != created.id for existing in function_config.function_config_attribute_configs):
        function_config.function_config_attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_enum_attribute_config


async def add_class_attribute_config(
    function_config: FunctionConfig,
    name: str,
    type_class_config_id: UUID,
    description: str | None = None,
    default_value: str | None = None,
    is_primary: bool = False,
    is_public: bool = True,
    is_required: bool = False,
    is_unique: bool = False,
    is_virtual: bool = False,
    type: FunctionAttributeType = FunctionAttributeType.input,
    position: int = 0,
    is_identity_key: bool = False,
) -> FunctionConfigAttributeConfig:
    """
    Attach one pre-existing typed class AttributeConfig contract edge under this FunctionConfig.
    """

    # --- AWARE: LOGIC START add_class_attribute_config
    if position < 0:
        raise RuntimeError("FunctionConfig.add_class_attribute_config requires position >= 0")

    function_config_id = function_config.id
    if function_config_id is None:
        raise RuntimeError("FunctionConfig.add_class_attribute_config requires FunctionConfig.id")

    created = await FunctionConfigAttributeConfig.create_class_via_function_config(
        function_config_id=function_config_id,
        owner_key=function_config.owner_key,
        name=name,
        type_class_config_id=type_class_config_id,
        description=description,
        default_value=default_value,
        is_primary=is_primary,
        is_public=is_public,
        is_required=is_required,
        is_unique=is_unique,
        is_virtual=is_virtual,
        type=type,
        position=position,
        is_identity_key=is_identity_key,
    )
    if all(existing.id != created.id for existing in function_config.function_config_attribute_configs):
        function_config.function_config_attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_class_attribute_config


async def remove_attribute_config(
    function_config: FunctionConfig,
    name: str,
    type: FunctionAttributeType = FunctionAttributeType.input,
    attribute_config_id: UUID | None = None,
) -> None:
    """
    Remove one AttributeConfig membership from this FunctionConfig.

    Contract:
    - Mutates only function_config_attribute_configs on this FunctionConfig.
    - Attribute identity comes from committed semantic baseline truth when available.
    - Rooted OIG commit reachability owns the stale AttributeConfig deletion after the edge is removed.
    """

    # --- AWARE: LOGIC START remove_attribute_config
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("FunctionConfig.remove_attribute_config requires non-empty name")

    normalized_attribute_config_id = UUID(str(attribute_config_id)) if attribute_config_id is not None else None
    normalized_type = type if isinstance(type, FunctionAttributeType) else FunctionAttributeType(str(type))

    retained_edges: list[FunctionConfigAttributeConfig] = []
    removed = False
    for edge in function_config.function_config_attribute_configs:
        edge_attribute_config_id = edge.attribute_config_id
        if edge_attribute_config_id is None:
            edge_attribute_config_id = edge.attribute_config.id
        edge_matches_id = (
            normalized_attribute_config_id is not None and edge_attribute_config_id == normalized_attribute_config_id
        )
        edge_type = edge.type if isinstance(edge.type, FunctionAttributeType) else FunctionAttributeType(str(edge.type))
        edge_matches_signature = (
            normalized_attribute_config_id is None
            and (edge.name or "").strip() == normalized_name
            and edge_type == normalized_type
        )
        if edge_matches_id or edge_matches_signature:
            removed = True
            continue
        retained_edges.append(edge)

    if removed:
        function_config.function_config_attribute_configs[:] = retained_edges
    return None
    # --- AWARE: LOGIC END remove_attribute_config


async def create_function_impl(
    function_config: FunctionConfig,
    key: str = "default",
    impl_kind: FunctionImplKind = FunctionImplKind.instruction_body,
) -> FunctionImpl:
    """
    Create or return the canonical execution rail (`FunctionImpl`) for this FunctionConfig.

    Contract:
    - Parent (`FunctionConfig`) owns `function_impl` propagation.
    - One rail per FunctionConfig (idempotent under parent scope).
    - `impl_kind` carries whether this rail is an instruction body or an auto constructor template.
    """

    # --- AWARE: LOGIC START create_function_impl
    function_config_id = function_config.id
    if function_config_id is None:
        raise RuntimeError("FunctionConfig.create_function_impl requires FunctionConfig.id")

    created = await FunctionImpl.build_via_function_config(
        function_config_id=function_config_id,
        key=key,
    )

    existing_impl = function_config.function_impl
    if existing_impl is not None and existing_impl.id != created.id:
        raise RuntimeError(
            "FunctionConfig.create_function_impl encountered conflicting impl reference: "
            f"function_config_id={function_config_id} existing_impl_id={existing_impl.id} created_impl_id={created.id}"
        )

    function_config.function_impl = created
    return created
    # --- AWARE: LOGIC END create_function_impl


async def create_invocation(
    function_config: FunctionConfig,
    position: int,
    kind: FunctionInvocationKind,
    target_function_config_id: UUID,
    relationship_fingerprint: str = "owner",
    class_config_relationship_id: UUID | None = None,
    root_invocation_id: UUID | None = None,
    root_kind: FunctionInvocationRootKind = FunctionInvocationRootKind.owner,
    capture_name: str | None = None,
) -> FunctionConfigInvocation:
    """
    Create one deterministic invocation-plan step under this FunctionConfig.

    Contract:
    - Parent (`FunctionConfig`) owns invocation membership propagation.
    - Identity is constructor-keyed on
      `(function_config_id via parent path, position, kind, target_function_config_id,
    relationship_fingerprint)`.
    - `class_config_relationship_id` remains explicit traversal metadata; owner-local invocations use
      `relationship_fingerprint = owner` and `class_config_relationship_id = null`.
    """

    # --- AWARE: LOGIC START create_invocation
    function_config_id = function_config.id
    if function_config_id is None:
        raise RuntimeError("FunctionConfig.create_invocation requires FunctionConfig.id")

    relationship_fingerprint_n = (relationship_fingerprint or "").strip()
    if class_config_relationship_id is None:
        if relationship_fingerprint_n and relationship_fingerprint_n != "owner":
            raise RuntimeError(
                "FunctionConfig.create_invocation owner-local invocation requires "
                "relationship_fingerprint='owner' when class_config_relationship_id is null"
            )
        relationship_fingerprint_n = "owner"
    else:
        expected = str(class_config_relationship_id)
        if not relationship_fingerprint_n or relationship_fingerprint_n == "owner":
            relationship_fingerprint_n = expected
        elif relationship_fingerprint_n != expected:
            raise RuntimeError(
                "FunctionConfig.create_invocation relationship_fingerprint mismatch for "
                "class_config_relationship_id: "
                f"fingerprint={relationship_fingerprint_n!r} expected={expected!r}"
            )

    created = await FunctionConfigInvocation.create_via_function_config(
        function_config_id=function_config_id,
        position=position,
        kind=kind,
        target_function_config_id=target_function_config_id,
        relationship_fingerprint=relationship_fingerprint_n,
        class_config_relationship_id=class_config_relationship_id,
        root_invocation_id=root_invocation_id,
        root_kind=root_kind,
        capture_name=capture_name,
    )
    if all(existing.id != created.id for existing in function_config.invocations):
        function_config.invocations.append(created)
    return created
    # --- AWARE: LOGIC END create_invocation
