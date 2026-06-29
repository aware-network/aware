from __future__ import annotations

from pathlib import Path

from tree_sitter import Node

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_code.language_service.features.navigation_capabilities.contracts import (
    CursorInRangeMatcher,
    ExperienceNodeTargetResolver,
    NodeTextReader,
    PathToUriResolver,
    ProjectionTargetResolver,
    UriToPathResolver,
)
from aware_code.language_service.position import ByteRange
from aware_code.language_service.programs import parse_tree
from aware_code.language_service.types import DefinitionTarget
from aware_workspace.compiler.workspace import WorkspaceSnapshot


def resolve_nearest_experience_toml_for_uri(
    *,
    uri: str,
    uri_to_path: UriToPathResolver,
) -> Path | None:
    try:
        uri_path = uri_to_path(uri)
    except Exception:
        return None
    for parent in [uri_path.parent, *uri_path.parents]:
        candidate = parent / "aware.experience.toml"
        if candidate.is_file():
            return candidate
    return None


def collect_experience_definition_targets_by_symbol(
    *,
    uri: str,
    symbol: str,
    uri_to_path: UriToPathResolver,
    path_to_uri: PathToUriResolver,
    node_text: NodeTextReader,
) -> list[DefinitionTarget]:
    token = (symbol or "").strip()
    if not token:
        return []
    experience_toml = resolve_nearest_experience_toml_for_uri(uri=uri, uri_to_path=uri_to_path)
    if experience_toml is None:
        return []
    try:
        workspace = ExperienceWorkspace.from_toml(toml_path=experience_toml)
        snapshot = workspace.build_snapshot()
    except Exception:
        return []

    targets: list[DefinitionTarget] = []
    for relpath in snapshot.source_files:
        source_path = (snapshot.package_root / relpath).resolve()
        if not source_path.is_file():
            continue
        try:
            source_bytes = source_path.read_bytes()
            root = parse_tree(document_bytes=source_bytes)
        except Exception:
            continue
        for child in root.named_children:
            if child.type != "experience_def":
                continue
            name_node = child.child_by_field_name("name")
            if name_node is None:
                continue
            name = node_text(name_node).strip()
            if name != token:
                continue
            targets.append(
                DefinitionTarget(
                    uri=path_to_uri(source_path),
                    range=ByteRange(start=name_node.start_byte, end=name_node.end_byte),
                )
            )
    return targets


def collect_experience_view_definition_targets_by_symbol(
    *,
    uri: str,
    symbol: str,
    uri_to_path: UriToPathResolver,
    path_to_uri: PathToUriResolver,
    node_text: NodeTextReader,
) -> list[DefinitionTarget]:
    token = (symbol or "").strip()
    if not token:
        return []
    parts = [part for part in token.split(".") if part]
    if len(parts) != 3:
        return []
    experience_name, observable_name, view_key = parts

    experience_toml = resolve_nearest_experience_toml_for_uri(uri=uri, uri_to_path=uri_to_path)
    if experience_toml is None:
        return []
    try:
        workspace = ExperienceWorkspace.from_toml(toml_path=experience_toml)
        snapshot = workspace.build_snapshot()
    except Exception:
        return []

    targets: list[DefinitionTarget] = []
    for relpath in snapshot.source_files:
        source_path = (snapshot.package_root / relpath).resolve()
        if not source_path.is_file():
            continue
        try:
            source_bytes = source_path.read_bytes()
            root = parse_tree(document_bytes=source_bytes)
        except Exception:
            continue
        for child in root.named_children:
            if child.type != "experience_def":
                continue
            name_node = child.child_by_field_name("name")
            if name_node is None:
                continue
            name = node_text(name_node).strip()
            if name != experience_name:
                continue
            for item in child.named_children:
                if item.type != "experience_item":
                    continue
                for member in item.named_children:
                    if member.type != "experience_observable_group":
                        continue
                    observable_node = member.child_by_field_name("observable")
                    observable = node_text(observable_node).strip()
                    if observable != observable_name:
                        continue
                    for view_node in member.named_children:
                        if view_node.type != "experience_view_def":
                            continue
                        key_node = view_node.child_by_field_name("view_key")
                        if key_node is None:
                            continue
                        key = node_text(key_node).strip()
                        if key != view_key:
                            continue
                        targets.append(
                            DefinitionTarget(
                                uri=path_to_uri(source_path),
                                range=ByteRange(
                                    start=key_node.start_byte,
                                    end=key_node.end_byte,
                                ),
                            )
                        )
    return targets


def collect_experience_node_definition_targets_by_symbol(
    *,
    uri: str,
    experience_symbol: str,
    node_symbol: str,
    uri_to_path: UriToPathResolver,
    path_to_uri: PathToUriResolver,
    node_text: NodeTextReader,
) -> list[DefinitionTarget]:
    experience_name = (experience_symbol or "").strip()
    token = (node_symbol or "").strip()
    if not experience_name or not token:
        return []
    parts = [part for part in token.split(".") if part]
    if not parts:
        return []
    if len(parts) > 2:
        return []
    node_name = parts[0]
    node_identity = parts[1] if len(parts) == 2 else None

    experience_toml = resolve_nearest_experience_toml_for_uri(uri=uri, uri_to_path=uri_to_path)
    if experience_toml is None:
        return []
    try:
        workspace = ExperienceWorkspace.from_toml(toml_path=experience_toml)
        snapshot = workspace.build_snapshot()
    except Exception:
        return []

    targets: list[DefinitionTarget] = []
    for relpath in snapshot.source_files:
        source_path = (snapshot.package_root / relpath).resolve()
        if not source_path.is_file():
            continue
        try:
            source_bytes = source_path.read_bytes()
            root = parse_tree(document_bytes=source_bytes)
        except Exception:
            continue
        for child in root.named_children:
            if child.type != "experience_def":
                continue
            name_node = child.child_by_field_name("name")
            if name_node is None:
                continue
            name = node_text(name_node).strip()
            if name != experience_name:
                continue

            for exp_item in child.named_children:
                if exp_item.type != "experience_item":
                    continue
                for member in exp_item.named_children:
                    if member.type != "experience_node_def":
                        continue

                    member_name_node = member.child_by_field_name("name")
                    member_name = node_text(member_name_node).strip()
                    if member_name_node is None or member_name != node_name:
                        continue

                    if node_identity is None:
                        targets.append(
                            DefinitionTarget(
                                uri=path_to_uri(source_path),
                                range=ByteRange(
                                    start=member_name_node.start_byte,
                                    end=member_name_node.end_byte,
                                ),
                            )
                        )
                        continue

                    for node_member in member.named_children:
                        if node_member.type != "experience_node_identity_def":
                            continue
                        key_node = node_member.child_by_field_name("key_name")
                        if key_node is None:
                            continue
                        key = node_text(key_node).strip()
                        if key != node_identity:
                            continue
                        targets.append(
                            DefinitionTarget(
                                uri=path_to_uri(source_path),
                                range=ByteRange(
                                    start=key_node.start_byte,
                                    end=key_node.end_byte,
                                ),
                            )
                        )
    return targets


def collect_experience_definition_targets(
    *,
    snapshot: WorkspaceSnapshot | None,
    uri: str,
    byte_offset: int,
    document_bytes: bytes,
    cursor_in_range: CursorInRangeMatcher,
    node_text: NodeTextReader,
    experience_targets_by_symbol: ProjectionTargetResolver,
    experience_node_targets_by_symbol: ExperienceNodeTargetResolver,
    projection_targets_by_symbol: ProjectionTargetResolver,
    projection_view_targets_by_symbol: ProjectionTargetResolver,
) -> list[DefinitionTarget]:
    if snapshot is None:
        return []
    if not document_bytes or (b"experience" not in document_bytes and b"graph" not in document_bytes):
        return []

    try:
        root = parse_tree(document_bytes=document_bytes)
    except Exception:
        return []

    cursor = max(int(byte_offset), 0)
    queue: list[Node] = [root]
    while queue:
        node = queue.pop()
        queue.extend(node.named_children)
        if node.type == "graph_def":
            if not cursor_in_range(
                byte_offset=cursor,
                start=node.start_byte,
                end=node.end_byte,
            ):
                continue

            experience_node = node.child_by_field_name("experience")
            experience_symbol = node_text(experience_node).strip()
            if (
                experience_node is not None
                and cursor_in_range(
                    byte_offset=cursor,
                    start=experience_node.start_byte,
                    end=experience_node.end_byte,
                )
            ):
                if not experience_symbol:
                    return []
                return experience_targets_by_symbol(uri=uri, symbol=experience_symbol)

            for graph_item in node.named_children:
                if graph_item.type != "graph_item":
                    continue
                for stmt in graph_item.named_children:
                    if stmt.type == "graph_root_stmt":
                        ref_node = stmt.child_by_field_name("ref")
                        ref_symbol = node_text(ref_node).strip()
                        if (
                            ref_node is not None
                            and cursor_in_range(
                                byte_offset=cursor,
                                start=ref_node.start_byte,
                                end=ref_node.end_byte,
                            )
                        ):
                            if not experience_symbol or not ref_symbol:
                                return []
                            return experience_node_targets_by_symbol(
                                uri=uri,
                                experience_symbol=experience_symbol,
                                node_symbol=ref_symbol,
                            )
                    if stmt.type == "graph_edge_stmt":
                        parent_node = stmt.child_by_field_name("parent")
                        child_node = stmt.child_by_field_name("child")
                        parent_symbol = node_text(parent_node).strip()
                        child_symbol = node_text(child_node).strip()
                        if (
                            parent_node is not None
                            and cursor_in_range(
                                byte_offset=cursor,
                                start=parent_node.start_byte,
                                end=parent_node.end_byte,
                            )
                        ):
                            if not experience_symbol or not parent_symbol:
                                return []
                            return experience_node_targets_by_symbol(
                                uri=uri,
                                experience_symbol=experience_symbol,
                                node_symbol=parent_symbol,
                            )
                        if (
                            child_node is not None
                            and cursor_in_range(
                                byte_offset=cursor,
                                start=child_node.start_byte,
                                end=child_node.end_byte,
                            )
                        ):
                            if not experience_symbol or not child_symbol:
                                return []
                            return experience_node_targets_by_symbol(
                                uri=uri,
                                experience_symbol=experience_symbol,
                                node_symbol=child_symbol,
                            )
            continue

        if node.type != "experience_def":
            continue
        if not cursor_in_range(
            byte_offset=cursor,
            start=node.start_byte,
            end=node.end_byte,
        ):
            continue

        projection_node = node.child_by_field_name("projection")
        projection_ref = node_text(projection_node).strip()
        if projection_node is not None and cursor_in_range(
            byte_offset=cursor,
            start=projection_node.start_byte,
            end=projection_node.end_byte,
        ):
            if not projection_ref:
                return []
            return projection_targets_by_symbol(uri=uri, symbol=projection_ref)

        for exp_item in node.named_children:
            if exp_item.type != "experience_item":
                continue
            children = list(exp_item.named_children)
            if not children:
                continue
            item = children[0]
            if item.type != "experience_observable_group":
                continue

            observable_node = item.child_by_field_name("observable")
            observable_name = node_text(observable_node).strip()
            if observable_node is not None and cursor_in_range(
                byte_offset=cursor,
                start=observable_node.start_byte,
                end=observable_node.end_byte,
            ):
                if not projection_ref:
                    return []
                return projection_targets_by_symbol(uri=uri, symbol=projection_ref)

            for view_node in item.named_children:
                if view_node.type != "experience_view_def":
                    continue
                view_key_node = view_node.child_by_field_name("view_key")
                view_key = node_text(view_key_node).strip()
                if view_key_node is None or not cursor_in_range(
                    byte_offset=cursor,
                    start=view_key_node.start_byte,
                    end=view_key_node.end_byte,
                ):
                    continue
                if not projection_ref or not observable_name or not view_key:
                    return []
                full_view_ref = view_key
                prefix = f"{observable_name}."
                if not full_view_ref.startswith(prefix):
                    full_view_ref = f"{observable_name}.{full_view_ref}"
                return projection_view_targets_by_symbol(
                    uri=uri,
                    symbol=f"{projection_ref}.{full_view_ref}",
                )

    return []
