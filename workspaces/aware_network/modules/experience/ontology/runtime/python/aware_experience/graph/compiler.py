from __future__ import annotations

import re
from pathlib import Path

from tree_sitter import Node, Parser

from aware_experience.compiler.models import (
    ExperienceGraphEdgeOwnership,
    ExperienceGraphOwnership,
    ExperienceProjectionExperienceOwnership,
)
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

_GRAPH_HEADER_RE = re.compile(r"\bgraph\s+[A-Za-z_][A-Za-z0-9_]*\s+on\b")


def load_graph_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_experience_ownership: tuple[
        ExperienceProjectionExperienceOwnership, ...
    ],
) -> tuple[ExperienceGraphOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    experience_identity_catalog = _build_experience_identity_catalog(
        projection_experience_ownership
    )
    graphs_by_name: dict[str, ExperienceGraphOwnership] = {}

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="graph source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))
        if tree.root_node.has_error and _GRAPH_HEADER_RE.search(source_text):
            raise ValueError(f"Graph source contains parse errors: {source_path}")

        for node in tree.root_node.named_children:
            if node.type != "graph_def":
                continue
            graph_name = _symbol_key(_field_text(node, "name"))
            if not graph_name:
                continue
            if graph_name in graphs_by_name:
                raise ValueError(
                    f"Duplicate graph declaration {graph_name!r} across experience sources"
                )

            experience_name = _symbol_key(_field_text(node, "experience"))
            if not experience_name:
                raise ValueError(
                    f"Graph declaration {graph_name!r} missing experience target in {source_path}"
                )

            allowed_refs = experience_identity_catalog.get(experience_name)
            if allowed_refs is None:
                raise ValueError(
                    f"Graph declaration {graph_name!r} references unknown experience "
                    f"{experience_name!r} (source={source_path})"
                )

            root_ref: str | None = None
            edges: list[ExperienceGraphEdgeOwnership] = []
            edge_pairs_seen: set[tuple[str, str]] = set()
            parent_by_child: dict[str, str] = {}
            adjacency: dict[str, set[str]] = {}
            refs_seen: set[str] = set()

            for item in node.named_children:
                if item.type != "graph_item":
                    continue
                for graph_stmt in item.named_children:
                    if graph_stmt.type == "graph_root_stmt":
                        current_root = _normalize_graph_node_identity_ref(
                            _field_text(graph_stmt, "ref")
                        )
                        _assert_known_graph_ref(
                            graph_name=graph_name,
                            ref=current_root,
                            allowed_refs=allowed_refs,
                            source_path=source_path,
                        )
                        if root_ref is not None:
                            raise ValueError(
                                f"Graph declaration {graph_name!r} has multiple root declarations "
                                f"in {source_path}"
                            )
                        root_ref = current_root
                        refs_seen.add(current_root)
                    elif graph_stmt.type == "graph_edge_stmt":
                        parent_ref = _normalize_graph_node_identity_ref(
                            _field_text(graph_stmt, "parent")
                        )
                        child_ref = _normalize_graph_node_identity_ref(
                            _field_text(graph_stmt, "child")
                        )
                        _assert_known_graph_ref(
                            graph_name=graph_name,
                            ref=parent_ref,
                            allowed_refs=allowed_refs,
                            source_path=source_path,
                        )
                        _assert_known_graph_ref(
                            graph_name=graph_name,
                            ref=child_ref,
                            allowed_refs=allowed_refs,
                            source_path=source_path,
                        )
                        if parent_ref == child_ref:
                            raise ValueError(
                                f"Graph declaration {graph_name!r} contains self edge "
                                f"{parent_ref!r} -> {child_ref!r} in {source_path}"
                            )
                        edge_pair = (parent_ref, child_ref)
                        if edge_pair in edge_pairs_seen:
                            raise ValueError(
                                f"Graph declaration {graph_name!r} contains duplicate edge "
                                f"{parent_ref!r} -> {child_ref!r} in {source_path}"
                            )
                        edge_pairs_seen.add(edge_pair)

                        existing_parent = parent_by_child.get(child_ref)
                        if (
                            existing_parent is not None
                            and existing_parent != parent_ref
                        ):
                            raise ValueError(
                                f"Graph declaration {graph_name!r} assigns multiple parents to child {child_ref!r} "
                                f"({existing_parent!r}, {parent_ref!r}) in {source_path}"
                            )
                        parent_by_child[child_ref] = parent_ref
                        adjacency.setdefault(parent_ref, set()).add(child_ref)
                        refs_seen.add(parent_ref)
                        refs_seen.add(child_ref)
                        edges.append(
                            ExperienceGraphEdgeOwnership(
                                parent=parent_ref,
                                child=child_ref,
                                source_path=source_rel,
                            )
                        )

            if root_ref is None:
                raise ValueError(
                    f"Graph declaration {graph_name!r} must declare exactly one root in {source_path}"
                )
            if root_ref in parent_by_child:
                raise ValueError(
                    f"Graph declaration {graph_name!r} root {root_ref!r} cannot appear as a child edge target "
                    f"in {source_path}"
                )
            for ref in refs_seen:
                if ref == root_ref:
                    continue
                if ref not in parent_by_child:
                    raise ValueError(
                        f"Graph declaration {graph_name!r} contains disconnected node identity {ref!r} "
                        f"without parent edge in {source_path}"
                    )

            _assert_acyclic_and_reachable(
                graph_name=graph_name,
                root_ref=root_ref,
                refs_seen=refs_seen,
                adjacency=adjacency,
                source_path=source_path,
            )

            graphs_by_name[graph_name] = ExperienceGraphOwnership(
                name=graph_name,
                experience=experience_name,
                source_path=source_rel,
                root=root_ref,
                edges=tuple(
                    sorted(
                        edges,
                        key=lambda item: (item.parent, item.child, item.source_path),
                    )
                ),
            )

    return tuple(
        sorted(
            graphs_by_name.values(),
            key=lambda item: (item.name, item.experience, item.source_path),
        )
    )


def _build_experience_identity_catalog(
    projection_experience_ownership: tuple[
        ExperienceProjectionExperienceOwnership, ...
    ],
) -> dict[str, frozenset[str]]:
    catalog: dict[str, frozenset[str]] = {}
    for ownership in projection_experience_ownership:
        refs: set[str] = set()
        for node in ownership.nodes:
            for identity in node.identities:
                identity_key = (identity.key or "").strip()
                if not identity_key:
                    continue
                if identity_key in refs:
                    raise ValueError(
                        f"Experience declaration {ownership.name!r} has duplicate graph identity "
                        f"{identity_key!r}; graph refs are bare identities"
                    )
                refs.add(identity_key)
        catalog[_symbol_key(ownership.name)] = frozenset(refs)
    return catalog


def _assert_acyclic_and_reachable(
    *,
    graph_name: str,
    root_ref: str,
    refs_seen: set[str],
    adjacency: dict[str, set[str]],
    source_path: Path,
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def _visit(current: str) -> None:
        if current in visiting:
            raise ValueError(
                f"Graph declaration {graph_name!r} contains a cycle at node identity {current!r} in {source_path}"
            )
        if current in visited:
            return
        visiting.add(current)
        for nxt in sorted(adjacency.get(current, ())):
            _visit(nxt)
        visiting.remove(current)
        visited.add(current)

    _visit(root_ref)

    for ref in refs_seen:
        if ref not in visited:
            raise ValueError(
                f"Graph declaration {graph_name!r} has unreachable node identity {ref!r} from root "
                f"{root_ref!r} in {source_path}"
            )


def _assert_known_graph_ref(
    *,
    graph_name: str,
    ref: str,
    allowed_refs: frozenset[str],
    source_path: Path,
) -> None:
    if ref in allowed_refs:
        return
    raise ValueError(
        f"Graph declaration {graph_name!r} references unknown node identity {ref!r} "
        f"(source={source_path})"
    )


def _normalize_graph_node_identity_ref(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        raise ValueError("Graph node identity reference must be non-empty")
    if "." in token:
        raise ValueError(
            "Graph node identity reference must use bare identity form; "
            + f"got {token!r}"
        )
    return token


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _node_text(target)


def _node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "load_graph_ownership_from_sources",
]
