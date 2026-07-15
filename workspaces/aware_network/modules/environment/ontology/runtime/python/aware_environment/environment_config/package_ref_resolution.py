from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import json
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
from aware_environment.materialization.projection_catalog import (
    require_environment_meta_projection_catalog,
)
from aware_environment_ontology.environment.environment_config import EnvironmentConfig
from aware_environment_ontology.environment.environment_config_ontology_config import (
    EnvironmentConfigOntologyConfig,
)
from aware_environment_ontology.environment.environment_config_package import (
    EnvironmentConfigPackage,
)
from aware_environment_ontology.environment.environment_config_package_ontology_package import (
    EnvironmentConfigPackageOntologyPackage,
)
from aware_environment_ontology.stable_ids import stable_environment_config_package_id
from aware_ontology_ontology.stable_ids import (
    stable_ontology_config_id,
    stable_ontology_package_id,
)

_REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH = Path(
    ".aware/workspace/revision-filesystem.manifest.json"
)
_OCG_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY = "ocg_language_materialization"
_COMMITTED_PROJECTION_DTO_ARTIFACT_ROLES = (
    "dependency_import_resolution",
    "package_bootstrap",
)
_TRoot = TypeVar("_TRoot", bound=ORMModel)


@dataclass(frozen=True, slots=True)
class EnvironmentRuntimePackageRef:
    """Workspace-selected EnvironmentConfigPackage pointer."""

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
class ResolvedEnvironmentOntologyConfigRef:
    """EnvironmentConfig pointer to one OntologyConfig commit."""

    membership: EnvironmentConfigOntologyConfig
    name: str
    fqn_prefix: str
    ontology_config_id: UUID
    ontology_config_object_instance_graph_commit_id: UUID


@dataclass(frozen=True, slots=True)
class ResolvedEnvironmentOntologyPackageRef:
    """EnvironmentConfigPackage pointer to one OntologyPackage commit."""

    membership: EnvironmentConfigPackageOntologyPackage
    name: str
    fqn_prefix: str
    ontology_package_id: UUID
    ontology_package_object_instance_graph_commit_id: UUID


@dataclass(frozen=True, slots=True)
class ResolvedEnvironmentOntologyPointerRef:
    """Matched EnvironmentConfig/OntologyConfig and package/OntologyPackage pins."""

    name: str
    fqn_prefix: str
    ontology_config_ref: ResolvedEnvironmentOntologyConfigRef
    ontology_package_ref: ResolvedEnvironmentOntologyPackageRef


@dataclass(frozen=True, slots=True)
class ResolvedEnvironmentRuntimePackageRef:
    """Resolved EnvironmentConfigPackage plus ontology-owned runtime pointers."""

    package_ref: EnvironmentRuntimePackageRef
    materialized_workspace_root: Path
    manifest_path: Path | None
    manifest_relative_path: str | None
    environment_handle: str
    environment_package_id: UUID
    environment_config_id: UUID
    environment_config_object_instance_graph_commit_id: UUID
    environment_package: EnvironmentConfigPackage
    environment_config: EnvironmentConfig
    ontology_pointers: tuple[ResolvedEnvironmentOntologyPointerRef, ...]
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
class EnvironmentRuntimeArtifactRef:
    """Generic WorkspaceRevision artifact ref normalized for Environment helpers."""

    artifact_family: str
    artifact_key: str
    artifact_role: str
    required_for: tuple[str, ...] = ()
    status: str = "available"
    package_name: str | None = None
    revision_code_package_id: UUID | None = None
    semantic_package_commit_id: UUID | None = None
    source_code_package_id: UUID | None = None
    source_object_instance_graph_commit_id: UUID | None = None
    input_object_instance_graph_commit_id: UUID | None = None
    workspace_relative_path: str | None = None
    digest: str | None = None
    digest_algorithm: str | None = None
    media_type: str | None = None
    runtime_contract_version: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedEnvironmentRuntimeArtifact:
    """Validated file artifact available from a materialized WorkspaceRevision."""

    artifact_ref: EnvironmentRuntimeArtifactRef
    path: Path
    workspace_relative_path: str
    sha256: str | None
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ResolvedCommittedProjectionDtoArtifactBundle:
    """Revision-backed DTO package artifacts available to Environment."""

    package_name: str | None
    import_root: str | None
    artifacts: tuple[ResolvedEnvironmentRuntimeArtifact, ...]
    missing_requirements: tuple[str, ...] = ()

    @property
    def deployment_ready(self) -> bool:
        return not self.missing_requirements

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def dto_artifact_digest(self) -> str | None:
        for artifact in sorted(
            self.artifacts,
            key=lambda item: (
                item.artifact_ref.artifact_role != "package_bootstrap",
                item.artifact_ref.artifact_role,
                item.workspace_relative_path,
            ),
        ):
            if artifact.sha256:
                return f"sha256:{artifact.sha256}"
            digest = _clean(artifact.artifact_ref.digest)
            if digest is not None:
                return digest
        return None


@dataclass(frozen=True, slots=True)
class _DomainCommitRef:
    branch_id: UUID
    projection_hash: str
    domain_commit_id: UUID


async def resolve_committed_environment_runtime_package_ref(
    *,
    index: MetaGraphRuntimeIndex,
    package_ref: EnvironmentRuntimePackageRef,
    materialized_workspace_root: str | Path,
    meta_projection_catalog: object | None = None,
) -> ResolvedEnvironmentRuntimePackageRef:
    """Resolve EnvironmentConfigPackage truth without composing runtime artifacts."""

    _validate_environment_ref(package_ref)
    projection_catalog = require_environment_meta_projection_catalog(
        meta_projection_catalog or index,
        required_projection_names=(
            "EnvironmentConfigPackage",
            "EnvironmentConfig",
        ),
        source="resolve_committed_environment_runtime_package_ref",
    )
    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
    package_oig_commit_id = _required_semantic_package_oig_commit_id(package_ref)
    legacy_branch_id = _optional_uuid(package_ref.semantic_branch_id)
    environment_package_projection_hash = projection_catalog.projection_hash_for_name(
        "EnvironmentConfigPackage"
    )
    store = FSCommitStore()
    package_commit_ref = await _resolve_environment_package_commit_ref(
        store=store,
        projection_hash=environment_package_projection_hash,
        object_instance_graph_commit_id=package_oig_commit_id,
        legacy_branch_id=legacy_branch_id,
    )
    if package_commit_ref is None:
        raise RuntimeError(
            "Environment package ref could not resolve "
            "EnvironmentConfigPackage ObjectInstanceGraphCommit: "
            f"semantic_object_instance_graph_commit_id={package_oig_commit_id} "
            f"projection_hash={environment_package_projection_hash}"
        )

    environment_package_id = _optional_uuid(
        package_ref.semantic_package_id
    ) or stable_environment_config_package_id(handle=package_ref.package_name)
    environment_package = await _hydrate_root_from_commit(
        index=index,
        branch_id=package_commit_ref.branch_id,
        projection_hash=package_commit_ref.projection_hash,
        commit_id=package_commit_ref.domain_commit_id,
        root_id=environment_package_id,
        root_type=EnvironmentConfigPackage,
    )
    if environment_package is None:
        raise RuntimeError(
            "Environment package ref could not hydrate EnvironmentConfigPackage "
            "from semantic commit: "
            f"package_name={package_ref.package_name!r} "
            f"semantic_package_id={environment_package_id}"
        )

    _validate_environment_package_ref_pair(
        package_ref=package_ref,
        environment_package=environment_package,
    )
    environment_config_oig_commit_id = (
        environment_package.environment_config_object_instance_graph_commit_id
    )
    if environment_config_oig_commit_id is None:
        raise RuntimeError(
            "Environment package ref resolved EnvironmentConfigPackage without "
            "environment_config_object_instance_graph_commit_id: "
            f"environment_package={environment_package.id}"
        )
    environment_config_projection_hash = projection_catalog.projection_hash_for_name(
        "EnvironmentConfig"
    )
    environment_config_commit_ref = await _find_domain_commit_ref_for_oig_commit_id(
        store=store,
        projection_hash=environment_config_projection_hash,
        object_instance_graph_commit_id=environment_config_oig_commit_id,
    )
    if environment_config_commit_ref is None:
        raise RuntimeError(
            "Environment package ref could not resolve pinned EnvironmentConfig "
            "ObjectInstanceGraphCommit: "
            f"object_instance_graph_commit_id={environment_config_oig_commit_id}"
        )
    environment_config = await _hydrate_root_from_commit(
        index=index,
        branch_id=environment_config_commit_ref.branch_id,
        projection_hash=environment_config_commit_ref.projection_hash,
        commit_id=environment_config_commit_ref.domain_commit_id,
        root_id=environment_package.environment_config_id,
        root_type=EnvironmentConfig,
    )
    if environment_config is None:
        raise RuntimeError(
            "Environment package ref could not hydrate pinned EnvironmentConfig "
            f"root: environment_config_id={environment_package.environment_config_id} "
            f"commit_id={environment_config_commit_ref.domain_commit_id}"
        )
    _validate_environment_config_ref_pair(
        package_ref=package_ref,
        environment_package=environment_package,
        environment_config=environment_config,
    )

    ontology_pointers = _resolve_environment_ontology_pointers(
        environment_package=environment_package,
        environment_config=environment_config,
    )
    manifest_path = _resolve_manifest_path(
        package_ref=package_ref,
        materialized_workspace_root=root,
    )
    return ResolvedEnvironmentRuntimePackageRef(
        package_ref=package_ref,
        materialized_workspace_root=root,
        manifest_path=manifest_path,
        manifest_relative_path=(
            _relative_to_root(
                path=manifest_path,
                root=root,
                label="manifest_path",
            )
            if manifest_path is not None
            else None
        ),
        environment_handle=environment_package.handle,
        environment_package_id=environment_package.id,
        environment_config_id=environment_config.id,
        environment_config_object_instance_graph_commit_id=(
            environment_config_oig_commit_id
        ),
        environment_package=environment_package,
        environment_config=environment_config,
        ontology_pointers=ontology_pointers,
        workspace_package_id=_clean(package_ref.workspace_package_id),
        semantic_package_id=str(environment_package.id),
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_head_commit_id=_clean(package_ref.semantic_head_commit_id),
        semantic_branch_id=_clean(package_ref.semantic_branch_id),
        semantic_root_kind=_clean(package_ref.semantic_root_kind),
        semantic_root_id=_clean(package_ref.semantic_root_id),
        semantic_root_object_instance_graph_commit_id=str(
            environment_config_oig_commit_id
        ),
        source_code_package_id=_clean(package_ref.source_code_package_id),
    )


async def resolve_committed_environment_runtime_package_refs(
    *,
    index: MetaGraphRuntimeIndex,
    package_refs: Sequence[EnvironmentRuntimePackageRef],
    materialized_workspace_root: str | Path,
    meta_projection_catalog: object | None = None,
) -> tuple[ResolvedEnvironmentRuntimePackageRef, ...]:
    resolved = tuple(
        [
            await resolve_committed_environment_runtime_package_ref(
                index=index,
                package_ref=package_ref,
                materialized_workspace_root=materialized_workspace_root,
                meta_projection_catalog=meta_projection_catalog,
            )
            for package_ref in package_refs
        ]
    )
    _reject_duplicate_resolved_refs(resolved)
    return resolved


def resolve_committed_projection_dto_artifact_bundle(
    *,
    artifact_refs: Sequence[object],
    materialized_workspace_root: str | Path,
    dto_package_name: str | None = None,
    dto_import_root: str | None = None,
    dto_class_ref: str | None = None,
    class_config_id: UUID | str | None = None,
) -> ResolvedCommittedProjectionDtoArtifactBundle:
    """Resolve DTO package artifacts only from WorkspaceRevision artifact refs."""

    root = Path(materialized_workspace_root).expanduser().resolve()
    _validate_revision_filesystem_root(root)
    _ = class_config_id
    package_name = _clean(dto_package_name)
    import_root = _clean(dto_import_root) or _dto_import_root_from_class_ref(
        dto_class_ref
    )
    normalized_artifact_refs = tuple(
        _environment_runtime_artifact_ref_from_ref(artifact_ref)
        for artifact_ref in artifact_refs
    )
    matched_refs = tuple(
        sorted(
            (
                artifact_ref
                for artifact_ref in normalized_artifact_refs
                if _artifact_ref_satisfies_committed_projection_dto_requirement(
                    artifact_ref=artifact_ref,
                    dto_package_name=package_name,
                    dto_import_root=import_root,
                )
            ),
            key=lambda item: (
                item.artifact_role,
                item.package_name or "",
                item.workspace_relative_path or "",
                item.artifact_key,
            ),
        )
    )
    resolved_artifacts = tuple(
        _resolve_environment_runtime_artifact(
            artifact_ref=artifact_ref,
            materialized_workspace_root=root,
        )
        for artifact_ref in matched_refs
    )
    covered_roles = {
        artifact.artifact_ref.artifact_role for artifact in resolved_artifacts
    }
    missing = tuple(
        role
        for role in _COMMITTED_PROJECTION_DTO_ARTIFACT_ROLES
        if role not in covered_roles
    )
    if package_name is None and import_root is None:
        missing = ("dto_package_name_or_import_root", *missing)
    return ResolvedCommittedProjectionDtoArtifactBundle(
        package_name=package_name,
        import_root=import_root,
        artifacts=resolved_artifacts,
        missing_requirements=missing,
    )


async def _resolve_environment_package_commit_ref(
    *,
    store: FSCommitStore,
    projection_hash: str,
    object_instance_graph_commit_id: UUID,
    legacy_branch_id: UUID | None,
) -> _DomainCommitRef | None:
    if legacy_branch_id is None:
        return await _find_domain_commit_ref_for_oig_commit_id(
            store=store,
            projection_hash=projection_hash,
            object_instance_graph_commit_id=object_instance_graph_commit_id,
        )
    domain_commit_id = await store.domain_commit_id_for_object_instance_graph_commit_id(
        branch_id=legacy_branch_id,
        projection_hash=projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    if domain_commit_id is not None:
        return _DomainCommitRef(
            branch_id=legacy_branch_id,
            projection_hash=projection_hash,
            domain_commit_id=domain_commit_id,
        )
    legacy_domain_commit = await store.get_commit(
        branch_id=legacy_branch_id,
        projection_hash=projection_hash,
        commit_id=object_instance_graph_commit_id,
    )
    if legacy_domain_commit is None:
        return None
    return _DomainCommitRef(
        branch_id=legacy_branch_id,
        projection_hash=projection_hash,
        domain_commit_id=object_instance_graph_commit_id,
    )


def _resolve_environment_ontology_pointers(
    *,
    environment_package: EnvironmentConfigPackage,
    environment_config: EnvironmentConfig,
) -> tuple[ResolvedEnvironmentOntologyPointerRef, ...]:
    config_memberships = {
        _ontology_membership_key(membership): membership
        for membership in environment_config.ontology_configs
    }
    package_memberships = {
        _ontology_membership_key(membership): membership
        for membership in environment_package.ontology_packages
    }
    if not config_memberships:
        raise RuntimeError(
            "EnvironmentConfig has no ontology_config memberships; Environment "
            "environment resolution can only return OntologyConfig pointers."
        )
    if set(config_memberships) != set(package_memberships):
        missing_package = sorted(set(config_memberships) - set(package_memberships))
        missing_config = sorted(set(package_memberships) - set(config_memberships))
        raise RuntimeError(
            "EnvironmentConfig and EnvironmentConfigPackage ontology memberships "
            "do not match: "
            f"missing_package_memberships={missing_package} "
            f"missing_config_memberships={missing_config}"
        )
    pointers: list[ResolvedEnvironmentOntologyPointerRef] = []
    for key in sorted(config_memberships):
        config_membership = config_memberships[key]
        package_membership = package_memberships[key]
        config_ref = _ontology_config_ref_from_membership(config_membership)
        package_ref = _ontology_package_ref_from_membership(package_membership)
        pointers.append(
            ResolvedEnvironmentOntologyPointerRef(
                name=config_ref.name,
                fqn_prefix=config_ref.fqn_prefix,
                ontology_config_ref=config_ref,
                ontology_package_ref=package_ref,
            )
        )
    return tuple(pointers)


def _ontology_membership_key(
    membership: (
        EnvironmentConfigOntologyConfig | EnvironmentConfigPackageOntologyPackage
    ),
) -> tuple[str, str]:
    return (membership.name, membership.fqn_prefix)


def _ontology_config_ref_from_membership(
    membership: EnvironmentConfigOntologyConfig,
) -> ResolvedEnvironmentOntologyConfigRef:
    commit_id = membership.ontology_config_object_instance_graph_commit_id
    if commit_id is None:
        raise RuntimeError(
            "EnvironmentConfig ontology_config membership is missing "
            "ontology_config_object_instance_graph_commit_id: "
            f"membership_id={membership.id}"
        )
    return ResolvedEnvironmentOntologyConfigRef(
        membership=membership,
        name=membership.name,
        fqn_prefix=membership.fqn_prefix,
        ontology_config_id=membership.ontology_config_id
        or stable_ontology_config_id(
            name=membership.name,
            fqn_prefix=membership.fqn_prefix,
        ),
        ontology_config_object_instance_graph_commit_id=commit_id,
    )


def _ontology_package_ref_from_membership(
    membership: EnvironmentConfigPackageOntologyPackage,
) -> ResolvedEnvironmentOntologyPackageRef:
    commit_id = membership.ontology_package_object_instance_graph_commit_id
    if commit_id is None:
        raise RuntimeError(
            "EnvironmentConfigPackage ontology_package membership is missing "
            "ontology_package_object_instance_graph_commit_id: "
            f"membership_id={membership.id}"
        )
    return ResolvedEnvironmentOntologyPackageRef(
        membership=membership,
        name=membership.name,
        fqn_prefix=membership.fqn_prefix,
        ontology_package_id=membership.ontology_package_id
        or stable_ontology_package_id(
            name=membership.name,
            fqn_prefix=membership.fqn_prefix,
        ),
        ontology_package_object_instance_graph_commit_id=commit_id,
    )


def _resolve_environment_runtime_artifact(
    *,
    artifact_ref: EnvironmentRuntimeArtifactRef,
    materialized_workspace_root: Path,
) -> ResolvedEnvironmentRuntimeArtifact:
    workspace_relative_path = _clean(artifact_ref.workspace_relative_path)
    if workspace_relative_path is None:
        raise RuntimeError(
            "Environment artifact ref requires workspace_relative_path: "
            f"artifact_key={artifact_ref.artifact_key!r}"
        )
    rel_path = Path(workspace_relative_path)
    if rel_path.is_absolute():
        raise RuntimeError(
            "Environment artifact ref must use a workspace-relative path: "
            f"artifact_key={artifact_ref.artifact_key!r} "
            f"path={workspace_relative_path!r}"
        )
    path = (materialized_workspace_root / rel_path).resolve()
    normalized_relative_path = _relative_to_root(
        path=path,
        root=materialized_workspace_root,
        label="workspace_relative_path",
    )
    if not path.is_file():
        raise FileNotFoundError(
            "Environment artifact ref points at a missing file: "
            f"artifact_key={artifact_ref.artifact_key!r} path={path}"
        )
    digest = _verify_environment_runtime_artifact_digest(
        path=path,
        artifact_ref=artifact_ref,
    )
    return ResolvedEnvironmentRuntimeArtifact(
        artifact_ref=artifact_ref,
        path=path,
        workspace_relative_path=normalized_relative_path,
        sha256=digest,
        size_bytes=path.stat().st_size,
    )


def _verify_environment_runtime_artifact_digest(
    *,
    path: Path,
    artifact_ref: EnvironmentRuntimeArtifactRef,
) -> str | None:
    expected = _clean(artifact_ref.digest)
    if expected is None:
        return None
    algorithm = (_clean(artifact_ref.digest_algorithm) or "sha256").lower()
    expected_digest = expected
    if ":" in expected:
        algorithm, expected_digest = expected.split(":", 1)
        algorithm = algorithm.strip().lower()
        expected_digest = expected_digest.strip()
    if algorithm != "sha256":
        raise RuntimeError(
            "Environment artifact ref uses unsupported digest algorithm: "
            f"artifact_key={artifact_ref.artifact_key!r} algorithm={algorithm!r}"
        )
    actual = sha256(path.read_bytes()).hexdigest()
    if actual.lower() != expected_digest.lower():
        raise RuntimeError(
            "Environment artifact ref digest mismatch: "
            f"artifact_key={artifact_ref.artifact_key!r} "
            f"expected={expected_digest} actual={actual}"
        )
    return actual


def _artifact_ref_satisfies_committed_projection_dto_requirement(
    *,
    artifact_ref: EnvironmentRuntimeArtifactRef,
    dto_package_name: str | None,
    dto_import_root: str | None,
) -> bool:
    if artifact_ref.artifact_family != _OCG_LANGUAGE_MATERIALIZATION_ARTIFACT_FAMILY:
        return False
    if artifact_ref.status not in {"available", "materialized"}:
        return False
    if artifact_ref.artifact_role not in _COMMITTED_PROJECTION_DTO_ARTIFACT_ROLES:
        return False
    if not _artifact_ref_matches_dto_target(
        artifact_ref=artifact_ref,
        dto_package_name=dto_package_name,
        dto_import_root=dto_import_root,
    ):
        return False
    return True


def _artifact_ref_matches_dto_target(
    *,
    artifact_ref: EnvironmentRuntimeArtifactRef,
    dto_package_name: str | None,
    dto_import_root: str | None,
) -> bool:
    target_tokens = _dto_target_tokens(
        dto_package_name=dto_package_name,
        dto_import_root=dto_import_root,
    )
    if not target_tokens:
        return False
    ref_tokens = _artifact_ref_dto_tokens(artifact_ref)
    return bool(target_tokens.intersection(ref_tokens))


def _dto_target_tokens(
    *,
    dto_package_name: str | None,
    dto_import_root: str | None,
) -> set[str]:
    tokens: set[str] = set()
    for value in (dto_package_name, dto_import_root):
        tokens.update(_package_identity_tokens(value))
    return tokens


def _artifact_ref_dto_tokens(artifact_ref: EnvironmentRuntimeArtifactRef) -> set[str]:
    tokens = _package_identity_tokens(artifact_ref.package_name)
    for value in (artifact_ref.artifact_key, artifact_ref.workspace_relative_path):
        cleaned = _clean(value)
        if cleaned is None:
            continue
        for part in Path(cleaned).parts:
            tokens.update(_package_identity_tokens(part))
        for part in cleaned.replace(":", "/").split("/"):
            tokens.update(_package_identity_tokens(part))
    return tokens


def _package_identity_tokens(value: str | None) -> set[str]:
    cleaned = _clean(value)
    if cleaned is None:
        return set()
    if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
        return set()
    dotted_root = cleaned.split(".", 1)[0]
    raw_tokens = {cleaned, dotted_root}
    tokens: set[str] = set()
    for token in raw_tokens:
        normalized = token.strip().lower()
        if not normalized:
            continue
        tokens.add(normalized)
        tokens.add(normalized.replace("-", "_"))
        tokens.add(normalized.replace("_", "-"))
    return tokens


def _dto_import_root_from_class_ref(class_ref: str | None) -> str | None:
    cleaned = _clean(class_ref)
    if cleaned is None or "." not in cleaned:
        return None
    root = cleaned.split(".", 1)[0]
    if "/" in root or "\\" in root or ".." in root:
        return None
    return root


def _environment_runtime_artifact_ref_from_ref(
    ref: object,
) -> EnvironmentRuntimeArtifactRef:
    return EnvironmentRuntimeArtifactRef(
        artifact_family=_text_value(_object_field(ref, "artifact_family")) or "",
        artifact_key=_text_value(_object_field(ref, "artifact_key")) or "",
        artifact_role=_text_value(_object_field(ref, "artifact_role")) or "runtime",
        required_for=_strings_tuple(_object_field(ref, "required_for")),
        status=_text_value(_object_field(ref, "status")) or "available",
        package_name=_text_value(_object_field(ref, "package_name")),
        revision_code_package_id=_optional_uuid(
            _object_field(ref, "revision_code_package_id")
        ),
        semantic_package_commit_id=_optional_uuid(
            _object_field(ref, "semantic_package_commit_id")
        ),
        source_code_package_id=_optional_uuid(
            _object_field(ref, "source_code_package_id")
        ),
        source_object_instance_graph_commit_id=_optional_uuid(
            _object_field(ref, "source_object_instance_graph_commit_id")
        ),
        input_object_instance_graph_commit_id=_optional_uuid(
            _object_field(ref, "input_object_instance_graph_commit_id")
        ),
        workspace_relative_path=_text_value(
            _object_field(ref, "workspace_relative_path")
        ),
        digest=_text_value(_object_field(ref, "digest")),
        digest_algorithm=_text_value(_object_field(ref, "digest_algorithm")),
        media_type=_text_value(_object_field(ref, "media_type")),
        runtime_contract_version=_text_value(
            _object_field(ref, "runtime_contract_version")
        ),
    )


def _object_field(ref: object, name: str) -> object:
    if isinstance(ref, Mapping):
        return ref.get(name)
    return getattr(ref, name, None)


def _strings_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if not isinstance(value, Sequence):
        return ()
    return tuple(
        text for item in value for text in (_text_value(item),) if text is not None
    )


def _text_value(value: object) -> str | None:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _validate_environment_ref(package_ref: EnvironmentRuntimePackageRef) -> None:
    if _clean(package_ref.family_key) != "environment":
        raise RuntimeError(
            "Environment package ref requires family_key='environment': "
            f"{package_ref.family_key!r}"
        )
    if _clean(package_ref.package_kind) != "environment":
        raise RuntimeError(
            "Environment package ref requires package_kind='environment': "
            f"{package_ref.package_kind!r}"
        )
    if not _clean(package_ref.package_name):
        raise RuntimeError("Environment package ref requires package_name.")
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    if semantic_root_kind is not None and semantic_root_kind not in {
        "environment_config",
        "environment_config_package",
    }:
        raise RuntimeError(
            "Environment package ref semantic_root_kind must be "
            "'environment_config' or 'environment_config_package' when provided: "
            f"{semantic_root_kind!r}"
        )


def _validate_revision_filesystem_root(root: Path) -> None:
    if not root.is_dir():
        raise FileNotFoundError(
            "Environment package ref requires an existing materialized "
            f"workspace root: {root}"
        )
    manifest_path = (root / _REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Environment package ref requires a WorkspaceRevision filesystem "
            f"manifest at {manifest_path}"
        )


def _validate_environment_package_ref_pair(
    *,
    package_ref: EnvironmentRuntimePackageRef,
    environment_package: EnvironmentConfigPackage,
) -> None:
    if environment_package.handle != package_ref.package_name:
        raise RuntimeError(
            "Environment package ref package_name does not match "
            "EnvironmentConfigPackage.handle: "
            f"ref={package_ref.package_name!r} "
            f"environment_package={environment_package.handle!r}"
        )
    semantic_package_id = _optional_uuid(package_ref.semantic_package_id)
    if (
        semantic_package_id is not None
        and semantic_package_id != environment_package.id
    ):
        raise RuntimeError(
            "Environment package ref semantic_package_id does not match "
            "EnvironmentConfigPackage: "
            f"ref={semantic_package_id} environment_package={environment_package.id}"
        )
    pinned_commit_id = _optional_uuid(
        package_ref.semantic_root_object_instance_graph_commit_id
    )
    if (
        pinned_commit_id is not None
        and pinned_commit_id
        != environment_package.environment_config_object_instance_graph_commit_id
    ):
        raise RuntimeError(
            "Environment package ref "
            "semantic_root_object_instance_graph_commit_id does not match "
            "EnvironmentConfigPackage pin: "
            f"ref={pinned_commit_id} "
            f"environment_package="
            f"{environment_package.environment_config_object_instance_graph_commit_id}"
        )


def _validate_environment_config_ref_pair(
    *,
    package_ref: EnvironmentRuntimePackageRef,
    environment_package: EnvironmentConfigPackage,
    environment_config: EnvironmentConfig,
) -> None:
    _validate_environment_package_config_pair(
        environment_package=environment_package,
        environment_config=environment_config,
    )
    semantic_root_id = _optional_uuid(package_ref.semantic_root_id)
    if semantic_root_id is None:
        return
    semantic_root_kind = _clean(package_ref.semantic_root_kind)
    expected_root_id = (
        environment_config.id
        if semantic_root_kind == "environment_config"
        else environment_package.id
    )
    if semantic_root_id != expected_root_id:
        raise RuntimeError(
            "Environment package ref semantic_root_id does not match "
            f"{semantic_root_kind or 'environment_config_package'} root: "
            f"ref={semantic_root_id} expected={expected_root_id}"
        )


def _validate_environment_package_config_pair(
    *,
    environment_package: EnvironmentConfigPackage,
    environment_config: EnvironmentConfig,
) -> None:
    if environment_config.id != environment_package.environment_config_id:
        raise RuntimeError(
            "EnvironmentConfigPackage points at a different EnvironmentConfig "
            "than the hydrated root: "
            f"package={environment_package.environment_config_id} "
            f"environment_config={environment_config.id}"
        )


def _resolve_manifest_path(
    *,
    package_ref: EnvironmentRuntimePackageRef,
    materialized_workspace_root: Path,
) -> Path | None:
    raw_manifest_path = package_ref.manifest_path
    if raw_manifest_path is None:
        return None
    manifest_path = Path(raw_manifest_path).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = materialized_workspace_root / manifest_path
    resolved_manifest_path = manifest_path.resolve()
    _relative_to_root(
        path=resolved_manifest_path,
        root=materialized_workspace_root,
        label="manifest_path",
    )
    return resolved_manifest_path


def _reject_duplicate_resolved_refs(
    refs: tuple[ResolvedEnvironmentRuntimePackageRef, ...],
) -> None:
    seen: dict[str, ResolvedEnvironmentRuntimePackageRef] = {}
    for ref in refs:
        key = _resolved_ref_key(ref)
        existing = seen.get(key)
        if (
            existing is not None
            and existing.manifest_path is not None
            and ref.manifest_path is not None
            and existing.manifest_path != ref.manifest_path
        ):
            raise RuntimeError(
                "Conflicting environment package refs resolve to the same "
                f"semantic package identity: {key!r}"
            )
        seen[key] = ref


def _resolved_ref_key(ref: ResolvedEnvironmentRuntimePackageRef) -> str:
    if ref.semantic_package_id is not None:
        return f"semantic_package_id:{ref.semantic_package_id}"
    if ref.semantic_root_id is not None:
        return f"semantic_root_id:{ref.semantic_root_id}"
    if ref.manifest_path is not None:
        return f"manifest_path:{ref.manifest_path.as_posix()}"
    return f"package_name:{ref.environment_handle}"


async def _find_domain_commit_ref_for_oig_commit_id(
    *,
    store: FSCommitStore,
    projection_hash: str,
    object_instance_graph_commit_id: UUID,
) -> _DomainCommitRef | None:
    indexed_ref = _find_indexed_domain_commit_ref_for_oig_commit_id(
        store=store,
        projection_hash=projection_hash,
        object_instance_graph_commit_id=object_instance_graph_commit_id,
    )
    if indexed_ref is not None:
        return indexed_ref
    async for branch_id, _head in store.iter_lane_heads_by_projection(
        projection_hash=projection_hash,
    ):
        domain_commit_id = (
            await store.domain_commit_id_for_object_instance_graph_commit_id(
                branch_id=branch_id,
                projection_hash=projection_hash,
                object_instance_graph_commit_id=object_instance_graph_commit_id,
            )
        )
        if domain_commit_id is not None:
            return _DomainCommitRef(
                branch_id=branch_id,
                projection_hash=projection_hash,
                domain_commit_id=domain_commit_id,
            )
    return None


def _find_indexed_domain_commit_ref_for_oig_commit_id(
    *,
    store: FSCommitStore,
    projection_hash: str,
    object_instance_graph_commit_id: UUID,
) -> _DomainCommitRef | None:
    oig_root = store.aware_root / ".aware" / "oig"
    if not oig_root.exists():
        return None
    for branch_dir in sorted(path for path in oig_root.iterdir() if path.is_dir()):
        try:
            branch_id = UUID(branch_dir.name)
        except Exception:
            continue
        index_path = (
            branch_dir
            / projection_hash
            / "indexes"
            / "object_instance_graph_commits"
            / f"{object_instance_graph_commit_id}.json"
        )
        if not index_path.is_file():
            continue
        try:
            payload = json.loads(index_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(
                "Invalid ObjectInstanceGraphCommit index payload: " f"{index_path}"
            ) from exc
        if not isinstance(payload, dict):
            raise RuntimeError(
                "Invalid ObjectInstanceGraphCommit index payload: " f"{index_path}"
            )
        indexed_projection_hash = payload.get("projection_hash")
        if indexed_projection_hash != projection_hash:
            raise RuntimeError(
                "ObjectInstanceGraphCommit index projection mismatch: "
                f"expected={projection_hash} actual={indexed_projection_hash!r}"
            )
        domain_commit_id = _optional_uuid(payload.get("domain_commit_id"))
        if domain_commit_id is None:
            raise RuntimeError(
                "ObjectInstanceGraphCommit index missing domain_commit_id: "
                f"{index_path}"
            )
        return _DomainCommitRef(
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_commit_id=domain_commit_id,
        )
    return None


async def _hydrate_root_from_commit(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    commit_id: UUID,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot | None:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            f"Environment package ref missing projection hash: {projection_hash}"
        )
    oig, _ = await CachedLaneMaterializer().get(
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


def _relative_to_root(*, path: Path, root: Path, label: str) -> str:
    resolved_path = path.expanduser().resolve()
    resolved_root = root.expanduser().resolve()
    try:
        relative = resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(
            "Environment package ref path resolved outside materialized "
            f"workspace root: label={label} root={resolved_root} path={resolved_path}"
        ) from exc
    return relative.as_posix() or "."


def _required_uuid(value: str | None, *, label: str) -> UUID:
    parsed = _optional_uuid(value)
    if parsed is None:
        raise RuntimeError(f"Environment package ref requires {label}.")
    return parsed


def _required_semantic_package_oig_commit_id(
    package_ref: EnvironmentRuntimePackageRef,
) -> UUID:
    return _required_uuid(
        _clean(package_ref.semantic_object_instance_graph_commit_id)
        or _clean(package_ref.semantic_head_commit_id),
        label="semantic_object_instance_graph_commit_id",
    )


def _optional_uuid(value: str | UUID | object | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        return None
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
    "EnvironmentRuntimeArtifactRef",
    "EnvironmentRuntimePackageRef",
    "ResolvedCommittedProjectionDtoArtifactBundle",
    "ResolvedEnvironmentOntologyConfigRef",
    "ResolvedEnvironmentOntologyPackageRef",
    "ResolvedEnvironmentOntologyPointerRef",
    "ResolvedEnvironmentRuntimeArtifact",
    "ResolvedEnvironmentRuntimePackageRef",
    "resolve_committed_projection_dto_artifact_bundle",
    "resolve_committed_environment_runtime_package_ref",
    "resolve_committed_environment_runtime_package_refs",
]
