from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph_package_implementation_policy_enums import (
    ObjectConfigGraphPackageFunctionImplOwnership,
    ObjectConfigGraphPackageFunctionImplParityPolicy,
)
from aware_meta_ontology.graph.config.object_config_graph_package import ObjectConfigGraphPackage

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# Code Ontology
from aware_code_ontology.package.code_package import CodePackage

# Meta Ontology
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
    ObjectInstanceGraphCommit,
)

# Meta Runtime
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# Meta
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id

# --- AWARE: USER_IMPORTS END


async def build(
    package_name: str,
    fqn_prefix: str,
    source_code_package_id: UUID | None = None,
    object_config_graph_id: UUID | None = None,
    object_config_graph_object_instance_graph_commit_id: UUID | None = None,
    object_config_graph_package_id: UUID | None = None,
    function_impl_ownership: ObjectConfigGraphPackageFunctionImplOwnership = ObjectConfigGraphPackageFunctionImplOwnership.authored,
    function_impl_parity_policy: ObjectConfigGraphPackageFunctionImplParityPolicy = ObjectConfigGraphPackageFunctionImplParityPolicy.off,
    implementation_policy_source: str = "aware_toml",
    title: str | None = None,
    description: str | None = None,
) -> ObjectConfigGraphPackage:
    """
    Create deterministic ObjectConfigGraphPackage for runtime/package proofs.

    Contract:
    - Identity is keyed by `(package_name, fqn_prefix)`.
    - `source_code_package_id` is the explicit provenance link back to canonical source-package truth.
    - `object_config_graph_id` is the semantic graph owned by this package when already materialized.
    - `object_config_graph_object_instance_graph_commit_id` pins the committed OCG root.
    - `function_impl_*` policy is package-level semantic execution authority derived from `aware.toml`.
    """

    # --- AWARE: LOGIC START build
    normalized_package_name = (package_name or "").strip()
    normalized_fqn_prefix = (fqn_prefix or "").strip()
    if not normalized_package_name:
        raise RuntimeError("ObjectConfigGraphPackage.build requires non-empty package_name")
    if not normalized_fqn_prefix:
        raise RuntimeError("ObjectConfigGraphPackage.build requires non-empty fqn_prefix")

    expected_package_id = stable_object_config_graph_package_id(
        package_name=normalized_package_name,
        fqn_prefix=normalized_fqn_prefix,
    )
    if object_config_graph_package_id is not None and object_config_graph_package_id != expected_package_id:
        raise RuntimeError(
            "ObjectConfigGraphPackage.build object_config_graph_package_id does not match deterministic "
            "stable-id for (package_name, fqn_prefix): "
            f"provided={object_config_graph_package_id} expected={expected_package_id} "
            f"package_name={normalized_package_name!r} fqn_prefix={normalized_fqn_prefix!r}"
        )
    resolved_package_id = expected_package_id

    session = current_handler_session()

    # Cross-projection package provenance may already exist on the branch but not yet be
    # materialized in the current handler session. Keep FK truth canonical, and attach the
    # object eagerly only when the current session already has it.
    source_code_package = (
        session.imap_get(CodePackage, source_code_package_id) if source_code_package_id is not None else None
    )
    object_config_graph = (
        session.imap_get(ObjectConfigGraph, object_config_graph_id) if object_config_graph_id is not None else None
    )
    object_config_graph_object_instance_graph_commit = (
        session.imap_get(
            ObjectInstanceGraphCommit,
            object_config_graph_object_instance_graph_commit_id,
        )
        if object_config_graph_object_instance_graph_commit_id is not None
        else None
    )
    normalized_title = (title or "").strip() or None
    normalized_description = (description or "").strip() or None
    normalized_policy_source = (implementation_policy_source or "").strip() or "aware_toml"

    existing = session.imap_get(ObjectConfigGraphPackage, resolved_package_id)
    if existing is not None:
        if (existing.package_name or "").strip() != normalized_package_name or (
            existing.fqn_prefix or ""
        ).strip() != normalized_fqn_prefix:
            raise RuntimeError(
                "ObjectConfigGraphPackage.build payload mismatch for existing package: "
                f"object_config_graph_package_id={resolved_package_id}"
            )
        existing_source_code_package_id = existing.source_code_package_id
        if source_code_package_id is not None:
            if existing_source_code_package_id is None:
                existing.source_code_package_id = source_code_package_id
                existing.source_code_package = source_code_package
            elif existing_source_code_package_id != source_code_package_id:
                raise RuntimeError(
                    "ObjectConfigGraphPackage.build source_code_package_id mismatch for existing package: "
                    f"object_config_graph_package_id={resolved_package_id} "
                    f"existing={existing_source_code_package_id} provided={source_code_package_id}"
                )

        existing_object_config_graph_id = existing.object_config_graph_id
        if object_config_graph_id is not None:
            if existing_object_config_graph_id is None:
                existing.object_config_graph_id = object_config_graph_id
                existing.object_config_graph = object_config_graph
            elif existing_object_config_graph_id != object_config_graph_id:
                raise RuntimeError(
                    "ObjectConfigGraphPackage.build object_config_graph_id mismatch for existing package: "
                    f"object_config_graph_package_id={resolved_package_id} "
                    f"existing={existing_object_config_graph_id} provided={object_config_graph_id}"
                )

        existing_graph_commit_id = existing.object_config_graph_object_instance_graph_commit_id
        if object_config_graph_object_instance_graph_commit_id is not None:
            if existing_graph_commit_id is None:
                existing.object_config_graph_object_instance_graph_commit_id = (
                    object_config_graph_object_instance_graph_commit_id
                )
                existing.object_config_graph_object_instance_graph_commit = (
                    object_config_graph_object_instance_graph_commit
                )
            elif existing_graph_commit_id != object_config_graph_object_instance_graph_commit_id:
                existing.object_config_graph_object_instance_graph_commit_id = (
                    object_config_graph_object_instance_graph_commit_id
                )
                existing.object_config_graph_object_instance_graph_commit = (
                    object_config_graph_object_instance_graph_commit
                )

        existing_title = (existing.title or "").strip() or None
        if normalized_title is not None:
            if existing_title is None:
                existing.title = normalized_title
            elif existing_title != normalized_title:
                raise RuntimeError(
                    "ObjectConfigGraphPackage.build title mismatch for existing package: "
                    f"object_config_graph_package_id={resolved_package_id}"
                )

        existing_description = (existing.description or "").strip() or None
        if normalized_description is not None:
            if existing_description is None:
                existing.description = normalized_description
            elif existing_description != normalized_description:
                raise RuntimeError(
                    "ObjectConfigGraphPackage.build description mismatch for existing package: "
                    f"object_config_graph_package_id={resolved_package_id}"
                )
        existing.function_impl_ownership = function_impl_ownership
        existing.function_impl_parity_policy = function_impl_parity_policy
        existing.implementation_policy_source = normalized_policy_source
        return existing

    return ObjectConfigGraphPackage(
        id=resolved_package_id,
        package_name=normalized_package_name,
        fqn_prefix=normalized_fqn_prefix,
        source_code_package=source_code_package,
        source_code_package_id=source_code_package_id,
        object_config_graph=object_config_graph,
        object_config_graph_id=object_config_graph_id,
        object_config_graph_object_instance_graph_commit=(object_config_graph_object_instance_graph_commit),
        object_config_graph_object_instance_graph_commit_id=(object_config_graph_object_instance_graph_commit_id),
        title=normalized_title,
        description=normalized_description,
        function_impl_ownership=function_impl_ownership,
        function_impl_parity_policy=function_impl_parity_policy,
        implementation_policy_source=normalized_policy_source,
    )
    # --- AWARE: LOGIC END build


async def attach_object_config_graph(
    object_config_graph_package: ObjectConfigGraphPackage,
    object_config_graph_id: UUID,
    object_config_graph_object_instance_graph_commit_id: UUID | None = None,
    title: str | None = None,
    description: str | None = None,
) -> bool:
    """
    Attach canonical `ObjectConfigGraph` leaf truth to this semantic package root.

    Contract:
    - Parent package scope is already resolved by instance invocation.
    - `object_config_graph_id` must point at the canonical graph leaf owned by this package.
    - `object_config_graph_object_instance_graph_commit_id`, when provided, must point at the
      historical OIG commit for that canonical graph leaf.
    - The package shell may exist before the graph leaf is materialized; this method deepens
      the package shell without collapsing package and graph layers.
    """

    # --- AWARE: LOGIC START attach_object_config_graph
    existing_graph_id = object_config_graph_package.object_config_graph_id
    if existing_graph_id is None:
        object_config_graph_package.object_config_graph_id = object_config_graph_id
        object_config_graph_package.object_config_graph = None
    elif existing_graph_id != object_config_graph_id:
        raise RuntimeError(
            "ObjectConfigGraphPackage.attach_object_config_graph graph mismatch for existing package: "
            f"object_config_graph_package_id={object_config_graph_package.id} "
            f"existing={existing_graph_id} provided={object_config_graph_id}"
        )

    existing_graph_commit_id = object_config_graph_package.object_config_graph_object_instance_graph_commit_id
    if object_config_graph_object_instance_graph_commit_id is not None:
        if existing_graph_commit_id is None:
            object_config_graph_package.object_config_graph_object_instance_graph_commit_id = (
                object_config_graph_object_instance_graph_commit_id
            )
            object_config_graph_package.object_config_graph_object_instance_graph_commit = None
        elif existing_graph_commit_id != object_config_graph_object_instance_graph_commit_id:
            object_config_graph_package.object_config_graph_object_instance_graph_commit_id = (
                object_config_graph_object_instance_graph_commit_id
            )
            object_config_graph_package.object_config_graph_object_instance_graph_commit = None

    normalized_title = (title or "").strip() or None
    existing_title = (object_config_graph_package.title or "").strip() or None
    if normalized_title is not None:
        if existing_title is None:
            object_config_graph_package.title = normalized_title
        elif existing_title != normalized_title:
            raise RuntimeError(
                "ObjectConfigGraphPackage.attach_object_config_graph title mismatch for existing package: "
                f"object_config_graph_package_id={object_config_graph_package.id}"
            )

    normalized_description = (description or "").strip() or None
    existing_description = (object_config_graph_package.description or "").strip() or None
    if normalized_description is not None:
        if existing_description is None:
            object_config_graph_package.description = normalized_description
        elif existing_description != normalized_description:
            raise RuntimeError(
                "ObjectConfigGraphPackage.attach_object_config_graph description mismatch for existing package: "
                f"object_config_graph_package_id={object_config_graph_package.id}"
            )

    return True
    # --- AWARE: LOGIC END attach_object_config_graph
