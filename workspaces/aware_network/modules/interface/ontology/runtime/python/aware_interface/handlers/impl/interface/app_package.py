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
from aware_interface_ontology.interface.app_package import AppPackage
from aware_interface_ontology.interface.app_package_experience_package import AppPackageExperiencePackage
from aware_interface_ontology.interface.app_package_interface_package import AppPackageInterfacePackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(
    name: str,
    app_config_id: UUID,
    app_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_app_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    dependencies: JsonArray = JsonArray(),
    dart: JsonObject = JsonObject(),
    metadata_json: JsonObject = JsonObject(),
) -> AppPackage:
    """
    Create the canonical app package root over an AppConfig.

    Contract:
    - AppPackage is the installable app package boundary.
    - AppConfig owns screen composition intent.
    - Apps depend on ExperiencePackage and InterfacePackage truth; they do not
      target Environment profile/session/process/thread coordinates directly.
    - `app_config_object_instance_graph_commit_id`, when present, pins exact
      AppConfig replay truth for WorkspaceRevision consumers.
    - `source_code_package_id` is raw-source provenance only.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build


async def sync_manifest_truth(
    app_package: AppPackage,
    app_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    version_number: int = 1,
    title: str | None = None,
    description: str | None = None,
    aware_app_version: int = 1,
    manifest_relative_path: str | None = None,
    package_root: str = ".",
    dependencies: JsonArray = JsonArray(),
    dart: JsonObject = JsonObject(),
    metadata_json: JsonObject = JsonObject(),
) -> AppPackage:
    """
    Sync mutable app manifest truth onto an existing AppPackage root.

    Contract:
    - Manifest evidence is replay metadata, not dependency authority.
    - Typed package dependencies remain represented through child portal rows.
    - Environment admission remains resolved by Experience/Interface services.
    """

    # --- AWARE: LOGIC START sync_manifest_truth
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END sync_manifest_truth


async def attach_experience_package(
    app_package: AppPackage,
    experience_package_id: UUID,
    experience_package_object_instance_graph_commit_id: UUID | None = None,
    role: str = "experience",
    description: str | None = None,
) -> AppPackageExperiencePackage:
    """
    Attach one ExperiencePackage dependency to this app.

    Contract:
    - The app selects Experience entry points and layout bindings through
      AppConfigScreenConfig.
    - Environment package/profile/session targets must remain behind
      Experience resolution, not on AppPackage.
    """

    # --- AWARE: LOGIC START attach_experience_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_experience_package


async def attach_interface_package(
    app_package: AppPackage,
    interface_package_id: UUID,
    interface_package_object_instance_graph_commit_id: UUID | None = None,
    role: str = "interface",
    description: str | None = None,
) -> AppPackageInterfacePackage:
    """
    Attach one InterfacePackage dependency to this app.

    Contract:
    - InterfacePackage supplies reusable shell/pane/render composition truth.
    - It does not authorize app-owned Environment targets or app-specific
      pane defaults.
    """

    # --- AWARE: LOGIC START attach_interface_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_interface_package
