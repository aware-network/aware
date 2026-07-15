from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tree_sitter import Node

from aware_code.language_service.position import ByteRange

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.projection.compiler import load_projection_experience_ownership_from_sources

from .projection import (
    ProjectionAddDiagnostic,
    ProjectionLookup,
    ProjectionSuggestFn,
    match_projection_symbol,
)


def collect_experience_diagnostics(
    *,
    projection_root: Node | None,
    document_bytes: bytes,
    lookup: ProjectionLookup,
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
    uri: str | None = None,
    uri_to_path: Callable[[str], Path] | None = None,
    enabled_groups: frozenset[str] | None = None,
) -> None:
    if projection_root is None:
        return
    if b"projection" not in document_bytes and b"experience" not in document_bytes and b"graph" not in document_bytes:
        return

    _add = add
    _suggest = suggest
    _is_enabled = lambda group: enabled_groups is None or group in enabled_groups  # noqa: E731

    def _tree_node_text(node: Node | None) -> str:
        if node is None or node.text is None:
            return ""
        return node.text.decode("utf-8", errors="replace")

    projection_observable_keys: dict[tuple[str, str], set[str]] = {}
    projection_observable_view_keys: dict[tuple[str, str], dict[str, set[str]]] = {}
    projection_name_candidates: list[str] = []
    for p_uri, _p_pkg, p_proj in lookup.projection_index:
        p_name = (p_proj.name or "").strip()
        p_projection_name = (p_proj.projection_name or "").strip()
        if p_name:
            projection_name_candidates.append(p_name)
        if p_projection_name:
            projection_name_candidates.append(p_projection_name)

        observable_keys: set[str] = set()
        observable_view_keys: dict[str, set[str]] = {}
        for p_view in p_proj.projection_views or []:
            full_key = (p_view.key or "").strip()
            if not full_key:
                continue
            parts = [part for part in full_key.split(".") if part]
            if len(parts) >= 2:
                observable_name = ".".join(parts[:-1])
                view_name = parts[-1]
                observable_keys.add(observable_name)
                observable_view_keys.setdefault(observable_name, set()).add(view_name)
        projection_observable_keys[(p_uri, p_name)] = observable_keys
        projection_observable_view_keys[(p_uri, p_name)] = observable_view_keys

    if _is_enabled("projection"):
        experience_queue: list[Node] = [projection_root]
        while experience_queue:
            node = experience_queue.pop()
            experience_queue.extend(node.children)
            if node.type != "experience_def":
                continue

            exp_projection_node = node.child_by_field_name("projection")
            exp_projection_ref = _tree_node_text(exp_projection_node).strip()
            if (
                exp_projection_node is None
                or not exp_projection_ref
                or exp_projection_node.end_byte <= exp_projection_node.start_byte
            ):
                continue

            matches = match_projection_symbol(symbol=exp_projection_ref, lookup=lookup)
            if not matches:
                _add(
                    rng=ByteRange(
                        start=exp_projection_node.start_byte,
                        end=exp_projection_node.end_byte,
                    ),
                    message=(f"Projection not found for experience anchor: {exp_projection_ref}"),
                    code="aware.experience.projection_not_found",
                    data={
                        "suggestions": _suggest(
                            exp_projection_ref,
                            sorted(set(projection_name_candidates)),
                        )
                    },
                )
                continue

            match_candidates = list(matches)
            packages = {pkg for _uri, pkg, _proj in match_candidates if isinstance(pkg, str) and pkg}
            if "." not in exp_projection_ref and lookup.local_pkg is not None and lookup.local_pkg in packages:
                packages = {lookup.local_pkg}
            if len(packages) > 1:
                _add(
                    rng=ByteRange(
                        start=exp_projection_node.start_byte,
                        end=exp_projection_node.end_byte,
                    ),
                    message=(
                        f"Ambiguous experience projection {exp_projection_ref!r}; "
                        "qualify with package (e.g. `aware_identity.Identity`)."
                    ),
                    code="aware.experience.projection_ambiguous",
                    data={"matches": sorted(packages)},
                    severity=2,
                )

            resolved_uri, _resolved_pkg, resolved_proj = match_candidates[0]
            resolved_name = (resolved_proj.name or "").strip()
            known_observables = projection_observable_keys.get((resolved_uri, resolved_name), set())
            known_observable_view_keys = projection_observable_view_keys.get((resolved_uri, resolved_name), {})
            known_observable_candidates = sorted(known_observables)

            seen_branch_names: set[str] = set()
            default_branch_ranges: list[ByteRange] = []
            seen_observable_names: set[str] = set()

            exp_items = [ch for ch in node.named_children if ch.type == "experience_item"]
            for exp_item in exp_items:
                item_nodes = list(exp_item.named_children)
                if not item_nodes:
                    continue
                item = item_nodes[0]

                if item.type == "experience_branch":
                    name_node = item.child_by_field_name("name")
                    branch_name = _tree_node_text(name_node).strip()
                    if name_node is None or not branch_name or name_node.end_byte <= name_node.start_byte:
                        continue
                    branch_rng = ByteRange(
                        start=name_node.start_byte,
                        end=name_node.end_byte,
                    )

                    if branch_name in seen_branch_names:
                        _add(
                            rng=branch_rng,
                            message=f"Duplicate experience branch {branch_name!r}.",
                            code="aware.experience.branch_duplicate",
                        )
                    else:
                        seen_branch_names.add(branch_name)

                    if any(ch.type == "default" for ch in item.children):
                        default_branch_ranges.append(branch_rng)
                    continue

                if item.type != "experience_observable_group":
                    continue

                observable_node = item.child_by_field_name("observable")
                observable_name = _tree_node_text(observable_node).strip()
                if (
                    observable_node is None
                    or not observable_name
                    or observable_node.end_byte <= observable_node.start_byte
                ):
                    continue

                observable_rng = ByteRange(
                    start=observable_node.start_byte,
                    end=observable_node.end_byte,
                )
                if observable_name in seen_observable_names:
                    _add(
                        rng=observable_rng,
                        message=(f"Duplicate experience observable group {observable_name!r}."),
                        code="aware.experience.observable_duplicate",
                    )
                else:
                    seen_observable_names.add(observable_name)

                if known_observables and observable_name not in known_observables:
                    _add(
                        rng=observable_rng,
                        message=(
                            f"Observable {observable_name!r} is not declared in "
                            f"projection {(resolved_proj.projection_name or resolved_name)!r}."
                        ),
                        code="aware.experience.observable_not_found",
                        data={
                            "suggestions": _suggest(
                                observable_name,
                                known_observable_candidates,
                            )
                        },
                    )

                seen_view_names: set[str] = set()
                observable_default_view_ranges: list[ByteRange] = []
                for view_node in item.named_children:
                    if view_node.type != "experience_view_def":
                        continue
                    view_key_node = view_node.child_by_field_name("view_key")
                    view_key = _tree_node_text(view_key_node).strip()
                    if (
                        view_key_node is None
                        or not view_key
                        or view_key_node.end_byte <= view_key_node.start_byte
                    ):
                        continue
                    view_rng = ByteRange(
                        start=view_key_node.start_byte,
                        end=view_key_node.end_byte,
                    )
                    if view_key in seen_view_names:
                        _add(
                            rng=view_rng,
                            message=(
                                f"Duplicate experience view key {view_key!r} under "
                                f"observable {observable_name!r}."
                            ),
                            code="aware.experience.view_duplicate",
                        )
                    else:
                        seen_view_names.add(view_key)

                    known_views = known_observable_view_keys.get(observable_name, set())
                    lookup_view_key = view_key
                    if "." in lookup_view_key:
                        prefix = f"{observable_name}."
                        if lookup_view_key.startswith(prefix):
                            lookup_view_key = lookup_view_key[len(prefix):]
                        else:
                            lookup_view_key = lookup_view_key.rsplit(".", 1)[-1]
                    if known_views and lookup_view_key not in known_views:
                        _add(
                            rng=view_rng,
                            message=(
                                f"View {view_key!r} is not declared for observable "
                                f"{observable_name!r} in projection "
                                f"{(resolved_proj.projection_name or resolved_name)!r}."
                            ),
                            code="aware.experience.view_not_found",
                            data={
                                "suggestions": _suggest(
                                    lookup_view_key,
                                    sorted(known_views),
                                )
                            },
                        )

                    if any(ch.type == "default" for ch in view_node.children):
                        observable_default_view_ranges.append(view_rng)

                if len(observable_default_view_ranges) > 1:
                    for view_rng in observable_default_view_ranges:
                        _add(
                            rng=view_rng,
                            message=(
                                f"Observable {observable_name!r} defines multiple default "
                                "experience views; mark exactly one `view` as `default`."
                            ),
                            code="aware.experience.view_multiple_defaults",
                        )

            if len(default_branch_ranges) > 1:
                for branch_rng in default_branch_ranges:
                    _add(
                        rng=branch_rng,
                        message=(
                            "Experience defines multiple default branches; mark exactly one "
                            "`branch` as `default`."
                        ),
                        code="aware.experience.branch_multiple_defaults",
                    )

    if _is_enabled("graph") and b"graph" in document_bytes:
        _collect_experience_graph_diagnostics(
            projection_root=projection_root,
            add=_add,
            suggest=_suggest,
            uri=uri,
            uri_to_path=uri_to_path,
        )


def _resolve_experience_root_for_path(*, path: Path) -> Path | None:
    resolved = path.resolve()
    for parent in [resolved.parent, *resolved.parents]:
        if (parent / "aware.experience.toml").is_file():
            return parent
    return None


def _build_experience_identity_catalog(
    *,
    uri: str | None,
    uri_to_path: Callable[[str], Path] | None,
) -> dict[str, tuple[str, ...]]:
    if uri is None or uri_to_path is None:
        return {}
    try:
        doc_path = uri_to_path(uri)
    except Exception:
        return {}
    experience_root = _resolve_experience_root_for_path(path=doc_path)
    if experience_root is None:
        return {}
    experience_toml = experience_root / "aware.experience.toml"
    try:
        workspace = ExperienceWorkspace.from_toml(toml_path=experience_toml)
        snapshot = workspace.build_snapshot()
        ownerships = load_projection_experience_ownership_from_sources(
            package_root=snapshot.package_root,
            source_files=snapshot.source_files,
        )
    except Exception:
        return {}

    catalog: dict[str, tuple[str, ...]] = {}
    for ownership in ownerships:
        experience_name = _symbol_key(ownership.name)
        if not experience_name:
            continue
        refs: list[str] = []
        for node in ownership.nodes:
            node_name = (node.name or "").strip()
            if not node_name:
                continue
            for identity in node.identities:
                identity_key = (identity.key or "").strip()
                if not identity_key:
                    continue
                refs.append(f"{node_name}.{identity_key}")
        refs_sorted = tuple(sorted(set(refs)))
        catalog[experience_name] = refs_sorted
    return catalog


def _collect_experience_graph_diagnostics(
    *,
    projection_root: Node,
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
    uri: str | None,
    uri_to_path: Callable[[str], Path] | None,
) -> None:
    catalog = _build_experience_identity_catalog(uri=uri, uri_to_path=uri_to_path)
    experience_candidates = sorted(catalog.keys())

    graph_queue: list[Node] = [projection_root]
    while graph_queue:
        node = graph_queue.pop()
        graph_queue.extend(node.children)
        if node.type != "graph_def":
            continue

        name_node = node.child_by_field_name("name")
        experience_node = node.child_by_field_name("experience")
        graph_name = _tree_node_text(name_node)
        experience_name = _symbol_key(_tree_node_text(experience_node))
        if not graph_name:
            continue

        if not experience_name:
            if experience_node is not None and experience_node.end_byte > experience_node.start_byte:
                add(
                    rng=_node_range(experience_node),
                    message=f"Graph declaration {graph_name!r} must target an experience with `on <Experience>`.",
                    code="aware.experience.graph_experience_missing",
                )
            continue

        allowed_refs = set(catalog.get(experience_name, ()))
        if not allowed_refs:
            if experience_node is not None and experience_node.end_byte > experience_node.start_byte:
                add(
                    rng=_node_range(experience_node),
                    message=f"Graph declaration {graph_name!r} references unknown experience {experience_name!r}.",
                    code="aware.experience.graph_experience_not_found",
                    data={"suggestions": suggest(experience_name, experience_candidates)},
                )
            continue

        root_ref: str | None = None
        root_node_ref: Node | None = None
        parent_by_child: dict[str, str] = {}
        refs_seen: set[str] = set()
        adjacency: dict[str, set[str]] = {}
        edge_pairs_seen: set[tuple[str, str]] = set()
        graph_stmt_nodes = [item for item in node.named_children if item.type == "graph_item"]

        for item in graph_stmt_nodes:
            for stmt in item.named_children:
                if stmt.type == "graph_root_stmt":
                    ref_node = stmt.child_by_field_name("ref")
                    ref_range_node = ref_node if ref_node is not None else stmt
                    ref_token = _normalize_graph_ref(ref_node)
                    if ref_token is None:
                        if ref_node is not None and ref_node.end_byte > ref_node.start_byte:
                            add(
                                rng=_node_range(ref_node),
                                message="Graph node identity reference must use `<node>.<identity>`.",
                                code="aware.experience.graph_ref_invalid",
                            )
                        continue
                    if ref_token not in allowed_refs:
                        add(
                            rng=_node_range(ref_range_node),
                            message=(
                                f"Graph declaration {graph_name!r} references "
                                f"unknown node identity {ref_token!r}."
                            ),
                            code="aware.experience.graph_node_identity_not_found",
                            data={"suggestions": suggest(ref_token, sorted(allowed_refs))},
                        )
                    if root_ref is not None:
                        add(
                            rng=_node_range(ref_range_node),
                            message=f"Graph declaration {graph_name!r} has multiple root declarations.",
                            code="aware.experience.graph_root_multiple",
                        )
                    else:
                        root_ref = ref_token
                        root_node_ref = ref_node
                        refs_seen.add(ref_token)
                elif stmt.type == "graph_edge_stmt":
                    parent_node = stmt.child_by_field_name("parent")
                    child_node = stmt.child_by_field_name("child")
                    parent_range_node = parent_node if parent_node is not None else stmt
                    child_range_node = child_node if child_node is not None else stmt
                    parent_ref = _normalize_graph_ref(parent_node)
                    child_ref = _normalize_graph_ref(child_node)
                    if parent_ref is None:
                        if parent_node is not None and parent_node.end_byte > parent_node.start_byte:
                            add(
                                rng=_node_range(parent_node),
                                message="Graph node identity reference must use `<node>.<identity>`.",
                                code="aware.experience.graph_ref_invalid",
                            )
                        continue
                    if child_ref is None:
                        if child_node is not None and child_node.end_byte > child_node.start_byte:
                            add(
                                rng=_node_range(child_node),
                                message="Graph node identity reference must use `<node>.<identity>`.",
                                code="aware.experience.graph_ref_invalid",
                            )
                        continue
                    if parent_ref not in allowed_refs:
                        add(
                            rng=_node_range(parent_range_node),
                            message=(
                                f"Graph declaration {graph_name!r} references "
                                f"unknown node identity {parent_ref!r}."
                            ),
                            code="aware.experience.graph_node_identity_not_found",
                            data={"suggestions": suggest(parent_ref, sorted(allowed_refs))},
                        )
                    if child_ref not in allowed_refs:
                        add(
                            rng=_node_range(child_range_node),
                            message=(
                                f"Graph declaration {graph_name!r} references "
                                f"unknown node identity {child_ref!r}."
                            ),
                            code="aware.experience.graph_node_identity_not_found",
                            data={"suggestions": suggest(child_ref, sorted(allowed_refs))},
                        )
                    if parent_ref == child_ref:
                        add(
                            rng=_node_range(stmt),
                            message=f"Graph declaration {graph_name!r} contains self edge {parent_ref!r}.",
                            code="aware.experience.graph_edge_self",
                        )
                        continue

                    edge_key = (parent_ref, child_ref)
                    if edge_key in edge_pairs_seen:
                        add(
                            rng=_node_range(stmt),
                            message=(
                                f"Graph declaration {graph_name!r} contains "
                                f"duplicate edge {parent_ref!r} -> {child_ref!r}."
                            ),
                            code="aware.experience.graph_edge_duplicate",
                        )
                    edge_pairs_seen.add(edge_key)

                    existing_parent = parent_by_child.get(child_ref)
                    if existing_parent is not None and existing_parent != parent_ref:
                        add(
                            rng=_node_range(child_range_node),
                            message=(
                                f"Graph declaration {graph_name!r} assigns multiple parents to child {child_ref!r} "
                                f"({existing_parent!r}, {parent_ref!r})."
                            ),
                            code="aware.experience.graph_parent_multiple",
                        )
                    else:
                        parent_by_child[child_ref] = parent_ref

                    adjacency.setdefault(parent_ref, set()).add(child_ref)
                    refs_seen.add(parent_ref)
                    refs_seen.add(child_ref)

        if root_ref is None:
            add(
                rng=_node_range(node),
                message=f"Graph declaration {graph_name!r} must declare exactly one root.",
                code="aware.experience.graph_root_missing",
            )
            continue

        if root_ref in parent_by_child:
            add(
                rng=_node_range(root_node_ref if root_node_ref is not None else node),
                message=f"Graph declaration {graph_name!r} root {root_ref!r} cannot appear as a child edge target.",
                code="aware.experience.graph_root_as_child",
            )

        for ref in sorted(refs_seen):
            if ref == root_ref:
                continue
            if ref not in parent_by_child:
                add(
                    rng=_node_range(node),
                    message=f"Graph declaration {graph_name!r} contains disconnected node identity {ref!r}.",
                    code="aware.experience.graph_node_disconnected",
                )

        cycle_visiting: set[str] = set()
        cycle_visited: set[str] = set()
        has_cycle = False

        def _visit_cycle(current: str) -> None:
            nonlocal has_cycle
            if current in cycle_visiting:
                has_cycle = True
                return
            if current in cycle_visited:
                return
            cycle_visiting.add(current)
            for nxt in sorted(adjacency.get(current, ())):
                _visit_cycle(nxt)
            cycle_visiting.remove(current)
            cycle_visited.add(current)

        for ref in sorted(refs_seen):
            _visit_cycle(ref)

        if has_cycle:
            add(
                rng=_node_range(node),
                message=f"Graph declaration {graph_name!r} contains a cycle.",
                code="aware.experience.graph_cycle",
            )

        reachable: set[str] = set()

        def _visit_reachable(current: str) -> None:
            if current in reachable:
                return
            reachable.add(current)
            for nxt in sorted(adjacency.get(current, ())):
                _visit_reachable(nxt)

        _visit_reachable(root_ref)
        for ref in sorted(refs_seen):
            if ref not in reachable:
                add(
                    rng=_node_range(node),
                    message=(
                        f"Graph declaration {graph_name!r} has unreachable node identity "
                        f"{ref!r} from root {root_ref!r}."
                    ),
                    code="aware.experience.graph_unreachable",
                )


def _normalize_graph_ref(node: Node | None) -> str | None:
    token = _tree_node_text(node).strip()
    if not token:
        return None
    parts = [part for part in token.split(".") if part]
    if len(parts) != 2:
        return None
    return f"{parts[0]}.{parts[1]}"


def _tree_node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8", errors="replace").strip()


def _node_range(node: Node) -> ByteRange:
    return ByteRange(start=node.start_byte, end=node.end_byte)


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()
