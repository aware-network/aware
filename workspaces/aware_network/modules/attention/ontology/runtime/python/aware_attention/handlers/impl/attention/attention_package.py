from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.attention.attention_package import AttentionPackage
from aware_attention_ontology.attention.attention_package_layout_config import AttentionPackageLayoutConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage

# Attention Ontology
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.stable_ids import stable_attention_package_id

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(name: str, source_code_package_id: UUID | None = None) -> AttentionPackage:
    """
    Create the canonical Attention-owned semantic package root.

    Contract:
    - Identity is keyed by Attention package `name`.
    - `AttentionPackage` is the package/public root over authored layout topology owned by one
      `aware.attention.toml` package.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
      package.
    - Workspace and later Interface/workflow rails should mount `AttentionPackage`, not raw
      `LayoutConfig` objects.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("AttentionPackage.build requires non-empty name")

    package_id = stable_attention_package_id(name=normalized_name)

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_source_code_package = (
        session.imap_get(CodePackage, source_code_package_id)
        if session is not None and source_code_package_id is not None
        else None
    )

    if session is not None:
        existing = session.imap_get(AttentionPackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "AttentionPackage.build payload mismatch for existing package: "
                    f"attention_package_id={package_id}"
                )
            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "AttentionPackage.build source_code_package_id mismatch for existing package: "
                        f"attention_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            return existing

    return AttentionPackage(
        id=package_id,
        name=normalized_name,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
    )
    # --- AWARE: LOGIC END build


async def attach_layout_config(
    attention_package: AttentionPackage, layout_config_id: UUID
) -> AttentionPackageLayoutConfig:
    """
    Attach one canonical `LayoutConfig` under this Attention package root.

    Contract:
    - Parent `AttentionPackage` scope is injected by propagation.
    - Identity is keyed by the attached `LayoutConfig`.
    - One Attention package may own multiple layouts without collapsing package truth and layout
      topology into one object.
    """

    # --- AWARE: LOGIC START attach_layout_config
    attention_package_layout_config = await AttentionPackageLayoutConfig.build_via_attention_package(
        attention_package_id=attention_package.id,
        layout_config_id=layout_config_id,
    )
    existing_index = next(
        (
            index
            for index, entry in enumerate(attention_package.layout_configs)
            if entry.id == attention_package_layout_config.id
        ),
        None,
    )
    if existing_index is None:
        attention_package.layout_configs = [
            *attention_package.layout_configs,
            attention_package_layout_config,
        ]
    elif attention_package.layout_configs[existing_index] is not attention_package_layout_config:
        updated = [*attention_package.layout_configs]
        updated[existing_index] = attention_package_layout_config
        attention_package.layout_configs = updated

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None
    if session is not None and attention_package_layout_config.layout_config is None:
        resolved_layout_config = session.imap_get(LayoutConfig, layout_config_id)
        if resolved_layout_config is not None:
            attention_package_layout_config.layout_config = resolved_layout_config

    return attention_package_layout_config
    # --- AWARE: LOGIC END attach_layout_config
