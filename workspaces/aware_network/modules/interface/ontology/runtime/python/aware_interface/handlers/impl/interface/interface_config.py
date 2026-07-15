from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Interface Ontology
from aware_interface_ontology.interface.interface_enums import InterfaceOs
from aware_interface_ontology.interface.interface import Interface
from aware_interface_ontology.interface.interface_config import InterfaceConfig
from aware_interface_ontology.interface.interface_config_pane_config import InterfaceConfigPaneConfig
from aware_interface_ontology.interface.interface_config_window_config import InterfaceConfigWindowConfig
from aware_interface_ontology.interface.pane_config import PaneConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_config_pane_config_id,
    stable_interface_config_window_config_id,
    stable_interface_id,
    stable_pane_config_id,
)
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(name: str, description: str | None = None) -> InterfaceConfig:
    """
    Create one deterministic InterfaceConfig.
    """

    # --- AWARE: LOGIC START build
    interface_config_id = stable_interface_config_id(name=name)
    return InterfaceConfig(id=interface_config_id, name=name, description=description)
    # --- AWARE: LOGIC END build


async def create_interface(interface_config: InterfaceConfig, os: InterfaceOs, version: str) -> Interface:
    """
    Create one runtime Interface instance under this InterfaceConfig.
    """

    # --- AWARE: LOGIC START create_interface
    if interface_config.id is None:
        raise RuntimeError("InterfaceConfig.create_interface requires InterfaceConfig.id")

    for existing in interface_config.interfaces:
        if existing.os == os and existing.version == version:
            return existing

    stable_os = os.value if hasattr(os, "value") else str(os)
    created = Interface(
        id=stable_interface_id(
            interface_config_id=interface_config.id,
            os=stable_os,
            version=version,
        ),
        interface_config_id=interface_config.id,
        os=os,
        version=version,
    )
    interface_config.interfaces.append(created)
    return created
    # --- AWARE: LOGIC END create_interface


async def attach_window_config(
    interface_config: InterfaceConfig, window_config_id: UUID
) -> InterfaceConfigWindowConfig:
    """
    Attach one existing standalone WindowConfig beneath this InterfaceConfig.
    """

    # --- AWARE: LOGIC START attach_window_config
    if interface_config.id is None:
        raise RuntimeError("InterfaceConfig.attach_window_config requires InterfaceConfig.id")

    interface_config_window_config_id = stable_interface_config_window_config_id(
        interface_config_id=interface_config.id,
        window_config_id=window_config_id,
    )

    for existing in interface_config.interface_config_window_configs:
        if existing.id == interface_config_window_config_id or existing.window_config_id == window_config_id:
            return existing

    created = InterfaceConfigWindowConfig.model_construct(
        id=interface_config_window_config_id,
        interface_config_id=interface_config.id,
        window_config=None,
        window_config_id=window_config_id,
    )
    interface_config.interface_config_window_configs.append(created)
    return created
    # --- AWARE: LOGIC END attach_window_config


async def attach_pane_config(
    interface_config: InterfaceConfig, pane_config_id: UUID, narrative_key: str | None = None
) -> InterfaceConfigPaneConfig:
    """
    Attach one existing standalone PaneConfig beneath this InterfaceConfig.
    """

    # --- AWARE: LOGIC START attach_pane_config
    if interface_config.id is None:
        raise RuntimeError("InterfaceConfig.attach_pane_config requires InterfaceConfig.id")

    interface_config_pane_config_id = stable_interface_config_pane_config_id(
        interface_config_id=interface_config.id,
        pane_config_id=pane_config_id,
    )
    for existing in interface_config.interface_config_pane_configs:
        if existing.id == interface_config_pane_config_id or existing.pane_config_id == pane_config_id:
            if narrative_key is not None and existing.narrative_key != narrative_key:
                return await existing.set_narrative_key(narrative_key=narrative_key)
            return existing

    created = InterfaceConfigPaneConfig.model_construct(
        id=interface_config_pane_config_id,
        interface_config_id=interface_config.id,
        pane_config=None,
        section_mounts=[],
        pane_config_id=pane_config_id,
        narrative_key=narrative_key,
    )
    interface_config.interface_config_pane_configs.append(created)
    return created
    # --- AWARE: LOGIC END attach_pane_config


async def create_pane_config(
    interface_config: InterfaceConfig,
    name: str,
    projection_experience_view_id: UUID,
    pane_kind: str,
    view_ref: str | None = None,
    description: str | None = None,
) -> PaneConfig:
    """
    Compatibility helper: create one standalone PaneConfig and attach it to this InterfaceConfig.

    Contract:
    - Pane semantic identity remains standalone.
    - This helper exists so current runtime/materialization rails can stay on one projection lane during
      the extraction.
    - Long-term authored `pane` / `interface` grammar should replace this convenience path.
    """

    # --- AWARE: LOGIC START create_pane_config
    if interface_config.id is None:
        raise RuntimeError("InterfaceConfig.create_pane_config requires InterfaceConfig.id")

    pane_config_id = stable_pane_config_id(
        name=name,
        projection_experience_view_id=projection_experience_view_id,
    )

    try:
        session = current_handler_session()
    except RuntimeError:
        session = None

    resolved_pane_config = session.imap_get(PaneConfig, pane_config_id) if session is not None else None
    if resolved_pane_config is None:
        resolved_pane_config = PaneConfig.model_construct(
            id=pane_config_id,
            projection_experience_view_id=projection_experience_view_id,
            projection_experience_view=None,
            name=name,
            pane_kind=pane_kind,
            view_ref=view_ref,
            description=description,
        )

    _ = await attach_pane_config(interface_config=interface_config, pane_config_id=resolved_pane_config.id)
    return resolved_pane_config
    # --- AWARE: LOGIC END create_pane_config
