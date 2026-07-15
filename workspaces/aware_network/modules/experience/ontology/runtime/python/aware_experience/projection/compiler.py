from __future__ import annotations

from pathlib import Path
from typing import cast

from tree_sitter import Node, Parser

from aware_experience.compiler.models import (
    ExperienceProjectionBranchOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionNodeIdentityOwnership,
    ExperienceProjectionNodeOwnership,
    ExperienceProjectionObservableOwnership,
    ExperienceProjectionSectionSurfaceOwnership,
    ExperienceProjectionViewInvocationActionOwnership,
    ExperienceProjectionViewOwnership,
)
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def load_projection_experience_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_observable_truth_by_name: dict[str, frozenset[str]] | None = None,
) -> tuple[ExperienceProjectionExperienceOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    experiences_by_name: dict[str, ExperienceProjectionExperienceOwnership] = {}

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(
            base=package_root, candidate=source_path, label="experience source"
        )
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        for node in tree.root_node.named_children:
            if node.type != "experience_def":
                continue
            experience_name = _symbol_key(_field_text(node, "name"))
            if not experience_name:
                continue
            if experience_name in experiences_by_name:
                raise ValueError(
                    f"Duplicate experience declaration {experience_name!r} across experience sources"
                )

            projection = _normalize_projection_token(_field_text(node, "projection"))
            if not projection:
                raise ValueError(
                    f"Experience declaration {experience_name!r} missing projection target in {source_path}"
                )
            if projection_observable_truth_by_name is not None:
                if projection not in projection_observable_truth_by_name:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} references unknown projection "
                        f"{projection!r} (source={source_path})"
                    )
            projection_observable_truth = (
                projection_observable_truth_by_name.get(projection, frozenset())
                if projection_observable_truth_by_name is not None
                else None
            )

            branches_by_name: dict[str, ExperienceProjectionBranchOwnership] = {}
            observables_by_key: dict[str, ExperienceProjectionObservableOwnership] = {}
            nodes_by_ref: dict[str, ExperienceProjectionNodeOwnership] = {}
            identity_keys_seen: set[str] = set()
            raw_surface_rows: list[dict[str, str | None]] = []

            for item in node.named_children:
                if item.type != "experience_item":
                    continue
                for child in item.named_children:
                    if child.type == "experience_branch":
                        branch_name = _symbol_key(_field_text(child, "name"))
                        if not branch_name:
                            continue
                        if branch_name in branches_by_name:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} has duplicate branch "
                                f"{branch_name!r} in {source_path}"
                            )
                        branches_by_name[branch_name] = (
                            ExperienceProjectionBranchOwnership(
                                name=branch_name,
                                is_default=_has_default_token(child),
                                source_path=source_rel,
                            )
                        )
                    elif child.type == "experience_observable_group":
                        observable_key = _normalize_observable_token(
                            _field_text(child, "observable")
                        )
                        if not observable_key:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} has empty observable group "
                                f"in {source_path}"
                            )
                        if observable_key in observables_by_key:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} has duplicate observable "
                                f"{observable_key!r} in {source_path}"
                            )
                        if (
                            projection_observable_truth is not None
                            and observable_key not in projection_observable_truth
                        ):
                            raise ValueError(
                                f"Experience declaration {experience_name!r} references unknown observable "
                                f"{observable_key!r} for projection {projection!r} (source={source_path})"
                            )

                        views_by_key: dict[str, ExperienceProjectionViewOwnership] = {}
                        for group_child in child.named_children:
                            if group_child.type != "experience_view_def":
                                continue
                            view_key = _normalize_view_token(
                                _field_text(group_child, "view_key")
                            )
                            if not view_key:
                                continue
                            if view_key in views_by_key:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} observable "
                                    f"{observable_key!r} has duplicate view {view_key!r} in {source_path}"
                                )
                            api_view_ref = _normalize_api_view_ref(
                                _field_text(group_child, "api_view")
                            )
                            state_model_ref = _normalize_state_model_ref(
                                _field_text(group_child, "state_model")
                            )
                            if state_model_ref:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} observable "
                                    f"{observable_key!r} view {view_key!r} must not declare "
                                    "Experience-owned state <ClassRef>; API-owned ApiView is required "
                                    f"in {source_path}"
                                )
                            if not api_view_ref:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} observable "
                                    f"{observable_key!r} view {view_key!r} must mount "
                                    "API-owned ApiView with `api_view <api>.<view>` "
                                    f"in {source_path}"
                                )
                            state_provider_ref = _normalize_state_provider_ref(
                                _field_text(group_child, "state_provider")
                            )
                            if state_provider_ref:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} observable "
                                    f"{observable_key!r} view {view_key!r} cannot declare provider; "
                                    "provider fulfillment belongs to the Service "
                                    f"ApiView binding in {source_path}"
                                )
                            invocation_actions = _load_view_invocation_actions(
                                view_node=group_child,
                                source_path=source_path,
                                source_rel=source_rel,
                                experience_name=experience_name,
                                observable_key=observable_key,
                                view_key=view_key,
                            )
                            views_by_key[view_key] = ExperienceProjectionViewOwnership(
                                key=view_key,
                                is_default=_has_default_token(group_child),
                                source_path=source_rel,
                                state_model_ref=None,
                                api_view_ref=api_view_ref,
                                state_provider_ref=None,
                                invocation_actions=invocation_actions,
                            )
                        if not views_by_key:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} observable {observable_key!r} "
                                f"must include at least one view in {source_path}"
                            )
                        default_view_count = sum(
                            1 for view in views_by_key.values() if view.is_default
                        )
                        if default_view_count != 1:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} observable {observable_key!r} "
                                f"must include exactly one default view in {source_path}"
                            )
                        observables_by_key[observable_key] = (
                            ExperienceProjectionObservableOwnership(
                                key=observable_key,
                                source_path=source_rel,
                                views=tuple(
                                    sorted(
                                        views_by_key.values(),
                                        key=lambda item: (item.key, item.source_path),
                                    )
                                ),
                            )
                        )
                    elif child.type == "experience_node_def":
                        node_ref = _normalize_projection_node_ref(
                            _field_text(child, "node_ref")
                        )
                        if not node_ref:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} has empty node declaration "
                                f"in {source_path}"
                            )
                        node_name = node_ref
                        if node_ref in nodes_by_ref:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} has duplicate node declaration "
                                f"{node_ref!r} in {source_path}"
                            )

                        identities_by_key: dict[
                            str, ExperienceProjectionNodeIdentityOwnership
                        ] = {}
                        for node_child in child.named_children:
                            if node_child.type != "experience_node_identity_def":
                                continue
                            keyword = _node_identity_keyword(node_child)
                            if keyword != "id":
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} node {node_ref!r} "
                                    f"uses legacy identity token {keyword!r}; use `id` only "
                                    f"in {source_path}"
                                )
                            identity_key_raw = _field_text(node_child, "key_name")
                            identity_key = _normalize_node_identity_token(
                                identity_key_raw
                            )
                            if not identity_key:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} node {node_ref!r} "
                                    f"has empty key identity in {source_path}"
                                )
                            if identity_key in identities_by_key:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} node {node_ref!r} "
                                    f"has duplicate identity {identity_key!r} in {source_path}"
                                )
                            if identity_key in identity_keys_seen:
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} identity {identity_key!r} "
                                    f"is duplicated across node contracts in {source_path}"
                                )

                            identities_by_key[identity_key] = (
                                ExperienceProjectionNodeIdentityOwnership(
                                    key=identity_key,
                                    source_path=source_rel,
                                )
                            )
                            identity_keys_seen.add(identity_key)

                        if not identities_by_key:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} node {node_ref!r} "
                                f"must include at least one key identity in {source_path}"
                            )

                        nodes_by_ref[node_ref] = ExperienceProjectionNodeOwnership(
                            name=node_name,
                            node_ref=node_ref,
                            source_path=source_rel,
                            params=(),
                            identities=tuple(
                                sorted(
                                    identities_by_key.values(),
                                    key=lambda item: (item.key, item.source_path),
                                )
                            ),
                        )
                    elif child.type == "experience_surface_def":
                        surface_key = _normalize_surface_key_token(
                            _field_text(child, "surface_key")
                        )
                        if not surface_key:
                            raise ValueError(
                                f"Experience declaration {experience_name!r} has empty surface key "
                                f"in {source_path}"
                            )

                        section_key: str | None = None
                        view_ref: str | None = None
                        graph_identity_ref: str | None = None
                        node_identity_ref: str | None = None
                        source_surface_key: str | None = None
                        for surface_child in _iter_experience_surface_children(
                            node=child
                        ):
                            if surface_child.type == "experience_surface_section_decl":
                                if section_key is not None:
                                    raise ValueError(
                                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                        f"has duplicate section binding in {source_path}"
                                    )
                                section_key = _normalize_section_key_token(
                                    _field_text(surface_child, "section_key")
                                )
                                if not section_key:
                                    raise ValueError(
                                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                        f"has empty section binding in {source_path}"
                                    )
                                continue
                            if surface_child.type == "experience_surface_view_decl":
                                if view_ref is not None:
                                    raise ValueError(
                                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                        f"has duplicate view binding in {source_path}"
                                    )
                                view_ref = _normalize_surface_view_ref(
                                    _field_text(surface_child, "view_ref")
                                )
                                if not view_ref:
                                    raise ValueError(
                                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                        f"has empty view binding in {source_path}"
                                    )
                                continue
                            if (
                                surface_child.type
                                == "experience_surface_graph_anchor_decl"
                            ):
                                if graph_identity_ref is not None:
                                    raise ValueError(
                                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                        f"has duplicate graph anchor in {source_path}"
                                    )
                                graph_identity_ref = _normalize_surface_anchor_ref(
                                    _field_text(surface_child, "graph_identity")
                                )
                                if not graph_identity_ref:
                                    raise ValueError(
                                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                        f"has empty graph anchor in {source_path}"
                                    )
                                continue
                            if (
                                surface_child.type
                                == "experience_surface_node_anchor_decl"
                            ):
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                    "must use graph anchor only; node anchors are no longer part of the "
                                    f"canonical Experience contract in {source_path}"
                                )
                                continue
                            if surface_child.type == "experience_surface_source_decl":
                                raise ValueError(
                                    f"Experience declaration {experience_name!r} surface {surface_key!r} "
                                    "must not declare source surface linkage; the canonical Experience contract "
                                    f"is direct section/view/graph binding in {source_path}"
                                )

                        raw_surface_rows.append(
                            {
                                "surface_key": surface_key,
                                "section_key": section_key,
                                "view_ref": view_ref,
                                "graph_identity_ref": graph_identity_ref,
                                "node_identity_ref": node_identity_ref,
                                "source_surface_key": source_surface_key,
                            }
                        )

            default_branch_count = sum(
                1 for branch in branches_by_name.values() if branch.is_default
            )
            if default_branch_count > 1:
                raise ValueError(
                    f"Experience declaration {experience_name!r} allows at most one default branch in {source_path}"
                )

            section_surfaces_by_key: dict[
                str, ExperienceProjectionSectionSurfaceOwnership
            ] = {}
            observable_view_pairs = {
                (observable.key.casefold(), view.key.casefold())
                for observable in observables_by_key.values()
                for view in observable.views
            }
            for row in raw_surface_rows:
                surface_key = cast(str, row["surface_key"])
                if surface_key.casefold() in section_surfaces_by_key:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} has duplicate surface "
                        f"{surface_key!r} in {source_path}"
                    )
                section_key = (row["section_key"] or "").strip()
                if not section_key:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                        f"must include section binding in {source_path}"
                    )
                view_ref = (row["view_ref"] or "").strip()
                if not view_ref:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                        f"must include view binding in {source_path}"
                    )
                observable_key, view_key = _split_surface_view_ref(
                    view_ref=view_ref,
                    experience_name=experience_name,
                    source_path=source_path,
                )
                if (
                    observable_key.casefold(),
                    view_key.casefold(),
                ) not in observable_view_pairs:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                        f"references unknown view {view_ref!r} in {source_path}"
                    )
                graph_identity_ref = row["graph_identity_ref"]
                node_identity_ref = row["node_identity_ref"]
                if not graph_identity_ref:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                        f"must declare graph identity anchor in {source_path}"
                    )
                if node_identity_ref is not None:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                        "must not declare node identity anchor; graph identity is required in "
                        + f"{source_path}"
                    )
                if row["source_surface_key"] is not None:
                    raise ValueError(
                        f"Experience declaration {experience_name!r} surface {surface_key!r} "
                        "must not declare source surface linkage; graph binding is direct in "
                        + f"{source_path}"
                    )
                section_surfaces_by_key[surface_key.casefold()] = (
                    ExperienceProjectionSectionSurfaceOwnership(
                        surface_key=surface_key,
                        section_key=section_key,
                        observable_key=observable_key,
                        view_key=view_key,
                        source_path=source_rel,
                        source_surface_key=None,
                        graph_identity_ref=graph_identity_ref,
                        node_identity_ref=None,
                    )
                )

            experiences_by_name[experience_name] = (
                ExperienceProjectionExperienceOwnership(
                    name=experience_name,
                    projection=projection,
                    source_path=source_rel,
                    branches=tuple(
                        sorted(
                            branches_by_name.values(),
                            key=lambda item: (item.name, item.source_path),
                        )
                    ),
                    observables=tuple(
                        sorted(
                            observables_by_key.values(),
                            key=lambda item: (item.key, item.source_path),
                        )
                    ),
                    nodes=tuple(
                        sorted(
                            nodes_by_ref.values(),
                            key=lambda item: (item.node_ref, item.source_path),
                        )
                    ),
                    section_surfaces=tuple(
                        sorted(
                            section_surfaces_by_key.values(),
                            key=lambda item: (
                                item.section_key.casefold(),
                                item.surface_key.casefold(),
                            ),
                        )
                    ),
                )
            )

    return tuple(
        sorted(
            experiences_by_name.values(),
            key=lambda item: (item.name, item.projection, item.source_path),
        )
    )


def _iter_experience_surface_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in {
            "experience_surface_section_decl",
            "experience_surface_view_decl",
            "experience_surface_graph_anchor_decl",
            "experience_surface_node_anchor_decl",
            "experience_surface_source_decl",
        }:
            children.append(child)
            continue
        if child.type == "experience_surface_item":
            children.extend(
                grandchild for grandchild in child.named_children if grandchild.is_named
            )
    return tuple(children)


def _load_view_invocation_actions(
    *,
    view_node: Node,
    source_path: Path,
    source_rel: str,
    experience_name: str,
    observable_key: str,
    view_key: str,
) -> tuple[ExperienceProjectionViewInvocationActionOwnership, ...]:
    body = view_node.child_by_field_name("body")
    if body is None:
        return ()
    for child in body.named_children:
        if child.type != "experience_view_action_def":
            continue
        action_key = _normalize_view_action_key(_field_text(child, "action_key"))
        action_label = action_key or "<empty>"
        raise ValueError(
            f"Experience view {experience_name}.{observable_key}.{view_key} action "
            f"{action_label!r} is not allowed; API-owned ApiViewCapabilityEndpoint "
            f"owns view actions in {source_path}"
        )
    return ()


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _has_default_token(node: Node) -> bool:
    return any(child.type == "default" for child in node.children)


def _symbol_key(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_projection_token(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_observable_token(raw: str) -> str:
    return (raw or "").strip().casefold()


def _normalize_view_token(raw: str) -> str:
    return (raw or "").strip()


def _normalize_view_action_key(raw: str) -> str:
    return (raw or "").strip()


def _normalize_view_action_kind(raw: str) -> str:
    return (raw or "").strip().casefold()


def _normalize_view_action_target_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_policy_token(raw: str) -> str | None:
    token = (raw or "").strip()
    return token or None


def _decode_string_literal(raw: str) -> str:
    token = (raw or "").strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _normalize_state_model_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_api_view_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_state_provider_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_surface_key_token(raw: str) -> str:
    return (raw or "").strip()


def _normalize_section_key_token(raw: str) -> str:
    return (raw or "").strip()


def _normalize_surface_view_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_surface_anchor_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_projection_node_ref(raw: str) -> str:
    return (raw or "").strip()


def _normalize_projection_node_name(raw: str) -> str:
    return (raw or "").strip()


def _normalize_node_identity_token(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    return token


def _split_surface_view_ref(
    *, view_ref: str, experience_name: str, source_path: Path
) -> tuple[str, str]:
    token = (view_ref or "").strip()
    parts = [part.strip() for part in token.split(".") if part.strip()]
    if len(parts) < 2:
        raise ValueError(
            f"Experience declaration {experience_name!r} surface view reference must use "
            + f"<observable>.<view> form; got {view_ref!r} in {source_path}"
        )
    observable_key = parts[0]
    view_key = ".".join(parts[1:])
    if not observable_key or not view_key:
        raise ValueError(
            f"Experience declaration {experience_name!r} surface view reference must use "
            + f"<observable>.<view> form; got {view_ref!r} in {source_path}"
        )
    return observable_key, view_key


def _normalize_key_param_name(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    return token


def _node_identity_keyword(node: Node) -> str:
    for child in node.children:
        token = (child.type or "").strip()
        if token in {"id", "key"}:
            return token
    return ""


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
    "load_projection_experience_ownership_from_sources",
]
