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
from aware_interface.manifest import (
    load_aware_interface_toml_spec,
    load_aware_pane_toml_spec,
)

from aware_interface.pane_consumer_scope import (
    InterfaceDependencyScope as _InterfaceDependencyScope,
    InterfaceExperienceTruth as _InterfaceExperienceTruth,
    PaneConsumerScope as _PaneConsumerScope,
    WorkspacePaneCatalogEntry as _WorkspacePaneCatalogEntry,
)
from aware_interface.language_service_capability_metadata import (
    INTERFACE_SEMANTIC_SCOPE_KEYS,
)
from aware_interface.semantic_scope import (
    InterfaceSemanticScope,
)


@dataclass(frozen=True, slots=True)
class _InterfaceParsedSource:
    source_path: Path
    relpath: Path
    document_bytes: bytes
    root: Node
    is_current: bool


@dataclass(frozen=True, slots=True)
class _ResolvedInterfacePackage:
    manifest_kind: str
    manifest_path: Path
    package_root: Path
    sources: tuple[_InterfaceParsedSource, ...]


def _interface_root_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"interface"}),
    )
    return []


def _interface_api_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"api"}),
    )
    return []


def _interface_window_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"window"}),
    )
    return []


def _interface_layout_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"layout"}),
    )
    return []


def _interface_section_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"section"}),
    )
    return []


def _interface_pane_composition_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"pane_composition"}),
    )
    return []


def _interface_mount_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"mount"}),
    )
    return []


def _interface_narrative_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_interface_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"narrative"}),
    )
    return []


def _pane_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_pane_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"pane"}),
    )
    return []


def _view_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_pane_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"view"}),
    )
    return []


def _endpoint_diagnostics_provider(
    context: DiagnosticsCapabilityContext,
) -> list[AwareDiagnostic]:
    _collect_pane_package_diagnostics(
        context=context,
        enabled_groups=frozenset({"endpoint"}),
    )
    return []


def _byte_range_for_node(node: Node | None) -> ByteRange:
    if node is None:
        return ByteRange(start=0, end=0)
    return ByteRange(start=node.start_byte, end=node.end_byte)


def _qualified_text(document_bytes: bytes, node: Node | None) -> str:
    if node is None:
        return ""
    return (
        document_bytes[node.start_byte : node.end_byte]
        .decode("utf-8", errors="replace")
        .strip()
    )


def _symbol_key(value: str) -> str:
    return (value or "").strip()


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


def _load_interface_or_pane_sources(
    *,
    context: DiagnosticsCapabilityContext,
) -> _ResolvedInterfacePackage | None:
    current_path = context.execution.document_path.resolve()
    manifest_path = context.execution.owning_manifest_path()
    manifest_kind: str
    sources_dir: str
    include_paths: list[str]
    exclude_paths: list[str]

    if manifest_path is not None and manifest_path.name == "aware.pane.toml":
        spec = load_aware_pane_toml_spec(toml_path=manifest_path)
        manifest_kind = "aware_pane_toml"
        sources_dir = spec.build.sources_dir
        include_paths = spec.build.include_paths
        exclude_paths = spec.build.exclude_paths
    elif manifest_path is not None and manifest_path.name == "aware.interface.toml":
        spec = load_aware_interface_toml_spec(toml_path=manifest_path)
        manifest_kind = "aware_interface_toml"
        sources_dir = spec.build.sources_dir
        include_paths = spec.build.include_paths
        exclude_paths = spec.build.exclude_paths
    else:
        return None

    package_root = manifest_path.parent.resolve()
    source_files = _collect_package_source_files(
        package_root=package_root,
        sources_dir=sources_dir,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
    )
    if not source_files:
        return None

    parser = Parser(language=AWARE_LANGUAGE)
    sources: list[_InterfaceParsedSource] = []
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        document_bytes = (
            context.document_bytes
            if source_path == current_path
            else source_path.read_bytes()
        )
        sources.append(
            _InterfaceParsedSource(
                source_path=source_path,
                relpath=relpath,
                document_bytes=document_bytes,
                root=parser.parse(document_bytes).root_node,
                is_current=source_path == current_path,
            )
        )
    return _ResolvedInterfacePackage(
        manifest_kind=manifest_kind,
        manifest_path=manifest_path,
        package_root=package_root,
        sources=tuple(sources),
    )


def _validate_view_ref_against_catalog(
    *,
    view_ref: str,
    experience_catalog: dict[str, _InterfaceExperienceTruth],
) -> tuple[str, str] | None:
    parsed = _parse_view_ref(view_ref)
    if parsed is None:
        return (
            f"Interface pane view ref must use `experience.observable.view`: {view_ref!r}.",
            "aware.interface.view_invalid",
        )
    experience_name, observable_key, view_key = parsed
    experience_truth = experience_catalog.get(experience_name.casefold())
    if experience_truth is None:
        return (
            "Interface pane view "
            + f"{view_ref!r} references unknown experience {experience_name!r}.",
            "aware.interface.view_experience_unknown",
        )
    observable_truth = experience_truth.observables.get(observable_key.casefold())
    if observable_truth is None:
        return (
            f"Interface pane view {view_ref!r} references unknown observable {observable_key!r}.",
            "aware.interface.view_observable_unknown",
        )
    if view_key.casefold() not in observable_truth:
        return (
            f"Interface pane view {view_ref!r} references unknown view {view_key!r}.",
            "aware.interface.view_unknown",
        )
    return None


def _parse_view_ref(view_ref: str) -> tuple[str, str, str] | None:
    parts = [segment.strip() for segment in view_ref.split(".") if segment.strip()]
    if len(parts) < 3:
        return None
    return parts[0], parts[1], ".".join(parts[2:])


def _validate_view_ref_shape(view_ref: str) -> tuple[str, str] | None:
    if _parse_view_ref(view_ref) is None:
        return (
            f"Interface pane view ref must use `experience.observable.view`: {view_ref!r}.",
            "aware.interface.view_invalid",
        )
    return None


def _validate_interface_pane_view_against_dependency_scope(
    *,
    interface_name: str,
    pane_name: str,
    view_ref: str,
    dependency_scope: _InterfaceDependencyScope,
    mounted: bool,
) -> tuple[str, str] | None:
    issue = _validate_view_ref_against_catalog(
        view_ref=view_ref,
        experience_catalog=dependency_scope.experience_catalog,
    )
    if issue is None:
        return None
    message, code = issue
    if mounted:
        if code == "aware.interface.view_experience_unknown":
            return (
                f"Interface {interface_name!r} pane composition {pane_name!r} mounts view {view_ref!r} "
                + "outside the declared interface experience_package dependency scope.",
                "aware.interface.mount_view_scope_outside",
            )
        return (
            f"Interface {interface_name!r} pane composition {pane_name!r} mounts invalid view {view_ref!r}: "
            + message,
            "aware.interface.mount_view_unknown",
        )
    if code == "aware.interface.view_experience_unknown":
        return (
            f"Interface {interface_name!r} consumes pane {pane_name!r} view {view_ref!r} "
            + "outside the declared interface experience_package dependency scope.",
            "aware.interface.pane_composition_view_scope_outside",
        )
    return (
        f"Interface {interface_name!r} consumes pane {pane_name!r} view {view_ref!r} that is invalid "
        + f"against declared experience scope: {message}",
        "aware.interface.pane_composition_view_unknown",
    )


def _consumer_scope_label(scope: _PaneConsumerScope) -> str:
    return f"interface {scope.interface_name!r} in package {scope.interface_package_name!r}"


def _validate_pane_view_ref_against_consumer_scope(
    *,
    pane_name: str,
    view_ref: str,
    consumer_scope: _PaneConsumerScope,
) -> tuple[str, str] | None:
    parsed = _parse_view_ref(view_ref)
    if parsed is None:
        return None
    experience_name, _, _ = parsed
    issue = _validate_view_ref_against_catalog(
        view_ref=view_ref,
        experience_catalog=consumer_scope.experience_catalog,
    )
    if issue is None:
        return None
    message, code = issue
    if code == "aware.interface.view_experience_unknown":
        message = (
            f"Interface pane {pane_name!r} view {view_ref!r} is unresolved for consuming "
            + f"{_consumer_scope_label(consumer_scope)} because experience {experience_name!r} "
            + "is outside the declared interface experience_package dependency scope."
        )
    else:
        message = (
            f"Interface pane {pane_name!r} view {view_ref!r} is unresolved for consuming "
            + f"{_consumer_scope_label(consumer_scope)}: {message}"
        )
    return message, code


def _iter_semantic_children(body: Node, wrapper_type: str) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in body.named_children:
        if child.type == wrapper_type:
            children.extend(child.named_children)
            continue
        children.append(child)
    return tuple(children)


def _collect_interface_package_diagnostics(
    *,
    context: DiagnosticsCapabilityContext,
    enabled_groups: frozenset[str],
) -> None:
    resolved = _load_interface_or_pane_sources(context=context)
    if resolved is None or resolved.manifest_kind != "aware_interface_toml":
        return
    if (
        b"interface" not in context.document_bytes
        and b"window" not in context.document_bytes
    ):
        return

    def _is_enabled(group: str) -> bool:
        return group in enabled_groups

    semantic_scope = context.execution.semantic_scope_runtime(
        scope_key=INTERFACE_SEMANTIC_SCOPE_KEYS[0],
        expected_type=InterfaceSemanticScope,
    )
    if semantic_scope is None:
        return
    dependency_scope = semantic_scope.interface_dependency_scope
    if dependency_scope is None:
        return
    pane_catalog_resolution = semantic_scope.pane_catalog_resolution
    pane_catalog = (
        pane_catalog_resolution.pane_catalog
        if pane_catalog_resolution is not None
        else {}
    )

    interface_occurrences: dict[
        str, list[tuple[_InterfaceParsedSource, Node, Node | None]]
    ] = {}
    for source in resolved.sources:
        if source.is_current and source.root.has_error and _is_enabled("interface"):
            context.add(
                rng=ByteRange(start=0, end=len(source.document_bytes)),
                message=f"Interface source {source.relpath.as_posix()} has parse errors.",
                code="aware.interface.parse_error",
            )
        for node in source.root.named_children:
            if node.type != "interface_def":
                continue
            name_node = node.child_by_field_name("name")
            interface_name = _symbol_key(
                _qualified_text(source.document_bytes, name_node)
            )
            if interface_name:
                interface_occurrences.setdefault(interface_name.casefold(), []).append(
                    (source, node, name_node)
                )

    for source in resolved.sources:
        if not source.is_current:
            continue
        for node in source.root.named_children:
            if node.type != "interface_def":
                continue

            name_node = node.child_by_field_name("name")
            interface_name = _symbol_key(
                _qualified_text(source.document_bytes, name_node)
            )
            if not interface_name:
                if _is_enabled("interface"):
                    context.add(
                        rng=_byte_range_for_node(name_node or node),
                        message=(
                            f"Interface declaration has empty name in {source.relpath.as_posix()}."
                        ),
                        code="aware.interface.interface_empty",
                    )
                continue

            if (
                _is_enabled("interface")
                and len(interface_occurrences.get(interface_name.casefold(), ())) > 1
            ):
                context.add(
                    rng=_byte_range_for_node(name_node),
                    message=(
                        f"Duplicate interface declaration {interface_name!r} across interface sources."
                    ),
                    code="aware.interface.interface_duplicate",
                )

            body = node.child_by_field_name("body")
            if body is None:
                if _is_enabled("interface"):
                    context.add(
                        rng=_byte_range_for_node(name_node),
                        message=(
                            f"Interface declaration {interface_name!r} is missing a body."
                        ),
                        code="aware.interface.interface_body_missing",
                    )
                continue

            seen_window_keys: set[str] = set()
            seen_pane_names: set[str] = set()
            layout_sections_by_window: dict[str, dict[str, frozenset[str]]] = {}
            windows_seen = 0

            for child in _iter_semantic_children(body, "interface_item"):
                if child.type == "interface_api_decl":
                    api_ref_node = child.child_by_field_name("api")
                    if _is_enabled("api"):
                        context.add(
                            rng=_byte_range_for_node(api_ref_node or child),
                            message=(
                                f"Interface {interface_name!r} declares retired api ownership; "
                                "declare projection-view invocation actions instead."
                            ),
                            code="aware.interface.api_retired",
                        )
                    continue

                if child.type == "interface_window_def":
                    windows_seen += 1
                    _collect_window_diagnostics(
                        context=context,
                        source=source,
                        interface_name=interface_name,
                        node=child,
                        seen_window_keys=seen_window_keys,
                        layout_sections_by_window=layout_sections_by_window,
                        enabled_groups=enabled_groups,
                    )
                    continue

                if child.type == "interface_pane_def":
                    _collect_pane_composition_diagnostics(
                        context=context,
                        source=source,
                        interface_name=interface_name,
                        node=child,
                        seen_pane_names=seen_pane_names,
                        dependency_scope=dependency_scope,
                        pane_catalog=pane_catalog,
                        pane_catalog_authoritative=(
                            pane_catalog_resolution.declared_workspace
                            if pane_catalog_resolution is not None
                            else False
                        ),
                        layout_sections_by_window=layout_sections_by_window,
                        enabled_groups=enabled_groups,
                    )

            if _is_enabled("interface") and windows_seen == 0:
                context.add(
                    rng=_byte_range_for_node(name_node),
                    message=(
                        f"Interface {interface_name!r} must declare at least one window."
                    ),
                    code="aware.interface.window_required",
                )


def _collect_window_diagnostics(
    *,
    context: DiagnosticsCapabilityContext,
    source: _InterfaceParsedSource,
    interface_name: str,
    node: Node,
    seen_window_keys: set[str],
    layout_sections_by_window: dict[str, dict[str, frozenset[str]]],
    enabled_groups: frozenset[str],
) -> None:
    def _is_enabled(group: str) -> bool:
        return group in enabled_groups

    window_name_node = node.child_by_field_name("window_name")
    window_key = _symbol_key(_qualified_text(source.document_bytes, window_name_node))
    if not window_key:
        if _is_enabled("window"):
            context.add(
                rng=_byte_range_for_node(window_name_node or node),
                message=(f"Interface {interface_name!r} has a window with empty key."),
                code="aware.interface.window_empty",
            )
        return

    window_token = window_key.casefold()
    if window_token in seen_window_keys and _is_enabled("window"):
        context.add(
            rng=_byte_range_for_node(window_name_node),
            message=(f"Interface {interface_name!r} duplicates window {window_key!r}."),
            code="aware.interface.window_duplicate",
        )
    seen_window_keys.add(window_token)

    body = node.child_by_field_name("body")
    if body is None:
        if _is_enabled("window"):
            context.add(
                rng=_byte_range_for_node(window_name_node),
                message=(
                    f"Interface {interface_name!r} window {window_key!r} is missing a body."
                ),
                code="aware.interface.window_body_missing",
            )
        return

    seen_layout_keys: set[str] = set()
    layout_sections: dict[str, frozenset[str]] = {}
    default_layout_count = 0
    layout_count = 0
    for child in _iter_semantic_children(body, "interface_layout_item"):
        if child.type != "interface_layout_def":
            continue
        layout_count += 1
        layout_name_node = child.child_by_field_name("layout_name")
        layout_key = _symbol_key(
            _qualified_text(source.document_bytes, layout_name_node)
        )
        if not layout_key:
            if _is_enabled("layout"):
                context.add(
                    rng=_byte_range_for_node(layout_name_node or child),
                    message=(
                        f"Interface {interface_name!r} window {window_key!r} has a layout with empty key."
                    ),
                    code="aware.interface.layout_empty",
                )
            continue

        layout_token = layout_key.casefold()
        if layout_token in seen_layout_keys and _is_enabled("layout"):
            context.add(
                rng=_byte_range_for_node(layout_name_node),
                message=(
                    f"Interface {interface_name!r} window {window_key!r} duplicates layout {layout_key!r}."
                ),
                code="aware.interface.layout_duplicate",
            )
        seen_layout_keys.add(layout_token)

        if child.child_by_field_name("default_marker") is not None:
            default_layout_count += 1
            if default_layout_count > 1 and _is_enabled("layout"):
                context.add(
                    rng=_byte_range_for_node(layout_name_node),
                    message=(
                        f"Interface {interface_name!r} window {window_key!r} allows at most one default layout."
                    ),
                    code="aware.interface.layout_default_duplicate",
                )

        layout_body = child.child_by_field_name("body")
        if layout_body is None:
            if _is_enabled("layout"):
                context.add(
                    rng=_byte_range_for_node(layout_name_node),
                    message=(
                        f"Interface {interface_name!r} window {window_key!r} layout {layout_key!r} is missing a body."
                    ),
                    code="aware.interface.layout_body_missing",
                )
            continue

        seen_section_keys: set[str] = set()
        for layout_child in _iter_semantic_children(
            layout_body, "interface_layout_item"
        ):
            if layout_child.type != "interface_layout_section_def":
                continue
            section_name_node = layout_child.child_by_field_name("section_name")
            section_key = _symbol_key(
                _qualified_text(source.document_bytes, section_name_node)
            )
            if not section_key:
                if _is_enabled("section"):
                    context.add(
                        rng=_byte_range_for_node(section_name_node or layout_child),
                        message=(
                            f"Interface {interface_name!r} window {window_key!r} "
                            + f"layout {layout_key!r} has an empty section key."
                        ),
                        code="aware.interface.section_empty",
                    )
                continue
            section_token = section_key.casefold()
            if section_token in seen_section_keys and _is_enabled("section"):
                context.add(
                    rng=_byte_range_for_node(section_name_node),
                    message=(
                        f"Interface {interface_name!r} window {window_key!r} "
                        + f"layout {layout_key!r} duplicates section {section_key!r}."
                    ),
                    code="aware.interface.section_duplicate",
                )
            seen_section_keys.add(section_token)
        layout_sections[layout_token] = frozenset(seen_section_keys)

    if layout_count == 0 and _is_enabled("layout"):
        context.add(
            rng=_byte_range_for_node(window_name_node),
            message=(
                f"Interface {interface_name!r} window {window_key!r} must declare at least one layout."
            ),
            code="aware.interface.layout_required",
        )
    if layout_sections:
        layout_sections_by_window[window_key.casefold()] = layout_sections


def _collect_pane_composition_diagnostics(
    *,
    context: DiagnosticsCapabilityContext,
    source: _InterfaceParsedSource,
    interface_name: str,
    node: Node,
    seen_pane_names: set[str],
    dependency_scope: _InterfaceDependencyScope,
    pane_catalog: dict[str, _WorkspacePaneCatalogEntry],
    pane_catalog_authoritative: bool,
    layout_sections_by_window: dict[str, dict[str, frozenset[str]]],
    enabled_groups: frozenset[str],
) -> None:
    def _is_enabled(group: str) -> bool:
        return group in enabled_groups

    pane_name_node = node.child_by_field_name("pane_name")
    pane_name = _symbol_key(_qualified_text(source.document_bytes, pane_name_node))
    if not pane_name:
        if _is_enabled("pane_composition"):
            context.add(
                rng=_byte_range_for_node(pane_name_node or node),
                message=(
                    f"Interface {interface_name!r} has a pane composition with empty name."
                ),
                code="aware.interface.pane_composition_empty",
            )
        return

    pane_token = pane_name.casefold()
    if pane_token in seen_pane_names and _is_enabled("pane_composition"):
        context.add(
            rng=_byte_range_for_node(pane_name_node),
            message=(
                f"Interface {interface_name!r} duplicates pane composition {pane_name!r}."
            ),
            code="aware.interface.pane_composition_duplicate",
        )
    seen_pane_names.add(pane_token)

    pane_entry = pane_catalog.get(pane_token)
    if (
        _is_enabled("pane_composition")
        and pane_entry is None
        and (pane_catalog_authoritative or pane_catalog)
    ):
        context.add(
            rng=_byte_range_for_node(pane_name_node),
            message=(
                f"Interface {interface_name!r} references unknown pane {pane_name!r}."
            ),
            code="aware.interface.pane_composition_unknown",
        )

    body = node.child_by_field_name("body")
    if body is None:
        if _is_enabled("pane_composition"):
            context.add(
                rng=_byte_range_for_node(pane_name_node),
                message=(
                    f"Interface {interface_name!r} pane composition {pane_name!r} is missing a body."
                ),
                code="aware.interface.pane_composition_body_missing",
            )
        return

    mount_count = 0
    seen_mount_targets: set[str] = set()
    narrative_seen = False
    for child in _iter_semantic_children(body, "interface_pane_item"):
        if child.type == "interface_pane_mount_def":
            mount_count += 1
            target_node = child.child_by_field_name("target")
            target_ref = _qualified_text(source.document_bytes, target_node)
            target_parts = target_ref.split(".")
            if len(target_parts) != 3 and _is_enabled("mount"):
                context.add(
                    rng=_byte_range_for_node(target_node or child),
                    message=(
                        f"Interface {interface_name!r} pane composition {pane_name!r} "
                        + f"has invalid mount target {target_ref!r}."
                    ),
                    code="aware.interface.mount_invalid",
                )
                continue

            mount_key = target_ref.casefold()
            if mount_key in seen_mount_targets and _is_enabled("mount"):
                context.add(
                    rng=_byte_range_for_node(target_node),
                    message=(
                        f"Interface {interface_name!r} pane composition {pane_name!r} "
                        + f"duplicates mount {target_ref!r}."
                    ),
                    code="aware.interface.mount_duplicate",
                )
            seen_mount_targets.add(mount_key)

            window_scope = layout_sections_by_window.get(target_parts[0].casefold())
            if _is_enabled("mount") and window_scope is None:
                context.add(
                    rng=_byte_range_for_node(target_node),
                    message=(
                        f"Interface {interface_name!r} pane composition {pane_name!r} "
                        + f"mounts unknown window {target_parts[0]!r}."
                    ),
                    code="aware.interface.mount_window_unknown",
                )
                continue

            layout_scope = (
                window_scope.get(target_parts[1].casefold())
                if window_scope is not None
                else None
            )
            if _is_enabled("mount") and layout_scope is None:
                context.add(
                    rng=_byte_range_for_node(target_node),
                    message=(
                        f"Interface {interface_name!r} pane composition {pane_name!r} "
                        + f"mounts unknown layout {target_parts[1]!r} under window {target_parts[0]!r}."
                    ),
                    code="aware.interface.mount_layout_unknown",
                )
                continue

            if (
                _is_enabled("mount")
                and layout_scope is not None
                and target_parts[2].casefold() not in layout_scope
            ):
                context.add(
                    rng=_byte_range_for_node(target_node),
                    message=(
                        f"Interface {interface_name!r} pane composition {pane_name!r} "
                        + f"mounts unknown section {target_parts[2]!r} under "
                        + f"{target_parts[0]!r}.{target_parts[1]!r}."
                    ),
                    code="aware.interface.mount_section_unknown",
                )
            continue

        if child.type == "interface_pane_narrative_def":
            if narrative_seen and _is_enabled("narrative"):
                context.add(
                    rng=_byte_range_for_node(
                        child.child_by_field_name("narrative") or child
                    ),
                    message=(
                        f"Interface {interface_name!r} pane composition {pane_name!r} has multiple narratives."
                    ),
                    code="aware.interface.narrative_duplicate",
                )
            narrative_seen = True

    if _is_enabled("pane_composition") and pane_entry is not None and mount_count > 0:
        for pane_view_ref in pane_entry.view_refs:
            issue = _validate_interface_pane_view_against_dependency_scope(
                interface_name=interface_name,
                pane_name=pane_name,
                view_ref=pane_view_ref,
                dependency_scope=dependency_scope,
                mounted=True,
            )
            if issue is None:
                continue
            message, code = issue
            context.add(
                rng=_byte_range_for_node(pane_name_node),
                message=message,
                code=code,
            )

    if mount_count == 0 and _is_enabled("mount"):
        context.add(
            rng=_byte_range_for_node(pane_name_node),
            message=(
                f"Interface {interface_name!r} pane composition {pane_name!r} must declare at least one mount."
            ),
            code="aware.interface.mount_required",
        )


def _collect_pane_package_diagnostics(
    *,
    context: DiagnosticsCapabilityContext,
    enabled_groups: frozenset[str],
) -> None:
    resolved = _load_interface_or_pane_sources(context=context)
    if resolved is None or resolved.manifest_kind != "aware_pane_toml":
        return
    if b"pane" not in context.document_bytes and b"view" not in context.document_bytes:
        return

    def _is_enabled(group: str) -> bool:
        return group in enabled_groups

    semantic_scope = context.execution.semantic_scope_runtime(
        scope_key=INTERFACE_SEMANTIC_SCOPE_KEYS[0],
        expected_type=InterfaceSemanticScope,
    )
    if semantic_scope is None:
        return

    pane_occurrences: dict[
        str, list[tuple[_InterfaceParsedSource, Node, Node | None]]
    ] = {}
    for source in resolved.sources:
        if source.is_current and source.root.has_error and _is_enabled("pane"):
            context.add(
                rng=ByteRange(start=0, end=len(source.document_bytes)),
                message=f"Pane source {source.relpath.as_posix()} has parse errors.",
                code="aware.interface.pane_parse_error",
            )
        for node in source.root.named_children:
            if node.type != "pane_def":
                continue
            name_node = node.child_by_field_name("name")
            pane_name = _symbol_key(_qualified_text(source.document_bytes, name_node))
            if pane_name:
                pane_occurrences.setdefault(pane_name.casefold(), []).append(
                    (source, node, name_node)
                )

    for source in resolved.sources:
        if not source.is_current:
            continue
        for node in source.root.named_children:
            if node.type != "pane_def":
                continue

            pane_name_node = node.child_by_field_name("name")
            pane_name = _symbol_key(
                _qualified_text(source.document_bytes, pane_name_node)
            )
            if not pane_name:
                if _is_enabled("pane"):
                    context.add(
                        rng=_byte_range_for_node(pane_name_node or node),
                        message=(
                            f"Interface pane declaration has empty name in {source.relpath.as_posix()}."
                        ),
                        code="aware.interface.pane_empty",
                    )
                continue

            if (
                _is_enabled("pane")
                and len(pane_occurrences.get(pane_name.casefold(), ())) > 1
            ):
                context.add(
                    rng=_byte_range_for_node(pane_name_node),
                    message=(
                        f"Duplicate pane declaration {pane_name!r} across pane sources."
                    ),
                    code="aware.interface.pane_duplicate",
                )

            body = node.child_by_field_name("body")
            if body is None:
                if _is_enabled("pane"):
                    context.add(
                        rng=_byte_range_for_node(pane_name_node),
                        message=(
                            f"Interface pane declaration {pane_name!r} is missing a body."
                        ),
                        code="aware.interface.pane_body_missing",
                    )
                continue

            kind_seen = False
            view_count = 0
            default_view_count = 0
            seen_view_refs: set[str] = set()
            pane_consumer_scopes = semantic_scope.pane_consumer_scopes(
                pane_name=pane_name
            )
            for child in _iter_semantic_children(body, "pane_item"):
                if child.type == "pane_kind_decl":
                    if kind_seen and _is_enabled("pane"):
                        context.add(
                            rng=_byte_range_for_node(
                                child.child_by_field_name("kind") or child
                            ),
                            message=(
                                f"Interface pane {pane_name!r} has multiple kind declarations."
                            ),
                            code="aware.interface.pane_kind_duplicate",
                        )
                    kind_seen = True
                    continue

                if child.type == "pane_view_def":
                    view_count += 1
                    if child.child_by_field_name("default_marker") is not None:
                        default_view_count += 1
                    view_ref_node = child.child_by_field_name("view")
                    view_ref = _qualified_text(source.document_bytes, view_ref_node)
                    if not view_ref:
                        if _is_enabled("view"):
                            context.add(
                                rng=_byte_range_for_node(view_ref_node or child),
                                message=(
                                    f"Interface pane {pane_name!r} has a view with empty reference."
                                ),
                                code="aware.interface.view_empty",
                            )
                        continue
                    view_key = view_ref.casefold()
                    if view_key in seen_view_refs and _is_enabled("view"):
                        context.add(
                            rng=_byte_range_for_node(view_ref_node),
                            message=(
                                f"Interface pane {pane_name!r} duplicates view {view_ref!r}."
                            ),
                            code="aware.interface.view_duplicate",
                        )
                    seen_view_refs.add(view_key)
                    if _is_enabled("view"):
                        issue = _validate_view_ref_shape(view_ref)
                        if issue is not None:
                            message, code = issue
                            context.add(
                                rng=_byte_range_for_node(view_ref_node),
                                message=message,
                                code=code,
                            )
                            continue
                        for consumer_scope in pane_consumer_scopes:
                            issue = _validate_pane_view_ref_against_consumer_scope(
                                pane_name=pane_name,
                                view_ref=view_ref,
                                consumer_scope=consumer_scope,
                            )
                            if issue is None:
                                continue
                            message, code = issue
                            context.add(
                                rng=_byte_range_for_node(view_ref_node),
                                message=message,
                                code=code,
                            )
                    continue

                if child.type == "pane_endpoint_def":
                    endpoint_ref_node = child.child_by_field_name("endpoint")
                    if _is_enabled("endpoint"):
                        context.add(
                            rng=_byte_range_for_node(endpoint_ref_node or child),
                            message=(
                                f"Interface pane {pane_name!r} declares retired endpoint ownership; "
                                "declare projection-view invocation actions and bind render actions "
                                "by view_action_key."
                            ),
                            code="aware.interface.endpoint_retired",
                        )
                    continue

            if _is_enabled("pane") and not kind_seen:
                context.add(
                    rng=_byte_range_for_node(pane_name_node),
                    message=(
                        f"Interface pane {pane_name!r} must declare exactly one kind."
                    ),
                    code="aware.interface.pane_kind_required",
                )
            if _is_enabled("pane") and view_count == 0:
                context.add(
                    rng=_byte_range_for_node(pane_name_node),
                    message=(
                        f"Interface pane {pane_name!r} must declare at least one view."
                    ),
                    code="aware.interface.view_required",
                )
            if _is_enabled("pane") and default_view_count != 1:
                context.add(
                    rng=_byte_range_for_node(pane_name_node),
                    message=(
                        f"Interface pane {pane_name!r} requires exactly one default view; got {default_view_count}."
                    ),
                    code="aware.interface.view_default_required",
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


def _interface_root_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_interface")


def _interface_api_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_api")


def _interface_window_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_window")


def _interface_layout_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_layout")


def _interface_section_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_section")


def _interface_pane_composition_tokens_provider(
    collector: SemanticTokenCollector,
) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_pane_composition")


def _interface_mount_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_mount")


def _interface_narrative_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_narrative")


def _pane_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_pane")


def _view_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_view")


def _endpoint_tokens_provider(collector: SemanticTokenCollector) -> None:
    _semantic_tokens_provider(collector, owner_group="interface_endpoint")
