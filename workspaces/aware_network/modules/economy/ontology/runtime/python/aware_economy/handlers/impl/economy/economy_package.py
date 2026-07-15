from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Economy Ontology
from aware_economy_ontology.economy.economy_package import EconomyPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code_ontology.package.code_package import CodePackage
from aware_economy_ontology.stable_ids import stable_economy_package_id
from aware_meta.runtime.handler_context import current_handler_session

# --- AWARE: USER_IMPORTS END


async def build(name: str, source_code_package_id: UUID | None = None) -> EconomyPackage:
    """
    Create the canonical Economy-owned semantic package root.

    Contract:
    - Identity is keyed by Economy package `name`.
    - `EconomyPackage` is the package/public root for authored Economy truth.
    - `source_code_package_id` is the explicit raw-source provenance link for this semantic leaf
      package.
    - Concrete price/contract materialization remains Economy-owned and will resolve under this
      package rail, not under Service.
    """

    # --- AWARE: LOGIC START build
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("EconomyPackage.build requires non-empty name")

    package_id = stable_economy_package_id(name=normalized_name)

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
        existing = session.imap_get(EconomyPackage, package_id)
        if existing is not None:
            if (existing.name or "").strip() != normalized_name:
                raise RuntimeError(
                    "EconomyPackage.build payload mismatch for existing package: " f"economy_package_id={package_id}"
                )

            existing_source_code_package_id = existing.source_code_package_id
            if source_code_package_id is not None:
                if existing_source_code_package_id is None:
                    existing.source_code_package_id = source_code_package_id
                    existing.source_code_package = resolved_source_code_package
                elif existing_source_code_package_id != source_code_package_id:
                    raise RuntimeError(
                        "EconomyPackage.build source_code_package_id mismatch for existing package: "
                        f"economy_package_id={package_id} "
                        f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                    )
            return existing

    return EconomyPackage.model_construct(
        id=package_id,
        name=normalized_name,
        source_code_package=resolved_source_code_package,
        source_code_package_id=source_code_package_id,
    )
    # --- AWARE: LOGIC END build
