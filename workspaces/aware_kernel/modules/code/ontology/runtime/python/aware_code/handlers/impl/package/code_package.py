from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Code Ontology
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package_enums import CodePackageArtifactStatus
from aware_code_ontology.code.code_plan import (
    CodeContentPlan,
    CodePackageDelta,
    CodePackageDeltaApplyResult,
    CodePackageDeltaProduction,
    CodePackagePathRole,
)
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.package.code_package_artifact import CodePackageArtifact
from aware_code_ontology.package.code_package_code import CodePackageCode
from aware_code_ontology.package.code_package_delta_producer import CodePackageDeltaProducer
from aware_code_ontology.package.code_package_test import CodePackageTest
from aware_code_ontology.package.code_package_test_framework import CodePackageTestFramework

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_code.handlers.impl.package import (
    code_package_delta_producer as delta_producer_handler,
)
from aware_code.package.code_access import (
    find_package_code_edge,
    normalize_package_relative_path,
    resolve_edge_code,
)
from aware_code.package.text_upsert import (
    build_code_content_plan_copy_from_text,
    resolve_code_package_text_language,
)
from aware_code.semantic_contract_config import code_package_config_for_id
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.language.test_discovery import (
    CodeTestDiscoveryCode,
    CodeTestDiscoveryContext,
    CodeTestDiscoverySection,
    CodeTestFrameworkDiscoveryDescriptor,
)
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.stable_ids import (
    stable_code_package_id,
    stable_code_test_framework_id,
)
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_plan import CodePackageDeltaKind
from aware_code_ontology.code.code_test_framework import CodeTestFramework
from aware_code_ontology.package.code_package_config import CodePackageConfig
from aware_meta.runtime.handler_context import current_handler_session


async def _link_delta_production(
    *,
    code_package: CodePackage,
    code_package_code: CodePackageCode,
    delta_production: CodePackageDeltaProduction | None,
) -> None:
    if delta_production is None:
        return

    producer_ref = delta_production.producer
    provider_key = (producer_ref.provider_key or "").strip()
    producer_key = (producer_ref.producer_key or "").strip()
    if not provider_key or not producer_key:
        raise RuntimeError("CodePackage delta production requires non-empty provider_key and producer_key")

    producer = await upsert_delta_producer(
        code_package,
        provider_key=provider_key,
        producer_key=producer_key,
        producer_kind=producer_ref.producer_kind,
        provider_payload=producer_ref.provider_payload,
    )
    await delta_producer_handler.link_code(
        producer,
        code_package_code_id=code_package_code.id,
        input_code_package_id=delta_production.input_code_package_id,
        input_object_instance_graph_commit_id=delta_production.input_object_instance_graph_commit_id,
        input_digest=delta_production.input_digest,
        output_digest=delta_production.output_digest,
        emission_payload=delta_production.emission_payload,
    )


def _stable_code_package_id_via_config(
    *,
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
) -> UUID:
    return stable_code_package_id(
        code_package_config_id=code_package_config_id,
        package_name=package_name,
        language=language,
    )


def _resolve_code_package_config(code_package: CodePackage) -> CodePackageConfig:
    code_package_config_id = getattr(code_package, "code_package_config_id", None)
    if code_package_config_id is None:
        raise RuntimeError(
            "CodePackage operation requires parent CodePackageConfig: " + f"code_package_id={code_package.id}"
        )
    session = current_handler_session()
    code_package_config = session.imap_get(CodePackageConfig, code_package_config_id)
    if code_package_config is not None:
        return code_package_config
    resolved = code_package_config_for_id(code_package_config_id)
    if resolved is not None:
        return resolved

    raise RuntimeError(
        "CodePackage operation requires materialized parent CodePackageConfig; "
        "manifest_kind is CodePackageConfig semantic contract truth and must not "
        "be inferred from CodePackage.manifest_relative_path: "
        + f"code_package_id={code_package.id} "
        + f"code_package_config_id={code_package_config_id}"
    )


# --- AWARE: USER_IMPORTS END


async def create_code(
    code_package: CodePackage,
    relative_path: str,
    plan: CodeContentPlan,
    path_role: CodePackagePathRole = CodePackagePathRole.authored_source,
    delta_production: CodePackageDeltaProduction | None = None,
) -> CodePackageCode:
    """
    Create package-owned Code under this CodePackage from a canonical content plan.
    """

    # --- AWARE: LOGIC START create_code
    created = await CodePackageCode.create_via_code_package(
        code_package_id=code_package.id,
        relative_path=relative_path,
        plan=plan.model_copy(deep=True),
        path_role=path_role,
        delta_production=delta_production,
    )
    await _link_delta_production(
        code_package=code_package,
        code_package_code=created,
        delta_production=delta_production,
    )
    for existing in code_package.code_package_codes:
        if existing.id == created.id:
            return existing
    code_package.code_package_codes.append(created)
    return created
    # --- AWARE: LOGIC END create_code


async def upsert_delta_producer(
    code_package: CodePackage,
    provider_key: str,
    producer_key: str,
    producer_kind: str | None = None,
    provider_payload: JsonObject | None = None,
) -> CodePackageDeltaProducer:
    """
    Upsert one package-local raw delta producer identity.

    This stores generic producer identity for routing/blame only. Code does
    not interpret provider payloads or semantic materialization truth.
    """

    # --- AWARE: LOGIC START upsert_delta_producer
    normalized_provider_key = (provider_key or "").strip()
    normalized_producer_key = (producer_key or "").strip()
    if not normalized_provider_key:
        raise RuntimeError("CodePackage.upsert_delta_producer requires non-empty provider_key")
    if not normalized_producer_key:
        raise RuntimeError("CodePackage.upsert_delta_producer requires non-empty producer_key")

    producer = await CodePackageDeltaProducer.build_via_code_package(
        code_package_id=code_package.id,
        provider_key=normalized_provider_key,
        producer_key=normalized_producer_key,
        producer_kind=producer_kind,
        provider_payload=provider_payload,
    )
    for attached in code_package.delta_producers:
        if attached.id == producer.id:
            return attached
    code_package.delta_producers.append(producer)
    return producer
    # --- AWARE: LOGIC END upsert_delta_producer


async def attach_artifact(
    code_package: CodePackage,
    output_key: str,
    artifact_key: str,
    status: CodePackageArtifactStatus = CodePackageArtifactStatus.available,
    artifact_family: str | None = None,
    artifact_role: str | None = None,
    required_for: list[str] = [],
    producer_key: str | None = None,
    producer_kind: str | None = None,
    materialization_index: int | None = None,
    source_code_package_id: UUID | None = None,
    source_object_instance_graph_commit_id: UUID | None = None,
    input_code_package_id: UUID | None = None,
    input_object_instance_graph_commit_id: UUID | None = None,
    digest: str | None = None,
    relative_path: str | None = None,
    uri: str | None = None,
    media_type: str | None = None,
    runtime_contract_version: str | None = None,
    provider_payload: JsonObject | None = None,
    receipt_payload: JsonObject | None = None,
    error: str | None = None,
) -> CodePackageArtifact:
    """
    Attach one package-owned artifact evidence row.

    Contract:
    - This is the package output evidence lane.
    - WorkspaceRevision should hydrate artifacts through the pinned
      WorkspaceRevisionCodePackage commit instead of owning per-artifact
      pointers.
    """

    # --- AWARE: LOGIC START attach_artifact
    artifact = await CodePackageArtifact.build_via_code_package(
        code_package_id=code_package.id,
        output_key=output_key,
        artifact_key=artifact_key,
        status=status,
        artifact_family=artifact_family,
        artifact_role=artifact_role,
        required_for=list(required_for or []),
        producer_key=producer_key,
        producer_kind=producer_kind,
        materialization_index=materialization_index,
        source_code_package_id=source_code_package_id,
        source_object_instance_graph_commit_id=source_object_instance_graph_commit_id,
        input_code_package_id=input_code_package_id,
        input_object_instance_graph_commit_id=input_object_instance_graph_commit_id,
        digest=digest,
        relative_path=relative_path,
        uri=uri,
        media_type=media_type,
        runtime_contract_version=runtime_contract_version,
        provider_payload=provider_payload,
        receipt_payload=receipt_payload,
        error=error,
    )
    for existing in code_package.artifacts:
        if existing.id == artifact.id:
            return existing
    code_package.artifacts.append(artifact)
    return artifact
    # --- AWARE: LOGIC END attach_artifact


async def delete_code(code_package: CodePackage, relative_path: str) -> bool:
    """
    Delete one package-owned code attachment by package-relative path.
    """

    # --- AWARE: LOGIC START delete_code
    existing = find_package_code_edge(code_package, relative_path)
    if existing is None:
        return False

    await existing.delete()
    code_package.code_package_codes[:] = [edge for edge in code_package.code_package_codes if edge.id != existing.id]
    return True
    # --- AWARE: LOGIC END delete_code


async def upsert_code(
    code_package: CodePackage,
    relative_path: str,
    plan: CodeContentPlan,
    path_role: CodePackagePathRole = CodePackagePathRole.authored_source,
    delta_production: CodePackageDeltaProduction | None = None,
) -> CodePackageCode:
    """
    Create or replace package-owned Code under this CodePackage from a canonical content plan.
    """

    # --- AWARE: LOGIC START upsert_code
    existing = find_package_code_edge(code_package, relative_path)
    if existing is None:
        return await create_code(
            code_package,
            relative_path=relative_path,
            plan=plan,
            path_role=path_role,
            delta_production=delta_production,
        )

    code = resolve_edge_code(existing)
    if existing.path_role != path_role:
        existing = await existing.update_path_role(path_role=path_role)
    await code.apply_content_plan(
        plan=plan.model_copy(deep=True),
    )
    await _link_delta_production(
        code_package=code_package,
        code_package_code=existing,
        delta_production=delta_production,
    )
    for attached in code_package.code_package_codes:
        if attached.id == existing.id:
            return attached
    code_package.code_package_codes.append(existing)
    return existing
    # --- AWARE: LOGIC END upsert_code


async def upsert_code_from_text(
    code_package: CodePackage, relative_path: str, content_text: str, language: CodeLanguage | None = None
) -> CodePackageCode:
    """
    Compatibility wrapper that parses raw text and delegates to `upsert_code(...)`.
    """

    # --- AWARE: LOGIC START upsert_code_from_text
    resolved_language = resolve_code_package_text_language(
        code_package=code_package,
        language=language,
    )
    return await upsert_code(
        code_package,
        relative_path=relative_path,
        plan=build_code_content_plan_copy_from_text(
            content_text=content_text,
            language=resolved_language,
        ),
    )
    # --- AWARE: LOGIC END upsert_code_from_text


async def upsert_codes_from_text(
    code_package: CodePackage, relative_paths: list[str], content_texts: list[str], language: CodeLanguage | None = None
) -> None:
    """
    Batch compatibility wrapper that parses raw text and upserts package-owned Code entries in one
    invocation.

    Contract:
    - `relative_paths` and `content_texts` must have equal lengths.
    - Each `relative_path` must be unique within the request.
    - This preserves the public `CodePackage` mutation boundary while reducing repeated invocation
    overhead.
    """

    # --- AWARE: LOGIC START upsert_codes_from_text
    if len(relative_paths) != len(content_texts):
        raise RuntimeError(
            "CodePackage.upsert_codes_from_text requires matching relative_paths/content_texts lengths: "
            + f"relative_paths={len(relative_paths)} content_texts={len(content_texts)}"
        )

    normalized_relative_paths = [normalize_package_relative_path(relative_path) for relative_path in relative_paths]
    if len(set(normalized_relative_paths)) != len(normalized_relative_paths):
        raise RuntimeError("CodePackage.upsert_codes_from_text requires unique relative_paths within one batch")

    resolved_language = resolve_code_package_text_language(
        code_package=code_package,
        language=language,
    )
    for relative_path, content_text in zip(normalized_relative_paths, content_texts, strict=True):
        _ = await upsert_code(
            code_package,
            relative_path=relative_path,
            plan=build_code_content_plan_copy_from_text(
                content_text=content_text,
                language=resolved_language,
            ),
        )
    # --- AWARE: LOGIC END upsert_codes_from_text


async def apply_delta(code_package: CodePackage, delta: CodePackageDelta) -> CodePackageDeltaApplyResult:
    """
    Apply a canonical CodePackageDelta through the package-owned mutation boundary.

    Contract:
    - Create/update entries upsert package-owned Code.
    - Delete entries remove package-owned Code by package-relative path.
    - This is the shared Code-owned IR consumed by Workspace commit and semantic owners.
    """

    # --- AWARE: LOGIC START apply_delta
    applied_path_count = 0
    created_path_count = 0
    updated_path_count = 0
    deleted_path_count = 0
    deleted_missing_path_count = 0
    skipped_path_count = 0
    seen_relative_paths: set[str] = set()

    for path_delta in delta.paths:
        relative_path = normalize_package_relative_path(path_delta.relative_path)
        if not relative_path:
            skipped_path_count += 1
            continue
        if relative_path in seen_relative_paths:
            raise RuntimeError(
                "CodePackage.apply_delta requires unique relative_path entries within one delta: "
                + f"relative_path={relative_path}"
            )
        seen_relative_paths.add(relative_path)

        if path_delta.kind is CodePackageDeltaKind.delete:
            deleted = await delete_code(code_package, relative_path=relative_path)
            if deleted:
                applied_path_count += 1
                deleted_path_count += 1
            else:
                deleted_missing_path_count += 1
            continue

        existing = find_package_code_edge(code_package, relative_path)
        plan = path_delta.content_plan
        if plan is None:
            if path_delta.content_text is None:
                raise RuntimeError(
                    "CodePackage.apply_delta create/update entries require content_text or content_plan: "
                    + f"relative_path={relative_path}"
                )
            plan = build_code_content_plan_copy_from_text(
                content_text=path_delta.content_text,
                language=resolve_code_package_text_language(
                    code_package=code_package,
                    language=path_delta.language,
                ),
            )

        _ = await upsert_code(
            code_package,
            relative_path=relative_path,
            plan=plan,
            path_role=path_delta.path_role,
            delta_production=path_delta.production or delta.production,
        )
        applied_path_count += 1
        if existing is None:
            created_path_count += 1
        else:
            updated_path_count += 1

    return CodePackageDeltaApplyResult(
        applied_path_count=applied_path_count,
        created_path_count=created_path_count,
        updated_path_count=updated_path_count,
        deleted_path_count=deleted_path_count,
        deleted_missing_path_count=deleted_missing_path_count,
        skipped_path_count=skipped_path_count,
    )
    # --- AWARE: LOGIC END apply_delta


async def sync_tests(code_package: CodePackage, manifest_text: str | None = None) -> None:
    """
    Discover and attach package-owned test framework/test inventory from language plugin truth.

    Contract:
    - Framework declarations are language-owned (for example pyproject.toml or pubspec.yaml).
    - Test units attach to existing Code/CodeSection truth already upserted under this CodePackage.
    - This is idempotent inventory sync only; execution receipts materialize later under
    CodePackageTest.runs.
    """

    # --- AWARE: LOGIC START sync_tests
    setup_code_plugins()
    try:
        language_plugin = CodeLanguagePluginRegistry.get(code_package.language)
    except KeyError:
        return
    code_package_config = _resolve_code_package_config(code_package)

    code_by_relative_path: dict[str, Code] = {}
    code_edge_by_relative_path: dict[str, CodePackageCode] = {}
    discovery_codes: list[CodeTestDiscoveryCode] = []
    for edge in code_package.code_package_codes:
        relative_path = normalize_package_relative_path(edge.relative_path)
        code = resolve_edge_code(edge)
        code_by_relative_path[relative_path] = code
        code_edge_by_relative_path[relative_path] = edge
        content_text = code.content_part_text.inline_text or ""
        discovery_codes.append(
            CodeTestDiscoveryCode(
                relative_path=relative_path,
                content_text=content_text or "",
                sections=tuple(
                    CodeTestDiscoverySection(
                        code_section_id=section.id,
                        section_key=section.section_key,
                        qualname=section.qualname,
                        section_type=section.type,
                    )
                    for section in code.code_sections
                ),
            )
        )

    discovery_result = language_plugin.discover_tests(
        CodeTestDiscoveryContext(
            package_name=code_package.package_name,
            language=code_package.language,
            manifest_kind=code_package_config.manifest_kind,
            manifest_relative_path=code_package.manifest_relative_path,
            package_root=code_package.package_root,
            sources_root=code_package.sources_root,
            manifest_text=manifest_text,
            codes=tuple(discovery_codes),
        )
    )

    framework_descriptors = {
        descriptor.name: descriptor for descriptor in discovery_result.frameworks if (descriptor.name or "").strip()
    }
    for unit in discovery_result.units:
        framework_name = (unit.framework_name or "").strip()
        if not framework_name:
            raise RuntimeError("CodePackage.sync_tests discovered a unit without framework_name")
        _ = framework_descriptors.setdefault(
            framework_name,
            CodeTestFrameworkDiscoveryDescriptor(name=framework_name, title=framework_name),
        )

    session = current_handler_session()
    frameworks_by_name: dict[str, CodeTestFramework] = {}
    for framework_name, descriptor in sorted(framework_descriptors.items()):
        normalized_framework_name = (framework_name or "").strip()
        if not normalized_framework_name:
            continue
        framework_id = stable_code_test_framework_id(name=normalized_framework_name)
        normalized_title = (descriptor.title or "").strip() or None
        framework = session.imap_get(CodeTestFramework, framework_id)
        if framework is None:
            framework = CodeTestFramework(
                id=framework_id,
                name=normalized_framework_name,
                title=normalized_title,
            )
        elif (framework.name or "").strip() != normalized_framework_name:
            raise RuntimeError(
                "CodePackage.sync_tests framework payload mismatch: " + f"code_test_framework_id={framework_id}"
            )
        else:
            framework.title = normalized_title
        frameworks_by_name[normalized_framework_name] = framework
        _ = await attach_test_framework(
            code_package,
            framework_id=framework.id,
            declaration_kind=descriptor.declaration_kind,
            declaration_ref=descriptor.declaration_ref,
        )

    for unit in discovery_result.units:
        relative_path = normalize_package_relative_path(unit.relative_path)
        code = code_by_relative_path.get(relative_path)
        if code is None:
            raise RuntimeError(
                "CodePackage.sync_tests discovered unit for unknown package Code path: "
                + f"relative_path={relative_path}"
            )
        framework = frameworks_by_name.get((unit.framework_name or "").strip())
        if framework is None:
            raise RuntimeError(
                "CodePackage.sync_tests discovered unit for unknown framework: "
                + f"framework_name={unit.framework_name}"
            )
        code_edge = code_edge_by_relative_path[relative_path]
        code_test_unit = await code_edge.sync_test_unit(
            framework_id=framework.id,
            code_section_id=unit.code_section_id,
            unit_key=unit.unit_key,
            selector=unit.selector,
            kind=unit.kind,
            name=unit.name,
            selector_prefix=relative_path,
        )
        _ = await attach_test(
            code_package,
            code_test_id=code_test_unit.code_test_id,
            relative_path=relative_path,
        )
    # --- AWARE: LOGIC END sync_tests


async def attach_test_framework(
    code_package: CodePackage, framework_id: UUID, declaration_kind: str = "unknown", declaration_ref: str | None = None
) -> CodePackageTestFramework:
    """
    Attach an existing CodeTestFramework to this package with declaration provenance.
    """

    # --- AWARE: LOGIC START attach_test_framework
    created = await CodePackageTestFramework.build_via_code_package(
        code_package_id=code_package.id,
        code_test_framework_id=framework_id,
        declaration_kind=declaration_kind,
        declaration_ref=declaration_ref,
    )
    for existing in code_package.code_package_test_frameworks:
        if existing.id == created.id:
            return existing
    code_package.code_package_test_frameworks.append(created)
    return created
    # --- AWARE: LOGIC END attach_test_framework


async def attach_test(code_package: CodePackage, code_test_id: UUID, relative_path: str) -> CodePackageTest:
    """
    Attach an existing CodeTest to this package inventory.
    """

    # --- AWARE: LOGIC START attach_test
    created = await CodePackageTest.build_via_code_package(
        code_package_id=code_package.id,
        code_test_id=code_test_id,
        relative_path=relative_path,
    )
    for existing in code_package.tests:
        if existing.id == created.id:
            return existing
    code_package.tests.append(created)
    return created
    # --- AWARE: LOGIC END attach_test


async def create_code_from_text(
    code_package: CodePackage, relative_path: str, content_text: str, language: CodeLanguage | None = None
) -> CodePackageCode:
    """
    Compatibility wrapper that parses raw text and delegates to `create_code(...)`.
    """

    # --- AWARE: LOGIC START create_code_from_text
    resolved_language = resolve_code_package_text_language(
        code_package=code_package,
        language=language,
    )
    return await create_code(
        code_package,
        relative_path=relative_path,
        plan=build_code_content_plan_copy_from_text(
            content_text=content_text,
            language=resolved_language,
        ),
    )
    # --- AWARE: LOGIC END create_code_from_text


async def build_via_code_package_config(
    code_package_config_id: UUID,
    package_name: str,
    language: CodeLanguage,
    manifest_relative_path: str,
    package_root: str,
    sources_root: str | None = None,
    fqn_prefix: str | None = None,
    surface: str | None = None,
) -> CodePackage:
    """
    Create a deterministic CodePackage under a CodePackageConfig.

    Contract:
    - Parent CodePackageConfig context is propagated by constructor lowering.
    - Identity is config-scoped by `(code_package_config_id, package_name, language)`.
    - `manifest_relative_path`, `package_root`, and `sources_root` are package layout payload.
    - Semantic package kind and manifest-kind truth live on CodePackageConfig.
    """

    # --- AWARE: LOGIC START build_via_code_package_config
    normalized_package_name = (package_name or "").strip()
    if not normalized_package_name:
        raise RuntimeError("CodePackage.build_via_code_package_config requires non-empty package_name")

    normalized_manifest_relative_path = (manifest_relative_path or "").strip()
    if not normalized_manifest_relative_path:
        raise RuntimeError("CodePackage.build_via_code_package_config requires non-empty manifest_relative_path")

    normalized_package_root = (package_root or "").strip()
    if not normalized_package_root:
        raise RuntimeError("CodePackage.build_via_code_package_config requires non-empty package_root")

    normalized_sources_root = (sources_root or "").strip() or None
    normalized_fqn_prefix = (fqn_prefix or "").strip() or None
    package_id = _stable_code_package_id_via_config(
        code_package_config_id=code_package_config_id,
        package_name=normalized_package_name,
        language=language,
    )

    session = current_handler_session()
    from aware_code_ontology.package.code_package_config import CodePackageConfig

    _ = session.imap_get(CodePackageConfig, code_package_config_id)

    existing = session.imap_get(CodePackage, package_id)
    if existing is not None:
        if (
            getattr(existing, "code_package_config_id", code_package_config_id) != code_package_config_id
            or (existing.package_name or "").strip() != normalized_package_name
            or existing.language != language
        ):
            raise RuntimeError(
                "CodePackage.build_via_code_package_config payload mismatch for existing package: "
                + f"code_package_id={package_id}"
            )
        existing.surface = surface
        if getattr(existing, "code_package_config_id", None) != code_package_config_id:
            object.__setattr__(
                existing,
                "code_package_config_id",
                code_package_config_id,
            )
        existing.manifest_relative_path = normalized_manifest_relative_path
        existing.package_root = normalized_package_root
        existing.sources_root = normalized_sources_root
        existing.fqn_prefix = normalized_fqn_prefix
        return existing

    created = CodePackage(
        id=package_id,
        code_package_config_id=code_package_config_id,
        package_name=normalized_package_name,
        language=language,
        surface=surface,
        manifest_relative_path=normalized_manifest_relative_path,
        package_root=normalized_package_root,
        sources_root=normalized_sources_root,
        fqn_prefix=normalized_fqn_prefix,
    )
    if getattr(created, "code_package_config_id", None) != code_package_config_id:
        object.__setattr__(
            created,
            "code_package_config_id",
            code_package_config_id,
        )
    return created
    # --- AWARE: LOGIC END build_via_code_package_config
