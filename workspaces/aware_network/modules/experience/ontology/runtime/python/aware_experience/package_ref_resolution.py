from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar
from uuid import UUID

from aware_experience.stable_ids import stable_experience_package_id
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.experience_package import ExperiencePackage
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import (
    reify_oig_root_model,
    reify_oig_session,
)
from aware_orm.models.orm_model import ORMModel


_REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH = Path(
    ".aware/workspace/revision-filesystem.manifest.json"
)
_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class ExperienceRuntimePackageRef:
    """Runtime ref for a Workspace-selected ExperiencePackage semantic package."""

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


@dataclass(frozen=True, slots=True)
class ResolvedExperienceRuntimePackageRef:
    """Resolved ExperiencePackage coordinates inside a WorkspaceRevision filesystem."""

    package_ref: ExperienceRuntimePackageRef
    materialized_workspace_root: Path
    manifest_path: Path | None
    manifest_relative_path: str | None
    package_name: str
    experience_name: str
    experience_package_id: UUID
    environment_experience_id: UUID
    source_code_package_id: UUID | None
    semantic_branch_id: str
    semantic_package_id: str
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    projection_experience_head_commit_id: UUID | None = None
    projection_experience_names: tuple[str, ...] = ()
    projection_experience_graph_head_commit_id: UUID | None = None
    projection_experience_section_graph_binding_head_commit_id: UUID | None = None


async def resolve_committed_experience_runtime_package_ref(
    *,
    index: MetaGraphRuntimeIndex,
    package_ref: ExperienceRuntimePackageRef,
    materialized_workspace_root: str | Path,
) -> ResolvedExperienceRuntimePackageRef:
    """Resolve a committed ExperiencePackage ref without rebuilding source."""

    _validate_experience_ref(package_ref)
    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
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
    experience_package_projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="ExperiencePackage",
    )
    store = FSCommitStore(root_dir=root)
    branch_id = _optional_uuid(package_ref.semantic_branch_id)
    if branch_id is None:
        if _clean(package_ref.semantic_object_instance_graph_commit_id) is None:
            raise RuntimeError(
                "Branchless Experience runtime package refs require "
                "semantic_object_instance_graph_commit_id; legacy "
                "semantic_head_commit_id refs must also provide semantic_branch_id."
            )
        package_commit_refs = (
            await store.domain_commit_refs_for_object_instance_graph_commit_id(
                projection_hash=experience_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if not package_commit_refs:
            raise RuntimeError(
                "Experience runtime package ref semantic_object_instance_graph_commit_id "
                "did not resolve to any indexed ExperiencePackage branch: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={experience_package_projection_hash}"
            )
        if len(package_commit_refs) != 1:
            raise RuntimeError(
                "Experience runtime package ref semantic_object_instance_graph_commit_id "
                "resolved to multiple ExperiencePackage branches: "
                f"semantic_object_instance_graph_commit_id={package_commit_ref_id} "
                f"projection_hash={experience_package_projection_hash} "
                f"branches={[str(ref.branch_id) for ref in package_commit_refs]!r}"
            )
        package_commit_ref = package_commit_refs[0]
        branch_id = package_commit_ref.branch_id
        package_domain_commit_id = package_commit_ref.domain_commit_id
    else:
        package_domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=experience_package_projection_hash,
                object_instance_graph_commit_id=package_commit_ref_id,
            )
        )
        if package_domain_commit_id is None:
            legacy_domain_commit = await store.get_commit(
                branch_id=branch_id,
                projection_hash=experience_package_projection_hash,
                commit_id=package_commit_ref_id,
            )
            if legacy_domain_commit is None:
                raise RuntimeError(
                    f"Experience runtime package ref {package_commit_ref_label} is neither "
                    "an indexed ObjectInstanceGraphCommit id nor a domain commit id: "
                    f"{package_commit_ref_label}={package_commit_ref_id} "
                    f"branch_id={branch_id} "
                    f"projection_hash={experience_package_projection_hash}"
                )
            package_domain_commit_id = package_commit_ref_id

    experience_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_experience_package_id(name=package_ref.package_name)
    experience_package = await _hydrate_root_from_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=experience_package_projection_hash,
        commit_id=package_domain_commit_id,
        root_id=experience_package_id,
        root_type=ExperiencePackage,
        hydrate_portal_targets=True,
        store=store,
    )
    if experience_package is None:
        raise RuntimeError(
            "Experience runtime package ref could not hydrate ExperiencePackage "
            "from semantic commit: "
            f"package_name={package_ref.package_name!r} "
            f"semantic_package_id={experience_package_id}"
        )
    if experience_package.id is None:
        raise RuntimeError(
            "Experience runtime package ref hydrated ExperiencePackage without id: "
            f"package_name={package_ref.package_name!r}"
        )
    _validate_experience_package_ref_pair(
        package_ref=package_ref,
        experience_package=experience_package,
    )
    environment_experience = experience_package.environment_experience
    experience_name = _experience_name_from_package(
        package_ref=package_ref,
        experience_package=experience_package,
        environment_experience=environment_experience,
    )
    manifest_relative_path = _manifest_relative_path_from_ref(package_ref=package_ref)
    projection_experience_head_commit_id = await _head_commit_id_by_projection_name(
        store=store,
        index=index,
        branch_id=branch_id,
        projection_name="ProjectionExperience",
    )

    return ResolvedExperienceRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=None,
        manifest_relative_path=manifest_relative_path,
        package_name=experience_package.name,
        experience_name=experience_name,
        experience_package_id=experience_package.id,
        environment_experience_id=experience_package.environment_experience_id,
        source_code_package_id=experience_package.source_code_package_id,
        semantic_branch_id=str(branch_id),
        semantic_package_id=str(experience_package.id),
        semantic_object_instance_graph_commit_id=_clean(
            package_ref.semantic_object_instance_graph_commit_id
        ),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=_clean(
            package_ref.semantic_root_object_instance_graph_commit_id
        ),
        projection_experience_head_commit_id=projection_experience_head_commit_id,
        projection_experience_names=await _projection_experience_names_from_head(
            store=store,
            index=index,
            branch_id=branch_id,
            head_commit_id=projection_experience_head_commit_id,
        ),
        projection_experience_graph_head_commit_id=await _head_commit_id_by_projection_name(
            store=store,
            index=index,
            branch_id=branch_id,
            projection_name="ProjectionExperienceGraph",
        ),
        projection_experience_section_graph_binding_head_commit_id=await _head_commit_id_by_projection_name(
            store=store,
            index=index,
            branch_id=branch_id,
            projection_name="ProjectionExperienceSectionGraphBinding",
        ),
    )


async def resolve_committed_experience_runtime_package_refs(
    *,
    index: MetaGraphRuntimeIndex,
    package_refs: tuple[ExperienceRuntimePackageRef, ...],
    materialized_workspace_root: str | Path,
) -> tuple[ResolvedExperienceRuntimePackageRef, ...]:
    resolved = tuple(
        [
            await resolve_committed_experience_runtime_package_ref(
                index=index,
                package_ref=package_ref,
                materialized_workspace_root=materialized_workspace_root,
            )
            for package_ref in package_refs
        ]
    )
    return resolved


def _validate_experience_ref(package_ref: ExperienceRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) != "experience":
        raise RuntimeError(
            "Experience runtime package ref requires family_key='experience': "
            f"{package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) not in {"experience", "experience_package"}:
        raise RuntimeError(
            "Experience runtime package ref requires package_kind='experience' "
            f"or 'experience_package': {package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("Experience runtime package ref requires a package_name.")
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "environment_experience",
        "experience_package",
    }:
        raise RuntimeError(
            "Experience runtime package ref semantic_root_kind must be "
            "'environment_experience' or 'experience_package' when provided: "
            f"{semantic_root_kind!r}"
        )


def _validate_revision_filesystem_root(root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(
            "Experience runtime package ref requires an existing materialized "
            f"workspace root: {root}"
        )
    manifest_path = (root / _REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Experience runtime package ref requires a WorkspaceRevision filesystem "
            f"manifest at {manifest_path}"
        )


def _manifest_relative_path_from_ref(
    *,
    package_ref: ExperienceRuntimePackageRef,
) -> str | None:
    raw_manifest_path = package_ref.manifest_path
    if raw_manifest_path is None or not str(raw_manifest_path).strip():
        return None
    manifest_path = Path(raw_manifest_path).expanduser()
    return manifest_path.as_posix()


def _validate_experience_package_ref_pair(
    *,
    package_ref: ExperienceRuntimePackageRef,
    experience_package: ExperiencePackage,
) -> None:
    if experience_package.name != package_ref.package_name:
        raise RuntimeError(
            "Experience runtime package ref package_name does not match "
            f"ExperiencePackage: ref={package_ref.package_name!r} "
            f"experience_package={experience_package.name!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if semantic_package_id is not None and semantic_package_id != experience_package.id:
        raise RuntimeError(
            "Experience runtime package ref semantic_package_id does not match "
            "ExperiencePackage: "
            f"ref={semantic_package_id} experience_package={experience_package.id}"
        )
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is not None:
        semantic_root_kind = _clean(package_ref.semantic_root_kind)
        expected_root_id = (
            experience_package.environment_experience_id
            if semantic_root_kind == "environment_experience"
            else experience_package.id
        )
        if semantic_root_id != expected_root_id:
            raise RuntimeError(
                "Experience runtime package ref semantic_root_id does not match "
                f"{semantic_root_kind or 'experience_package'} root: "
                f"ref={semantic_root_id} expected={expected_root_id}"
            )


def _experience_name_from_package(
    *,
    package_ref: ExperienceRuntimePackageRef,
    experience_package: ExperiencePackage,
    environment_experience: EnvironmentExperience | None,
) -> str:
    if environment_experience is not None:
        fqn_prefix = (environment_experience.fqn_prefix or "").strip()
        if fqn_prefix:
            return fqn_prefix
    package_name = (experience_package.name or package_ref.package_name).strip()
    return package_name.replace("-", "_")


async def _head_commit_id_by_projection_name(
    *,
    store: FSCommitStore,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_name: str,
) -> UUID | None:
    projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name=projection_name,
    )
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    if head is None or not head.get("commit_id"):
        return None
    return UUID(str(head["commit_id"]))


async def _projection_experience_names_from_head(
    *,
    store: FSCommitStore,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    head_commit_id: UUID | None,
) -> tuple[str, ...]:
    if head_commit_id is None:
        return ()
    projection_hash = _find_projection_hash_by_name(
        index=index,
        projection_name="ProjectionExperience",
    )
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Experience runtime package ref missing projection hash: {projection_hash}"
        )
    oig, _ = await CachedLaneMaterializer(commits=store).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=head_commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    session = reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )
    names = {
        name
        for obj in session.imap_all_objects()
        if isinstance(obj, ProjectionExperience)
        for name in ((obj.name or "").strip(),)
        if name
    }
    return tuple(sorted(names, key=lambda value: value.casefold()))


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
            f"Experience runtime package ref missing projection hash: {projection_hash}"
        )
    oig, _ = await CachedLaneMaterializer(commits=store).get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=commit_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    _ = hydrate_portal_targets
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
        if (opg.name or "").strip() == target:
            return opg.projection_hash
    raise ValueError(
        f"Projection {projection_name!r} was not found in hosted environment OCG"
    )


def _relative_to_root(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Experience runtime package ref path resolved outside materialized "
            f"workspace root: label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


def _required_uuid(value: str | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Experience runtime package ref requires {label}.")
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
    "ExperienceRuntimePackageRef",
    "ResolvedExperienceRuntimePackageRef",
    "resolve_committed_experience_runtime_package_ref",
    "resolve_committed_experience_runtime_package_refs",
]
