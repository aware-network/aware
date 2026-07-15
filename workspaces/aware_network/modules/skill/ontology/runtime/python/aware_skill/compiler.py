from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from tree_sitter import Node, Parser
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE

from .models import (
    SkillApiOwnership,
    SkillEndpointOwnership,
    SkillOwnership,
    SkillStepOwnership,
)


def load_skill_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[SkillOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    skills_by_name: dict[str, SkillOwnership] = {}

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="skill source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        if tree.root_node.has_error:
            raise ValueError(f"Skill source {source_path} has parse errors")

        for node in tree.root_node.named_children:
            if node.type != "skill_def":
                continue
            skill_name = _symbol_key(_field_text(node, "name"))
            if not skill_name:
                raise ValueError(f"Skill declaration has empty name in {source_path}")
            if skill_name in skills_by_name:
                raise ValueError(f"Duplicate skill declaration {skill_name!r} across skill sources")

            apis_by_ref: dict[str, SkillApiOwnership] = {}
            endpoints_by_name: dict[str, SkillEndpointOwnership] = {}
            steps_by_position: dict[int, SkillStepOwnership] = {}
            description = _first_literal_text(node)

            for child in _iter_skill_children(node=node):
                if child.type == "skill_api_decl":
                    api_ref = _qualified_text(child.child_by_field_name("api"))
                    if not api_ref:
                        raise ValueError(
                            f"Skill declaration {skill_name!r} has api declaration with empty target in {source_path}"
                        )
                    api_key = api_ref.casefold()
                    if api_key in apis_by_ref:
                        raise ValueError(
                            f"Skill declaration {skill_name!r} has duplicate api binding {api_ref!r} in {source_path}"
                        )
                    apis_by_ref[api_key] = SkillApiOwnership(api_ref=api_ref, source_path=source_rel)
                    continue

                if child.type == "skill_endpoint_def":
                    endpoint_name = _symbol_key(_field_text(child, "endpoint_name"))
                    endpoint_ref = _qualified_text(child.child_by_field_name("endpoint"))
                    if not endpoint_name:
                        raise ValueError(
                            f"Skill declaration {skill_name!r} has endpoint with empty name in {source_path}"
                        )
                    if len(endpoint_ref.split(".")) < 3:
                        raise ValueError(
                            f"Skill declaration {skill_name!r} endpoint {endpoint_name!r} has invalid endpoint "
                            + f"ref {endpoint_ref!r} in {source_path}; expected api.capability.endpoint"
                        )
                    if _resolve_declared_api_ref(
                        endpoint_ref=endpoint_ref,
                        declared_api_refs=tuple(api.api_ref for api in apis_by_ref.values()),
                    ) is None:
                        raise ValueError(
                            f"Skill declaration {skill_name!r} endpoint {endpoint_name!r} references undeclared "
                            + f"api endpoint {endpoint_ref!r} in {source_path}"
                        )
                    endpoint_key = endpoint_name.casefold()
                    if endpoint_key in endpoints_by_name:
                        raise ValueError(
                            f"Skill declaration {skill_name!r} has duplicate endpoint name {endpoint_name!r} "
                            + f"in {source_path}"
                        )
                    endpoints_by_name[endpoint_key] = SkillEndpointOwnership(
                        name=endpoint_name,
                        endpoint_ref=endpoint_ref,
                        source_path=source_rel,
                        description=_first_literal_text(child),
                    )
                    continue

                if child.type != "skill_step_def":
                    continue
                step = _load_skill_step_definition(
                    node=child,
                    skill_name=skill_name,
                    source_path=source_path,
                    source_rel=source_rel,
                    endpoint_names=tuple(endpoint.name for endpoint in endpoints_by_name.values()),
                )
                if step.position in steps_by_position:
                    raise ValueError(
                        f"Skill declaration {skill_name!r} has duplicate step position {step.position} "
                        + f"in {source_path}"
                    )
                steps_by_position[step.position] = step

            if not apis_by_ref:
                raise ValueError(f"Skill declaration {skill_name!r} must include at least one api in {source_path}")
            if not endpoints_by_name:
                raise ValueError(
                    f"Skill declaration {skill_name!r} must include at least one endpoint in {source_path}"
                )
            if not steps_by_position:
                raise ValueError(f"Skill declaration {skill_name!r} must include at least one step in {source_path}")

            skills_by_name[skill_name] = SkillOwnership(
                name=skill_name,
                source_path=source_rel,
                apis=tuple(sorted(apis_by_ref.values(), key=lambda item: (item.api_ref, item.source_path))),
                endpoints=tuple(sorted(endpoints_by_name.values(), key=lambda item: (item.name, item.source_path))),
                steps=tuple(sorted(steps_by_position.values(), key=lambda item: (item.position, item.source_path))),
                description=description,
            )

    return tuple(sorted(skills_by_name.values(), key=lambda item: (item.name, item.source_path)))


def _load_skill_step_definition(
    *,
    node: Node,
    skill_name: str,
    source_path: Path,
    source_rel: str,
    endpoint_names: tuple[str, ...],
) -> SkillStepOwnership:
    raw_position = _field_text(node, "position")
    try:
        position = int(raw_position)
    except ValueError as exc:
        raise ValueError(
            f"Skill declaration {skill_name!r} has invalid step position {raw_position!r} in {source_path}"
        ) from exc
    if position <= 0:
        raise ValueError(f"Skill declaration {skill_name!r} step position must be positive in {source_path}")

    endpoint_name = _symbol_key(_field_text(node, "endpoint_name"))
    if endpoint_name.casefold() not in {name.casefold() for name in endpoint_names}:
        raise ValueError(
            f"Skill declaration {skill_name!r} step {position} references unknown endpoint "
            + f"{endpoint_name!r} in {source_path}"
        )

    instruction = _first_literal_text(node)
    if not instruction:
        raise ValueError(f"Skill declaration {skill_name!r} step {position} requires instruction in {source_path}")
    return SkillStepOwnership(
        position=position,
        endpoint_name=endpoint_name,
        instruction=instruction,
        source_path=source_rel,
    )


def _resolve_declared_api_ref(*, endpoint_ref: str, declared_api_refs: tuple[str, ...]) -> str | None:
    matches = [
        api_ref
        for api_ref in declared_api_refs
        if endpoint_ref == api_ref or endpoint_ref.startswith(api_ref + ".")
    ]
    if not matches:
        return None
    return max(matches, key=len)


def _iter_skill_children(*, node: Node) -> tuple[Node, ...]:
    children: list[Node] = []
    for child in node.named_children:
        if child.type in {"skill_api_decl", "skill_endpoint_def", "skill_step_def"}:
            children.append(child)
            continue
        if child.type == "skill_item":
            children.extend(grandchild for grandchild in child.named_children if grandchild.is_named)
    return tuple(children)


def _first_literal_text(node: Node) -> str | None:
    for child in node.named_children:
        if child.type in {"string_literal", "triple_string_literal"}:
            value = _decode_literal_text(child)
            if value:
                return value
            continue
        if child.type in {"skill_endpoint_block", "skill_step_block"}:
            nested = _first_literal_text(child)
            if nested:
                return nested
    return None


def _decode_literal_text(node: Node) -> str | None:
    raw = _qualified_text(node)
    if not raw:
        return None
    if raw.startswith('"""') and raw.endswith('"""'):
        value = raw[3:-3].strip()
        return value or None
    try:
        value = cast(object, json.loads(raw))
    except json.JSONDecodeError:
        if raw.startswith('"') and raw.endswith('"'):
            value = raw[1:-1].strip()
            return value or None
        return raw.strip() or None
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _qualified_text(target)


def _qualified_text(node: Node | None) -> str:
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
    if candidate_resolved == base_resolved or base_resolved in candidate_resolved.parents:
        return
    raise ValueError(f"{label} path must stay within package root: {candidate_resolved}")


__all__ = [
    "load_skill_ownership_from_sources",
]
