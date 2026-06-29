from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TypeVar
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_ontology.api.api import Api
from aware_api_ontology.api.api_capability import ApiCapability
from aware_api_ontology.api.api_capability_endpoint import ApiCapabilityEndpoint
from aware_api_ontology.api.api_capability_endpoint_function import (
    ApiCapabilityEndpointFunction,
)
from aware_api_ontology.api.api_capability_endpoint_request_config import (
    ApiCapabilityEndpointRequestConfig,
)
from aware_api_ontology.api.api_graph import ApiGraph
from aware_api_ontology.api.api_graph_capability import ApiGraphCapability
from aware_api_ontology.api.api_graph_capability_function import (
    ApiGraphCapabilityFunction,
)
from aware_api_ontology.api.api_graph_function import ApiGraphFunction
from aware_api_ontology.api.api_package import ApiPackage
from aware_api_ontology.api.api_package_language_package import (
    ApiPackageLanguagePackage,
)
from aware_api_ontology.stable_ids import (
    stable_api_capability_endpoint_function_id,
    stable_api_capability_endpoint_id,
    stable_api_capability_endpoint_request_config_id,
    stable_api_capability_id,
    stable_api_graph_capability_function_id,
    stable_api_graph_capability_id,
    stable_api_graph_function_id,
    stable_api_graph_id,
    stable_api_id,
    stable_api_package_id,
    stable_api_package_language_package_id,
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
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class ApiReferenceSnapshotCommitResult:
    api: Api
    endpoint_ids_by_ref: dict[str, UUID]
    endpoint_function_ids_by_ref: dict[str, dict[str, UUID]]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ApiPackageManifestSnapshotCommitResult:
    api_package: ApiPackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ApiPackageLanguagePackageSnapshotRef:
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str
    role: str = "public_package"
    output_key: str = "python.public_package"
    include_paths: JsonArray = field(default_factory=JsonArray)
    exclude_paths: JsonArray = field(default_factory=JsonArray)


_API_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://api/package/manifest-snapshot-commit/v1",
)
_API_REFERENCE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://api/reference/snapshot-commit/v1",
)


async def commit_api_reference_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    api_name: str,
    endpoint_refs: Sequence[str],
    endpoint_request_class_config_ids: Mapping[str, UUID] | None = None,
    endpoint_fulfillment_names: Mapping[str, Sequence[str]] | None = None,
    api_graph_function_config_id: UUID | None = None,
) -> ApiReferenceSnapshotCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "Api reference snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    object_config_graph_id = index.ocg.id
    if object_config_graph_id is None:
        raise RuntimeError("Api reference snapshot requires ObjectConfigGraph id")

    (
        api,
        endpoint_ids_by_ref,
        endpoint_function_ids_by_ref,
        objects_by_id,
    ) = _build_api_reference_snapshot_objects(
        api_name=api_name,
        endpoint_refs=endpoint_refs,
        object_config_graph_id=object_config_graph_id,
        endpoint_request_class_config_ids=endpoint_request_class_config_ids or {},
        endpoint_fulfillment_names=endpoint_fulfillment_names or {},
        api_graph_function_config_id=api_graph_function_config_id,
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
            "Api reference snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    before_oig = await _load_api_package_before_oig(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_oig_id=domain_oig_id,
        root_object_id=api.id,
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
        raise RuntimeError(
            "Api reference snapshot commit produced no OIG changes: "
            f"api_name={api_name!r}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = _api_reference_snapshot_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
        api_id=api.id,
        graph_hash_post=after_oig.hash,
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=api.id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(actor_id),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label="Api.materialize_reference_snapshot",
            call_target="generated_materialization",
            object_id=api.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Api reference snapshot commit did not append a lane commit: "
            f"api_name={api_name!r}"
        )

    return ApiReferenceSnapshotCommitResult(
        api=api,
        endpoint_ids_by_ref=endpoint_ids_by_ref,
        endpoint_function_ids_by_ref=endpoint_function_ids_by_ref,
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=len(objects_by_id),
        change_count=len(changes),
    )


async def commit_api_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    package_name: str,
    api_id: UUID,
    api_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_api_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    targets: JsonObject,
    language_package_refs: Sequence[ApiPackageLanguagePackageSnapshotRef] = (),
) -> ApiPackageManifestSnapshotCommitResult:
    opg = index.opg_by_hash.get(projection_hash)
    if opg is None:
        raise RuntimeError(
            "ApiPackage manifest snapshot commit missing projection hash: "
            f"{projection_hash}"
        )

    api_package, objects_by_id = _build_api_package_manifest_snapshot_objects(
        package_name=package_name,
        api_id=api_id,
        api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
        source_code_package_id=source_code_package_id,
        fqn_prefix=fqn_prefix,
        version_number=version_number,
        title=title,
        description=description,
        aware_api_version=aware_api_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=compilation_mode,
        dependencies=dependencies,
        targets=targets,
        language_package_refs=language_package_refs,
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
            "ApiPackage manifest snapshot commit missing ObjectProjectionGraphIdentity: "
            f"projection_hash={projection_hash}"
        )
    oigi_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=opgi.id,
        object_instance_graph_id=domain_oig_id,
    )
    before_oig = await _load_api_package_before_oig(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        domain_oig_id=domain_oig_id,
        root_object_id=api_package.id,
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
        raise RuntimeError(
            "ApiPackage manifest snapshot commit produced no OIG changes: "
            f"package_name={package_name!r}"
        )
    after_oig = materialize_meta_oig_post(
        before_oig=before_oig,
        changes=changes,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    commit_id = _api_package_manifest_snapshot_commit_id(
        branch_id=branch_id,
        projection_hash=projection_hash,
        api_package_id=api_package.id,
        graph_hash_post=after_oig.hash,
    )
    commit = await FSLaneCommitter().commit(
        branch_id=branch_id,
        projection_hash=projection_hash,
        object_instance_graph_identity_id=oigi_id,
        object_instance_graph_id=domain_oig_id,
        before_oig=before_oig,
        root_object_id=api_package.id,
        changes=changes,
        graph_hash_pre=before_oig.hash,
        graph_hash_post=after_oig.hash,
        author_id=resolve_meta_author_id(actor_id),
        commit_id=commit_id,
        commit_action=CommitActionDescriptor(
            operation_label="ApiPackage.materialize_manifest_snapshot",
            call_target="generated_materialization",
            object_id=api_package.id,
        ),
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "ApiPackage manifest snapshot commit did not append a lane commit: "
            f"package_name={package_name!r}"
        )

    return ApiPackageManifestSnapshotCommitResult(
        api_package=api_package,
        commit_id=commit.commit.id,
        head_commit_id=commit.commit.id,
        object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
            object_instance_graph_identity_id=commit.object_instance_graph_identity_id,
            commit_id=commit.commit.id,
        ),
        object_count=len(objects_by_id),
        change_count=len(changes),
    )


def _build_api_package_manifest_snapshot_objects(
    *,
    package_name: str,
    api_id: UUID,
    api_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_api_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    dependencies: JsonArray,
    targets: JsonObject,
    language_package_refs: Sequence[ApiPackageLanguagePackageSnapshotRef] = (),
) -> tuple[ApiPackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (package_name or "").strip()
    if not normalized_name:
        raise RuntimeError("ApiPackage snapshot requires non-empty package_name")
    api_package = _remember(
        objects_by_id,
        ApiPackage(
            id=stable_api_package_id(name=normalized_name),
            name=normalized_name,
            api_id=api_id,
            api_object_instance_graph_commit_id=api_object_instance_graph_commit_id,
            source_code_package_id=source_code_package_id,
            fqn_prefix=(fqn_prefix or "").strip() or None,
            version_number=version_number,
            title=(title or "").strip() or None,
            description=(description or "").strip() or None,
            aware_api_version=aware_api_version,
            manifest_relative_path=(manifest_relative_path or "").strip() or None,
            package_root=(package_root or "").strip() or ".",
            sources_root=(sources_root or "").strip() or "apis",
            include_paths=JsonArray(include_paths or []),
            exclude_paths=JsonArray(exclude_paths or []),
            force_fresh_scan=force_fresh_scan,
            compilation_mode=(compilation_mode or "").strip() or "raw_xor",
            dependencies=JsonArray(dependencies or []),
            targets=JsonObject(targets or {}),
        ),
    )
    for language_ref in sorted(
        language_package_refs,
        key=lambda item: (
            item.language.value,
            item.output_key,
            item.package_name,
            str(item.code_package_id),
        ),
    ):
        package_name_text = (language_ref.package_name or "").strip()
        import_root = (language_ref.import_root or "").strip()
        manifest_path = (language_ref.manifest_relative_path or "").strip()
        if not package_name_text:
            raise RuntimeError("ApiPackage language package snapshot requires name")
        if not import_root:
            raise RuntimeError(
                "ApiPackage language package snapshot requires import_root"
            )
        if not manifest_path:
            raise RuntimeError(
                "ApiPackage language package snapshot requires manifest_relative_path"
            )
        language_package = _remember(
            objects_by_id,
            ApiPackageLanguagePackage(
                id=stable_api_package_language_package_id(
                    api_package_id=api_package.id,
                    code_package_id=language_ref.code_package_id,
                ),
                api_package_id=api_package.id,
                code_package_id=language_ref.code_package_id,
                package_name=package_name_text,
                language=language_ref.language,
                import_root=import_root,
                manifest_relative_path=manifest_path,
                package_root=(language_ref.package_root or "").strip() or ".",
                role=(language_ref.role or "").strip() or "public_package",
                output_key=(
                    (language_ref.output_key or "").strip() or "python.public_package"
                ),
                include_paths=JsonArray(language_ref.include_paths or []),
                exclude_paths=JsonArray(language_ref.exclude_paths or []),
            ),
        )
        api_package.language_packages.append(language_package)
    return api_package, objects_by_id


def _build_api_reference_snapshot_objects(
    *,
    api_name: str,
    endpoint_refs: Sequence[str],
    object_config_graph_id: UUID,
    endpoint_request_class_config_ids: Mapping[str, UUID],
    endpoint_fulfillment_names: Mapping[str, Sequence[str]],
    api_graph_function_config_id: UUID | None,
) -> tuple[Api, dict[str, UUID], dict[str, dict[str, UUID]], dict[UUID, BaseORMModel]]:
    normalized_api_name = (api_name or "").casefold().strip()
    if not normalized_api_name:
        raise RuntimeError("Api reference snapshot requires non-empty api_name")
    normalized_endpoint_refs = tuple(
        sorted(
            {(endpoint_ref or "").casefold().strip() for endpoint_ref in endpoint_refs}
        )
    )
    if not normalized_endpoint_refs or any(
        not endpoint_ref for endpoint_ref in normalized_endpoint_refs
    ):
        raise RuntimeError("Api reference snapshot requires endpoint refs")

    objects_by_id: dict[UUID, BaseORMModel] = {}
    endpoint_ids_by_ref: dict[str, UUID] = {}
    endpoint_function_ids_by_ref: dict[str, dict[str, UUID]] = {}
    api = _remember(
        objects_by_id,
        Api(
            id=stable_api_id(name=normalized_api_name),
            name=normalized_api_name,
            description=None,
        ),
    )
    capabilities_by_name: dict[str, ApiCapability] = {}
    api_graph: ApiGraph | None = None
    api_graph_functions_by_config_id: dict[UUID, ApiGraphFunction] = {}
    api_graph_capabilities_by_capability_id: dict[UUID, ApiGraphCapability] = {}
    api_graph_capability_functions_by_key: dict[
        tuple[UUID, UUID, str],
        ApiGraphCapabilityFunction,
    ] = {}
    for endpoint_ref in normalized_endpoint_refs:
        ref_api_name, capability_name, endpoint_name = _split_endpoint_ref(endpoint_ref)
        if ref_api_name != normalized_api_name:
            raise RuntimeError(
                "Api reference snapshot endpoint ref belongs to a different api: "
                f"api_name={normalized_api_name!r} endpoint_ref={endpoint_ref!r}"
            )
        capability = capabilities_by_name.get(capability_name)
        if capability is None:
            capability = _remember(
                objects_by_id,
                ApiCapability(
                    id=stable_api_capability_id(
                        api_id=api.id,
                        name=capability_name,
                    ),
                    api_id=api.id,
                    name=capability_name,
                    description=None,
                ),
            )
            capabilities_by_name[capability_name] = capability
            api.api_capabilities.append(capability)
        endpoint = _remember(
            objects_by_id,
            ApiCapabilityEndpoint(
                id=stable_api_capability_endpoint_id(
                    api_capability_id=capability.id,
                    name=endpoint_name,
                ),
                api_capability_id=capability.id,
                name=endpoint_name,
                description=None,
            ),
        )
        capability.api_capability_endpoints.append(endpoint)
        endpoint_ids_by_ref[endpoint_ref] = endpoint.id
        request_class_config_id = endpoint_request_class_config_ids.get(endpoint_ref)
        if request_class_config_id is not None:
            request_config = _remember(
                objects_by_id,
                ApiCapabilityEndpointRequestConfig(
                    id=stable_api_capability_endpoint_request_config_id(
                        api_capability_endpoint_id=endpoint.id,
                        class_config_id=request_class_config_id,
                    ),
                    api_capability_endpoint_id=endpoint.id,
                    class_config_id=request_class_config_id,
                    description=None,
                ),
            )
            endpoint.request_config = request_config

        fulfillment_names = tuple(
            sorted(
                {
                    (name or "").casefold().strip()
                    for name in endpoint_fulfillment_names.get(endpoint_ref, ())
                }
            )
        )
        if not fulfillment_names:
            continue
        if api_graph_function_config_id is None:
            raise RuntimeError(
                "Api reference snapshot fulfillment bindings require "
                "api_graph_function_config_id"
            )
        if api_graph is None:
            api_graph = _remember(
                objects_by_id,
                ApiGraph(
                    id=stable_api_graph_id(
                        api_id=api.id,
                        object_config_graph_id=object_config_graph_id,
                    ),
                    api_id=api.id,
                    object_config_graph_id=object_config_graph_id,
                    description=None,
                ),
            )
            api.api_graphs.append(api_graph)
        api_graph_function = api_graph_functions_by_config_id.get(
            api_graph_function_config_id
        )
        if api_graph_function is None:
            api_graph_function = _remember(
                objects_by_id,
                ApiGraphFunction(
                    id=stable_api_graph_function_id(
                        api_graph_id=api_graph.id,
                        class_config_function_config_id=api_graph_function_config_id,
                    ),
                    api_graph_id=api_graph.id,
                    class_config_function_config_id=api_graph_function_config_id,
                    description=None,
                ),
            )
            api_graph_functions_by_config_id[api_graph_function_config_id] = (
                api_graph_function
            )
            api_graph.api_graph_functions.append(api_graph_function)
        api_graph_capability = api_graph_capabilities_by_capability_id.get(
            capability.id
        )
        if api_graph_capability is None:
            api_graph_capability = _remember(
                objects_by_id,
                ApiGraphCapability(
                    id=stable_api_graph_capability_id(
                        api_graph_id=api_graph.id,
                        api_capability_id=capability.id,
                    ),
                    api_graph_id=api_graph.id,
                    api_capability_id=capability.id,
                    description=None,
                ),
            )
            api_graph_capabilities_by_capability_id[capability.id] = (
                api_graph_capability
            )
            api_graph.api_graph_capabilities.append(api_graph_capability)
        endpoint_function_ids: dict[str, UUID] = {}
        for fulfillment_name in fulfillment_names:
            graph_capability_function_key = (
                api_graph_capability.id,
                api_graph_function.id,
                fulfillment_name,
            )
            graph_capability_function = api_graph_capability_functions_by_key.get(
                graph_capability_function_key
            )
            if graph_capability_function is None:
                graph_capability_function = _remember(
                    objects_by_id,
                    ApiGraphCapabilityFunction(
                        id=stable_api_graph_capability_function_id(
                            api_graph_capability_id=api_graph_capability.id,
                            api_graph_function_id=api_graph_function.id,
                            name=fulfillment_name,
                        ),
                        api_graph_capability_id=api_graph_capability.id,
                        api_graph_function_id=api_graph_function.id,
                        name=fulfillment_name,
                        description=None,
                    ),
                )
                api_graph_capability_functions_by_key[graph_capability_function_key] = (
                    graph_capability_function
                )
                api_graph_capability.api_graph_capability_functions.append(
                    graph_capability_function
                )
            endpoint_function = _remember(
                objects_by_id,
                ApiCapabilityEndpointFunction(
                    id=stable_api_capability_endpoint_function_id(
                        api_capability_endpoint_id=endpoint.id,
                        api_graph_capability_function_id=graph_capability_function.id,
                        name=fulfillment_name,
                    ),
                    api_capability_endpoint_id=endpoint.id,
                    api_graph_capability_function_id=graph_capability_function.id,
                    name=fulfillment_name,
                    description=None,
                ),
            )
            endpoint.api_capability_endpoint_functions.append(endpoint_function)
            endpoint_function_ids[fulfillment_name] = endpoint_function.id
        endpoint_function_ids_by_ref[endpoint_ref] = endpoint_function_ids
    return api, endpoint_ids_by_ref, endpoint_function_ids_by_ref, objects_by_id


async def _load_api_package_before_oig(
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


def _api_package_manifest_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    api_package_id: UUID,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        _API_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
        f"{branch_id}:{projection_hash}:{api_package_id}:{graph_hash_post}",
    )


def _api_reference_snapshot_commit_id(
    *,
    branch_id: UUID,
    projection_hash: str,
    api_id: UUID,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        _API_REFERENCE_SNAPSHOT_COMMIT_NAMESPACE,
        f"{branch_id}:{projection_hash}:{api_id}:{graph_hash_post}",
    )


def _split_endpoint_ref(endpoint_ref: str) -> tuple[str, str, str]:
    parts = tuple(part.strip() for part in endpoint_ref.split("."))
    if len(parts) != 3 or any(not part for part in parts):
        raise RuntimeError(
            "Invalid API endpoint ref: expected <api>.<capability>.<endpoint>, "
            f"got {endpoint_ref!r}"
        )
    return parts


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TModel,
) -> _TModel:
    objects_by_id[obj.id] = obj
    return obj


__all__ = [
    "ApiPackageLanguagePackageSnapshotRef",
    "ApiPackageManifestSnapshotCommitResult",
    "ApiReferenceSnapshotCommitResult",
    "commit_api_reference_snapshot",
    "commit_api_package_manifest_snapshot",
]
