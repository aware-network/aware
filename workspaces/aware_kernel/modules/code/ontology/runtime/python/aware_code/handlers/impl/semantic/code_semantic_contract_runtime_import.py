from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code Ontology
from aware_code_ontology.semantic.code_semantic_contract_runtime_import import CodeSemanticContractRuntimeImport

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_code_semantic_contract_profile_package(
    code_semantic_contract_profile_package_id: UUID,
    provider_key: str,
    semantic_contract_module: str,
    import_role: str = "semantic_contract",
    owned_manifest_kinds: list[str] = [],
    capabilities: list[str] = [],
    required: bool = True,
    status: str = "active",
) -> CodeSemanticContractRuntimeImport:
    """
    Record one dynamic semantic contract runtime import required by a
    CodeSemanticContractProfilePackage.

    Contract:
    - This is runtime/provider activation truth, not product package import
      permission.
    - The current materializer still imports semantic contract handler
      modules, so profile packages must expose these dynamic runtime imports
      until the full contract surface becomes declarative.
    """

    # --- AWARE: LOGIC START build_via_code_semantic_contract_profile_package
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_code_semantic_contract_profile_package
