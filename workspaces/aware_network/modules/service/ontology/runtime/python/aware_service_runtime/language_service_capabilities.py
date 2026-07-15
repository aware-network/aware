from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from aware_language_service.core.features.diagnostics_capabilities.contracts import (
    AwareDiagnostic,
)
from aware_language_service.core.features.diagnostics_capabilities.executor import (
    DiagnosticsCapabilityContext,
)
from aware_language_service.core.features.semantic_tokens_capabilities.aware_context import (
    collect_aware_contextual_tokens_for_owner_groups,
)
from aware_language_service.core.features.semantic_tokens_capabilities.collector import (
    SemanticTokenCollector,
)
from aware_language_service.core.position import ByteRange
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_code.semantic_capability import (
    SemanticAnalysisCapabilityRequest,
    SemanticAnalysisCapabilityResult,
)

from aware_service_runtime.dependency_scope import ServiceDependencyScope
from aware_service_runtime.language_service_capability_metadata import (
    SERVICE_SEMANTIC_SCOPE_KEYS,
)
from aware_service_runtime.semantic_analysis import analyze_service_semantic_capability


@dataclass(frozen=True, slots=True)
class _ServiceParsedSource:
    source_path: Path
    relpath: Path
    document_bytes: bytes
    root: Node
    is_current: bool


def _service_root_diagnostics_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    _collect_service_diagnostics(
        context=context,
        enabled_groups=frozenset({"service"}),
    )
    return []


def _service_api_diagnostics_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    _collect_service_diagnostics(
        context=context,
        enabled_groups=frozenset({"api"}),
    )
    return []


def _service_experience_diagnostics_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    _collect_service_diagnostics(
        context=context,
        enabled_groups=frozenset({"experience"}),
    )
    return []


def _service_projection_diagnostics_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    _collect_service_diagnostics(
        context=context,
        enabled_groups=frozenset({"projection"}),
    )
    return []


def _service_operation_diagnostics_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    _collect_service_diagnostics(
        context=context,
        enabled_groups=frozenset({"operation"}),
    )
    return []


def _service_endpoint_diagnostics_provider(context: DiagnosticsCapabilityContext) -> list[AwareDiagnostic]:
    _collect_service_diagnostics(
        context=context,
        enabled_groups=frozenset({"endpoint"}),
    )
    return []


def _service_semantic_analysis_provider(
    request: SemanticAnalysisCapabilityRequest,
) -> SemanticAnalysisCapabilityResult:
    return analyze_service_semantic_capability(request)


def _byte_range_for_node(node: Node | None) -> ByteRange:
    if node is None:
        return ByteRange(start=0, end=0)
    return ByteRange(start=node.start_byte, end=node.end_byte)


def _qualified_text(document_bytes: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return document_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace").strip()


def _symbol_key(value: str) -> str:
    token = (value or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _iter_service_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in {"service_api_decl", "service_experience_decl", "service_operation_def"}:
            children.append(child)
            continue
        if child.type == "service_item":
            children.extend(grandchild for grandchild in child.named_children if grandchild.is_named)
    return tuple(children)


def _iter_service_api_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "service_api_projection_decl":
            children.append(child)
            continue
        if child.type == "service_api_item":
            children.extend(grandchild for grandchild in child.named_children if grandchild.is_named)
    return tuple(children)


def _iter_service_operation_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    body = node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type == "service_operation_endpoint_def":
            children.append(child)
            continue
        if child.type == "service_operation_item":
            children.extend(grandchild for grandchild in child.named_children if grandchild.is_named)
    return tuple(children)


def _resolve_declared_api_ref(*, endpoint_ref: str, declared_api_refs: tuple[str, ...]) -> str | None:
    matches = [
        api_ref
        for api_ref in declared_api_refs
        if endpoint_ref == api_ref or endpoint_ref.startswith(api_ref + ".")
    ]
    if not matches:
        return None
    return max(matches, key=len)


def _is_excluded(*, rel_path: str, exclude_patterns: list[str]) -> bool:
    token = PurePosixPath(rel_path)
    for raw_pattern in exclude_patterns:
        pattern = (raw_pattern or "").strip()
        if pattern and token.match(pattern):
            return True
    return False


def _collect_package_source_files(
    *,
    package_root: Path,
    sources_dir: str,
    include_paths: list[str],
    exclude_paths: list[str],
) -> tuple[Path, ...]:
    sources_root = (package_root / sources_dir).resolve()
    if not sources_root.exists() or not sources_root.is_dir():
        return ()

    files_by_rel: dict[str, Path] = {}
    for include in include_paths:
        pattern = (include or "").strip()
        if not pattern:
            continue
        for candidate in sources_root.glob(pattern):
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            try:
                rel_from_sources = resolved.relative_to(sources_root).as_posix()
                rel_from_package = resolved.relative_to(package_root).as_posix()
            except ValueError:
                continue
            if _is_excluded(rel_path=rel_from_sources, exclude_patterns=exclude_paths):
                continue
            files_by_rel[rel_from_package] = Path(rel_from_package)
    return tuple(files_by_rel[key] for key in sorted(files_by_rel))


def _load_service_sources(
    *,
    context: DiagnosticsCapabilityContext,
) -> tuple[_ServiceParsedSource, ...]:
    current_path = context.execution.document_path.resolve()
    manifest_path = context.execution.owning_manifest_path(filename="aware.service.toml")
    if manifest_path is None:
        return ()

    spec = load_aware_service_toml_spec(toml_path=manifest_path)
    package_root = manifest_path.parent.resolve()
    source_files = _collect_package_source_files(
        package_root=package_root,
        sources_dir=spec.build.sources_dir,
        include_paths=spec.build.include_paths,
        exclude_paths=spec.build.exclude_paths,
    )
    if not source_files:
        return ()

    parser = Parser(language=AWARE_LANGUAGE)
    sources: list[_ServiceParsedSource] = []
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        document_bytes = context.document_bytes if source_path == current_path else source_path.read_bytes()
        sources.append(
            _ServiceParsedSource(
                source_path=source_path,
                relpath=relpath,
                document_bytes=document_bytes,
                root=parser.parse(document_bytes).root_node,
                is_current=source_path == current_path,
            )
        )
    return tuple(sources)


def _collect_service_diagnostics(
    *,
    context: DiagnosticsCapabilityContext,
    enabled_groups: frozenset[str],
) -> None:
    service_sources = _load_service_sources(context=context)
    if not service_sources:
        return
    if (
        b"service" not in context.document_bytes
        and b"operation" not in context.document_bytes
        and b"endpoint" not in context.document_bytes
    ):
        return

    def _is_enabled(group: str) -> bool:
        return group in enabled_groups

    dependency_scope = context.execution.semantic_scope_runtime(
        scope_key=SERVICE_SEMANTIC_SCOPE_KEYS[0],
        expected_type=ServiceDependencyScope,
    )
    api_catalog = dependency_scope.api_catalog if dependency_scope is not None else {}

    service_occurrences: dict[str, list[tuple[_ServiceParsedSource, Node, Node | None]]] = {}
    for source in service_sources:
        if source.is_current and source.root.has_error and _is_enabled("service"):
            context.add(
                rng=ByteRange(start=0, end=len(source.document_bytes)),
                message=f"Service source {source.relpath.as_posix()} has parse errors.",
                code="aware.service.parse_error",
            )
        for node in source.root.named_children:
            if node.type != "service_def":
                continue
            name_node = node.child_by_field_name("name")
            service_name = _symbol_key(_qualified_text(source.document_bytes, name_node))
            if service_name:
                service_occurrences.setdefault(service_name.casefold(), []).append((source, node, name_node))

    for source in service_sources:
        if not source.is_current:
            continue
        for node in source.root.named_children:
            if node.type != "service_def":
                continue

            name_node = node.child_by_field_name("name")
            service_name = _symbol_key(_qualified_text(source.document_bytes, name_node))
            if not service_name:
                if _is_enabled("service"):
                    context.add(
                        rng=_byte_range_for_node(name_node or node),
                        message=(
                            f"Service declaration has empty name in {source.relpath.as_posix()}."
                        ),
                        code="aware.service.service_empty",
                    )
                continue

            if _is_enabled("service") and len(service_occurrences.get(service_name.casefold(), ())) > 1:
                context.add(
                    rng=_byte_range_for_node(name_node),
                    message=(
                        f"Duplicate service declaration {service_name!r} across service sources."
                    ),
                    code="aware.service.service_duplicate",
                )

            service_children = _iter_service_children(node=node)
            api_nodes = tuple(child for child in service_children if child.type == "service_api_decl")
            experience_nodes = tuple(
                child for child in service_children if child.type == "service_experience_decl"
            )
            operation_nodes = tuple(child for child in service_children if child.type == "service_operation_def")

            if _is_enabled("service") and not api_nodes:
                context.add(
                    rng=_byte_range_for_node(name_node),
                    message=(
                        f"Service declaration {service_name!r} must include at least one api."
                    ),
                    code="aware.service.api_required",
                )
            if _is_enabled("service") and not operation_nodes:
                context.add(
                    rng=_byte_range_for_node(name_node),
                    message=(
                        f"Service declaration {service_name!r} must include at least one operation."
                    ),
                    code="aware.service.operation_required",
                )

            declared_api_refs: list[str] = []
            seen_api_refs: set[str] = set()
            for api_node in api_nodes:
                api_ref_node = api_node.child_by_field_name("api")
                api_ref = _qualified_text(source.document_bytes, api_ref_node)
                if not api_ref:
                    if _is_enabled("api"):
                        context.add(
                            rng=_byte_range_for_node(api_ref_node or api_node),
                            message=(
                                f"Service declaration {service_name!r} has api declaration with empty target."
                            ),
                            code="aware.service.api_empty",
                        )
                    continue

                api_key = api_ref.casefold()
                if api_key in seen_api_refs:
                    if _is_enabled("api"):
                        context.add(
                            rng=_byte_range_for_node(api_ref_node),
                            message=(
                                f"Service declaration {service_name!r} has duplicate api binding {api_ref!r}."
                            ),
                            code="aware.service.api_duplicate",
                        )
                    continue

                seen_api_refs.add(api_key)
                declared_api_refs.append(api_ref)
                if _is_enabled("api") and api_catalog and api_key not in api_catalog:
                    context.add(
                        rng=_byte_range_for_node(api_ref_node),
                        message=(
                            f"Service declaration {service_name!r} references unknown api {api_ref!r} "
                            + "outside resolved service dependency truth."
                        ),
                        code="aware.service.api_unknown",
                    )
                seen_projection_refs: set[str] = set()
                for projection_node in _iter_service_api_children(node=api_node):
                    if projection_node.type != "service_api_projection_decl":
                        continue
                    projection_ref_node = projection_node.child_by_field_name("projection")
                    projection_ref = _qualified_text(source.document_bytes, projection_ref_node)
                    if not projection_ref:
                        if _is_enabled("projection"):
                            context.add(
                                rng=_byte_range_for_node(projection_ref_node or projection_node),
                                message=(
                                    f"Service declaration {service_name!r} api {api_ref!r} "
                                    "has projection with empty target."
                                ),
                                code="aware.service.projection_empty",
                            )
                        continue

                    projection_key = projection_ref.casefold()
                    if projection_key in seen_projection_refs and _is_enabled("projection"):
                        context.add(
                            rng=_byte_range_for_node(projection_ref_node),
                            message=(
                                f"Service declaration {service_name!r} api {api_ref!r} "
                                + f"has duplicate projection {projection_ref!r}."
                            ),
                            code="aware.service.projection_duplicate",
                        )
                    seen_projection_refs.add(projection_key)

            seen_experience_refs: set[str] = set()
            for experience_node in experience_nodes:
                experience_ref_node = experience_node.child_by_field_name("experience")
                experience_ref = _qualified_text(source.document_bytes, experience_ref_node)
                if not experience_ref:
                    if _is_enabled("experience"):
                        context.add(
                            rng=_byte_range_for_node(experience_ref_node or experience_node),
                            message=(
                                f"Service declaration {service_name!r} has experience declaration with empty target."
                            ),
                            code="aware.service.experience_empty",
                        )
                    continue
                experience_key = experience_ref.casefold()
                if experience_key in seen_experience_refs and _is_enabled("experience"):
                    context.add(
                        rng=_byte_range_for_node(experience_ref_node),
                        message=(
                            f"Service declaration {service_name!r} has duplicate experience binding "
                            + f"{experience_ref!r}."
                        ),
                        code="aware.service.experience_duplicate",
                    )
                seen_experience_refs.add(experience_key)

            seen_operation_names: set[str] = set()
            declared_api_refs_tuple = tuple(declared_api_refs)
            for operation_node in operation_nodes:
                operation_name_node = operation_node.child_by_field_name("operation_name")
                operation_name = _symbol_key(_qualified_text(source.document_bytes, operation_name_node))
                if not operation_name:
                    if _is_enabled("operation"):
                        context.add(
                            rng=_byte_range_for_node(operation_name_node or operation_node),
                            message=(
                                f"Service declaration {service_name!r} has operation with empty name."
                            ),
                            code="aware.service.operation_empty",
                        )
                    continue

                operation_key = operation_name.casefold()
                if operation_key in seen_operation_names and _is_enabled("operation"):
                    context.add(
                        rng=_byte_range_for_node(operation_name_node),
                        message=(
                            f"Service declaration {service_name!r} has duplicate operation {operation_name!r}."
                        ),
                        code="aware.service.operation_duplicate",
                    )
                seen_operation_names.add(operation_key)

                endpoint_nodes = tuple(
                    child
                    for child in _iter_service_operation_children(node=operation_node)
                    if child.type == "service_operation_endpoint_def"
                )
                if _is_enabled("endpoint") and not endpoint_nodes:
                    context.add(
                        rng=_byte_range_for_node(operation_name_node),
                        message=(
                            f"Service declaration {service_name!r} operation {operation_name!r} "
                            "must include at least one endpoint."
                        ),
                        code="aware.service.endpoint_required",
                    )

                seen_endpoint_refs: set[str] = set()
                for endpoint_node in endpoint_nodes:
                    endpoint_ref_node = endpoint_node.child_by_field_name("endpoint")
                    endpoint_ref = _qualified_text(source.document_bytes, endpoint_ref_node)
                    if not endpoint_ref:
                        if _is_enabled("endpoint"):
                            context.add(
                                rng=_byte_range_for_node(endpoint_ref_node or endpoint_node),
                                message=(
                                    f"Service declaration {service_name!r} "
                                    + f"operation {operation_name!r} has endpoint with empty ref."
                                ),
                                code="aware.service.endpoint_empty",
                            )
                        continue

                    if len(endpoint_ref.split(".")) < 3:
                        if _is_enabled("endpoint"):
                            context.add(
                                rng=_byte_range_for_node(endpoint_ref_node),
                                message=(
                                    f"Service declaration {service_name!r} "
                                    + f"operation {operation_name!r} has invalid endpoint ref "
                                    + f"{endpoint_ref!r}; expected api.capability.endpoint."
                                ),
                                code="aware.service.endpoint_invalid",
                            )
                        continue

                    if (
                        _is_enabled("endpoint")
                        and _resolve_declared_api_ref(
                            endpoint_ref=endpoint_ref,
                            declared_api_refs=declared_api_refs_tuple,
                        )
                        is None
                    ):
                        context.add(
                            rng=_byte_range_for_node(endpoint_ref_node),
                            message=(
                                f"Service declaration {service_name!r} "
                                + f"operation {operation_name!r} references undeclared api endpoint "
                                + f"{endpoint_ref!r}."
                            ),
                            code="aware.service.endpoint_api_not_declared",
                        )

                    endpoint_key = endpoint_ref.casefold()
                    if endpoint_key in seen_endpoint_refs and _is_enabled("endpoint"):
                        context.add(
                            rng=_byte_range_for_node(endpoint_ref_node),
                            message=(
                                f"Service declaration {service_name!r} "
                                + f"operation {operation_name!r} has duplicate endpoint binding "
                                + f"{endpoint_ref!r}."
                            ),
                            code="aware.service.endpoint_duplicate",
                        )
                    seen_endpoint_refs.add(endpoint_key)

                    resolved_api_ref = _resolve_declared_api_ref(
                        endpoint_ref=endpoint_ref,
                        declared_api_refs=declared_api_refs_tuple,
                    )
                    if (
                        _is_enabled("endpoint")
                        and api_catalog
                        and resolved_api_ref is not None
                    ):
                        api_truth = api_catalog.get(resolved_api_ref.casefold())
                        if api_truth is not None and endpoint_ref not in api_truth.endpoint_refs:
                            context.add(
                                rng=_byte_range_for_node(endpoint_ref_node),
                                message=(
                                    f"Service declaration {service_name!r} operation {operation_name!r} "
                                    + f"references unknown endpoint {endpoint_ref!r} outside resolved API truth."
                                ),
                                code="aware.service.endpoint_unknown",
                            )


def _semantic_tokens_provider(
    collector: SemanticTokenCollector,
    *,
    owner_group: str,
) -> None:
    collect_aware_contextual_tokens_for_owner_groups(
        collector=collector,
        enabled_owner_groups=frozenset({owner_group}),
    )


def _service_root_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="service_service")


def _service_api_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="service_api")


def _service_experience_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="service_experience")


def _service_projection_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="service_projection")


def _service_operation_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="service_operation")


def _service_endpoint_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="service_endpoint")
