from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_orm.models.orm_model import ORMModel
from aware_skill_ontology.skill.skill_config import SkillConfig
from aware_skill_ontology.skill.skill_package import SkillPackage
from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage
from aware_skill_ontology.stable_ids import stable_skill_package_id

_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class SkillRuntimePackageRef:
    """Runtime ref for an environment-selected SkillPackage semantic package."""

    family_key: str
    package_kind: str
    package_name: str
    manifest_path: str | Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(_clean(self.semantic_package_id) or _clean(self.semantic_root_id))


@dataclass(frozen=True, slots=True)
class ResolvedSkillRuntimePackageRef:
    """Resolved SkillPackage coordinates from committed package/root truth."""

    package_ref: SkillRuntimePackageRef
    package_name: str
    skill_package_id: UUID
    skill_config_id: UUID
    skill_config_object_instance_graph_commit_id: UUID
    skill_package: SkillPackage
    skill_config: SkillConfig
    skill_package_api_packages: tuple[SkillPackageApiPackage, ...]
    api_package_ids: tuple[UUID, ...]
    skill_config_projection_hash: str
    skill_config_domain_commit_id: UUID
    materialized_workspace_root: Path | None = None
    manifest_path: Path | None = None
    manifest_relative_path: str | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def toml_paths(self) -> tuple[Path, ...]:
        """Compatibility shape for callers still accepting implementation TOML paths."""

        return (self.manifest_path,) if self.manifest_path is not None else ()


async def resolve_committed_skill_runtime_package_ref(
    *,
    index: MetaGraphRuntimeIndex,
    package_ref: SkillRuntimePackageRef,
    materialized_workspace_root: str | Path | None = None,
) -> ResolvedSkillRuntimePackageRef:
    """Resolve a committed SkillPackage ref without reopening aware.skill.toml."""

    _validate_skill_ref(package_ref)
    root = (
        Path(materialized_workspace_root).expanduser().resolve()
        if materialized_workspace_root is not None
        else None
    )
    package_commit_ref_label = "semantic_object_instance_graph_commit_id"
    package_commit_ref_value = _clean(
        package_ref.semantic_object_instance_graph_commit_id
    )
    if package_commit_ref_value is None:
        package_commit_ref_label = "semantic_head_commit_id"
        package_commit_ref_value = _clean(package_ref.semantic_head_commit_id)
    package_commit_ref_id = _required_uuid(
        package_commit_ref_value,
        label=package_commit_ref_label,
    )
    skill_package_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="SkillPackage",
    )
    store = FSCommitStore(root_dir=root) if root is not None else FSCommitStore()
    branch_id = _optional_uuid(package_ref.semantic_branch_id)
    if branch_id is None:
        if _clean(package_ref.semantic_object_instance_graph_commit_id) is None:
            raise RuntimeError(
                "Branchless Skill runtime package refs require "
                "semantic_object_instance_graph_commit_id; legacy "
                "semantic_head_commit_id refs must also provide semantic_branch_id."
            )
        package_commit_refs = (
            await store.domain_commit_refs_for_object_instance_graph_commit_id(
                projection_hash=skill_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if not package_commit_refs:
            raise RuntimeError(
                "Skill runtime package ref semantic_object_instance_graph_commit_id "
                "did not resolve to any indexed SkillPackage branch: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={skill_package_projection_hash}"
            )
        if len(package_commit_refs) != 1:
            raise RuntimeError(
                "Skill runtime package ref semantic_object_instance_graph_commit_id "
                "resolved to multiple SkillPackage branches: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={skill_package_projection_hash} "
                f"branches={[str(ref.branch_id) for ref in package_commit_refs]!r}"
            )
        package_commit_ref = package_commit_refs[0]
        branch_id = package_commit_ref.branch_id
        package_domain_commit_id = package_commit_ref.domain_commit_id
    else:
        package_domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=skill_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if package_domain_commit_id is None:
            legacy_domain_commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=skill_package_projection_hash,
                commit_id=package_commit_ref_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    f"Skill runtime package ref {package_commit_ref_label} is neither "
                    "an indexed ObjectInstanceGraphCommit id nor a domain commit id: "
                    f"{package_commit_ref_label}={package_commit_ref_id} "
                    f"branch_id={branch_id} "
                    f"projection_hash={skill_package_projection_hash}"
                )
            package_domain_commit_id = package_commit_ref_id

    skill_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_skill_package_id(
        name=package_ref.package_name,
    )
    skill_package = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=skill_package_projection_hash,
        commit_id=package_domain_commit_id,
        root_id=skill_package_id,
        root_type=SkillPackage,
        hydrate_portal_targets=True,
        store=store,
    )
    if skill_package is None:
        raise RuntimeError(
            "Skill runtime package ref could not hydrate SkillPackage from "
            "semantic commit: "
            f"package_name={package_ref.package_name!r} "
            f"semantic_package_id={skill_package_id}"
        )

    _validate_skill_package_ref_pair(
        package_ref=package_ref,
        skill_package=skill_package,
    )
    preferred_skill_config_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="SkillConfig",
    )
    skill_config_commit_ref = await _skill_config_domain_commit_ref_from_package(
        index=index,
        store=store,
        skill_package=skill_package,
        branch_id=branch_id,
        preferred_projection_hash=preferred_skill_config_projection_hash,
    )
    if skill_config_commit_ref is None:
        raise RuntimeError(
            "Skill runtime package ref resolved SkillPackage without a hydrated "
            "skill_config_object_instance_graph_commit.commit_id: "
            f"skill_package={skill_package.id}"
        )
    skill_config_projection_hash, skill_config_domain_commit_id = (
        skill_config_commit_ref
    )
    skill_config = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=skill_config_projection_hash,
        commit_id=skill_config_domain_commit_id,
        root_id=skill_package.skill_config_id,
        root_type=SkillConfig,
        hydrate_portal_targets=True,
        store=store,
    )
    if skill_config is None:
        raise RuntimeError(
            "Skill runtime package ref could not hydrate pinned SkillConfig "
            f"root: skill_config_id={skill_package.skill_config_id} "
            f"commit_id={skill_config_domain_commit_id}"
        )
    _validate_skill_config_ref_pair(
        package_ref=package_ref,
        skill_package=skill_package,
        skill_config=skill_config,
    )

    manifest_path = _resolve_optional_manifest_path(
        package_ref=package_ref,
        materialized_workspace_root=root,
    )
    root_commit_id = skill_package.skill_config_object_instance_graph_commit_id
    if root_commit_id is None:
        raise RuntimeError(
            "Committed SkillPackage runtime ref requires "
            "skill_config_object_instance_graph_commit_id."
        )
    skill_package_api_packages = tuple(skill_package.api_packages)
    api_package_ids = tuple(edge.api_package_id for edge in skill_package_api_packages)
    return ResolvedSkillRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=manifest_path,
        manifest_relative_path=(
            _relative_to_root(path=manifest_path, root=root, label="manifest_path")
            if manifest_path is not None and root is not None
            else None
        ),
        package_name=skill_package.name,
        skill_package_id=skill_package.id,
        skill_config_id=skill_config.id,
        skill_config_object_instance_graph_commit_id=root_commit_id,
        skill_package=skill_package,
        skill_config=skill_config,
        skill_package_api_packages=skill_package_api_packages,
        api_package_ids=api_package_ids,
        skill_config_projection_hash=skill_config_projection_hash,
        skill_config_domain_commit_id=skill_config_domain_commit_id,
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=str(skill_package.id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_branch_id=str(branch_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=str(root_commit_id),
        source_code_package_id=(
            str(skill_package.source_code_package_id)
            if skill_package.source_code_package_id is not None
            else _clean(package_ref.source_code_package_id)
        ),
    )


async def resolve_committed_skill_runtime_package_refs(
    *,
    index: MetaGraphRuntimeIndex,
    package_refs: Sequence[SkillRuntimePackageRef],
    materialized_workspace_root: str | Path | None = None,
) -> tuple[ResolvedSkillRuntimePackageRef, ...]:
    resolved = tuple(
        [
            await resolve_committed_skill_runtime_package_ref(
                index=index,
                package_ref=package_ref,
                materialized_workspace_root=materialized_workspace_root,
            )
            for package_ref in package_refs
        ]
    )
    _reject_duplicate_resolved_refs(resolved)
    return resolved


def _validate_skill_ref(package_ref: SkillRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) != "skill":
        raise RuntimeError(
            "Skill runtime package ref requires family_key='skill': "
            f"{package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) != "skill":
        raise RuntimeError(
            "Skill runtime package ref requires package_kind='skill': "
            f"{package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("Skill runtime package ref requires a package_name.")
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "skill_config",
        "skill_package",
    }:
        raise RuntimeError(
            "Skill runtime package ref semantic_root_kind must be "
            "'skill_config' or 'skill_package' when provided: "
            f"{semantic_root_kind!r}"
        )


def _resolve_optional_manifest_path(
    *,
    package_ref: SkillRuntimePackageRef,
    materialized_workspace_root: Path | None,
) -> Path | None:
    raw_manifest_path = package_ref.manifest_path
    if raw_manifest_path is None or not str(raw_manifest_path).strip():
        return None
    manifest_path = Path(raw_manifest_path).expanduser()
    if not manifest_path.is_absolute():
        if materialized_workspace_root is None:
            raise RuntimeError(
                "Skill runtime package ref relative manifest_path requires "
                "materialized_workspace_root."
            )
        manifest_path = materialized_workspace_root / manifest_path
    resolved_manifest_path = manifest_path.resolve()
    if materialized_workspace_root is not None:
        _relative_to_root(
            path=resolved_manifest_path,
            root=materialized_workspace_root,
            label="manifest_path",
        )
    if not resolved_manifest_path.is_file():
        raise FileNotFoundError(
            "Skill runtime package ref manifest_path does not exist"
            + (
                " inside the materialized workspace root"
                if materialized_workspace_root is not None
                else ""
            )
            + f": {resolved_manifest_path}"
        )
    return resolved_manifest_path


def _reject_duplicate_resolved_refs(
    refs: tuple[ResolvedSkillRuntimePackageRef, ...],
) -> None:
    seen: dict[str, ResolvedSkillRuntimePackageRef] = {}
    for ref in refs:
        key = _resolved_ref_key(ref)
        existing = seen.get(key)
        if existing is not None and existing.skill_package_id != ref.skill_package_id:
            raise RuntimeError(
                "Conflicting skill runtime package refs resolve to the same "
                f"semantic package identity: {key!r}"
            )
        seen[key] = ref


def _resolved_ref_key(ref: ResolvedSkillRuntimePackageRef) -> str:
    if ref.semantic_package_id is not None:
        return f"semantic_package_id:{ref.semantic_package_id}"
    if ref.semantic_root_id is not None:
        return f"semantic_root_id:{ref.semantic_root_id}"
    if ref.manifest_path is not None:
        return f"manifest_path:{ref.manifest_path.as_posix()}"
    return f"skill_package_id:{ref.skill_package_id}"


def _validate_skill_package_ref_pair(
    *,
    package_ref: SkillRuntimePackageRef,
    skill_package: SkillPackage,
) -> None:
    if skill_package.name != package_ref.package_name:
        raise RuntimeError(
            "Skill runtime package ref package_name does not match "
            f"SkillPackage: ref={package_ref.package_name!r} "
            f"skill_package={skill_package.name!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if semantic_package_id is not None and semantic_package_id != skill_package.id:
        raise RuntimeError(
            "Skill runtime package ref semantic_package_id does not match "
            f"SkillPackage: ref={semantic_package_id} skill_package={skill_package.id}"
        )
    pinned_commit_id = _optional_uuid(
        package_ref.semantic_root_object_instance_graph_commit_id
    )
    if (
        pinned_commit_id is not None
        and pinned_commit_id
        != skill_package.skill_config_object_instance_graph_commit_id
    ):
        raise RuntimeError(
            "Skill runtime package ref semantic_root_object_instance_graph_commit_id "
            "does not match SkillPackage pin: "
            f"ref={pinned_commit_id} "
            f"skill_package={skill_package.skill_config_object_instance_graph_commit_id}"
        )


def _validate_skill_config_ref_pair(
    *,
    package_ref: SkillRuntimePackageRef,
    skill_package: SkillPackage,
    skill_config: SkillConfig,
) -> None:
    if skill_config.id != skill_package.skill_config_id:
        raise RuntimeError(
            "SkillPackage points at a different SkillConfig than the hydrated "
            f"skill root: package={skill_package.skill_config_id} "
            f"skill_config={skill_config.id}"
        )
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is None:
        return
    expected_root_id = (
        skill_config.id if semantic_root_kind == "skill_config" else skill_package.id
    )
    if semantic_root_id != expected_root_id:
        raise RuntimeError(
            "Skill runtime package ref semantic_root_id does not match "
            f"{semantic_root_kind or 'skill_package'} root: "
            f"ref={semantic_root_id} expected={expected_root_id}"
        )


async def _skill_config_domain_commit_ref_from_package(
    *,
    index: MetaGraphRuntimeIndex,
    store: FSCommitStore,
    skill_package: SkillPackage,
    branch_id: UUID,
    preferred_projection_hash: str,
) -> tuple[str, UUID] | None:
    pinned_commit_id = skill_package.skill_config_object_instance_graph_commit_id
    if pinned_commit_id is not None:
        matches: list[tuple[str, UUID]] = []
        for projection_hash in _candidate_projection_hashes_by_name(
            index=index,
            projection_name="SkillConfig",
            preferred_projection_hash=preferred_projection_hash,
        ):
            domain_commit_id = (
                await store.domain_commit_id_for_object_instance_graph_commit_id(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    object_instance_graph_commit_id=pinned_commit_id,
                )
            )
            if domain_commit_id is not None:
                matches.append((projection_hash, domain_commit_id))
        if len(matches) > 1:
            raise RuntimeError(
                "Skill runtime package ref skill_config_object_instance_graph_commit_id "
                "resolved to multiple SkillConfig projections: "
                f"skill_package={skill_package.id} "
                f"skill_config_object_instance_graph_commit_id={pinned_commit_id} "
                f"matches={matches!r}"
            )
        if matches:
            return matches[0]

    skill_config_commit = skill_package.skill_config_object_instance_graph_commit
    if skill_config_commit is not None and skill_config_commit.commit_id is not None:
        return preferred_projection_hash, skill_config_commit.commit_id
    return None


def _candidate_projection_hashes_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
    preferred_projection_hash: str,
) -> tuple[str, ...]:
    projection_token = projection_name.strip()
    candidates: list[str] = [preferred_projection_hash]
    candidates.extend(
        projection_hash
        for projection_hash, opg in sorted(
            index.opg_by_hash.items(),
            key=lambda item: item[0],
        )
        if (opg.name or "").strip() == projection_token
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        deduped.append(candidate)
        seen.add(candidate)
    return tuple(deduped)


async def _hydrate_root_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    root_id: UUID,
    root_type: type[_TRoot],
    hydrate_portal_targets: bool,
    store: FSCommitStore,
) -> _TRoot | None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Skill runtime package ref missing projection hash: {projection_hash}"
        )
    oig, _ = await CachedLaneMaterializer(commits=store).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_root_model(
        index=index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=branch_id,
    )


def _find_projection_hash_by_name(
    *,
    index: MetaGraphRuntimeIndex,
    projection_name: str,
) -> str:
    target = (projection_name or "").strip()
    for opg in index.ocg.object_projection_graphs:
        name = (opg.name or "").strip()
        if name == target:
            return opg.projection_hash
    raise ValueError(
        f"Projection {projection_name!r} was not found in Skill runtime OCG"
    )


def _relative_to_root(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Skill runtime package ref path resolved outside materialized "
            f"workspace root: label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


def _required_uuid(value: str | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Skill runtime package ref requires {label}.")
    return parsed


def _optional_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    stripped = value.strip()
    if not stripped:
        return None
    return UUID(stripped)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "ResolvedSkillRuntimePackageRef",
    "SkillRuntimePackageRef",
    "resolve_committed_skill_runtime_package_ref",
    "resolve_committed_skill_runtime_package_refs",
]
