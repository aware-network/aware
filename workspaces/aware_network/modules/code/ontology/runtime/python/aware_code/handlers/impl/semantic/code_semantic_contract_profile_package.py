from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.semantic.code_semantic_contract_profile_package import CodeSemanticContractProfilePackage
from aware_code_ontology.semantic.code_semantic_contract_runtime_import import CodeSemanticContractRuntimeImport

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build(
    code_package_id: UUID,
    semantic_contract_profile_id: UUID,
    profile_package_key: str,
    profile_key: str,
    source_workspace_handle: str | None = None,
    manifest_relative_path: str | None = None,
    runtime_import_mode: str = "dynamic_contract_module",
    runtime_import_required: bool = True,
    status: str = "active",
) -> CodeSemanticContractProfilePackage:
    """
    Bind one manifest-backed Code package/artifact to a semantic contract
    profile.

    Contract:
    - Each workspace publishes profile packages for its own provider
      surface.
    - Cross-workspace activation targets these package artifacts through
      Workspace dependency/profile resolution.
    - `runtime_import_required` records the current handler-backed bridge:
      semantic contract modules still need dynamic import availability even
      when no product package import is granted.
    """

    # --- AWARE: LOGIC START build
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build


async def attach_runtime_import(
    code_semantic_contract_profile_package: CodeSemanticContractProfilePackage,
    provider_key: str,
    semantic_contract_module: str,
    import_role: str = "semantic_contract",
    owned_manifest_kinds: list[str] = [],
    capabilities: list[str] = [],
    required: bool = True,
    status: str = "active",
) -> CodeSemanticContractRuntimeImport:
    """
    Attach one dynamic semantic contract module import under this profile
    package.
    """

    # --- AWARE: LOGIC START attach_runtime_import
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END attach_runtime_import
