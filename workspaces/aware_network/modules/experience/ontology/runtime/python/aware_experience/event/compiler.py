from __future__ import annotations

from pathlib import Path
from typing import Any

from aware_experience.compiler.workspace import (
    ExperienceWorkspace,
)
from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE
from aware_experience.compiler.models import (
    ExperienceEventBindingOwnership,
    ExperienceEventOwnership,
    ProjectionOwnedClassTruth,
)


def load_event_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_truth_by_name: dict[str, dict[str, ProjectionOwnedClassTruth]] | None = None,
    package_name: str | None = None,
    fqn_prefix: str | None = None,
    is_dependency: bool = False,
) -> tuple[ExperienceEventOwnership, ...]:
    events: list[ExperienceEventOwnership] = []
    event_names: set[str] = set()
    for relpath in source_files:
        rel = relpath.as_posix()
        if "/events/" not in f"/{rel}" and not rel.startswith("events/"):
            continue
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="event source")
        text = source_path.read_text(encoding="utf-8")
        for (
            symbol,
            option_values,
            raw_bindings,
        ) in _parse_event_declarations_from_source(source_text=text):
            event_name = (option_values.get("name") or "").strip()
            renderer_key = (option_values.get("renderer") or "").strip()
            if not event_name:
                raise ValueError(f"Event declaration {symbol!r} missing `name` option in {source_path}")
            if not renderer_key:
                raise ValueError(f"Event declaration {symbol!r} missing `renderer` option in {source_path}")
            if event_name in event_names:
                raise ValueError(f"Duplicate event name {event_name!r} across experience sources")
            event_names.add(event_name)

            bindings: list[ExperienceEventBindingOwnership] = []
            for projection, type_ref, operation, attribute in raw_bindings:
                projection_norm = _normalize_projection_token(projection)
                if not projection_norm:
                    raise ValueError(f"Event declaration {symbol!r} has empty projection binding in {source_path}")
                type_ref_value = (type_ref or "").strip()
                if "." not in type_ref_value:
                    raise ValueError(
                        f"Event declaration {symbol!r} binding must use qualified type_ref <projection>.<Class> "
                        f"(received {type_ref_value!r}) in {source_path}"
                    )
                type_projection_raw, class_name = type_ref_value.rsplit(".", 1)
                type_projection = _normalize_projection_token(type_projection_raw)
                if projection_norm != type_projection:
                    raise ValueError(
                        f"Event declaration {symbol!r} binding projection/type mismatch in {source_path}: "
                        f"projection={projection!r} type_ref={type_ref_value!r}"
                    )
                class_truth: ProjectionOwnedClassTruth | None = None
                class_fqn: str | None = None
                if projection_truth_by_name is not None:
                    if projection_norm not in projection_truth_by_name:
                        raise ValueError(
                            f"Event declaration {symbol!r} references unknown projection {projection_norm!r} "
                            f"(source={source_path})"
                        )
                    class_catalog = projection_truth_by_name[projection_norm]
                    if not class_catalog:
                        raise ValueError(
                            f"Event declaration {symbol!r} projection {projection_norm!r} has no class catalog "
                            f"in composed environment manifests (source={source_path})"
                        )
                    class_truth = class_catalog.get(class_name)
                    if class_truth is None:
                        raise ValueError(
                            f"Event declaration {symbol!r} references unknown class token {class_name!r} "
                            f"for projection {projection_norm!r} (source={source_path})"
                        )
                    class_fqn = class_truth.class_fqn
                binding_attribute = (attribute or "").strip() or None
                if projection_truth_by_name is not None and binding_attribute is not None and class_truth is not None:
                    attribute_root = binding_attribute.split(".", 1)[0].strip()
                    if not attribute_root:
                        raise ValueError(
                            f"Event declaration {symbol!r} has invalid empty attribute path "
                            f"for projection {projection_norm!r} class {class_name!r} (source={source_path})"
                        )
                    if attribute_root not in class_truth.attributes:
                        raise ValueError(
                            f"Event declaration {symbol!r} references unknown attribute path root "
                            f"{attribute_root!r} for class token {class_name!r} projection {projection_norm!r} "
                            f"(source={source_path})"
                        )
                bindings.append(
                    ExperienceEventBindingOwnership(
                        projection=projection_norm,
                        type_ref=type_ref_value,
                        class_fqn=class_fqn,
                        operation=(operation or "").strip().lower(),
                        attribute=binding_attribute,
                    )
                )
            if not bindings:
                raise ValueError(
                    f"Event declaration {symbol!r} must include at least one `bind ...` clause in {source_path}"
                )
            bindings.sort(
                key=lambda item: (
                    item.projection,
                    item.type_ref,
                    item.operation,
                    item.attribute or "",
                )
            )
            events.append(
                ExperienceEventOwnership(
                    symbol=symbol,
                    event_name=event_name,
                    renderer_key=renderer_key,
                    title=(option_values.get("title") or "").strip() or None,
                    description=(option_values.get("description") or "").strip() or None,
                    source_path=relpath.as_posix(),
                    bindings=tuple(bindings),
                    package_name=_normalize_optional_token(package_name),
                    fqn_prefix=_normalize_optional_token(fqn_prefix),
                    is_dependency=is_dependency,
                )
            )
    events.sort(key=lambda item: (item.event_name, item.symbol, item.source_path))
    return tuple(events)


def load_dependency_event_ownership_from_snapshot(
    *,
    snapshot: Any,
    projection_truth_by_name: dict[str, dict[str, ProjectionOwnedClassTruth]] | None = None,
) -> tuple[ExperienceEventOwnership, ...]:
    events: list[ExperienceEventOwnership] = []
    for dependency in getattr(getattr(snapshot, "spec", None), "dependencies", ()) or ():
        package_name = _normalize_optional_token(getattr(dependency, "package_name", None))
        if package_name is None:
            continue
        dependency_snapshot = _resolve_dependency_experience_snapshot(
            snapshot=snapshot,
            package_name=package_name,
        )
        if dependency_snapshot is None:
            continue
        dependency_package_name = _normalize_optional_token(
            dependency_snapshot.spec.experience.package_name
        )
        dependency_fqn_prefix = _normalize_optional_token(
            dependency_snapshot.spec.experience.fqn_prefix
        )
        events.extend(
            load_event_ownership_from_sources(
                package_root=dependency_snapshot.package_root,
                source_files=dependency_snapshot.source_files,
                projection_truth_by_name=projection_truth_by_name,
                package_name=dependency_package_name,
                fqn_prefix=dependency_fqn_prefix,
                is_dependency=True,
            )
        )
    events.sort(
        key=lambda item: (
            item.package_name or "",
            item.event_name.casefold(),
            item.symbol.casefold(),
            item.source_path,
        )
    )
    return tuple(events)


def _parse_event_declarations_from_source(*, source_text: str) -> tuple[
    tuple[
        str,
        dict[str, str],
        tuple[tuple[str, str, str, str | None], ...],
    ],
    ...,
]:
    parser = Parser(language=AWARE_LANGUAGE)
    source_bytes = source_text.encode("utf-8")
    tree = parser.parse(source_bytes)
    parsed: list[tuple[str, dict[str, str], tuple[tuple[str, str, str, str | None], ...]]] = []
    if tree.root_node.has_error:
        raise ValueError("Event source contains parse errors")
    for event_node in _iter_nodes(node=tree.root_node, node_type="event_def"):
        symbol = _decode_node_text(event_node=event_node.child_by_field_name("name"))
        options: dict[str, str] = {}
        options_node = event_node.child_by_field_name("options")
        if options_node is not None:
            for option_node in options_node.named_children:
                keyword, value_node = _event_option_field(option_node=option_node)
                if keyword is None or value_node is None:
                    continue
                options[keyword] = _decode_string_literal(_decode_node_text(event_node=value_node))
        bindings: list[tuple[str, str, str, str | None]] = []
        for binding in event_node.named_children:
            if binding.type != "event_binding":
                continue
            projection = _decode_node_text(event_node=binding.child_by_field_name("projection")).strip()
            type_ref = _decode_node_text(event_node=binding.child_by_field_name("type")).strip()
            operation = _decode_node_text(event_node=binding.child_by_field_name("operation")).strip()
            attribute_node = binding.child_by_field_name("attribute")
            attribute = (
                _decode_node_text(event_node=attribute_node).strip()
                if attribute_node is not None
                else None
            )
            bindings.append((projection, type_ref, operation, attribute))
        parsed.append((symbol, options, tuple(bindings)))
    return tuple(parsed)


def _iter_nodes(*, node: Node, node_type: str) -> tuple[Node, ...]:
    matches: list[Node] = []
    if node.type == node_type:
        matches.append(node)
    for child in node.named_children:
        matches.extend(_iter_nodes(node=child, node_type=node_type))
    return tuple(matches)


def _event_option_field(*, option_node: Node) -> tuple[str | None, Node | None]:
    field_by_keyword = (
        ("name", "event_name"),
        ("renderer", "renderer_key"),
        ("title", "title"),
        ("description", "description"),
    )
    for keyword, field_name in field_by_keyword:
        value_node = option_node.child_by_field_name(field_name)
        if value_node is not None:
            return keyword, value_node
    return None, None


def _decode_node_text(*, event_node: Node | None) -> str:
    if event_node is None:
        return ""
    payload = event_node.text
    if payload is None:
        return ""
    return payload.decode("utf-8")


def _decode_string_literal(raw: str) -> str:
    token = raw.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _normalize_projection_token(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_optional_token(raw: object) -> str | None:
    if not isinstance(raw, str):
        return None
    token = raw.strip()
    return token or None


def _resolve_dependency_experience_snapshot(
    *,
    snapshot: Any,
    package_name: str,
) -> Any | None:
    repo_root = getattr(snapshot, "repo_root", None)
    current_spec_path = getattr(snapshot, "spec_path", None)
    if not isinstance(repo_root, Path):
        return None
    current_spec_resolved = (
        current_spec_path.resolve()
        if isinstance(current_spec_path, Path)
        else None
    )
    for manifest_path in _iter_experience_manifest_candidates(repo_root=repo_root):
        resolved_manifest_path = manifest_path.resolve()
        if current_spec_resolved is not None and resolved_manifest_path == current_spec_resolved:
            continue
        try:
            dependency_snapshot = ExperienceWorkspace.from_toml(
                toml_path=resolved_manifest_path,
                repo_root=repo_root,
            ).build_snapshot()
        except Exception:
            continue
        candidate_package_name = _normalize_optional_token(
            dependency_snapshot.spec.experience.package_name
        )
        if candidate_package_name == package_name:
            return dependency_snapshot
    return None


def _iter_experience_manifest_candidates(*, repo_root: Path) -> tuple[Path, ...]:
    roots = (
        repo_root / "experiences",
        repo_root / "workspaces",
        repo_root / "modules",
    )
    manifests: dict[str, Path] = {}
    for root in roots:
        if not root.exists():
            continue
        for candidate in root.rglob("aware.experience.toml"):
            if candidate.is_file():
                manifests[candidate.resolve().as_posix()] = candidate
    return tuple(manifests[key] for key in sorted(manifests))


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents:
        return
    raise ValueError(f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}")


__all__ = [
    "load_dependency_event_ownership_from_snapshot",
    "load_event_ownership_from_sources",
]
