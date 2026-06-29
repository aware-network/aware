from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
)
from aware_code.types import JsonArray, JsonObject
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.fs_store import (
    CommitActionDescriptor,
    FSCommitStore,
)
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_sdk_ontology.sdk.sdk_config import SdkConfig
from aware_sdk_ontology.sdk.sdk_operation import SdkOperation
from aware_sdk_ontology.sdk.sdk_operation_api_capability_endpoint import (
    SdkOperationApiCapabilityEndpoint,
)
from aware_sdk_ontology.sdk.sdk_operation_dependency import SdkOperationDependency
from aware_sdk_ontology.sdk.sdk_package import SdkPackage
from aware_sdk_ontology.sdk.sdk_package_api_package import SdkPackageApiPackage
from aware_sdk_ontology.sdk.sdk_package_dependency import SdkPackageDependency
from aware_sdk_ontology.sdk.sdk_package_implementation_package import (
    SdkPackageImplementationPackage,
)
from aware_sdk_ontology.sdk.sdk_package_object_config_graph_package import (
    SdkPackageObjectConfigGraphPackage,
)
from aware_sdk_ontology.stable_ids import (
    stable_sdk_config_id,
    stable_sdk_operation_api_capability_endpoint_id,
    stable_sdk_operation_dependency_id,
    stable_sdk_operation_id,
    stable_sdk_package_api_package_id,
    stable_sdk_package_dependency_id,
    stable_sdk_package_id,
    stable_sdk_package_implementation_package_id,
    stable_sdk_package_object_config_graph_package_id,
)

from ..models import (
    SdkOperationDependencyPlan,
    SdkOperationEndpointPlan,
    SdkOperationPlan,
)

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class SdkConfigManifestSnapshotCommitResult:
    sdk_config: SdkConfig
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class SdkPackageManifestSnapshotCommitResult:
    sdk_package: SdkPackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class SdkPackageDependencySnapshotRef:
    target_package_name: str
    target_sdk_package_id: UUID
    target_sdk_package_object_instance_graph_commit_id: UUID | None = None
    target_version_number: int | None = None
    expected_hash_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkPackageObjectConfigGraphPackageSnapshotRef:
    object_config_graph_package_id: UUID
    manifest_relative_path: str
    role: str = "local_state"
    package_kind: str = "state"
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None
    expected_hash_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SdkPackageImplementationPackageSnapshotRef:
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str
    entrypoint: str | None = None
    role: str = "public_package"
    include_paths: JsonArray = field(default_factory=JsonArray)
    exclude_paths: JsonArray = field(default_factory=JsonArray)


_SDK_CONFIG_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://sdk/config/manifest-snapshot-commit/v1",
)
_SDK_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://sdk/package/manifest-snapshot-commit/v1",
)


async def commit_sdk_config_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    title: str | None,
    description: str | None,
    operations: Sequence[SdkOperationPlan],
) -> SdkConfigManifestSnapshotCommitResult:
    sdk_config, objects_by_id = _build_sdk_config_manifest_snapshot_objects(
        name=name,
        title=title,
        description=description,
        operations=operations,
    )
    commit = await _commit_manifest_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=sdk_config.id,
        root_object=sdk_config,
        objects_by_id=objects_by_id,
        operation_label="SdkConfig.materialize_manifest_snapshot",
        commit_id_namespace=_SDK_CONFIG_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return SdkConfigManifestSnapshotCommitResult(
        sdk_config=sdk_config,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_sdk_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    sdk_config_id: UUID,
    sdk_config_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_sdk_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    targets: JsonObject,
    api_package_ids: Sequence[UUID],
    object_config_graph_package_refs: Sequence[
        SdkPackageObjectConfigGraphPackageSnapshotRef
    ] = (),
    implementation_package_refs: Sequence[
        SdkPackageImplementationPackageSnapshotRef
    ] = (),
    sdk_package_dependency_refs: Sequence[SdkPackageDependencySnapshotRef] = (),
) -> SdkPackageManifestSnapshotCommitResult:
    sdk_package, objects_by_id = _build_sdk_package_manifest_snapshot_objects(
        name=name,
        sdk_config_id=sdk_config_id,
        sdk_config_object_instance_graph_commit_id=(
            sdk_config_object_instance_graph_commit_id
        ),
        source_code_package_id=source_code_package_id,
        fqn_prefix=fqn_prefix,
        version_number=version_number,
        title=title,
        description=description,
        aware_sdk_version=aware_sdk_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=compilation_mode,
        dependencies=dependencies,
        targets=targets,
        api_package_ids=api_package_ids,
        object_config_graph_package_refs=object_config_graph_package_refs,
        implementation_package_refs=implementation_package_refs,
        sdk_package_dependency_refs=sdk_package_dependency_refs,
    )
    commit = await _commit_manifest_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=sdk_package.id,
        root_object=sdk_package,
        objects_by_id=objects_by_id,
        operation_label="SdkPackage.materialize_manifest_snapshot",
        commit_id_namespace=_SDK_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return SdkPackageManifestSnapshotCommitResult(
        sdk_package=sdk_package,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


def _build_sdk_config_manifest_snapshot_objects(
    *,
    name: str,
    title: str | None,
    description: str | None,
    operations: Sequence[SdkOperationPlan],
) -> tuple[SdkConfig, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkConfig snapshot requires non-empty name")
    sdk_config = _remember(
        objects_by_id,
        SdkConfig(
            id=stable_sdk_config_id(name=normalized_name),
            name=normalized_name,
            title=(title or "").strip() or None,
            description=(description or "").strip() or None,
        ),
    )
    for operation_plan in operations:
        operation_name = (operation_plan.name or "").strip()
        if not operation_name:
            raise RuntimeError(
                f"SdkConfig snapshot contains empty operation name: {normalized_name}"
            )
        operation = _remember(
            objects_by_id,
            SdkOperation(
                id=stable_sdk_operation_id(
                    sdk_config_id=sdk_config.id,
                    name=operation_name,
                ),
                sdk_config_id=sdk_config.id,
                name=operation_name,
                description=(operation_plan.description or "").strip() or None,
            ),
        )
        sdk_config.operations.append(operation)
        for endpoint_plan in operation_plan.api_endpoints:
            endpoint_name = (endpoint_plan.name or "").strip()
            if not endpoint_name:
                raise RuntimeError(
                    "SdkConfig snapshot contains empty endpoint name: "
                    f"sdk_config={normalized_name!r} operation={operation_name!r}"
                )
            api_capability_endpoint_id = _api_capability_endpoint_id_from_plan(
                endpoint_plan,
            )
            endpoint = _remember(
                objects_by_id,
                SdkOperationApiCapabilityEndpoint(
                    id=stable_sdk_operation_api_capability_endpoint_id(
                        sdk_operation_id=operation.id,
                        name=endpoint_name,
                        api_capability_endpoint_id=api_capability_endpoint_id,
                    ),
                    sdk_operation_id=operation.id,
                    name=endpoint_name,
                    api_capability_endpoint_id=api_capability_endpoint_id,
                    endpoint_ref=(endpoint_plan.endpoint_ref or "").strip() or None,
                    role=(endpoint_plan.role or "").strip() or "primary",
                    order=endpoint_plan.order,
                    required=endpoint_plan.required,
                ),
            )
            operation.api_capability_endpoints.append(endpoint)
        for dependency_plan in operation_plan.sdk_operation_dependencies:
            target_operation_ref = (
                dependency_plan.target_operation_ref or ""
            ).strip()
            if not target_operation_ref:
                raise RuntimeError(
                    "SdkConfig snapshot contains empty SDK operation dependency "
                    + f"ref: sdk_config={normalized_name!r} "
                    + f"operation={operation_name!r}"
                )
            target_sdk_operation_id = _sdk_operation_dependency_target_id(
                dependency_plan,
            )
            operation_dependency = _remember(
                objects_by_id,
                SdkOperationDependency(
                    id=stable_sdk_operation_dependency_id(
                        sdk_operation_id=operation.id,
                        target_sdk_operation_id=target_sdk_operation_id,
                    ),
                    sdk_operation_id=operation.id,
                    target_sdk_operation_id=target_sdk_operation_id,
                    target_operation_ref=target_operation_ref,
                    target_sdk_name=(
                        dependency_plan.target_sdk_name or ""
                    ).strip(),
                    target_operation_name=(
                        dependency_plan.target_operation_name or ""
                    ).strip(),
                    target_package_name=(
                        dependency_plan.target_package_name or ""
                    ).strip()
                    or None,
                    role=(dependency_plan.role or "").strip() or "dependency",
                    order=dependency_plan.order,
                    required=dependency_plan.required,
                    description=(
                        dependency_plan.description or ""
                    ).strip()
                    or None,
                ),
            )
            operation.sdk_operation_dependencies.append(operation_dependency)
    return sdk_config, objects_by_id


def _sdk_operation_dependency_target_id(
    dependency_plan: SdkOperationDependencyPlan,
) -> UUID:
    target_sdk_name = (dependency_plan.target_sdk_name or "").strip()
    target_operation_name = (dependency_plan.target_operation_name or "").strip()
    if not target_sdk_name or not target_operation_name:
        raise RuntimeError(
            "SdkConfig snapshot contains invalid SDK operation dependency "
            + f"target: {dependency_plan.target_operation_ref!r}"
        )
    return stable_sdk_operation_id(
        sdk_config_id=stable_sdk_config_id(name=target_sdk_name),
        name=target_operation_name,
    )


def _build_sdk_package_manifest_snapshot_objects(
    *,
    name: str,
    sdk_config_id: UUID,
    sdk_config_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_sdk_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    targets: JsonObject,
    api_package_ids: Sequence[UUID],
    object_config_graph_package_refs: Sequence[
        SdkPackageObjectConfigGraphPackageSnapshotRef
    ] = (),
    implementation_package_refs: Sequence[
        SdkPackageImplementationPackageSnapshotRef
    ] = (),
    sdk_package_dependency_refs: Sequence[SdkPackageDependencySnapshotRef] = (),
) -> tuple[SdkPackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("SdkPackage snapshot requires non-empty name")
    sdk_package = _remember(
        objects_by_id,
        SdkPackage(
            id=stable_sdk_package_id(name=normalized_name),
            name=normalized_name,
            sdk_config_id=sdk_config_id,
            sdk_config_object_instance_graph_commit_id=(
                sdk_config_object_instance_graph_commit_id
            ),
            source_code_package_id=source_code_package_id,
            fqn_prefix=(fqn_prefix or "").strip() or None,
            version_number=version_number,
            title=(title or "").strip() or None,
            description=(description or "").strip() or None,
            aware_sdk_version=aware_sdk_version,
            manifest_relative_path=(manifest_relative_path or "").strip() or None,
            package_root=(package_root or "").strip() or ".",
            sources_root=(sources_root or "").strip() or "sdks",
            include_paths=JsonArray(include_paths or []),
            exclude_paths=JsonArray(exclude_paths or []),
            force_fresh_scan=force_fresh_scan,
            compilation_mode=(compilation_mode or "").strip() or "raw_xor",
            dependencies=JsonArray(dependencies or []),
            targets=JsonObject(targets or {}),
        ),
    )
    for api_package_id in sorted(set(api_package_ids), key=str):
        api_package = _remember(
            objects_by_id,
            SdkPackageApiPackage(
                id=stable_sdk_package_api_package_id(
                    sdk_package_id=sdk_package.id,
                    api_package_id=api_package_id,
                ),
                sdk_package_id=sdk_package.id,
                api_package_id=api_package_id,
                description="SDK API package dependency.",
            ),
        )
        sdk_package.api_packages.append(api_package)
    for ocg_package_ref in sorted(
        object_config_graph_package_refs,
        key=lambda item: (
            item.manifest_relative_path,
            str(item.object_config_graph_package_id),
        ),
    ):
        manifest_path = (ocg_package_ref.manifest_relative_path or "").strip()
        if not manifest_path:
            raise RuntimeError(
                "SdkPackage ObjectConfigGraphPackage snapshot requires "
                "manifest_relative_path"
            )
        expected_hash = (
            (ocg_package_ref.expected_hash_sha256 or "").strip().lower() or None
        )
        if expected_hash is not None and (
            len(expected_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in expected_hash)
        ):
            raise RuntimeError(
                "SdkPackage ObjectConfigGraphPackage expected_hash_sha256 must "
                "be a lowercase 64-character SHA-256 hex digest"
            )
        ocg_package = _remember(
            objects_by_id,
            SdkPackageObjectConfigGraphPackage(
                id=stable_sdk_package_object_config_graph_package_id(
                    sdk_package_id=sdk_package.id,
                    object_config_graph_package_id=(
                        ocg_package_ref.object_config_graph_package_id
                    ),
                ),
                sdk_package_id=sdk_package.id,
                object_config_graph_package_id=(
                    ocg_package_ref.object_config_graph_package_id
                ),
                object_config_graph_package_object_instance_graph_commit_id=(
                    ocg_package_ref.object_config_graph_package_object_instance_graph_commit_id
                ),
                role=(ocg_package_ref.role or "").strip() or "local_state",
                manifest_relative_path=manifest_path,
                package_kind=(ocg_package_ref.package_kind or "").strip() or "state",
                expected_hash_sha256=expected_hash,
                description=(ocg_package_ref.description or "").strip() or None,
            ),
        )
        sdk_package.object_config_graph_packages.append(ocg_package)
    for implementation_ref in sorted(
        implementation_package_refs,
        key=lambda item: (
            item.language.value,
            item.package_name,
            str(item.code_package_id),
        ),
    ):
        package_name = (implementation_ref.package_name or "").strip()
        import_root = (implementation_ref.import_root or "").strip()
        manifest_path = (implementation_ref.manifest_relative_path or "").strip()
        if not package_name:
            raise RuntimeError(
                "SdkPackage implementation package snapshot requires package_name"
            )
        if not import_root:
            raise RuntimeError(
                "SdkPackage implementation package snapshot requires import_root"
            )
        if not manifest_path:
            raise RuntimeError(
                "SdkPackage implementation package snapshot requires "
                "manifest_relative_path"
            )
        implementation_package = _remember(
            objects_by_id,
            SdkPackageImplementationPackage(
                id=stable_sdk_package_implementation_package_id(
                    sdk_package_id=sdk_package.id,
                    code_package_id=implementation_ref.code_package_id,
                ),
                sdk_package_id=sdk_package.id,
                code_package_id=implementation_ref.code_package_id,
                package_name=package_name,
                language=implementation_ref.language,
                import_root=import_root,
                manifest_relative_path=manifest_path,
                package_root=(implementation_ref.package_root or "").strip() or ".",
                entrypoint=(implementation_ref.entrypoint or "").strip() or None,
                role=(implementation_ref.role or "").strip() or "public_package",
                include_paths=JsonArray(implementation_ref.include_paths or []),
                exclude_paths=JsonArray(implementation_ref.exclude_paths or []),
            ),
        )
        sdk_package.implementation_packages.append(implementation_package)
    for dependency_ref in sorted(
        sdk_package_dependency_refs,
        key=lambda item: (item.target_package_name, str(item.target_sdk_package_id)),
    ):
        target_package_name = (dependency_ref.target_package_name or "").strip()
        if not target_package_name:
            raise RuntimeError(
                "SdkPackage dependency snapshot requires target package name"
            )
        expected_hash = (
            (dependency_ref.expected_hash_sha256 or "").strip().lower() or None
        )
        if expected_hash is not None and (
            len(expected_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in expected_hash)
        ):
            raise RuntimeError(
                "SdkPackage dependency snapshot expected_hash_sha256 must be a "
                + "lowercase 64-character SHA-256 hex digest"
            )
        sdk_package_dependency = _remember(
            objects_by_id,
            SdkPackageDependency(
                id=stable_sdk_package_dependency_id(
                    sdk_package_id=sdk_package.id,
                    target_sdk_package_id=dependency_ref.target_sdk_package_id,
                ),
                sdk_package_id=sdk_package.id,
                target_sdk_package_id=dependency_ref.target_sdk_package_id,
                target_package_name=target_package_name,
                target_sdk_package_object_instance_graph_commit_id=(
                    dependency_ref.target_sdk_package_object_instance_graph_commit_id
                ),
                target_version_number=dependency_ref.target_version_number,
                expected_hash_sha256=expected_hash,
                description=(dependency_ref.description or "").strip() or None,
            ),
        )
        sdk_package.sdk_package_dependencies.append(sdk_package_dependency)
    return sdk_package, objects_by_id


@dataclass(frozen=True, slots=True)
class _ManifestSnapshotCommit:
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


async def _commit_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    root_object: BaseORMModel,
    objects_by_id: Mapping[UUID, BaseORMModel],
    operation_label: str,
    commit_id_namespace: UUID,
) -> _ManifestSnapshotCommit:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "SDK manifest snapshot commit missing projection hash: "
            f"{projection_hash}"
        )
    domain_oig_id = stable_object_instance_graph_id(
        object_projection_graph_id=opg.id,
        key=str(branch_id),
    )
    _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
        index=index,
        projection_hash=projection_hash,
    )
    if opgi is None:
        raise RuntimeError(
            "SDK manifest snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    before_oig = await _load_before_oig(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_oig_id=domain_oig_id,
        root_object_id=root_object_id,
    )
    object_ids = frozenset(objects_by_id)
    change_set = ORMChangeSet(
        collected_at=datetime.now(UTC),
        created_ids=object_ids,
        touched_ids=object_ids,
        deleted_ids=frozenset(),
        objects_by_id=dict(objects_by_id),
        scalar_fields_by_id={},
        list_fields_by_id={},
        scalar_baseline={},
        list_baseline={},
        list_added={},
        list_removed={},
    )
    changes = build_object_instance_graph_changes_from_orm_change_set(
        before_oig=before_oig,
        object_instance_graph_identity_id=oigi_id,
        ocg=index.ocg,
        opg=opg,
        change_set=change_set,
        class_configs_by_id=index.class_configs_by_id,
        relationships_by_id=index.relationships_by_id,
        enum_option_resolver=default_meta_enum_option_resolver,
        class_instance_resolver=None,
        union_selections=None,
    )
    if not changes:
        head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        raw_head_commit_id = None if head is None else head.get("commit_id")
        if raw_head_commit_id is None:
            raise RuntimeError(
                "SDK manifest snapshot commit produced no OIG changes and no "
                f"existing lane head: operation_label={operation_label!r}"
            )
        head_commit_id = (
            raw_head_commit_id
            if isinstance(raw_head_commit_id, UUID)
            else UUID(str(raw_head_commit_id))
        )
        return _ManifestSnapshotCommit(
            commit_id=head_commit_id,
            head_commit_id=head_commit_id,
            object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=oigi_id,
                commit_id=head_commit_id,
            ),
            object_count=len(objects_by_id),
            change_count=0,
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = _manifest_snapshot_commit_id(
        namespace=commit_id_namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        graph_hash_post=after_oig.hash,
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=root_object_id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(actor_id),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label=operation_label,
            call_target="generated_materialization",
            object_id=root_object.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "SDK manifest snapshot commit did not append a lane commit: "
            f"operation_label={operation_label!r} root_object_id={root_object_id}"
        )
    return _ManifestSnapshotCommit(
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=len(objects_by_id),
        change_count=len(changes),
    )


async def _load_before_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_oig_id: UUID,
    root_object_id: UUID,
):
    opg = index.opg_by_hash[projection_hash]
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if head is not None and head.get("commit_id") is not None:
        oig, _ = await OIGMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=None,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
        return oig
    return build_rooted_object_instance_graph_base(
        key=str(branch_id),
        name=f"OIG_{branch_id.hex[:8]}",
        description="ROOTED_BASE",
        object_config_graph=index.ocg,
        object_projection_graph=opg,
        root_source_object_id=root_object_id,
        oig_id=domain_oig_id,
    )


def _api_capability_endpoint_id_from_plan(
    endpoint_plan: SdkOperationEndpointPlan,
) -> UUID:
    api_ref = endpoint_plan.api_ref
    capability_name = endpoint_plan.capability_name
    endpoint_name = endpoint_plan.name
    api_id = stable_api_id(name=api_ref)
    capability_id = stable_api_capability_id(
        api_id=api_id,
        name=capability_name,
    )
    return stable_api_capability_endpoint_id(
        api_capability_id=capability_id,
        name=endpoint_name,
    )


def _manifest_snapshot_commit_id(
    *,
    namespace: UUID,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        namespace,
        f"{branch_id}:{projection_hash}:{root_object_id}:{graph_hash_post}",
    )


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TModel,
) -> _TModel:
    objects_by_id[obj.id] = obj
    return obj


__all__ = [
    "SdkConfigManifestSnapshotCommitResult",
    "SdkPackageManifestSnapshotCommitResult",
    "SdkPackageDependencySnapshotRef",
    "SdkPackageObjectConfigGraphPackageSnapshotRef",
    "commit_sdk_config_manifest_snapshot",
    "commit_sdk_package_manifest_snapshot",
]
