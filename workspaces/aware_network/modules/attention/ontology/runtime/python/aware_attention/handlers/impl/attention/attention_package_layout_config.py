from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Attention Ontology
from aware_attention_ontology.attention.attention_package_layout_config import AttentionPackageLayoutConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_attention_ontology.layout.layout_config import LayoutConfig
from aware_attention_ontology.stable_ids import (
    stable_attention_package_layout_config_id,
)

# Runtime
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build_via_attention_package(
    attention_package_id: UUID, layout_config_id: UUID
) -> AttentionPackageLayoutConfig:
    """
    Create one package-level Attention bridge to one `LayoutConfig`.

    Contract:
    - Parent `AttentionPackage` scope is injected by propagation.
    - Identity is keyed by the attached `LayoutConfig`.
    - This preserves AttentionPackage as the package/public root while `LayoutConfig` remains
      the canonical topology object.
    """

    # --- AWARE: LOGIC START build_via_attention_package
    edge_id = stable_attention_package_layout_config_id(
        attention_package_id=attention_package_id,
        layout_config_id=layout_config_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_layout_config = session.imap_get(LayoutConfig, layout_config_id) if session is not None else None

    if session is not None:
        existing = session.imap_get(AttentionPackageLayoutConfig, edge_id)
        if existing is not None:
            if existing.layout_config_id not in (None, layout_config_id):
                raise RuntimeError(
                    "AttentionPackageLayoutConfig existing layout_config_id mismatch: "
                    f"attention_package_layout_config_id={edge_id}"
                )
            if existing.layout_config is None:
                existing.layout_config = resolved_layout_config
            return existing

    return AttentionPackageLayoutConfig(
        id=edge_id,
        attention_package_id=attention_package_id,
        layout_config=resolved_layout_config,
        layout_config_id=layout_config_id,
    )
    # --- AWARE: LOGIC END build_via_attention_package
