from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Sdk Ontology
from aware_sdk_ontology.sdk.sdk_package_api_package import SdkPackageApiPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_sdk_ontology.stable_ids import stable_sdk_package_api_package_id

# --- AWARE: USER_IMPORTS END


async def build_via_sdk_package(
    sdk_package_id: UUID, api_package_id: UUID, description: str | None = None
) -> SdkPackageApiPackage:
    """
    Create one package-level SDK bridge to one API package.

    Contract:
    - Parent `SdkPackage` scope is injected by propagation.
    - Identity is keyed by the attached `ApiPackage`.
    - This is package/import truth; operation endpoint routing remains operation-owned.
    """

    # --- AWARE: LOGIC START build_via_sdk_package
    return SdkPackageApiPackage(
        id=stable_sdk_package_api_package_id(
            sdk_package_id=sdk_package_id,
            api_package_id=api_package_id,
        ),
        sdk_package_id=sdk_package_id,
        api_package_id=api_package_id,
        description=(description or "").strip() or None,
    )
    # --- AWARE: LOGIC END build_via_sdk_package
