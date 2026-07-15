from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from aware_content.handlers._generated import meta_handlers as content_meta_handlers
from aware_code.handlers._generated import meta_handlers as code_meta_handlers
from aware_code.handlers.impl.code import code as code_handler
from aware_code.handlers.impl.code import code_section as code_section_handler
from aware_code.handlers.impl.code import code_test as code_test_handler
from aware_code.handlers.impl.code import (
    code_test_framework as code_test_framework_handler,
)
from aware_code.handlers.impl.code import code_test_unit as code_test_unit_handler
from aware_code.handlers.impl.code import (
    code_test_unit_run as code_test_unit_run_handler,
)
from aware_code.handlers.impl.annotation import (
    code_section_annotation as code_section_annotation_handler,
)
from aware_code.handlers.impl.import_ import (
    code_section_import as code_section_import_handler,
)
from aware_code.handlers.impl.import_ import (
    code_section_import_name as code_section_import_name_handler,
)
from aware_code.handlers.impl.module import code_module as code_module_handler
from aware_code.handlers.impl.package import code_package as code_package_handler
from aware_code.handlers.impl.package import (
    code_package_artifact as code_package_artifact_handler,
)
from aware_code.handlers.impl.package import (
    code_package_code as code_package_code_handler,
)
from aware_code.handlers.impl.package import (
    code_package_delta_producer as code_package_delta_producer_handler,
)
from aware_code.handlers.impl.package import (
    code_package_delta_producer_code as code_package_delta_producer_code_handler,
)
from aware_code.handlers.impl.package import (
    code_package_test as code_package_test_handler,
)
from aware_code.handlers.impl.package import (
    code_package_test_framework as code_package_test_framework_handler,
)
from aware_code.handlers.impl.package import (
    code_package_test_run as code_package_test_run_handler,
)
from aware_code.ontology.materialization import build_code_content_plan_from_text
from aware_code.package.test_execution import (
    CodePackageTestRunReceipt,
    CodePackageTestUnitRunReceipt,
    materialize_code_package_test_run_receipt,
)
from aware_code.semantic_contract_config import source_code_package_config_ref
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage, CodeTestRunStatus
from aware_code_ontology.code.code_plan import (
    CodeContentPlan,
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageDeltaProducerRef,
    CodePackageDeltaProduction,
    CodePackagePathRole,
)
from aware_code_ontology.code.code_section import CodeSection
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_code_ontology.code.code_test import CodeTest
from aware_code_ontology.code.code_test_framework import CodeTestFramework
from aware_code_ontology.code.code_test_unit import CodeTestUnit
from aware_code_ontology.code.code_test_unit_run import CodeTestUnitRun
from aware_code_ontology.module.code_module import CodeModule
from aware_code_ontology.module.code_module_code_package import CodeModuleCodePackage
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_artifact import CodePackageArtifact
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_code_ontology.package.code_package_delta_producer import (
    CodePackageDeltaProducer,
)
from aware_code_ontology.package.code_package_delta_producer_code import (
    CodePackageDeltaProducerCode,
)
from aware_code_ontology.package.code_package_test import CodePackageTest
from aware_code_ontology.package.code_package_test_framework import (
    CodePackageTestFramework,
)
from aware_code_ontology.package.code_package_test_run import CodePackageTestRun
from aware_code_ontology.package.code_package_enums import CodePackageArtifactStatus
from aware_code.stable_ids import (
    stable_code_id,
    stable_code_module_code_package_id,
    stable_code_module_id,
    stable_code_package_artifact_id,
    stable_code_package_code_id,
    stable_code_package_id,
    stable_code_package_test_framework_id,
    stable_code_package_test_id,
    stable_code_package_test_run_id,
    stable_code_section_annotation_id,
    stable_code_section_id,
    stable_code_section_import_id,
    stable_code_section_import_name_id,
    stable_code_test_framework_id,
    stable_code_test_id,
    stable_code_test_unit_id,
    stable_code_test_unit_run_id,
)
from aware_code_ontology.annotation.code_section_annotation import CodeSectionAnnotation
from aware_code_ontology.import_.code_section_import import CodeSectionImport
from aware_code_ontology.import_.code_section_import_name import CodeSectionImportName
from aware_content.handlers.impl.part import (
    content_part_text as content_part_text_handler,
)
from aware_content.handlers.impl.part import (
    content_part_text_segment as content_part_text_segment_handler,
)
from aware_content_ontology.part.content_part_text import ContentPartText
from aware_content_ontology.part.content_part_text_segment import ContentPartTextSegment
from aware_meta.handlers._generated import meta_handlers as meta_meta_handlers
from aware_meta.runtime import (
    MetaGraphFunctionImplOwnership,
    MetaGraphImplementationPolicy,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot,
    materialize_meta_runtime_lane_head,
)
from aware_orm.runtime.invocation import (
    reset_invocation_provider,
    set_invocation_provider,
)
from aware_orm.session.change_collector import scoped_change_collection
from aware_orm.session.current_session_ctx import current_session, set_session
from aware_orm.session.session import Session
from _code_runtime_test_paths import CODE_PACKAGE_MANIFEST_PATHS, REPO_ROOT


def _code_package_manifest_paths(repo_root):
    assert repo_root == REPO_ROOT
    return CODE_PACKAGE_MANIFEST_PATHS


def _build_code_meta_runtime(
    *,
    repo_root,
    aware_root,
) -> MetaGraphRuntime:
    CodeContentPlan.model_rebuild()
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_code_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            code_meta_handlers,
            content_meta_handlers,
            meta_meta_handlers,
        ),
        bootstrap_modules=(
            code_meta_handlers,
            content_meta_handlers,
            meta_meta_handlers,
        ),
        implementation_policy=MetaGraphImplementationPolicy(
            default_function_impl_ownership=MetaGraphFunctionImplOwnership.authored,
        ),
    )
    assert runtime.context is not None
    return runtime


def _ensure_source_code_package_config_ref(
    *,
    manifest_kind: str,
    surface: str,
    manifest_relative_path: str,
):
    config_ref = source_code_package_config_ref(
        manifest_kind=manifest_kind,
        surface=surface,
    )
    session = current_session()
    if session is not None and not session.imap_contains(
        CodePackageConfig,
        config_ref.config_id,
    ):
        session.imap_add(
            CodePackageConfig(
                id=config_ref.config_id,
                config_key=config_ref.config_key,
                provider_key="aware_code",
                semantic_owner="aware_code.provider",
                contract="aware.code",
                package_role="aware_code.provider",
                manifest_kind=config_ref.manifest_kind,
                manifest_filename=manifest_relative_path.rsplit("/", 1)[-1],
                semantic_package_family="code",
                semantic_package_kind="code_package",
                semantic_projection_name="CodePackage",
                semantic_root_kind="code_package",
                default_surface=config_ref.surface,
                materialization_capability=None,
            )
        )
    return config_ref


async def _build_code_package(
    *,
    package_name: str,
    language: CodeLanguage,
    surface: str,
    manifest_kind: str,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None = None,
    fqn_prefix: str | None = None,
) -> CodePackage:
    config_ref = _ensure_source_code_package_config_ref(
        manifest_kind=manifest_kind,
        surface=surface,
        manifest_relative_path=manifest_relative_path,
    )
    return await CodePackage.build_via_code_package_config(
        code_package_config_id=config_ref.config_id,
        package_name=package_name,
        language=language,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        fqn_prefix=fqn_prefix,
        surface=surface,
    )


async def _read_code_text(
    code_package: CodePackage,
    *,
    relative_path: str,
) -> str:
    normalized_relative_path = (relative_path or "").strip()
    for edge in code_package.code_package_codes:
        if (edge.relative_path or "").strip() != normalized_relative_path:
            continue
        code = edge.code
        if code is None or code.content_part_text is None:
            break
        return code.content_part_text.inline_text or ""
    raise ValueError(
        "missing package-owned code: "
        f"package={code_package.package_name} relative_path={relative_path}"
    )


class _LocalInvocationProvider:
    async def invoke_instance(
        self, *, orm_model, function_name: str, payload
    ):  # noqa: ANN001
        if isinstance(orm_model, CodePackage):
            if function_name == "create_code":
                return await code_package_handler.create_code(
                    orm_model,
                    relative_path=payload["relative_path"],
                    plan=payload["plan"],
                    path_role=payload.get(
                        "path_role", CodePackagePathRole.authored_source
                    ),
                    delta_production=payload.get("delta_production"),
                )
            if function_name == "upsert_code":
                return await code_package_handler.upsert_code(
                    orm_model,
                    relative_path=payload["relative_path"],
                    plan=payload["plan"],
                    path_role=payload.get(
                        "path_role", CodePackagePathRole.authored_source
                    ),
                    delta_production=payload.get("delta_production"),
                )
            if function_name == "upsert_delta_producer":
                return await code_package_handler.upsert_delta_producer(
                    orm_model,
                    provider_key=payload["provider_key"],
                    producer_key=payload["producer_key"],
                    producer_kind=payload.get("producer_kind"),
                    provider_payload=payload.get("provider_payload"),
                )
            if function_name == "read_code_text":
                return await code_package_handler.read_code_text(
                    orm_model,
                    relative_path=payload["relative_path"],
                )
            if function_name == "delete_code":
                return await code_package_handler.delete_code(
                    orm_model,
                    relative_path=payload["relative_path"],
                )
            if function_name == "create_code_from_text":
                return await code_package_handler.create_code_from_text(
                    orm_model,
                    relative_path=payload["relative_path"],
                    content_text=payload["content_text"],
                    language=payload.get("language"),
                )
            if function_name == "upsert_code_from_text":
                return await code_package_handler.upsert_code_from_text(
                    orm_model,
                    relative_path=payload["relative_path"],
                    content_text=payload["content_text"],
                    language=payload.get("language"),
                )
            if function_name == "upsert_codes_from_text":
                return await code_package_handler.upsert_codes_from_text(
                    orm_model,
                    relative_paths=payload["relative_paths"],
                    content_texts=payload["content_texts"],
                    language=payload.get("language"),
                )
            if function_name == "apply_delta":
                return await code_package_handler.apply_delta(
                    orm_model,
                    delta=payload["delta"],
                )
            if function_name == "sync_tests":
                return await code_package_handler.sync_tests(
                    orm_model,
                    manifest_text=payload.get("manifest_text"),
                )
            if function_name == "attach_test_framework":
                return await code_package_handler.attach_test_framework(
                    orm_model,
                    framework_id=payload["framework_id"],
                    declaration_kind=payload.get("declaration_kind", "unknown"),
                    declaration_ref=payload.get("declaration_ref"),
                )
            if function_name == "attach_test":
                return await code_package_handler.attach_test(
                    orm_model,
                    code_test_id=payload["code_test_id"],
                    relative_path=payload["relative_path"],
                )
            if function_name == "attach_artifact":
                return await code_package_handler.attach_artifact(
                    orm_model,
                    output_key=payload["output_key"],
                    artifact_key=payload["artifact_key"],
                    status=payload.get("status", CodePackageArtifactStatus.available),
                    artifact_family=payload.get("artifact_family"),
                    artifact_role=payload.get("artifact_role"),
                    required_for=payload.get("required_for", []),
                    producer_key=payload.get("producer_key"),
                    producer_kind=payload.get("producer_kind"),
                    materialization_index=payload.get("materialization_index"),
                    source_code_package_id=payload.get("source_code_package_id"),
                    source_object_instance_graph_commit_id=payload.get(
                        "source_object_instance_graph_commit_id"
                    ),
                    input_code_package_id=payload.get("input_code_package_id"),
                    input_object_instance_graph_commit_id=payload.get(
                        "input_object_instance_graph_commit_id"
                    ),
                    digest=payload.get("digest"),
                    relative_path=payload.get("relative_path"),
                    uri=payload.get("uri"),
                    media_type=payload.get("media_type"),
                    runtime_contract_version=payload.get("runtime_contract_version"),
                    provider_payload=payload.get("provider_payload"),
                    receipt_payload=payload.get("receipt_payload"),
                    error=payload.get("error"),
                )
        if isinstance(orm_model, CodePackageCode):
            if function_name == "update_path_role":
                return await code_package_code_handler.update_path_role(
                    orm_model,
                    path_role=payload["path_role"],
                )
            if function_name == "sync_test_unit":
                return await code_package_code_handler.sync_test_unit(
                    orm_model,
                    framework_id=payload["framework_id"],
                    code_section_id=payload["code_section_id"],
                    unit_key=payload["unit_key"],
                    selector=payload["selector"],
                    kind=payload.get("kind", "function"),
                    name=payload.get("name"),
                    discovery_kind=payload.get("discovery_kind", "language_plugin"),
                    selector_prefix=payload.get("selector_prefix"),
                )
            if function_name == "delete":
                return await code_package_code_handler.delete(orm_model)
        if isinstance(orm_model, CodePackageDeltaProducer):
            if function_name == "link_code":
                return await code_package_delta_producer_handler.link_code(
                    orm_model,
                    code_package_code_id=payload["code_package_code_id"],
                    input_code_package_id=payload.get("input_code_package_id"),
                    input_object_instance_graph_commit_id=payload.get(
                        "input_object_instance_graph_commit_id"
                    ),
                    input_digest=payload.get("input_digest"),
                    output_digest=payload.get("output_digest"),
                    emission_payload=payload.get("emission_payload"),
                )
        if isinstance(orm_model, CodeModule):
            if function_name == "attach_package":
                return await code_module_handler.attach_package(
                    orm_model,
                    code_package_id=payload["code_package_id"],
                    module_package_id=payload.get("module_package_id"),
                    module_package_kind=payload.get("module_package_kind"),
                    module_relative_package_root=payload.get(
                        "module_relative_package_root"
                    ),
                    manifest_relative_path=payload.get("manifest_relative_path"),
                    visibility=payload.get("visibility", "module"),
                    semantic_contract_role=payload.get("semantic_contract_role"),
                    semantic_contract_name=payload.get("semantic_contract_name"),
                    semantic_contract_provider_key=payload.get(
                        "semantic_contract_provider_key"
                    ),
                    semantic_contract_module=payload.get("semantic_contract_module"),
                    semantic_contract_owns_manifest_kinds=payload.get(
                        "semantic_contract_owns_manifest_kinds", []
                    ),
                    semantic_contract_capabilities=payload.get(
                        "semantic_contract_capabilities", []
                    ),
                    mirrors_ontology=payload.get("mirrors_ontology", False),
                )
        if isinstance(orm_model, Code):
            if function_name == "delete":
                return await code_handler.delete(orm_model)
            if function_name == "apply_content_plan":
                return await code_handler.apply_content_plan(
                    orm_model,
                    plan=payload["plan"],
                )
            if function_name == "create_section":
                return await code_handler.create_section(
                    orm_model,
                    section_key=payload["section_key"],
                    qualname=payload["qualname"],
                    type=payload["type"],
                    identity_hash=payload["identity_hash"],
                    byte_start=payload["byte_start"],
                    byte_end=payload["byte_end"],
                    metadata=payload.get("metadata"),
                )
            if function_name == "create_test":
                return await code_handler.create_test(
                    orm_model,
                    framework_id=payload["framework_id"],
                    discovery_kind=payload.get("discovery_kind", "language_plugin"),
                    selector_prefix=payload.get("selector_prefix"),
                )
            if function_name == "sync_test_unit":
                return await code_handler.sync_test_unit(
                    orm_model,
                    framework_id=payload["framework_id"],
                    code_section_id=payload["code_section_id"],
                    unit_key=payload["unit_key"],
                    selector=payload["selector"],
                    kind=payload.get("kind", "function"),
                    name=payload.get("name"),
                    discovery_kind=payload.get("discovery_kind", "language_plugin"),
                    selector_prefix=payload.get("selector_prefix"),
                )
            if function_name == "replace_content":
                return await code_handler.replace_content(
                    orm_model,
                    content_text=payload["content_text"],
                    language=payload.get("language"),
                )
        if isinstance(orm_model, CodeTest):
            if function_name == "create_unit":
                return await code_test_handler.create_unit(
                    orm_model,
                    code_section_id=payload["code_section_id"],
                    unit_key=payload["unit_key"],
                    selector=payload["selector"],
                    kind=payload.get("kind", "function"),
                    name=payload.get("name"),
                )
        if isinstance(orm_model, CodePackageTest):
            if function_name == "create_run":
                return await code_package_test_handler.create_run(
                    orm_model,
                    run_key=payload["run_key"],
                    backend_kind=payload["backend_kind"],
                    status=payload["status"],
                    started_at_utc=payload.get("started_at_utc"),
                    finished_at_utc=payload.get("finished_at_utc"),
                    duration_s=payload.get("duration_s"),
                    selected_unit_count=payload.get("selected_unit_count", 0),
                    total_tests=payload.get("total_tests", 0),
                    passed_tests=payload.get("passed_tests", 0),
                    failed_tests=payload.get("failed_tests", 0),
                    skipped_tests=payload.get("skipped_tests", 0),
                    unsupported_tests=payload.get("unsupported_tests", 0),
                    error=payload.get("error"),
                )
        if isinstance(orm_model, CodePackageTestRun):
            if function_name == "create_unit_run":
                return await code_package_test_run_handler.create_unit_run(
                    orm_model,
                    code_test_unit_id=payload["code_test_unit_id"],
                    status=payload["status"],
                    selector=payload["selector"],
                    duration_s=payload.get("duration_s"),
                    failures=payload.get("failures", []),
                    error=payload.get("error"),
                )
        if isinstance(orm_model, ContentPartText):
            if function_name == "delete":
                return await content_part_text_handler.delete(orm_model)
            if function_name == "apply_editor_patch":
                return await content_part_text_handler.apply_editor_patch(
                    orm_model,
                    patch=payload["patch"],
                )
            if function_name == "set_inline_text":
                return await content_part_text_handler.set_inline_text(
                    orm_model,
                    inline_text=payload["inline_text"],
                )
        if isinstance(orm_model, CodeSection):
            if function_name == "create_annotation":
                return await code_section_handler.create_annotation(
                    orm_model,
                    path=payload["path"],
                    verb=payload["verb"],
                    args=payload["args"],
                )
            if function_name == "create_import":
                return await code_section_handler.create_import(
                    orm_model,
                    module_text=payload["module_text"],
                    is_from_import=payload["is_from_import"],
                    is_star_import=payload.get("is_star_import", False),
                    relative_level=payload.get("relative_level", 0),
                    module_slot_key=payload["module_slot_key"],
                    module_byte_start=payload["module_byte_start"],
                    module_byte_end=payload["module_byte_end"],
                )
            if function_name == "delete":
                return await code_section_handler.delete(orm_model)
        if isinstance(orm_model, CodeSectionAnnotation):
            if function_name == "delete":
                return await code_section_annotation_handler.delete(orm_model)
        if isinstance(orm_model, CodeSectionImport):
            if function_name == "create_name":
                return await code_section_import_handler.create_name(
                    orm_model,
                    name_text=payload["name_text"],
                    alias_text=payload.get("alias_text"),
                    name_slot_key=payload["name_slot_key"],
                    name_byte_start=payload["name_byte_start"],
                    name_byte_end=payload["name_byte_end"],
                    alias_slot_key=payload.get("alias_slot_key"),
                    alias_byte_start=payload.get("alias_byte_start"),
                    alias_byte_end=payload.get("alias_byte_end"),
                )
            if function_name == "delete":
                return await code_section_import_handler.delete(orm_model)
        if isinstance(orm_model, CodeSectionImportName):
            if function_name == "delete":
                return await code_section_import_name_handler.delete(orm_model)
        if isinstance(orm_model, ContentPartTextSegment):
            if function_name == "delete_segment":
                return await content_part_text_segment_handler.delete_segment(orm_model)
        raise NotImplementedError(
            f"Unsupported local instance invocation: {type(orm_model).__name__}.{function_name}"
        )

    async def invoke_constructor(
        self, *, orm_class, function_name: str, payload
    ):  # noqa: ANN001
        if (
            orm_class is CodePackage
            and function_name == "build_via_code_package_config"
        ):
            return await code_package_handler.build_via_code_package_config(
                code_package_config_id=payload["code_package_config_id"],
                package_name=payload["package_name"],
                language=payload["language"],
                manifest_relative_path=payload["manifest_relative_path"],
                package_root=payload["package_root"],
                sources_root=payload.get("sources_root"),
                fqn_prefix=payload.get("fqn_prefix"),
                surface=payload.get("surface"),
            )
        if orm_class is CodePackageCode and function_name == "create_via_code_package":
            from aware_code.handlers.impl.package import (
                code_package_code as code_package_code_handler,
            )

            return await code_package_code_handler.create_via_code_package(
                code_package_id=payload["code_package_id"],
                relative_path=payload["relative_path"],
                plan=payload["plan"],
                path_role=payload.get("path_role", CodePackagePathRole.authored_source),
                delta_production=payload.get("delta_production"),
            )
        if orm_class is Code and function_name == "create_via_code_package_code":
            return await code_handler.create_via_code_package_code(
                code_package_code_id=payload["code_package_code_id"],
                relative_path=payload["relative_path"],
                plan=payload["plan"],
            )
        if (
            orm_class is CodePackageDeltaProducer
            and function_name == "build_via_code_package"
        ):
            return await code_package_delta_producer_handler.build_via_code_package(
                code_package_id=payload["code_package_id"],
                provider_key=payload["provider_key"],
                producer_key=payload["producer_key"],
                producer_kind=payload.get("producer_kind"),
                provider_payload=payload.get("provider_payload"),
            )
        if (
            orm_class is CodePackageArtifact
            and function_name == "build_via_code_package"
        ):
            return await code_package_artifact_handler.build_via_code_package(
                code_package_id=payload["code_package_id"],
                output_key=payload["output_key"],
                artifact_key=payload["artifact_key"],
                status=payload.get("status", CodePackageArtifactStatus.available),
                artifact_family=payload.get("artifact_family"),
                artifact_role=payload.get("artifact_role"),
                required_for=payload.get("required_for", []),
                producer_key=payload.get("producer_key"),
                producer_kind=payload.get("producer_kind"),
                materialization_index=payload.get("materialization_index"),
                source_code_package_id=payload.get("source_code_package_id"),
                source_object_instance_graph_commit_id=payload.get(
                    "source_object_instance_graph_commit_id"
                ),
                input_code_package_id=payload.get("input_code_package_id"),
                input_object_instance_graph_commit_id=payload.get(
                    "input_object_instance_graph_commit_id"
                ),
                digest=payload.get("digest"),
                relative_path=payload.get("relative_path"),
                uri=payload.get("uri"),
                media_type=payload.get("media_type"),
                runtime_contract_version=payload.get("runtime_contract_version"),
                provider_payload=payload.get("provider_payload"),
                receipt_payload=payload.get("receipt_payload"),
                error=payload.get("error"),
            )
        if (
            orm_class is CodePackageDeltaProducerCode
            and function_name == "build_via_code_package_delta_producer"
        ):
            return await code_package_delta_producer_code_handler.build_via_code_package_delta_producer(
                code_package_delta_producer_id=payload[
                    "code_package_delta_producer_id"
                ],
                code_package_code_id=payload["code_package_code_id"],
                input_code_package_id=payload.get("input_code_package_id"),
                input_object_instance_graph_commit_id=payload.get(
                    "input_object_instance_graph_commit_id"
                ),
                input_digest=payload.get("input_digest"),
                output_digest=payload.get("output_digest"),
                emission_payload=payload.get("emission_payload"),
            )
        if orm_class is CodeModule and function_name == "build":
            return await code_module_handler.build(
                name=payload["name"],
                languages=payload["languages"],
                aware_module_version=payload.get("aware_module_version", 1),
                manifest_relative_path=payload.get(
                    "manifest_relative_path", "aware.module.toml"
                ),
                manifest_hash=payload.get("manifest_hash"),
            )
        if orm_class is ContentPartText and function_name == "create_content_part_text":
            return await content_part_text_handler.create_content_part_text(
                key=payload.get("key", "default"),
                inline_text=payload.get("inline_text"),
            )
        if orm_class is ContentPartTextSegment and function_name in {
            "upsert",
            "upsert_via_content_part_text",
        }:
            return await content_part_text_segment_handler.upsert(
                segment_id=payload.get("segment_id"),
                content_part_text_id=payload.get("content_part_text_id"),
                byte_start=payload.get("byte_start"),
                byte_end=payload.get("byte_end"),
                style_id=payload.get("style_id"),
                parent_id=payload.get("parent_id"),
            )
        if orm_class is CodeSection and function_name == "build_via_code":
            return await code_section_handler.build_via_code(
                code_id=payload["code_id"],
                section_key=payload["section_key"],
                qualname=payload["qualname"],
                type=payload["type"],
                identity_hash=payload["identity_hash"],
                byte_start=payload["byte_start"],
                byte_end=payload["byte_end"],
                metadata=payload.get("metadata"),
            )
        if orm_class is CodeTest and function_name == "build_via_code":
            return await code_test_handler.build_via_code(
                code_id=payload["code_id"],
                framework_id=payload["framework_id"],
                discovery_kind=payload.get("discovery_kind", "language_plugin"),
                selector_prefix=payload.get("selector_prefix"),
            )
        if orm_class is CodeTestFramework and function_name == "build":
            return await code_test_framework_handler.build(
                name=payload["name"],
                title=payload.get("title"),
            )
        if orm_class is CodeTestUnit and function_name == "build_via_code_test":
            return await code_test_unit_handler.build_via_code_test(
                code_test_id=payload["code_test_id"],
                code_section_id=payload["code_section_id"],
                unit_key=payload["unit_key"],
                selector=payload["selector"],
                kind=payload.get("kind", "function"),
                name=payload.get("name"),
            )
        if (
            orm_class is CodePackageTestFramework
            and function_name == "build_via_code_package"
        ):
            return await code_package_test_framework_handler.build_via_code_package(
                code_package_id=payload["code_package_id"],
                code_test_framework_id=payload["code_test_framework_id"],
                declaration_kind=payload.get("declaration_kind", "unknown"),
                declaration_ref=payload.get("declaration_ref"),
            )
        if orm_class is CodePackageTest and function_name == "build_via_code_package":
            return await code_package_test_handler.build_via_code_package(
                code_package_id=payload["code_package_id"],
                code_test_id=payload["code_test_id"],
                relative_path=payload["relative_path"],
            )
        if (
            orm_class is CodePackageTestRun
            and function_name == "build_via_code_package_test"
        ):
            return await code_package_test_run_handler.build_via_code_package_test(
                code_package_test_id=payload["code_package_test_id"],
                run_key=payload["run_key"],
                backend_kind=payload["backend_kind"],
                status=payload["status"],
                started_at_utc=payload.get("started_at_utc"),
                finished_at_utc=payload.get("finished_at_utc"),
                duration_s=payload.get("duration_s"),
                selected_unit_count=payload.get("selected_unit_count", 0),
                total_tests=payload.get("total_tests", 0),
                passed_tests=payload.get("passed_tests", 0),
                failed_tests=payload.get("failed_tests", 0),
                skipped_tests=payload.get("skipped_tests", 0),
                unsupported_tests=payload.get("unsupported_tests", 0),
                error=payload.get("error"),
            )
        if (
            orm_class is CodeTestUnitRun
            and function_name == "build_via_code_package_test_run"
        ):
            return await code_test_unit_run_handler.build_via_code_package_test_run(
                code_package_test_run_id=payload["code_package_test_run_id"],
                code_test_unit_id=payload["code_test_unit_id"],
                status=payload["status"],
                selector=payload["selector"],
                duration_s=payload.get("duration_s"),
                failures=payload.get("failures", []),
                error=payload.get("error"),
            )
        if (
            orm_class is CodeSectionAnnotation
            and function_name == "build_via_code_section"
        ):
            from aware_code.handlers.impl.annotation import (
                code_section_annotation as annotation_handler,
            )

            return await annotation_handler.build_via_code_section(
                code_section_id=payload["code_section_id"],
                path=payload["path"],
                verb=payload["verb"],
                args=payload["args"],
            )
        if orm_class is CodeSectionImport and function_name == "build_via_code_section":
            return await code_section_import_handler.build_via_code_section(
                code_section_id=payload["code_section_id"],
                module_text=payload["module_text"],
                is_from_import=payload["is_from_import"],
                is_star_import=payload.get("is_star_import", False),
                relative_level=payload.get("relative_level", 0),
                module_slot_key=payload["module_slot_key"],
                module_byte_start=payload["module_byte_start"],
                module_byte_end=payload["module_byte_end"],
            )
        if (
            orm_class is CodeSectionImportName
            and function_name == "build_via_code_section_import"
        ):
            return await code_section_import_name_handler.build_via_code_section_import(
                code_section_import_id=payload["code_section_import_id"],
                name_text=payload["name_text"],
                alias_text=payload.get("alias_text"),
                name_slot_key=payload["name_slot_key"],
                name_byte_start=payload["name_byte_start"],
                name_byte_end=payload["name_byte_end"],
                alias_slot_key=payload.get("alias_slot_key"),
                alias_byte_start=payload.get("alias_byte_start"),
                alias_byte_end=payload.get("alias_byte_end"),
            )
        if (
            orm_class is CodeModuleCodePackage
            and function_name == "build_via_code_module"
        ):
            from aware_code.handlers.impl.module import (
                code_module_code_package as code_module_code_package_handler,
            )

            return await code_module_code_package_handler.build_via_code_module(
                code_module_id=payload["code_module_id"],
                code_package_id=payload["code_package_id"],
                module_package_id=payload.get("module_package_id"),
                module_package_kind=payload.get("module_package_kind"),
                module_relative_package_root=payload.get(
                    "module_relative_package_root"
                ),
                manifest_relative_path=payload.get("manifest_relative_path"),
                visibility=payload.get("visibility", "module"),
                semantic_contract_role=payload.get("semantic_contract_role"),
                semantic_contract_name=payload.get("semantic_contract_name"),
                semantic_contract_provider_key=payload.get(
                    "semantic_contract_provider_key"
                ),
                semantic_contract_module=payload.get("semantic_contract_module"),
                semantic_contract_owns_manifest_kinds=payload.get(
                    "semantic_contract_owns_manifest_kinds", []
                ),
                semantic_contract_capabilities=payload.get(
                    "semantic_contract_capabilities", []
                ),
                mirrors_ontology=payload.get("mirrors_ontology", False),
            )
        raise NotImplementedError(
            f"Unsupported local constructor invocation: {orm_class.__name__}.{function_name}"
        )


def _ids_by_class_name(assertions) -> dict[str, list[UUID]]:  # noqa: ANN001
    class_name_by_id = {
        cc_id: cc.name for cc_id, cc in assertions._class_configs_by_id.items()
    }
    ids_by_class_name: dict[str, list[UUID]] = {}
    for ci in assertions.oig.class_instances:
        if ci.id is None:
            continue
        class_name = class_name_by_id.get(ci.class_config_id)
        if class_name is None:
            continue
        ids_by_class_name.setdefault(class_name, []).append(UUID(str(ci.id)))
    return ids_by_class_name


def _class_instance_id_for_source(
    *, assertions, source_object_id: UUID
) -> UUID:  # noqa: ANN001
    for class_instance in assertions.oig.class_instances:
        if (
            class_instance.source_object_id == source_object_id
            and class_instance.id is not None
        ):
            return UUID(str(class_instance.id))
    raise AssertionError(
        f"Missing ClassInstance for source_object_id={source_object_id}"
    )


def _committed_oig_class_pair_counts(
    *, index, oig
) -> Counter[tuple[str, str]]:  # noqa: ANN001
    ci_by_id = {ci.id: ci for ci in oig.class_instances}
    cc_by_id = index.class_configs_by_id
    pair_counts: Counter[tuple[str, str]] = Counter()
    for rel in oig.class_instance_relationships:
        src = ci_by_id.get(rel.source_class_instance_id)
        tgt = ci_by_id.get(rel.target_class_instance_id)
        if src is None or tgt is None:
            continue
        pair_counts[
            (cc_by_id[src.class_config_id].name, cc_by_id[tgt.class_config_id].name)
        ] += 1
    return pair_counts


@pytest.mark.asyncio
async def test_code_package_attach_artifact_is_package_owned(monkeypatch) -> None:
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_package_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_package_artifact_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_artifact_runtime",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_artifact",
                )

                artifact = await code_package.attach_artifact(
                    output_key=" Runtime Bundle ",
                    artifact_key=" DIST/demo.whl ",
                    status="available",
                    artifact_family=" python ",
                    artifact_role=" wheel ",
                    required_for=["runtime", "sdk"],
                    producer_key=" aware-dev ",
                    producer_kind=" workspace_materialize ",
                    materialization_index=3,
                    source_code_package_id=code_package.id,
                    input_code_package_id=code_package.id,
                    digest=" sha256:first ",
                    relative_path=" dist/demo.whl ",
                    uri=" file://dist/demo.whl ",
                    media_type=" application/zip ",
                    runtime_contract_version=" v1 ",
                    provider_payload={"invocation_id": "demo"},
                    receipt_payload={"status": "succeeded"},
                )

                expected_artifact_id = stable_code_package_artifact_id(
                    code_package_id=code_package.id,
                    output_key="Runtime Bundle",
                    artifact_key="DIST/demo.whl",
                )
                assert artifact.id == expected_artifact_id
                assert artifact.code_package_id == code_package.id
                assert artifact.output_key == "Runtime Bundle"
                assert artifact.artifact_key == "DIST/demo.whl"
                assert artifact.status == CodePackageArtifactStatus.available
                assert artifact.artifact_family == "python"
                assert artifact.artifact_role == "wheel"
                assert artifact.required_for == ["runtime", "sdk"]
                assert artifact.producer_key == "aware-dev"
                assert artifact.producer_kind == "workspace_materialize"
                assert artifact.materialization_index == 3
                assert artifact.source_code_package_id == code_package.id
                assert artifact.input_code_package_id == code_package.id
                assert artifact.digest == "sha256:first"
                assert artifact.relative_path == "dist/demo.whl"
                assert artifact.uri == "file://dist/demo.whl"
                assert artifact.media_type == "application/zip"
                assert artifact.runtime_contract_version == "v1"
                assert artifact.provider_payload == {"invocation_id": "demo"}
                assert artifact.receipt_payload == {"status": "succeeded"}
                assert code_package.artifacts == [artifact]
                assert session.imap_get(CodePackageArtifact, expected_artifact_id) is artifact

                updated = await code_package.attach_artifact(
                    output_key=" Runtime Bundle ",
                    artifact_key=" DIST/demo.whl ",
                    status=CodePackageArtifactStatus.stale,
                    digest="sha256:updated",
                    receipt_payload={"status": "stale"},
                )

                assert updated is artifact
                assert len(code_package.artifacts) == 1
                assert artifact.status == CodePackageArtifactStatus.stale
                assert artifact.digest == "sha256:updated"
                assert artifact.receipt_payload == {"status": "stale"}
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_create_code_and_replace_content_via_local_provider(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_delta_producer_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_delta_producer_code_handler,
        "current_handler_session",
        lambda: session,
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_direct_package",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_direct",
                )
                attached = await code_package.create_code(
                    relative_path="src/main.aware",
                    plan=build_code_content_plan_from_text(
                        content_text="class A {}",
                        language=CodeLanguage.aware,
                    ),
                )
                code = attached.code

                expected_package_id = stable_code_package_id(
                    code_package_config_id=source_code_package_config_ref(
                        manifest_kind="aware_toml",
                        surface="runtime",
                    ).config_id,
                    package_name="aware_direct_package",
                    language=CodeLanguage.aware,
                )
                expected_attachment_id = stable_code_package_code_id(
                    code_package_id=expected_package_id,
                    relative_path="src/main.aware",
                )
                expected_code_id = stable_code_id(
                    code_package_code_id=expected_attachment_id,
                    relative_path="src/main.aware",
                )
                assert code_package.id == expected_package_id
                assert attached.id == expected_attachment_id
                assert code.id == expected_code_id
                assert code.relative_path == "src/main.aware"
                assert code.content_part_text.inline_text == "class A {}"
                assert len(code.code_sections) == 1

                first_section = code.code_sections[0]
                first_section_id = stable_code_section_id(
                    code_id=code.id,
                    section_key="A",
                    type="class",
                )
                assert first_section.id == first_section_id
                assert first_section.content_part_text_segment.byte_start == 0

                await code.replace_content(
                    content_text="class B {}",
                    language=CodeLanguage.aware,
                )

                assert code.language == CodeLanguage.aware
                assert code.content_part_text.inline_text == "class B {}"
                assert len(code.code_sections) == 1
                assert session.imap_get(CodeSection, first_section_id) is None

                replaced_section = code.code_sections[0]
                expected_replaced_id = stable_code_section_id(
                    code_id=code.id,
                    section_key="B",
                    type="class",
                )
                assert replaced_section.id == expected_replaced_id
                assert replaced_section.section_key == "B"
                assert replaced_section.qualname == "B"
                assert replaced_section.content_part_text_segment.byte_start == 0
                assert replaced_section.content_part_text_segment.byte_end == len(
                    "class B {}".encode("utf-8")
                )
                assert len(code.content_part_text.segments) == 1
                assert (
                    code.content_part_text.segments[0].id
                    == replaced_section.content_part_text_segment.id
                )
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_test_surface_and_unit_are_section_backed(monkeypatch) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(code_test_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_test_framework_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_test_unit_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_python_test_package",
                    language=CodeLanguage.python,
                    surface="runtime",
                    manifest_kind="pyproject_toml",
                    manifest_relative_path="pyproject.toml",
                    package_root=".",
                    sources_root=".",
                    fqn_prefix="aware_python_test",
                )
                attached = await code_package.upsert_code_from_text(
                    relative_path="tests/test_demo.py",
                    content_text="def test_demo():\n    assert True\n",
                    language=None,
                )
                code = attached.code
                function_section = next(
                    section
                    for section in code.code_sections
                    if section.type is CodeSectionType.function
                )
                framework = await CodeTestFramework.build(name="pytest", title="pytest")

                code_test = await code.create_test(
                    framework_id=framework.id,
                    selector_prefix="tests/test_demo.py",
                )
                unit = await code_test.create_unit(
                    code_section_id=function_section.id,
                    unit_key="pytest:tests/test_demo.py:test_demo",
                    selector="tests/test_demo.py::test_demo",
                    kind="function",
                    name="test_demo",
                )

                assert framework.id == stable_code_test_framework_id(name="pytest")
                assert code_test.id == stable_code_test_id(
                    code_id=code.id,
                    framework_id=framework.id,
                )
                assert unit.id == stable_code_test_unit_id(
                    code_test_id=code_test.id,
                    code_section_id=function_section.id,
                    unit_key="pytest:tests/test_demo.py:test_demo",
                )
                assert code.tests == [code_test]
                assert code_test.framework is framework
                assert code_test.units == [unit]
                assert unit.code_section is function_section
                assert unit.unit_key == "pytest:tests/test_demo.py:test_demo"
                assert unit.selector == "tests/test_demo.py::test_demo"
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_sync_tests_discovers_python_pytest_units(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(code_test_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_test_framework_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_test_unit_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_test_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_test_framework_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_python_discovery_package",
                    language=CodeLanguage.python,
                    surface="runtime",
                    manifest_kind="pyproject_toml",
                    manifest_relative_path="pyproject.toml",
                    package_root=".",
                    sources_root=".",
                    fqn_prefix="aware_python_discovery",
                )
                attached = await code_package.upsert_code_from_text(
                    relative_path="tests/test_demo.py",
                    content_text="def test_demo():\n    assert True\n",
                    language=None,
                )
                code = attached.code
                function_section = next(
                    section
                    for section in code.code_sections
                    if section.type is CodeSectionType.function
                )

                await code_package.sync_tests(
                    manifest_text='[project]\ndependencies = ["pytest>=8"]\n',
                )

                framework = code_package.test_frameworks[0]
                assert framework.name == "pytest"
                assert framework.id == stable_code_test_framework_id(name="pytest")
                framework_edge = code_package.code_package_test_frameworks[0]
                assert framework_edge.id == stable_code_package_test_framework_id(
                    code_package_id=code_package.id,
                    code_test_framework_id=framework.id,
                )
                assert framework_edge.code_test_framework is framework
                assert framework_edge.declaration_kind == "manifest"
                assert framework_edge.declaration_ref == "pyproject.toml"

                assert len(code.tests) == 1
                code_test = code.tests[0]
                assert code_test.framework is framework
                assert code_test.selector_prefix == "tests/test_demo.py"
                assert len(code_test.units) == 1
                unit = code_test.units[0]
                assert unit.code_section is function_section
                assert unit.unit_key == "pytest:tests/test_demo.py:test_demo"
                assert unit.selector == "tests/test_demo.py::test_demo"

                package_test = code_package.tests[0]
                assert package_test.id == stable_code_package_test_id(
                    code_package_id=code_package.id,
                    code_test_id=code_test.id,
                    relative_path="tests/test_demo.py",
                )
                assert package_test.code_test is code_test
                assert package_test.relative_path == "tests/test_demo.py"
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_test_run_receipt_materializes_under_package_test(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(code_test_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_test_framework_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_test_unit_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_test_unit_run_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_test_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_test_framework_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_test_run_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_python_materialized_run_package",
                    language=CodeLanguage.python,
                    surface="runtime",
                    manifest_kind="pyproject_toml",
                    manifest_relative_path="pyproject.toml",
                    package_root=".",
                    sources_root=".",
                    fqn_prefix="aware_python_materialized_run",
                )
                attached = await code_package.upsert_code_from_text(
                    relative_path="tests/test_demo.py",
                    content_text="def test_demo():\n    assert True\n",
                    language=None,
                )
                code = attached.code
                function_section = next(
                    section
                    for section in code.code_sections
                    if section.type is CodeSectionType.function
                )

                await code_package.sync_tests(
                    manifest_text='[project]\ndependencies = ["pytest>=8"]\n',
                )

                package_test = code_package.tests[0]
                code_test = package_test.code_test
                unit = code_test.units[0]
                assert code_test.framework is not None
                started_at_utc = datetime(2026, 4, 23, 8, 0, 0, tzinfo=timezone.utc)
                finished_at_utc = datetime(2026, 4, 23, 8, 0, 1, tzinfo=timezone.utc)
                unit_receipt = CodePackageTestUnitRunReceipt(
                    code_package_id=code_package.id,
                    code_package_code_id=attached.id,
                    code_id=code.id,
                    code_section_id=function_section.id,
                    code_test_framework_id=code_test.framework.id,
                    code_test_id=code_test.id,
                    code_package_test_id=package_test.id,
                    code_test_unit_id=unit.id,
                    framework_name="pytest",
                    relative_path="tests/test_demo.py",
                    selector="tests/test_demo.py::test_demo",
                    unit_key=unit.unit_key,
                    backend_kind="aware_test_runner",
                    status="passed",
                    exit_code=0,
                    total_tests=1,
                    passed_tests=1,
                    failed_tests=0,
                    skipped_tests=0,
                    duration_s=1.0,
                )
                receipt = CodePackageTestRunReceipt(
                    code_package_id=code_package.id,
                    package_name=code_package.package_name,
                    language=CodeLanguage.python,
                    manifest_kind="pyproject_toml",
                    manifest_relative_path="pyproject.toml",
                    package_root=".",
                    backend_kind="aware_test_runner",
                    status="passed",
                    started_at_utc=started_at_utc,
                    finished_at_utc=finished_at_utc,
                    duration_s=1.0,
                    selected_unit_count=1,
                    total_tests=1,
                    passed_tests=1,
                    failed_tests=0,
                    skipped_tests=0,
                    unit_receipts=(unit_receipt,),
                )

                runs = await materialize_code_package_test_run_receipt(
                    code_package=code_package,
                    receipt=receipt,
                    run_key="local-run-1",
                )

                assert len(runs) == 1
                run = runs[0]
                assert run is package_test.runs[0]
                assert run.id == stable_code_package_test_run_id(
                    code_package_test_id=package_test.id,
                    run_key="local-run-1",
                )
                assert run.code_package_test_id == package_test.id
                assert run.status is CodeTestRunStatus.passed
                assert run.started_at_utc == started_at_utc
                assert run.finished_at_utc == finished_at_utc
                assert run.total_tests == 1
                assert run.passed_tests == 1

                unit_run = run.unit_runs[0]
                assert unit_run.id == stable_code_test_unit_run_id(
                    code_package_test_run_id=run.id,
                    code_test_unit_id=unit.id,
                )
                assert unit_run.code_package_test_run_id == run.id
                assert unit_run.code_test_unit is unit
                assert unit_run.code_test_unit_id == unit.id
                assert unit_run.status is CodeTestRunStatus.passed
                assert unit_run.selector == "tests/test_demo.py::test_demo"
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_config_scoped_build_updates_existing_layout_contract(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_delta_producer_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_delta_producer_code_handler,
        "current_handler_session",
        lambda: session,
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                package = await _build_code_package(
                    package_name="aware_direct_package",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="aware",
                    fqn_prefix="aware_direct",
                )
                updated = await _build_code_package(
                    package_name="aware_direct_package",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="structure/ontology/aware.toml",
                    package_root="modules/demo",
                    sources_root="structure/ontology",
                    fqn_prefix="aware_direct_updated",
                )

                config_ref = source_code_package_config_ref(
                    manifest_kind="aware_toml",
                    surface="runtime",
                )
                assert updated is package
                assert updated.code_package_config_id == config_ref.config_id
                assert updated.surface == "runtime"
                assert updated.manifest_relative_path == "structure/ontology/aware.toml"
                assert updated.package_root == "modules/demo"
                assert updated.sources_root == "structure/ontology"
                assert updated.fqn_prefix == "aware_direct_updated"
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_read_and_delete_code_via_local_provider(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_direct_package_delete",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_direct_delete",
                )
                attached = await code_package.create_code(
                    relative_path="src/main.aware",
                    plan=build_code_content_plan_from_text(
                        content_text="class A {}",
                        language=CodeLanguage.aware,
                    ),
                )
                code = attached.code
                section = code.code_sections[0]
                content_part_text = code.content_part_text

                assert (
                    await _read_code_text(code_package, relative_path="src/main.aware")
                    == "class A {}"
                )
                assert (
                    await code_package.delete_code(relative_path="src/main.aware")
                    is True
                )
                assert (
                    await code_package.delete_code(relative_path="src/main.aware")
                    is False
                )

                assert code_package.code_package_codes == []
                assert session.imap_get(CodePackageCode, attached.id) is None
                assert session.imap_get(Code, code.id) is None
                assert session.imap_get(CodeSection, section.id) is None
                assert content_part_text is not None
                assert session.imap_get(ContentPartText, content_part_text.id) is None

                with pytest.raises(ValueError, match="missing package-owned code"):
                    await _read_code_text(code_package, relative_path="src/main.aware")
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_upsert_code_from_text_via_local_provider(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_direct_package_upsert",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_direct_upsert",
                )
                created = await code_package.upsert_code_from_text(
                    relative_path="src/main.aware",
                    content_text="class A {}",
                    language=None,
                )
                replaced = await code_package.upsert_code_from_text(
                    relative_path="src/main.aware",
                    content_text="class B {}",
                    language=None,
                )

                assert replaced.id == created.id
                assert replaced.code.id == created.code.id
                assert replaced.code.language == CodeLanguage.aware
                assert replaced.code.content_part_text.inline_text == "class B {}"
                assert (
                    await _read_code_text(code_package, relative_path="src/main.aware")
                    == "class B {}"
                )
                assert len(replaced.code.code_sections) == 1
                assert replaced.code.code_sections[0].section_key == "B"
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_upsert_codes_from_text_via_local_provider(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_direct_package_batch_upsert",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_direct_batch_upsert",
                )

                await code_package.upsert_codes_from_text(
                    relative_paths=["src/a.aware", "src/b.aware"],
                    content_texts=["class A {}", "class B {}"],
                    language=None,
                )
                await code_package.upsert_codes_from_text(
                    relative_paths=["src/a.aware", "src/b.aware"],
                    content_texts=["class A2 {}", "class B2 {}"],
                    language=None,
                )

                assert len(code_package.code_package_codes) == 2
                assert (
                    await _read_code_text(code_package, relative_path="src/a.aware")
                    == "class A2 {}"
                )
                assert (
                    await _read_code_text(code_package, relative_path="src/b.aware")
                    == "class B2 {}"
                )
                assert {
                    edge.relative_path for edge in code_package.code_package_codes
                } == {"src/a.aware", "src/b.aware"}
                assert {
                    edge.code.code_sections[0].section_key
                    for edge in code_package.code_package_codes
                } == {
                    "A2",
                    "B2",
                }
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_apply_delta_upserts_and_deletes_via_local_provider(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_delta_producer_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_delta_producer_code_handler,
        "current_handler_session",
        lambda: session,
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_direct_package_delta",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_direct_delta",
                )
                await code_package.upsert_code_from_text(
                    relative_path="src/remove.aware",
                    content_text="class Remove {}",
                    language=None,
                )

                created_result = await code_package.apply_delta(
                    delta=CodePackageDelta(
                        package_name="aware_direct_package_delta",
                        authority=CodePackageDeltaAuthorityKind.semantic_materialization,
                        authority_kind="semantic_materialization",
                        production=CodePackageDeltaProduction(
                            producer=CodePackageDeltaProducerRef(
                                provider_key="aware_api",
                                producer_key="semantic_materializer",
                                producer_kind="semantic_materialization",
                            ),
                            input_digest="source-digest",
                        ),
                        paths=[
                            CodePackageDeltaPath(
                                relative_path="src/create.aware",
                                kind=CodePackageDeltaKind.create,
                                content_text="class Created {}",
                                path_role=CodePackagePathRole.generated_code,
                                production=CodePackageDeltaProduction(
                                    producer=CodePackageDeltaProducerRef(
                                        provider_key="aware_api.python",
                                        producer_key="python_codegen",
                                        producer_kind="language_plugin",
                                    ),
                                    output_digest="created-digest",
                                ),
                            ),
                            CodePackageDeltaPath(
                                relative_path="src/remove.aware",
                                kind=CodePackageDeltaKind.update,
                                content_text="class RemoveUpdated {}",
                                path_role=CodePackagePathRole.generated_metadata,
                            ),
                        ],
                    )
                )

                assert created_result.applied_path_count == 2
                assert created_result.created_path_count == 1
                assert created_result.updated_path_count == 1
                assert (
                    await _read_code_text(
                        code_package, relative_path="src/create.aware"
                    )
                    == "class Created {}"
                )
                assert (
                    await _read_code_text(
                        code_package, relative_path="src/remove.aware"
                    )
                    == "class RemoveUpdated {}"
                )
                created_edge = next(
                    edge
                    for edge in code_package.code_package_codes
                    if edge.relative_path == "src/create.aware"
                )
                updated_edge = next(
                    edge
                    for edge in code_package.code_package_codes
                    if edge.relative_path == "src/remove.aware"
                )
                assert created_edge.path_role is CodePackagePathRole.generated_code
                assert updated_edge.path_role is CodePackagePathRole.generated_metadata
                producers_by_identity = {
                    (producer.provider_key, producer.producer_key): producer
                    for producer in code_package.delta_producers
                }
                assert set(producers_by_identity) == {
                    ("aware_api", "semantic_materializer"),
                    ("aware_api.python", "python_codegen"),
                }

                python_producer = producers_by_identity[
                    ("aware_api.python", "python_codegen")
                ]
                assert python_producer.producer_kind == "language_plugin"
                assert len(python_producer.code_package_delta_producer_codes) == 1
                created_link = python_producer.code_package_delta_producer_codes[0]
                assert created_link.code_package_code_id == created_edge.id
                assert created_link.code_package_code is created_edge
                assert created_link.output_digest == "created-digest"

                semantic_producer = producers_by_identity[
                    ("aware_api", "semantic_materializer")
                ]
                assert semantic_producer.producer_kind == "semantic_materialization"
                assert len(semantic_producer.code_package_delta_producer_codes) == 1
                updated_link = semantic_producer.code_package_delta_producer_codes[0]
                assert updated_link.code_package_code_id == updated_edge.id
                assert updated_link.code_package_code is updated_edge
                assert updated_link.input_digest == "source-digest"

                delete_result = await code_package.apply_delta(
                    delta=CodePackageDelta(
                        paths=[
                            CodePackageDeltaPath(
                                relative_path="src/remove.aware",
                                kind=CodePackageDeltaKind.delete,
                            ),
                            CodePackageDeltaPath(
                                relative_path="src/missing.aware",
                                kind=CodePackageDeltaKind.delete,
                            ),
                        ],
                    )
                )

                assert delete_result.applied_path_count == 1
                assert delete_result.deleted_path_count == 1
                assert delete_result.deleted_missing_path_count == 1
                with pytest.raises(ValueError, match="missing package-owned code"):
                    await _read_code_text(
                        code_package, relative_path="src/remove.aware"
                    )
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_upsert_code_from_text_replaces_detached_session_sections(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_direct_package_detached_sections",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_direct_detached",
                )
                created = await code_package.upsert_code_from_text(
                    relative_path="src/main.aware",
                    content_text="class A {}",
                    language=None,
                )
                code = created.code
                old_section = code.code_sections[0]
                assert session.imap_get(CodeSection, old_section.id) is old_section

                # Simulate the hydrated-session mismatch seen from Kernel workspace materialization:
                # the session still owns the CodeSection, but the collection edge is incomplete.
                code.code_sections[:] = []

                replaced = await code_package.upsert_code_from_text(
                    relative_path="src/main.aware",
                    content_text="class B {}",
                    language=None,
                )

                assert replaced.id == created.id
                assert replaced.code.id == created.code.id
                assert replaced.code.content_part_text.inline_text == "class B {}"
                assert len(replaced.code.code_sections) == 1
                assert replaced.code.code_sections[0].section_key == "B"
                assert session.imap_get(CodeSection, old_section.id) is None
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_upsert_code_from_text_deletes_annotation_sections(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    from aware_code.handlers.impl.annotation import (
        code_section_annotation as annotation_handler,
    )

    monkeypatch.setattr(annotation_handler, "current_handler_session", lambda: session)

    first_text = "\n".join(
        [
            "class StreamEvent {",
            "    kind String",
            "}",
            "",
            "ann aware_test.StreamEvent::kind discriminate key",
            "",
        ]
    )
    second_text = "\n".join(
        [
            "class StreamEvent {",
            "    kind String",
            "    sequence Int?",
            "}",
            "",
        ]
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_annotation_delete_upsert",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_test",
                )
                created = await code_package.upsert_code_from_text(
                    relative_path="src/stream_event.aware",
                    content_text=first_text,
                    language=None,
                )
                replaced = await code_package.upsert_code_from_text(
                    relative_path="src/stream_event.aware",
                    content_text=second_text,
                    language=None,
                )

                assert replaced.id == created.id
                assert replaced.code.id == created.code.id
                assert replaced.code.content_part_text.inline_text == second_text
                assert (
                    await _read_code_text(
                        code_package, relative_path="src/stream_event.aware"
                    )
                    == second_text
                )
                assert len(replaced.code.code_sections) == 1
                assert replaced.code.code_sections[0].section_key == "StreamEvent"
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_package_upsert_code_from_text_deletes_annotation_sections_via_meta_runtime(
    tmp_path,
) -> None:  # noqa: ANN001
    repo_root = REPO_ROOT
    setup_code_plugins()
    config_ref = source_code_package_config_ref(
        manifest_kind="aware_toml",
        surface="runtime",
    )

    first_text = "\n".join(
        [
            "class StreamEvent {",
            "    kind String",
            "}",
            "",
            "ann aware_test.StreamEvent::kind discriminate key",
            "",
        ]
    )
    second_text = "\n".join(
        [
            "class StreamEvent {",
            "    kind String",
            "    sequence Int?",
            "}",
            "",
        ]
    )

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_runtime_annotation_delete",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        context = runtime.context
        assert context is not None
        lane = runtime.bind(
            branch_id=uuid4(),
            projection="CodePackage",
        )

        with lane.activate(commit=True, publish=False):
            code_package = await CodePackage.build_via_code_package_config(
                code_package_config_id=config_ref.config_id,
                package_name="aware_annotation_delete_runtime",
                language=CodeLanguage.aware,
                manifest_relative_path="aware.toml",
                package_root=".",
                sources_root="src",
                fqn_prefix="aware_test",
                surface="runtime",
            )
            created = await code_package.upsert_code_from_text(
                relative_path="src/stream_event.aware",
                content_text=first_text,
                language=None,
            )
            replaced = await code_package.upsert_code_from_text(
                relative_path="src/stream_event.aware",
                content_text=second_text,
                language=None,
            )

            assert replaced.id == created.id
            assert replaced.code.id == created.code.id
            assert replaced.code.content_part_text.inline_text == second_text

            oig = await materialize_meta_runtime_lane_head(
                runtime=runtime,
                lane=lane,
            )
            head_pairs = _committed_oig_class_pair_counts(
                index=context.index,
                oig=oig,
            )
            assert head_pairs[("Code", "CodeSection")] == 1
            assert head_pairs[("CodeSection", "ContentPartTextSegment")] == 1


@pytest.mark.asyncio
async def test_code_module_attach_existing_package_via_local_handlers(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(code_module_handler, "current_handler_session", lambda: session)
    from aware_code.handlers.impl.module import (
        code_module_code_package as code_module_code_package_handler,
    )

    monkeypatch.setattr(
        code_module_code_package_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_module_package",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_module",
                )
                code_module = await code_module_handler.build(
                    name="workspace_module",
                    languages=[CodeLanguage.aware],
                    aware_module_version=1,
                    manifest_relative_path="aware.module.toml",
                    manifest_hash="sha256:module",
                )
                attached = await code_module_handler.attach_package(
                    code_module,
                    code_package_id=code_package.id,
                    module_package_id="ontology",
                    module_package_kind="ontology",
                    module_relative_package_root="modules/workspace/structure/ontology",
                    manifest_relative_path="structure/ontology/aware.toml",
                    semantic_contract_role="aware_code.ontology",
                    semantic_contract_name="aware.ontology",
                    semantic_contract_provider_key="aware_code",
                    semantic_contract_module="aware_code.semantic_contract",
                    semantic_contract_owns_manifest_kinds=["aware_toml", "aware_toml"],
                    semantic_contract_capabilities=[
                        "semantic_analysis",
                        "semantic_analysis",
                    ],
                    mirrors_ontology=True,
                )

                expected_module_id = stable_code_module_id(name="workspace_module")
                expected_package_id = stable_code_package_id(
                    code_package_config_id=source_code_package_config_ref(
                        manifest_kind="aware_toml",
                        surface="runtime",
                    ).config_id,
                    package_name="aware_module_package",
                    language=CodeLanguage.aware,
                )
                expected_link_id = stable_code_module_code_package_id(
                    code_module_id=expected_module_id,
                    code_package_id=expected_package_id,
                )

                assert code_module.id == expected_module_id
                assert code_module.aware_module_version == 1
                assert code_module.manifest_relative_path == "aware.module.toml"
                assert code_module.manifest_hash == "sha256:module"
                assert code_package.id == expected_package_id
                assert attached.id == expected_link_id
                assert attached.code_package_id == code_package.id
                assert attached.code_package.id == code_package.id
                assert attached.code_package is code_package
                assert attached.module_package_id == "ontology"
                assert attached.module_package_kind == "ontology"
                assert (
                    attached.module_relative_package_root
                    == "modules/workspace/structure/ontology"
                )
                assert (
                    attached.manifest_relative_path == "structure/ontology/aware.toml"
                )
                assert attached.visibility == "module"
                assert attached.semantic_contract_role == "aware_code.ontology"
                assert attached.semantic_contract_name == "aware.ontology"
                assert attached.semantic_contract_provider_key == "aware_code"
                assert (
                    attached.semantic_contract_module == "aware_code.semantic_contract"
                )
                assert attached.semantic_contract_owns_manifest_kinds == ["aware_toml"]
                assert attached.semantic_contract_capabilities == ["semantic_analysis"]
                assert attached.mirrors_ontology is True
                assert len(code_module.code_module_code_packages) == 1
                assert code_module.code_module_code_packages[0].id == expected_link_id
                assert (
                    session.imap_get(CodeModuleCodePackage, expected_link_id)
                    is not None
                )
                assert session.imap_get(CodeModule, expected_module_id) is not None
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_projection_is_not_operator_facing(tmp_path) -> None:  # noqa: ANN001
    repo_root = REPO_ROOT

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_code_meta_runtime(repo_root=repo_root, aware_root=aware_root)
        context = runtime.context
        assert context is not None
        idx = context.index
        opg_names = {str(opg.name) for opg in idx.ocg.object_projection_graphs}
        assert "code" not in opg_names


@pytest.mark.asyncio
async def test_code_create_annotation_content_via_local_provider(monkeypatch) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    from aware_code.handlers.impl.annotation import (
        code_section_annotation as annotation_handler,
    )

    monkeypatch.setattr(annotation_handler, "current_handler_session", lambda: session)

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_annotation_package",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_annotation",
                )
                code = (
                    await code_package.create_code(
                        relative_path="src/annotation.aware",
                        plan=build_code_content_plan_from_text(
                            content_text="ann grammar.program Apply Key value key\nclass A {}\n",
                            language=CodeLanguage.aware,
                        ),
                    )
                ).code

                assert len(code.code_sections) == 2
                annotation_section = next(
                    section
                    for section in code.code_sections
                    if section.code_section_annotation is not None
                )
                annotation_payload = annotation_section.code_section_annotation
                assert annotation_payload is not None
                assert annotation_payload.path == "grammar.program"
                assert annotation_payload.verb == "Apply"
                assert annotation_payload.args == ["Key", "value", "key"]
                assert annotation_payload.id == stable_code_section_annotation_id(
                    code_section_id=annotation_section.id
                )
    finally:
        reset_invocation_provider(provider_token)


@pytest.mark.asyncio
async def test_code_create_and_replace_import_content_via_local_provider(
    monkeypatch,
) -> None:
    setup_code_plugins()
    session = Session(branch_id=uuid4(), skip_db=True)
    provider = _LocalInvocationProvider()
    provider_token = set_invocation_provider(provider)
    monkeypatch.setattr(code_handler, "current_handler_session", lambda: session)
    monkeypatch.setattr(
        code_section_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_package_code_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_section_import_handler, "current_handler_session", lambda: session
    )
    monkeypatch.setattr(
        code_section_import_name_handler, "current_handler_session", lambda: session
    )

    try:
        with set_session(session):
            with scoped_change_collection(should_track=lambda _: False):
                code_package = await _build_code_package(
                    package_name="aware_import_package",
                    language=CodeLanguage.aware,
                    surface="runtime",
                    manifest_kind="aware_toml",
                    manifest_relative_path="aware.toml",
                    package_root=".",
                    sources_root="src",
                    fqn_prefix="aware_import",
                )
                code = (
                    await code_package.create_code(
                        relative_path="src/import.aware",
                        plan=build_code_content_plan_from_text(
                            content_text="import package.utils as helpers;",
                            language=CodeLanguage.aware,
                        ),
                    )
                ).code

                assert len(code.code_sections) == 1
                import_section = code.code_sections[0]
                assert import_section.code_section_import is not None
                import_payload = import_section.code_section_import
                assert import_payload.module_text == "package.utils"
                assert import_payload.is_from_import is False
                assert import_payload.is_star_import is False
                assert len(import_payload.code_section_import_names) == 1
                assert (
                    import_payload.code_section_import_names[0].name_text
                    == "package.utils"
                )
                assert (
                    import_payload.code_section_import_names[0].alias_text == "helpers"
                )
                assert import_payload.id == stable_code_section_import_id(
                    code_section_id=import_section.id
                )
                assert import_payload.code_section_import_names[
                    0
                ].id == stable_code_section_import_name_id(
                    code_section_import_id=import_payload.id,
                    name_text="package.utils",
                )

                old_section_id = import_section.id
                old_import_id = import_payload.id
                old_import_name_id = import_payload.code_section_import_names[0].id
                old_module_segment_id = import_payload.module_segment_id
                old_name_segment_id = import_payload.code_section_import_names[
                    0
                ].name_segment_id
                old_alias_segment_id = import_payload.code_section_import_names[
                    0
                ].alias_segment_id
                assert old_module_segment_id is not None
                assert old_name_segment_id is not None
                assert old_alias_segment_id is not None

                await code.replace_content(
                    content_text="import core.* as CoreUtils;",
                    language=CodeLanguage.aware,
                )

                assert session.imap_get(CodeSection, old_section_id) is None
                assert session.imap_get(CodeSectionImport, old_import_id) is None
                assert (
                    session.imap_get(CodeSectionImportName, old_import_name_id) is None
                )
                assert (
                    session.imap_get(ContentPartTextSegment, old_module_segment_id)
                    is None
                )
                assert (
                    session.imap_get(ContentPartTextSegment, old_name_segment_id)
                    is None
                )
                assert (
                    session.imap_get(ContentPartTextSegment, old_alias_segment_id)
                    is None
                )

                assert len(code.code_sections) == 1
                replaced_section = code.code_sections[0]
                assert replaced_section.code_section_import is not None
                replaced_payload = replaced_section.code_section_import
                assert replaced_payload.module_text == "core"
                assert replaced_payload.is_star_import is True
                assert len(replaced_payload.code_section_import_names) == 1
                replaced_name = replaced_payload.code_section_import_names[0]
                assert replaced_name.name_text == "*"
                assert replaced_name.alias_text == "CoreUtils"
                assert replaced_payload.id == stable_code_section_import_id(
                    code_section_id=replaced_section.id
                )
                assert replaced_name.id == stable_code_section_import_name_id(
                    code_section_import_id=replaced_payload.id,
                    name_text="*",
                )
                assert len(code.content_part_text.segments) == 4
    finally:
        reset_invocation_provider(provider_token)
