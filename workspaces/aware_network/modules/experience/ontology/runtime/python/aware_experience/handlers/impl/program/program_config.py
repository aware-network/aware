from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.program.program_enums import (
    ProgramAttributeType,
    ProgramBranchBindingMode,
)
from aware_experience_ontology.program.program_config import ProgramConfig
from aware_experience_ontology.program.program_config_actor_config import ProgramConfigActorConfig
from aware_experience_ontology.program.program_config_attribute_config import ProgramConfigAttributeConfig
from aware_experience_ontology.program.program_config_input_config import ProgramConfigInputConfig
from aware_experience_ontology.program.program_config_layout import ProgramConfigLayout
from aware_experience_ontology.program.program_config_port import ProgramConfigPort

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.primitive.code_primitive_enums import CodePrimitiveBaseType

# Meta Ontology
from aware_meta_ontology.attribute.attribute_config import AttributeConfig

# Experience Ontology
from aware_experience.stable_ids import stable_program_config_id

# Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build(
    key: str,
    title: str | None = None,
    description: str | None = None,
    narrative: str | None = None,
    intent: str | None = None,
    is_default: bool = False,
) -> ProgramConfig:
    """
    Create a deterministic graph-agnostic ProgramConfig.

    Contract:
    - Identity is compiler-derived from stable-id formula using `(key)`.
    - Graph ownership/linkage is represented only by ProgramConfigGraphProgramConfig.
    - Projection-port references are optional but explicit when present.
    """

    # --- AWARE: LOGIC START build
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProgramConfig.build requires non-empty key")
    config_id = stable_program_config_id(key=normalized_key)

    session = current_handler_session()
    existing = session.imap_get(ProgramConfig, config_id)
    if existing is not None:
        existing_key = (existing.key or "").strip()
        if existing_key != normalized_key:
            raise RuntimeError(
                "ProgramConfig.build key mismatch for existing config: " f"program_config_id={config_id}"
            )
        return existing

    return ProgramConfig(
        id=config_id,
        key=normalized_key,
        title=title,
        description=description,
        narrative=narrative,
        intent=(intent or "").strip() or None,
        is_default=bool(is_default),
    )
    # --- AWARE: LOGIC END build


async def add_attribute_config(
    program_config: ProgramConfig,
    attribute_config_id: UUID,
    type: ProgramAttributeType = ProgramAttributeType.input,
    position: int | None = None,
    required: bool = True,
    attribute_name: str | None = None,
) -> ProgramConfigAttributeConfig:
    """
    Attach one pre-existing typed AttributeConfig contract edge under this ProgramConfig.

    Contract:
    - Represents canonical program I/O schema intent.
    - Idempotent per `(program_config_id, attribute_config_id, type)`.
    - Fails closed when referenced AttributeConfig does not exist.
    """

    # --- AWARE: LOGIC START add_attribute_config
    program_config_id = program_config.id
    if program_config_id is None:
        raise RuntimeError("ProgramConfig.add_attribute_config requires id")

    session = current_handler_session()
    attribute_config = session.imap_get(AttributeConfig, attribute_config_id)
    if attribute_config is None:
        raise RuntimeError(
            "ProgramConfig.add_attribute_config requires AttributeConfig to exist. "
            "Create it first via AttributeConfig.create(...)."
        )
    if attribute_name is not None:
        expected_name = attribute_name.strip()
        if expected_name and (attribute_config.name or "").strip() != expected_name:
            raise RuntimeError(
                "ProgramConfig.add_attribute_config attribute name mismatch: "
                f"attribute_config_id={attribute_config_id}"
            )

    created = await ProgramConfigAttributeConfig.create_via_program_config(
        program_config_id=program_config_id,
        attribute_config_id=attribute_config_id,
        type=type,
        position=position,
        required=required,
    )

    for existing in program_config.attribute_configs:
        if existing.id == created.id:
            return existing
    program_config.attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_attribute_config


async def create_attribute_config(
    program_config: ProgramConfig,
    attribute_config_id: UUID,
    attribute_name: str,
    attribute_type_ref: str = "Any",
    enum_config_id: UUID | None = None,
    class_config_id: UUID | None = None,
    type: ProgramAttributeType = ProgramAttributeType.input,
    position: int | None = None,
    required: bool = True,
) -> ProgramConfigAttributeConfig:
    """
    Create AttributeConfig contract truth and attach typed association under this ProgramConfig.

    Contract:
    - Materializes AttributeConfig descriptor chain through canonical facade constructors.
    - Enum/Class contracts are link-only and must reference pre-existing OCG configs.
    - Creates/ensures ProgramConfigAttributeConfig association deterministically.
    """

    # --- AWARE: LOGIC START create_attribute_config
    program_config_id = program_config.id
    if program_config_id is None:
        raise RuntimeError("ProgramConfig.create_attribute_config requires id")

    normalized_name = (attribute_name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProgramConfig.create_attribute_config requires non-empty attribute_name")
    normalized_type_ref = (attribute_type_ref or "").strip() or "Any"
    if enum_config_id is not None and class_config_id is not None:
        raise RuntimeError(
            "ProgramConfig.create_attribute_config accepts at most one reference target: "
            "enum_config_id or class_config_id"
        )

    owner_key = str(program_config_id)
    if enum_config_id is not None:
        attribute_config = await AttributeConfig.create_enum(
            owner_key=owner_key,
            name=normalized_name,
            enum_config_id=enum_config_id,
            is_required=required,
        )
    elif class_config_id is not None:
        attribute_config = await AttributeConfig.create_class(
            owner_key=owner_key,
            name=normalized_name,
            type_class_config_id=class_config_id,
            is_required=required,
        )
    else:
        try:
            primitive_base_type = CodePrimitiveBaseType(normalized_type_ref.strip().casefold())
        except ValueError as exc:
            raise RuntimeError(
                "ProgramConfig.create_attribute_config requires primitive attribute_type_ref "
                "to resolve to CodePrimitiveBaseType when enum_config_id/class_config_id are absent: "
                f"attribute_type_ref={normalized_type_ref!r}"
            ) from exc
        attribute_config = await AttributeConfig.create_primitive(
            owner_key=owner_key,
            name=normalized_name,
            primitive_base_type=primitive_base_type,
            is_required=required,
        )

    created = await ProgramConfigAttributeConfig.create_via_program_config(
        program_config_id=program_config_id,
        attribute_config_id=attribute_config.id,
        type=type,
        position=position,
        required=required,
    )

    for existing in program_config.attribute_configs:
        if existing.id == created.id:
            return existing
    program_config.attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_attribute_config


async def create_input_config(
    program_config: ProgramConfig, name: str, source: str, required: bool = True, default_expr: JsonObject | None = None
) -> ProgramConfigInputConfig:
    """
    Create one deterministic ProgramConfigInputConfig under this ProgramConfig.
    """

    # --- AWARE: LOGIC START create_input_config
    program_config_id = program_config.id
    if program_config_id is None:
        raise RuntimeError("ProgramConfig.create_input_config requires id")

    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ProgramConfig.create_input_config requires non-empty name")
    normalized_source = (source or "").strip()
    if not normalized_source:
        raise RuntimeError("ProgramConfig.create_input_config requires non-empty source")

    created = await ProgramConfigInputConfig.build_via_program_config(
        program_config_id=program_config_id,
        name=normalized_name,
        source=normalized_source,
        required=required,
        default_expr=default_expr,
    )

    for existing in program_config.input_configs:
        if existing.id == created.id:
            return existing
    program_config.input_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_input_config


async def create_actor_config(
    program_config: ProgramConfig, actor_config_id: UUID, alias: str
) -> ProgramConfigActorConfig:
    """
    Create one deterministic ProgramConfigActorConfig under this ProgramConfig.
    """

    # --- AWARE: LOGIC START create_actor_config
    program_config_id = program_config.id
    if program_config_id is None:
        raise RuntimeError("ProgramConfig.create_actor_config requires id")

    normalized_alias = (alias or "").strip()
    if not normalized_alias:
        raise RuntimeError("ProgramConfig.create_actor_config requires non-empty alias")

    created = await ProgramConfigActorConfig.build_via_program_config(
        program_config_id=program_config_id,
        actor_config_id=actor_config_id,
        alias=normalized_alias,
    )

    for existing in program_config.actor_configs:
        if existing.id == created.id:
            return existing
    program_config.actor_configs.append(created)
    return created
    # --- AWARE: LOGIC END create_actor_config


async def create_port(
    program_config: ProgramConfig,
    projection_id: UUID,
    key: str | None = None,
    intent: str | None = None,
    branch_binding_mode: ProgramBranchBindingMode = ProgramBranchBindingMode.reference,
) -> ProgramConfigPort:
    """
    Create one deterministic ProgramConfigPort under this ProgramConfig.
    """

    # --- AWARE: LOGIC START create_port
    program_config_id = program_config.id
    if program_config_id is None:
        raise RuntimeError("ProgramConfig.create_port requires id")

    normalized_key = (key or "").strip() or None
    normalized_intent = (intent or "").strip() or None

    created = await ProgramConfigPort.build_via_program_config(
        program_config_id=program_config_id,
        projection_id=projection_id,
        key=normalized_key,
        intent=normalized_intent,
        branch_binding_mode=branch_binding_mode,
    )

    for existing in program_config.ports:
        if existing.id == created.id:
            return existing
    program_config.ports.append(created)
    return created
    # --- AWARE: LOGIC END create_port


async def create_layout(program_config: ProgramConfig, key: str, is_default: bool = False) -> ProgramConfigLayout:
    """
    Create one deterministic ProgramConfigLayout under this ProgramConfig.
    """

    # --- AWARE: LOGIC START create_layout
    program_config_id = program_config.id
    if program_config_id is None:
        raise RuntimeError("ProgramConfig.create_layout requires id")

    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ProgramConfig.create_layout requires non-empty key")

    if is_default:
        for existing in program_config.layouts:
            if existing.is_default:
                existing_key = (existing.key or "").strip()
                if existing_key != normalized_key:
                    raise RuntimeError("ProgramConfig.create_layout enforces single default layout")

    created = await ProgramConfigLayout.build_via_program_config(
        program_config_id=program_config_id,
        key=normalized_key,
        is_default=is_default,
    )

    for existing in program_config.layouts:
        if existing.id == created.id:
            return existing
    program_config.layouts.append(created)
    return created
    # --- AWARE: LOGIC END create_layout
