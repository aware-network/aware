from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import (
    JsonArray,
    JsonObject,
)

# Interface Ontology
from aware_interface_ontology.interface.render_component_package import RenderComponentPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    render_component_config_id: UUID,
    render_component_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_render_component_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = ".",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    python: JsonObject = JsonObject(),
    dart: JsonObject = JsonObject(),
) -> RenderComponentPackage:
    """
    Create the canonical Interface-owned package root over an existing `RenderComponentConfig`.

    Contract:
    - Identity is keyed by render component package `name`.
    - `RenderComponentPackage` is the package/public root over reusable rich renderer
      component contracts.
    - `render_component_config_id` must point at the canonical component contract root.
    - `render_component_config_object_instance_graph_commit_id` pins the historical
      ObjectInstanceGraphCommit for replayable component package truth.
    - `source_code_package_id` is the explicit raw-source provenance link for renderer
      implementation packages.
    - Manifest/build/python/dart attributes mirror `aware.render_component.toml` so committed
      package truth can drive Interface and Pane render component routing without reopening
      authoring TOML.
    - Panes may depend on this package, but components never own pane state or call services.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    render_component_package: RenderComponentPackage,
    render_component_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    fqn_prefix: str | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_render_component_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    sources_root: str = ".",
    include_paths: JsonArray = JsonArray(),
    exclude_paths: JsonArray = JsonArray(),
    force_fresh_scan: bool = True,
    python: JsonObject = JsonObject(),
    dart: JsonObject = JsonObject(),
) -> RenderComponentPackage:
    """
    Sync mutable manifest/build/python/dart truth onto an existing RenderComponentPackage root.

    This keeps `build` create-only while allowing committed package truth to follow the latest
    parsed `aware.render_component.toml` snapshot and pinned semantic RenderComponentConfig commit.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END sync_manifest_truth
