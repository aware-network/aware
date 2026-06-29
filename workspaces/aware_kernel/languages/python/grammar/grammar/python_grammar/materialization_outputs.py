"""Python-owned producers for declared materialization outputs."""

from __future__ import annotations

import json
import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

import msgpack

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.graph.config.model_bootstrap import get_node_function_config
from aware_meta.language_plugin import (
    MetaLanguageDeclaredOutputProducedFile,
    MetaLanguageDeclaredOutputProducerRequest,
    MetaLanguageDeclaredOutputProducerResult,
    MetaLanguageMaterializationDestination,
)
from aware_orm.runtime.models_manifest import (
    ClassModelEntry,
    EnumModelEntry,
    FunctionModelEntry,
    ModelsManifest,
)
from aware_meta.orm_artifacts.binding import (
    dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph,
)
from aware_meta.graph.config.render.ocg_node_paths_manifest import (
    OCGNodePathEntry,
    OCGNodePathsManifest,
)
from aware_utils.string_transform import to_pascal_case, to_snake_case

from python_grammar.layout_strategy import PythonLayoutStrategy


_PYTHON_MODELS_OUTPUT_KEY = "python.models_manifest"
_PYTHON_ORM_GRAPH_BINDING_OUTPUT_KEY = "python.orm_graph_binding"
_PYTHON_OCG_BINDING_SNAPSHOT_OUTPUT_KEY = "python.ocg_binding_snapshot"
_PYTHON_BOOTSTRAP_OUTPUT_KEY = "python.bootstrap_manifest"
_PYTHON_OCG_NODE_PATHS_OUTPUT_KEY = "python.ocg_node_paths"
_MATERIALIZATION_ROOT_DESTINATION_KIND = "materialization_root"
_PACKAGE_ARTIFACTS_ROOT_DESTINATION_KIND = "package_artifacts_root"
_API_PUBLIC_PACKAGE_RENDERER_PROFILE = "api_public_package"
_API_SERVICE_PROTOCOL_RENDERER_PROFILE = "api_service_protocol"
_VOLATILE_OCG_BINDING_KEY_PREFIX = "code_section_"


class _PythonEntityPathLayout(Protocol):
    def bind_graph(self, object_config_graph: object) -> None: ...

    def get_class_file_path(self, class_config: object) -> Path: ...

    def get_enum_file_path(self, enum_config: object) -> Path: ...


@dataclass(frozen=True, slots=True)
class _ResolvedDescriptorTarget:
    path: Path
    destination: MetaLanguageMaterializationDestination | None = None


@dataclass(frozen=True, slots=True)
class _ApiPublicPackageEntityPathLayout:
    def bind_graph(self, object_config_graph: object) -> None:
        del object_config_graph

    def get_class_file_path(self, class_config: object) -> Path:
        return Path("models") / _entity_file_name(class_config, label="class_config")

    def get_enum_file_path(self, enum_config: object) -> Path:
        return Path("models") / _entity_file_name(enum_config, label="enum_config")


def produce_python_declared_outputs(
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> MetaLanguageDeclaredOutputProducerResult:
    """Produce Python package metadata declared by the Python plugin."""

    import_root = _normalized_import_root(request.import_root or request.package_name)
    if not import_root:
        return MetaLanguageDeclaredOutputProducerResult(
            warnings=("Python declared output producer skipped: missing import_root.",)
        )

    produced_files: list[MetaLanguageDeclaredOutputProducedFile] = []
    produced_output_keys: set[str] = set()
    layout_strategy = _layout_strategy(request=request, import_root=import_root)
    models_manifest = (
        _build_models_manifest(
            request=request,
            import_root=import_root,
            layout_strategy=layout_strategy,
        )
        if _request_emits_runtime_model_index(request)
        else None
    )
    node_paths_manifest = (
        _build_ocg_node_paths_manifest(
            request=request,
            layout_strategy=layout_strategy,
        )
        if _request_emits_runtime_model_index(request)
        else OCGNodePathsManifest(language=CodeLanguage.python.value)
    )

    for descriptor in request.descriptors:
        if not _descriptor_applies_to_request(descriptor=descriptor, request=request):
            continue
        descriptor_targets = _resolve_descriptor_targets(
            descriptor.path_templates,
            import_root=import_root,
            package_name=request.package_name,
            destinations=request.destinations,
        )
        if not descriptor_targets:
            continue

        if descriptor.output_key == _PYTHON_MODELS_OUTPUT_KEY:
            if models_manifest is None:
                continue
            content = (
                models_manifest.model_dump_json(indent=2, exclude_none=True) + "\n"
            )
            for target in descriptor_targets:
                _validate_models_manifest_target(
                    manifest=models_manifest,
                    request=request,
                    import_root=import_root,
                    target=target,
                )
                produced_files.append(
                    _text_file_for_descriptor(
                        descriptor=descriptor,
                        target=target,
                        content=content,
                    )
                )
            produced_output_keys.add(descriptor.output_key)
        elif descriptor.output_key == _PYTHON_ORM_GRAPH_BINDING_OUTPUT_KEY:
            if models_manifest is None:
                continue
            produced_files.extend(
                _bytes_files_for_descriptor(
                    descriptor=descriptor,
                    targets=descriptor_targets,
                    content=dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
                        object_config_graph=request.language_graph
                    ),
                )
            )
            produced_output_keys.add(descriptor.output_key)
        elif descriptor.output_key == _PYTHON_OCG_BINDING_SNAPSHOT_OUTPUT_KEY:
            produced_files.extend(
                _bytes_files_for_descriptor(
                    descriptor=descriptor,
                    targets=descriptor_targets,
                    content=_dump_ocg_binding_snapshot_msgpack(
                        object_config_graph=request.language_graph
                    ),
                )
            )
            produced_output_keys.add(descriptor.output_key)
        elif descriptor.output_key == _PYTHON_BOOTSTRAP_OUTPUT_KEY:
            for target in descriptor_targets:
                target_import_root = _target_import_root(target, import_root)
                dependency_import_roots = _dependency_import_roots(
                    request,
                    target_import_root,
                    target.destination,
                )
                payload = {
                    "version": "v1",
                    "package_prefix": target_import_root,
                    "dependency_import_roots": dependency_import_roots,
                    "modules": _module_names(
                        request.generated_file_paths,
                        target_import_root,
                        target.destination,
                    ),
                }
                pydantic_model_dependency_import_roots = (
                    _pydantic_model_dependency_import_roots(
                        request,
                        target_import_root,
                        target.destination,
                        candidate_dependency_roots=dependency_import_roots,
                    )
                )
                if pydantic_model_dependency_import_roots:
                    payload["pydantic_model_dependency_import_roots"] = (
                        pydantic_model_dependency_import_roots
                    )
                produced_files.append(
                    _text_file_for_descriptor(
                        descriptor=descriptor,
                        target=target,
                        content=json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    )
                )
            produced_output_keys.add(descriptor.output_key)
        elif descriptor.output_key == _PYTHON_OCG_NODE_PATHS_OUTPUT_KEY:
            if not node_paths_manifest.nodes:
                continue
            produced_files.extend(
                _text_files_for_descriptor(
                    descriptor=descriptor,
                    targets=descriptor_targets,
                    content=node_paths_manifest.model_dump_json(
                        indent=2,
                        exclude_none=True,
                    )
                    + "\n",
                )
            )
            produced_output_keys.add(descriptor.output_key)
    return MetaLanguageDeclaredOutputProducerResult(
        produced_files=tuple(produced_files),
        metrics={
            "python_declared_output_count": len(produced_files),
            "python_declared_output_key_count": len(produced_output_keys),
            "python_declared_output_keys": tuple(sorted(produced_output_keys)),
        },
    )


def _layout_strategy(
    *,
    request: MetaLanguageDeclaredOutputProducerRequest,
    import_root: str,
) -> _PythonEntityPathLayout:
    if request.renderer_profile == _API_PUBLIC_PACKAGE_RENDERER_PROFILE:
        layout_strategy: _PythonEntityPathLayout = _ApiPublicPackageEntityPathLayout()
    else:
        layout_strategy = PythonLayoutStrategy(
            request.output_root,
            entity_template_paths={
                key: Path(value) for key, value in request.entity_file_paths.items()
            },
            generated_ocg_node_manifest=request.generated_ocg_node_manifest,
            import_root=import_root,
        )
    layout_strategy.bind_graph(request.language_graph)
    return layout_strategy


def _request_emits_runtime_model_index(
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> bool:
    return request.renderer_profile != _API_SERVICE_PROTOCOL_RENDERER_PROFILE


def _build_models_manifest(
    *,
    request: MetaLanguageDeclaredOutputProducerRequest,
    import_root: str,
    layout_strategy: _PythonEntityPathLayout,
) -> ModelsManifest | None:
    classes: list[ClassModelEntry] = []
    enums: list[EnumModelEntry] = []
    for node in request.language_graph.object_config_graph_nodes:
        if node.class_config is not None:
            class_config = node.class_config
            classes.append(
                ClassModelEntry(
                    class_config_id=class_config.id,
                    module=_module_name_for_path(
                        layout_strategy.get_class_file_path(class_config),
                        import_root,
                    ),
                    name=class_config.name,
                    aware_class_ref=_authored_class_ref_from_class_fqn(
                        class_fqn=class_config.class_fqn,
                    ),
                    functions=_function_entries(class_config),
                )
            )
        elif node.enum_config is not None:
            enum_config = node.enum_config
            enums.append(
                EnumModelEntry(
                    enum_config_id=enum_config.id,
                    module=_module_name_for_path(
                        layout_strategy.get_enum_file_path(enum_config),
                        import_root,
                    ),
                    name=enum_config.name,
                )
            )
    if not classes and not enums:
        return None
    classes.sort(key=lambda item: (item.module, item.name, str(item.class_config_id)))
    enums.sort(key=lambda item: (item.module, item.name, str(item.enum_config_id)))
    return ModelsManifest(
        language=CodeLanguage.python.value,
        classes=classes,
        enums=enums,
    )


def _function_entries(class_config: object) -> list[FunctionModelEntry]:
    class_name = str(getattr(class_config, "name", "") or "")
    entries: list[FunctionModelEntry] = []
    for link in getattr(class_config, "class_config_function_configs", ()) or ():
        function_config = getattr(link, "function_config", None)
        function_id = getattr(function_config, "id", None)
        function_name = str(getattr(function_config, "name", "") or "")
        if not isinstance(function_id, UUID) or not function_name:
            continue
        input_name, output_name = _function_io_class_names(
            class_name=class_name,
            function_name=function_name,
        )
        entries.append(
            FunctionModelEntry(
                function_config_id=function_id,
                name=function_name,
                input_model=input_name,
                output_model=output_name,
            )
        )
    return sorted(entries, key=lambda item: (item.name, str(item.function_config_id)))


def _authored_class_ref_from_class_fqn(*, class_fqn: str) -> str:
    parts = [part.strip() for part in class_fqn.split(".") if part.strip()]
    if len(parts) <= 2:
        return class_fqn.strip()
    return ".".join(
        [
            parts[0],
            *[part for part in parts[1:-1] if part.casefold() != "default"],
            parts[-1],
        ]
    )


def _function_io_class_names(*, class_name: str, function_name: str) -> tuple[str, str]:
    prefix = f"{to_pascal_case(class_name)}{to_pascal_case(function_name)}"
    return f"{prefix}Input", f"{prefix}Output"


def _build_ocg_node_paths_manifest(
    *,
    request: MetaLanguageDeclaredOutputProducerRequest,
    layout_strategy: _PythonEntityPathLayout,
) -> OCGNodePathsManifest:
    entries: list[OCGNodePathEntry] = []
    for node in request.language_graph.object_config_graph_nodes:
        entity_id: UUID | None = None
        relative_path: Path | None = None
        if node.class_config is not None:
            entity_id = node.class_config.id
            relative_path = layout_strategy.get_class_file_path(node.class_config)
        elif node.enum_config is not None:
            entity_id = node.enum_config.id
            relative_path = layout_strategy.get_enum_file_path(node.enum_config)
        else:
            function_config = get_node_function_config(node)
            if function_config is not None:
                entity_id = function_config.id
                relative_path = layout_strategy.get_function_file_path(function_config)
        if entity_id is None or relative_path is None:
            continue
        entries.append(
            OCGNodePathEntry(
                node_id=str(node.id),
                node_type=str(node.type.value),
                entity_id=str(entity_id),
                relative_path=relative_path.as_posix(),
            )
        )
    entries.sort(
        key=lambda item: (
            item.node_type,
            item.relative_path,
            item.entity_id,
            item.node_id,
        )
    )
    return OCGNodePathsManifest(language=CodeLanguage.python.value, nodes=entries)


def _dump_ocg_binding_snapshot_msgpack(*, object_config_graph: object) -> bytes:
    if hasattr(object_config_graph, "model_dump"):
        payload = object_config_graph.model_dump(mode="json", exclude_none=True)
    elif isinstance(object_config_graph, dict):
        payload = object_config_graph
    else:
        raise TypeError(
            "Python OCG binding snapshot output requires an ObjectConfigGraph "
            f"payload, got {type(object_config_graph).__name__}"
        )
    nodes = _strip_volatile_ocg_binding_fields(
        payload.get("object_config_graph_nodes", ())
    )
    return msgpack.dumps(
        {
            "version": 1,
            "object_config_graph_nodes": nodes,
        },
        use_bin_type=True,
    )


def _strip_volatile_ocg_binding_fields(value: object) -> object:
    """Remove source-section provenance fields without copying clean subtrees."""

    if isinstance(value, dict):
        normalized: dict[object, object] | None = None
        for key, child in value.items():
            if isinstance(key, str) and key.startswith(
                _VOLATILE_OCG_BINDING_KEY_PREFIX
            ):
                if normalized is None:
                    normalized = {}
                    for prior_key, prior_child in value.items():
                        if prior_key == key:
                            break
                        normalized[prior_key] = prior_child
                continue

            normalized_child = _strip_volatile_ocg_binding_fields(child)
            if normalized is not None:
                normalized[key] = normalized_child
            elif normalized_child is not child:
                normalized = {}
                for prior_key, prior_child in value.items():
                    if prior_key == key:
                        break
                    normalized[prior_key] = prior_child
                normalized[key] = normalized_child
        return value if normalized is None else normalized

    if isinstance(value, list):
        normalized_items: list[object] | None = None
        for index, child in enumerate(value):
            normalized_child = _strip_volatile_ocg_binding_fields(child)
            if normalized_items is not None:
                normalized_items.append(normalized_child)
            elif normalized_child is not child:
                normalized_items = list(value[:index])
                normalized_items.append(normalized_child)
        return value if normalized_items is None else normalized_items

    if isinstance(value, tuple):
        normalized_items = None
        for index, child in enumerate(value):
            normalized_child = _strip_volatile_ocg_binding_fields(child)
            if normalized_items is not None:
                normalized_items.append(normalized_child)
            elif normalized_child is not child:
                normalized_items = list(value[:index])
                normalized_items.append(normalized_child)
        return value if normalized_items is None else tuple(normalized_items)

    return value


def _entity_file_name(entity: object, *, label: str) -> str:
    name = str(getattr(entity, "name", "") or "").strip()
    if not name:
        raise ValueError(f"Cannot resolve Python model path for unnamed {label}.")
    return f"{to_snake_case(name)}.py"


def _validate_models_manifest_target(
    *,
    manifest: ModelsManifest,
    request: MetaLanguageDeclaredOutputProducerRequest,
    import_root: str,
    target: _ResolvedDescriptorTarget,
) -> None:
    if (
        target.destination is None
        or target.destination.kind != _PACKAGE_ARTIFACTS_ROOT_DESTINATION_KIND
    ):
        return
    available_modules = set(
        _module_names(
            request.generated_file_paths,
            import_root,
            target.destination,
        )
    )
    if not available_modules:
        return
    manifest_modules = {
        str(entry.module)
        for entry in (*manifest.classes, *manifest.enums)
        if str(entry.module).strip()
    }
    missing_modules = sorted(manifest_modules - available_modules)
    if not missing_modules:
        return
    preview = ", ".join(missing_modules[:5])
    if len(missing_modules) > 5:
        preview += f", ... (+{len(missing_modules) - 5} more)"
    target_key = target.destination.key if target.destination is not None else "default"
    raise ValueError(
        "Python models manifest references modules that are not present in "
        + f"generated package files for import_root={import_root!r}, "
        + f"target={target_key!r}: {preview}. "
        + "This usually means declared-output metadata is using a different "
        + "layout than the package renderer."
    )


def _text_files_for_descriptor(
    *,
    descriptor: object,
    targets: Iterable[_ResolvedDescriptorTarget],
    content: str,
) -> tuple[MetaLanguageDeclaredOutputProducedFile, ...]:
    return tuple(
        _text_file_for_descriptor(
            descriptor=descriptor,
            target=target,
            content=content,
        )
        for target in targets
    )


def _text_file_for_descriptor(
    *,
    descriptor: object,
    target: _ResolvedDescriptorTarget,
    content: str,
) -> MetaLanguageDeclaredOutputProducedFile:
    return MetaLanguageDeclaredOutputProducedFile(
        output_key=getattr(descriptor, "output_key"),
        path=target.path,
        content_text=content,
        output_kind=getattr(descriptor, "output_kind"),
        artifact_role=getattr(descriptor, "artifact_role"),
    )


def _bytes_files_for_descriptor(
    *,
    descriptor: object,
    targets: Iterable[_ResolvedDescriptorTarget],
    content: bytes,
) -> tuple[MetaLanguageDeclaredOutputProducedFile, ...]:
    return tuple(
        MetaLanguageDeclaredOutputProducedFile(
            output_key=getattr(descriptor, "output_key"),
            path=target.path,
            content_bytes=content,
            output_kind=getattr(descriptor, "output_kind"),
            artifact_role=getattr(descriptor, "artifact_role"),
        )
        for target in targets
    )


def _descriptor_applies_to_request(
    *,
    descriptor: object,
    request: MetaLanguageDeclaredOutputProducerRequest,
) -> bool:
    if request.renderer_profile == "ontology_dto" and getattr(
        descriptor, "output_key", None
    ) not in {
        _PYTHON_BOOTSTRAP_OUTPUT_KEY,
        _PYTHON_OCG_NODE_PATHS_OUTPUT_KEY,
    }:
        return False
    renderer_profiles = tuple(getattr(descriptor, "renderer_profiles", ()) or ())
    if renderer_profiles and request.renderer_profile not in renderer_profiles:
        return False
    renderer_kinds = tuple(getattr(descriptor, "renderer_kinds", ()) or ())
    if renderer_kinds and request.renderer_kind not in renderer_kinds:
        return False
    materialization_sources = tuple(
        getattr(descriptor, "materialization_sources", ()) or ()
    )
    if (
        materialization_sources
        and request.materialization_source is not None
        and request.materialization_source not in materialization_sources
    ):
        return False
    return True


def _resolve_descriptor_targets(
    path_templates: tuple[str, ...],
    *,
    import_root: str,
    package_name: str | None,
    destinations: tuple[MetaLanguageMaterializationDestination, ...],
) -> tuple[_ResolvedDescriptorTarget, ...]:
    targets: list[_ResolvedDescriptorTarget] = []
    if destinations:
        for destination in destinations:
            destination_import_root = destination.import_root or import_root
            for template in path_templates:
                path = _resolve_descriptor_path_for_destination(
                    template=template,
                    import_root=destination_import_root,
                    package_name=destination.package_name or package_name,
                    destination=destination,
                )
                if path is not None:
                    targets.append(
                        _ResolvedDescriptorTarget(
                            path=path,
                            destination=destination,
                        )
                    )
        return _dedupe_targets(targets)

    for template in path_templates:
        value = template.format(
            import_root=import_root,
            package_name=package_name or "",
            language="python",
        )
        targets.append(_ResolvedDescriptorTarget(path=Path(value)))
    return _dedupe_targets(targets)


def _resolve_descriptor_path_for_destination(
    *,
    template: str,
    import_root: str,
    package_name: str | None,
    destination: MetaLanguageMaterializationDestination,
) -> Path | None:
    value = template.format(
        import_root=import_root,
        package_name=package_name or "",
        language="python",
    )
    if destination.kind == _MATERIALIZATION_ROOT_DESTINATION_KIND:
        prefix = ".aware/materializations/"
        if not value.startswith(prefix):
            return None
        return destination.root / value.removeprefix(prefix)
    if destination.kind == _PACKAGE_ARTIFACTS_ROOT_DESTINATION_KIND:
        marker = "/_aware/"
        if marker not in value:
            return None
        return destination.root / value.split(marker, 1)[1]
    return destination.root / value


def _dedupe_targets(
    targets: Iterable[_ResolvedDescriptorTarget],
) -> tuple[_ResolvedDescriptorTarget, ...]:
    seen: set[str] = set()
    deduped: list[_ResolvedDescriptorTarget] = []
    for target in targets:
        key = target.path.as_posix()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(target)
    return tuple(deduped)


def _module_name_for_path(path: Path, import_root: str) -> str:
    parts = path.with_suffix("").parts
    return ".".join((import_root, *parts))


def _module_names(
    generated_file_paths: tuple[Path, ...],
    import_root: str,
    destination: MetaLanguageMaterializationDestination | None = None,
) -> list[str]:
    modules: set[str] = set()
    paths = (
        destination.file_paths
        if destination is not None and destination.file_paths
        else generated_file_paths
    )
    import_root_dir = (
        (destination.package_root / import_root).resolve()
        if destination is not None and destination.package_root is not None
        else None
    )
    for path in paths:
        if path.suffix != ".py" or path.name == "__init__.py":
            continue
        path = Path(path)
        if import_root_dir is not None:
            resolved = path.resolve()
            if import_root_dir not in resolved.parents:
                continue
            path = resolved.relative_to(import_root_dir)
        parts = path.with_suffix("").parts
        if not parts:
            continue
        if parts[0] == import_root:
            module_parts = parts
        else:
            module_parts = (import_root, *parts)
        modules.add(".".join(module_parts))
    return sorted(modules)


def _dependency_import_roots(
    request: MetaLanguageDeclaredOutputProducerRequest,
    import_root: str,
    destination: MetaLanguageMaterializationDestination | None = None,
) -> list[str]:
    roots: set[str] = set()
    explicit_roots: set[str] = set()
    explicit_roots.update(
        root
        for root in (
            _normalized_import_root(str(root))
            for root in request.package_dependency_import_roots
            if str(root).strip()
        )
        if root
    )
    if destination is not None:
        metadata_roots = destination.metadata.get("dependency_import_roots")
        if isinstance(metadata_roots, (list, tuple)):
            explicit_roots.update(
                root
                for root in (
                    _normalized_import_root(str(root))
                    for root in metadata_roots
                    if isinstance(root, str) and root.strip()
                )
                if root
            )
    roots.update(explicit_roots)
    override_roots = {
        root
        for root in (
            _normalized_import_root(override.split(".", 1)[0])
            for override in request.import_overrides.values()
        )
        if root
    }
    roots.update(override_roots)
    if not explicit_roots and not override_roots:
        roots.update(
            root
            for root in (
                _normalized_import_root(graph.fqn_prefix)
                for graph in request.language_external_graphs
            )
            if root
        )
    roots.discard(import_root)
    ordered = sorted(roots)
    if destination is None:
        package_files, import_root_dir = _request_package_files_for_import_root(
            request=request,
            import_root=import_root,
        )
        if not package_files:
            return ordered
        return _filter_dependency_import_roots(
            candidate_dependency_roots=ordered,
            package_files=package_files,
            import_root_dir=import_root_dir,
            import_root_name=import_root,
        )
    return _filter_dependency_import_roots(
        candidate_dependency_roots=ordered,
        package_files=destination.file_paths,
        import_root_dir=(
            destination.package_root / import_root
            if destination.package_root is not None
            else None
        ),
        import_root_name=import_root,
    )


def _request_package_files_for_import_root(
    *,
    request: MetaLanguageDeclaredOutputProducerRequest,
    import_root: str,
) -> tuple[tuple[Path, ...], Path | None]:
    import_root_dir = (request.output_root / import_root).resolve()
    package_files: list[Path] = []
    for raw_path in request.generated_file_paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = request.output_root / path
        path = path.resolve()
        if path.suffix != ".py" or import_root_dir not in path.parents:
            continue
        package_files.append(path)
    if not package_files:
        return (), None
    return tuple(package_files), import_root_dir


def _filter_dependency_import_roots(
    *,
    candidate_dependency_roots: list[str],
    package_files: tuple[Path, ...],
    import_root_dir: Path | None,
    import_root_name: str,
) -> list[str]:
    if not candidate_dependency_roots or not package_files or import_root_dir is None:
        return candidate_dependency_roots

    candidate_ordered: list[str] = []
    candidate_set: set[str] = set()
    for dependency_root in candidate_dependency_roots:
        dependency_root_norm = _normalized_import_root(dependency_root)
        if (
            not dependency_root_norm
            or dependency_root_norm == import_root_name
            or dependency_root_norm in candidate_set
        ):
            continue
        candidate_ordered.append(dependency_root_norm)
        candidate_set.add(dependency_root_norm)
    if not candidate_ordered:
        return []

    referenced_roots: set[str] = set()
    import_root_dir = import_root_dir.resolve()
    for file_path in package_files:
        path = Path(file_path).resolve()
        if path.suffix != ".py" or import_root_dir not in path.parents:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            module_name: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = _resolve_python_import_root_from_ast_import(
                        alias.name
                    )
                    if module_name is not None and module_name in candidate_set:
                        referenced_roots.add(module_name)
            elif isinstance(node, ast.ImportFrom):
                if node.level or not isinstance(node.module, str):
                    continue
                module_name = _resolve_python_import_root_from_ast_import(node.module)
                if module_name is not None and module_name in candidate_set:
                    referenced_roots.add(module_name)
    return [root for root in candidate_ordered if root in referenced_roots]


def _pydantic_model_dependency_import_roots(
    request: MetaLanguageDeclaredOutputProducerRequest,
    import_root: str,
    destination: MetaLanguageMaterializationDestination | None = None,
    *,
    candidate_dependency_roots: list[str],
) -> list[str]:
    if destination is None:
        package_files, import_root_dir = _request_package_files_for_import_root(
            request=request,
            import_root=import_root,
        )
    else:
        package_files = destination.file_paths
        import_root_dir = (
            destination.package_root / import_root
            if destination.package_root is not None
            else None
        )
    return _type_checking_dependency_import_roots(
        candidate_dependency_roots=candidate_dependency_roots,
        package_files=package_files,
        import_root_dir=import_root_dir,
        import_root_name=import_root,
    )


def _type_checking_dependency_import_roots(
    *,
    candidate_dependency_roots: list[str],
    package_files: tuple[Path, ...],
    import_root_dir: Path | None,
    import_root_name: str,
) -> list[str]:
    if not candidate_dependency_roots or not package_files or import_root_dir is None:
        return []

    candidate_ordered: list[str] = []
    candidate_set: set[str] = set()
    for dependency_root in candidate_dependency_roots:
        dependency_root_norm = _normalized_import_root(dependency_root)
        if (
            not dependency_root_norm
            or dependency_root_norm == import_root_name
            or dependency_root_norm in candidate_set
        ):
            continue
        candidate_ordered.append(dependency_root_norm)
        candidate_set.add(dependency_root_norm)
    if not candidate_ordered:
        return []

    referenced_roots: set[str] = set()
    import_root_dir = import_root_dir.resolve()
    for file_path in package_files:
        path = Path(file_path).resolve()
        if path.suffix != ".py" or import_root_dir not in path.parents:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        visitor = _TypeCheckingImportRootVisitor(candidate_roots=candidate_set)
        visitor.visit(tree)
        referenced_roots.update(visitor.referenced_roots)
    return [root for root in candidate_ordered if root in referenced_roots]


class _TypeCheckingImportRootVisitor(ast.NodeVisitor):
    def __init__(self, *, candidate_roots: set[str]) -> None:
        self._candidate_roots = candidate_roots
        self._type_checking_depth = 0
        self.referenced_roots: set[str] = set()

    def visit_If(self, node: ast.If) -> None:
        if _is_type_checking_guard(node.test):
            self._type_checking_depth += 1
            for child in node.body:
                self.visit(child)
            self._type_checking_depth -= 1
            for child in node.orelse:
                self.visit(child)
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        if self._type_checking_depth <= 0:
            return
        for alias in node.names:
            self._record_import_root(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if (
            self._type_checking_depth <= 0
            or node.level
            or not isinstance(node.module, str)
        ):
            return
        self._record_import_root(node.module)

    def _record_import_root(self, module_name: str) -> None:
        root = _resolve_python_import_root_from_ast_import(module_name)
        if root is not None and root in self._candidate_roots:
            self.referenced_roots.add(root)


def _is_type_checking_guard(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "TYPE_CHECKING"
    if isinstance(node, ast.Attribute):
        return node.attr == "TYPE_CHECKING"
    return False


def _resolve_python_import_root_from_ast_import(module_name: str) -> str | None:
    root = (module_name or "").split(".", 1)[0].strip()
    if not root:
        return None
    if root.startswith("_"):
        return None
    return root


def _target_import_root(
    target: _ResolvedDescriptorTarget,
    fallback: str,
) -> str:
    if target.destination is None:
        return fallback
    return _normalized_import_root(target.destination.import_root or fallback)


def _normalized_import_root(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().replace("-", "_")


__all__ = ["produce_python_declared_outputs"]
