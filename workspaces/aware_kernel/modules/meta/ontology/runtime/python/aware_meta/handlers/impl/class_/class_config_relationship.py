from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipIdentityRail,
    ClassConfigRelationshipReifiedRole,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_association import ClassConfigRelationshipAssociation
from aware_meta_ontology.class_.class_config_relationship_attribute import ClassConfigRelationshipAttribute

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Meta Runtime
from aware_meta.graph.config.stable_ids import stable_class_relationship_id

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def create_association(
    class_config_relationship: ClassConfigRelationship,
    class_config_id: UUID,
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
) -> ClassConfigRelationshipAssociation:
    """
    Attach one deterministic association edge under this relationship.
    """

    # --- AWARE: LOGIC START create_association
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_association


async def create_attribute(
    class_config_relationship: ClassConfigRelationship,
    attribute_config_id: UUID,
    direction: ClassConfigRelationshipDirection,
    role: ClassConfigRelationshipAttributeRole,
) -> ClassConfigRelationshipAttribute:
    """
    Attach one deterministic relationship-attribute edge under this relationship.
    """

    # --- AWARE: LOGIC START create_attribute
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END create_attribute


async def update_config(
    class_config_relationship: ClassConfigRelationship,
    relationship_type: ClassConfigRelationshipType,
    identity_rail: ClassConfigRelationshipIdentityRail | None = None,
    forward_required: bool = False,
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reified_from_relationship_id: UUID | None = None,
    reified_role: ClassConfigRelationshipReifiedRole | None = None,
) -> None:
    """
    Update mutable relationship configuration for an existing ClassConfigRelationship.

    Contract:
    - `target_class_config_id` and `relationship_key` are identity and are not mutable here.
    - Changing either identity field is replacement semantics, not in-place update.
    - This full-payload update treats nullable arguments as current semantic truth.
    """

    # --- AWARE: LOGIC START update_config
    if not isinstance(relationship_type, ClassConfigRelationshipType):
        raw_relationship_type = str(getattr(relationship_type, "value", relationship_type)).strip()
        try:
            relationship_type = ClassConfigRelationshipType(raw_relationship_type)
        except ValueError:
            relationship_type = ClassConfigRelationshipType[raw_relationship_type]

    if identity_rail is not None and not isinstance(
        identity_rail,
        ClassConfigRelationshipIdentityRail,
    ):
        raw_identity_rail = str(getattr(identity_rail, "value", identity_rail)).strip()
        try:
            identity_rail = ClassConfigRelationshipIdentityRail(raw_identity_rail)
        except ValueError:
            identity_rail = ClassConfigRelationshipIdentityRail[raw_identity_rail]

    if forward_loading_strategy is not None and not isinstance(
        forward_loading_strategy,
        ClassConfigRelationshipSideLoadingStrategy,
    ):
        raw_forward_loading_strategy = str(getattr(forward_loading_strategy, "value", forward_loading_strategy)).strip()
        try:
            forward_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(raw_forward_loading_strategy)
        except ValueError:
            forward_loading_strategy = ClassConfigRelationshipSideLoadingStrategy[raw_forward_loading_strategy]

    if reverse_loading_strategy is not None and not isinstance(
        reverse_loading_strategy,
        ClassConfigRelationshipSideLoadingStrategy,
    ):
        raw_reverse_loading_strategy = str(getattr(reverse_loading_strategy, "value", reverse_loading_strategy)).strip()
        try:
            reverse_loading_strategy = ClassConfigRelationshipSideLoadingStrategy(raw_reverse_loading_strategy)
        except ValueError:
            reverse_loading_strategy = ClassConfigRelationshipSideLoadingStrategy[raw_reverse_loading_strategy]

    if reified_role is not None and not isinstance(
        reified_role,
        ClassConfigRelationshipReifiedRole,
    ):
        raw_reified_role = str(getattr(reified_role, "value", reified_role)).strip()
        try:
            reified_role = ClassConfigRelationshipReifiedRole(raw_reified_role)
        except ValueError:
            reified_role = ClassConfigRelationshipReifiedRole[raw_reified_role]

    if reified_from_relationship_id is not None and not isinstance(
        reified_from_relationship_id,
        UUID,
    ):
        try:
            reified_from_relationship_id = UUID(str(reified_from_relationship_id))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "ClassConfigRelationship.update_config requires UUID-compatible "
                "reified_from_relationship_id: "
                f"reified_from_relationship_id={reified_from_relationship_id!r}"
            ) from exc

    reified_from_relationship = None
    if reified_from_relationship_id is not None:
        session = current_handler_session()
        reified_from_relationship = session.imap_get(
            ClassConfigRelationship,
            reified_from_relationship_id,
        )
        if reified_from_relationship is None:
            raise RuntimeError(
                "ClassConfigRelationship.update_config requires existing "
                "reified_from_relationship: "
                f"reified_from_relationship_id={reified_from_relationship_id}"
            )

    class_config_relationship.relationship_type = relationship_type
    class_config_relationship.identity_rail = identity_rail
    class_config_relationship.forward_required = forward_required
    class_config_relationship.forward_loading_strategy = forward_loading_strategy
    class_config_relationship.reverse_loading_strategy = reverse_loading_strategy
    class_config_relationship.reified_from_relationship = reified_from_relationship
    class_config_relationship.reified_from_relationship_id = reified_from_relationship_id
    class_config_relationship.reified_role = reified_role
    return None
    # --- AWARE: LOGIC END update_config


async def create_via_class_config(
    class_config_id: UUID,
    target_class_config_id: UUID,
    relationship_key: str,
    relationship_type: ClassConfigRelationshipType,
    identity_rail: ClassConfigRelationshipIdentityRail | None = None,
    forward_required: bool = False,
    forward_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reverse_loading_strategy: ClassConfigRelationshipSideLoadingStrategy | None = None,
    reified_from_relationship_id: UUID | None = None,
    reified_role: ClassConfigRelationshipReifiedRole | None = None,
) -> ClassConfigRelationship:
    """
    Create deterministic ClassConfigRelationship under a source ClassConfig scope.

    Contract:
    - Parent `ClassConfig` scope is propagated by traversal lowering.
    - Stable identity derives from propagated source class + `(target_class_config_id,
    relationship_key)`.
    - Association edges are materialized under this relationship via `create_association`.
    - Optional reification metadata does not participate in stable identity.
    """

    # --- AWARE: LOGIC START create_via_class_config
    normalized_relationship_key = (relationship_key or "").strip()
    if not normalized_relationship_key:
        raise RuntimeError("ClassConfigRelationship.create_via_class_config requires non-empty relationship_key")
    relationship_id = stable_class_relationship_id(
        source_class_id=class_config_id,
        target_class_id=target_class_config_id,
        relationship_key=normalized_relationship_key,
    )

    session = current_handler_session()
    existing = session.imap_get(ClassConfigRelationship, relationship_id)
    if existing is not None:
        if (
            existing.class_config_id != class_config_id
            or existing.target_class_config_id != target_class_config_id
            or (existing.relationship_key or "").strip() != normalized_relationship_key
            or existing.relationship_type != relationship_type
            or existing.identity_rail != identity_rail
            or existing.forward_required != forward_required
            or existing.forward_loading_strategy != forward_loading_strategy
            or existing.reverse_loading_strategy != reverse_loading_strategy
            or existing.reified_from_relationship_id != reified_from_relationship_id
            or existing.reified_role != reified_role
        ):
            raise RuntimeError(
                "ClassConfigRelationship.create_via_class_config payload mismatch "
                f"for existing relationship: relationship_id={relationship_id}"
            )
        return existing

    return ClassConfigRelationship(
        id=relationship_id,
        class_config_id=class_config_id,
        target_class_config_id=target_class_config_id,
        relationship_key=normalized_relationship_key,
        relationship_type=relationship_type,
        identity_rail=identity_rail,
        forward_required=forward_required,
        forward_loading_strategy=forward_loading_strategy,
        reverse_loading_strategy=reverse_loading_strategy,
        reified_from_relationship_id=reified_from_relationship_id,
        reified_role=reified_role,
        class_config_relationship_attributes=[],
    )
    # --- AWARE: LOGIC END create_via_class_config
