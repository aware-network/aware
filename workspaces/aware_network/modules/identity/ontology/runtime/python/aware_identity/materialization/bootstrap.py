from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from uuid import UUID

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
    SemanticPackageMaterializationRuntimeContextRequest,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.materialization.context import (
    build_meta_workspace_materialization_runtime_context,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session


@dataclass(frozen=True, slots=True)
class ActorIdentityBinding:
    actor_id: UUID
    identity_id: UUID
    identity_branch_id: UUID


async def build_identity_materialization_context(
    *,
    repo_root: Path,
    runtime_ontology_package_names: Sequence[str],
    semantic_ontology_package_catalog: Mapping[str, object],
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
) -> object:
    if (process_id is None) != (thread_id is None):
        raise ValueError(
            "Identity materialization requires process_id and thread_id together "
            + "when overriding the default boot lane"
        )

    resolved_repo_root = repo_root.expanduser().resolve()
    resolved_runtime_root = _runtime_storage_root(default_root=resolved_repo_root)
    package_names = _clean_runtime_ontology_package_names(
        runtime_ontology_package_names=runtime_ontology_package_names,
    )
    semantic_ontology_catalog = _semantic_ontology_package_catalog_payload(
        semantic_ontology_catalog=semantic_ontology_package_catalog,
    )
    context = build_meta_workspace_materialization_runtime_context(
        SemanticPackageMaterializationRuntimeContextRequest(
            provider_key="identity",
            semantic_owner="identity",
            workspace_root=resolved_runtime_root,
            repo_root=resolved_repo_root,
            actor_id=actor_id,
            context={
                "runtime_ontology_package_names": package_names,
                SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: (
                    semantic_ontology_catalog
                ),
            },
        )
    )
    if context is None:
        raise RuntimeError(
            "Identity materialization could not build a Meta runtime context: "
            + f"runtime_ontology_package_names={package_names!r}"
        )
    return context


def _clean_runtime_ontology_package_names(
    *,
    runtime_ontology_package_names: Sequence[str],
) -> tuple[str, ...]:
    package_names = tuple(
        dict.fromkeys(
            str(package_name).strip()
            for package_name in runtime_ontology_package_names
            if str(package_name).strip()
        )
    )
    if not package_names:
        raise ValueError(
            "Identity materialization requires at least one runtime ontology package name"
        )
    return package_names


def _runtime_storage_root(*, default_root: Path) -> Path:
    raw_root = os.environ.get("AWARE_ROOT")
    if raw_root is not None and raw_root.strip():
        return Path(raw_root).expanduser().resolve()
    return default_root


def _semantic_ontology_package_catalog_payload(
    *,
    semantic_ontology_catalog: Mapping[str, object],
) -> dict[str, object]:
    schema = semantic_ontology_catalog.get("schema")
    if schema != SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA:
        raise ValueError(
            "Identity materialization requires a semantic ontology package catalog "
            + f"with schema={SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA!r}; "
            + f"got {schema!r}"
        )
    raw_entries = semantic_ontology_catalog.get("entries")
    if not isinstance(raw_entries, (tuple, list)):
        raise ValueError("Identity semantic ontology catalog must include entries.")
    if not raw_entries:
        raise ValueError("Identity semantic ontology catalog must not be empty.")
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping):
            raise ValueError(
                "Identity semantic ontology catalog entries must be mappings."
            )
        package_name = str(raw_entry.get("package_name") or "").strip()
        if not package_name:
            raise ValueError(
                "Identity semantic ontology catalog entries must have non-empty "
                + "package_name values."
            )
    return dict(semantic_ontology_catalog)


def _optional_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    name: str,
) -> str | None:
    matches = sorted(
        {
            opg.projection_hash
            for opg in index.ocg.object_projection_graphs
            if (opg.name or "").strip() == name.strip()
        }
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(f"Expected one projection hash for {name!r}, got {matches}")
    return matches[0]


async def resolve_actor_identity_binding(
    *,
    index: object,
    actor_id: UUID,
    identity_projection_hash: str,
) -> ActorIdentityBinding | None:
    runtime_index = cast(MetaGraphRuntimeIndex, index)
    projection_hash = _resolve_identity_projection_hash(
        index=runtime_index,
        identity_projection_hash=identity_projection_hash,
    )
    if projection_hash is None:
        return None

    best: ActorIdentityBinding | None = None
    async for (
        identity_branch_id,
        _head,
    ) in FSCommitStore().iter_lane_heads_by_projection(
        projection_hash=projection_hash,
    ):
        candidate = await _materialize_actor_identity_binding(
            index=runtime_index,
            projection_hash=projection_hash,
            identity_branch_id=identity_branch_id,
            actor_id=actor_id,
        )
        if candidate is None:
            continue
        if best is None or _binding_score(candidate) >= _binding_score(best):
            best = candidate
    return best


def _resolve_identity_projection_hash(
    *,
    index: MetaGraphRuntimeIndex,
    identity_projection_hash: str | None,
) -> str | None:
    if isinstance(identity_projection_hash, str) and identity_projection_hash.strip():
        return identity_projection_hash.strip()
    return _optional_projection_hash_by_name(index=index, name="Identity")


async def _materialize_actor_identity_binding(
    *,
    index: MetaGraphRuntimeIndex,
    projection_hash: str,
    identity_branch_id: UUID,
    actor_id: UUID,
) -> ActorIdentityBinding | None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        return None
    try:
        graph, _ = await OIGMaterializer().get(
            branch_id=identity_branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        session = reify_oig_session(
            index=index,
            opg=opg,
            oig=graph,
            branch_id=identity_branch_id,
        )
    except Exception:
        return None

    actor_model_cls = _actor_model_cls_or_none()
    for obj in session.imap_all_objects():
        if actor_model_cls is not None and not isinstance(obj, actor_model_cls):
            continue
        if actor_model_cls is None and obj.__class__.__name__.casefold() != "actor":
            continue

        candidate_actor_id = getattr(obj, "id", None)
        identity_id = getattr(obj, "identity_id", None)
        if candidate_actor_id != actor_id or not isinstance(identity_id, UUID):
            continue
        return ActorIdentityBinding(
            actor_id=actor_id,
            identity_id=identity_id,
            identity_branch_id=identity_branch_id,
        )
    return None


def _actor_model_cls_or_none() -> type | None:
    try:
        from aware_identity_ontology.actor.actor import Actor
    except Exception:
        return None
    return Actor


def _binding_score(binding: ActorIdentityBinding) -> int:
    return 2 if binding.identity_branch_id == binding.identity_id else 1


__all__ = [
    "ActorIdentityBinding",
    "build_identity_materialization_context",
    "resolve_actor_identity_binding",
]
