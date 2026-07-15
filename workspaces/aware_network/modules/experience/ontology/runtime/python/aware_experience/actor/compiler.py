from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, Parser, Tree

from aware_experience.compiler.models import (
    ExperienceActorOwnership,
    ExperienceEnvironmentActorBinding,
    ExperienceRoleOwnership,
)
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def load_actor_role_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
) -> tuple[
    tuple[ExperienceRoleOwnership, ...],
    tuple[ExperienceActorOwnership, ...],
    tuple[ExperienceEnvironmentActorBinding, ...],
]:
    role_defs: dict[str, ExperienceRoleOwnership] = {}
    actor_defs: dict[str, ExperienceActorOwnership] = {}
    env_bindings: list[ExperienceEnvironmentActorBinding] = []

    parser = Parser(language=AWARE_LANGUAGE)
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="actor-role source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = _parse_actor_source_tree(parser=parser, source_text=source_text)

        for node in tree.root_node.named_children:
            if node.type == "role_def":
                name = _symbol_key(_field_text(node, "name"))
                if not name:
                    continue
                if name in role_defs:
                    raise ValueError(f"Duplicate role declaration {name!r} across experience sources")
                capabilities = tuple(
                    sorted(
                        _qualified_text(child.child_by_field_name("target"))
                        for child in node.named_children
                        if child.type == "role_capability_stmt" and _qualified_text(child.child_by_field_name("target"))
                    )
                )
                role_defs[name] = ExperienceRoleOwnership(
                    name=name,
                    source_path=source_rel,
                    capabilities=capabilities,
                )
            elif node.type == "actor_def":
                name = _symbol_key(_field_text(node, "name"))
                if not name:
                    continue
                if name in actor_defs:
                    raise ValueError(f"Duplicate actor declaration {name!r} across experience sources")
                kind = _qualified_text(node.child_by_field_name("kind"))
                actor_role_stmts = [child for child in node.named_children if child.type == "actor_role_stmt"]
                if actor_role_stmts:
                    raise ValueError(
                        f"Actor declaration {name!r} cannot declare roles; "
                        + "assign roles in `environment { actor ... { role ... } }`"
                    )
                actor_defs[name] = ExperienceActorOwnership(
                    name=name,
                    kind=kind,
                    roles=(),
                    source_path=source_rel,
                )
            elif node.type == "environment_def":
                environment_name = _symbol_key(_field_text(node, "name"))
                for item in node.named_children:
                    if item.type != "environment_item":
                        continue
                    actor_stmt = next(
                        (child for child in item.named_children if child.type == "environment_actor_stmt"),
                        None,
                    )
                    if actor_stmt is None:
                        continue
                    actor_name = _symbol_key(_qualified_text(actor_stmt.child_by_field_name("actor")))
                    binding_roles: list[str] = []
                    body = actor_stmt.child_by_field_name("body")
                    if body is not None:
                        for body_child in body.named_children:
                            if body_child.type != "environment_actor_role_stmt":
                                continue
                            role_name = _symbol_key(_qualified_text(body_child.child_by_field_name("role")))
                            if role_name:
                                binding_roles.append(role_name)
                    env_bindings.append(
                        ExperienceEnvironmentActorBinding(
                            environment=environment_name,
                            actor=actor_name,
                            roles=tuple(binding_roles),
                            source_path=source_rel,
                        )
                    )

        if tree.root_node.has_error and _contains_actor_declaration_tokens(source_text):
            raise ValueError(
                "Actor/role declarations could not be parsed by tree-sitter "
                + f"(source={source_path}); fix syntax or grammar before compile"
            )

    if role_defs and actor_defs:
        role_catalog = set(role_defs)
        for actor in actor_defs.values():
            for role_name in actor.roles:
                if role_name not in role_catalog:
                    raise ValueError(f"Actor declaration {actor.name!r} references unknown role {role_name!r}")
    if env_bindings:
        actor_catalog = set(actor_defs)
        role_catalog = set(role_defs)
        for binding in env_bindings:
            if binding.actor and binding.actor not in actor_catalog:
                raise ValueError(f"Environment {binding.environment!r} references unknown actor {binding.actor!r}")
            for role_name in binding.roles:
                if role_name not in role_catalog:
                    raise ValueError(
                        f"Environment {binding.environment!r} actor {binding.actor!r} "
                        + f"references unknown role {role_name!r}"
                    )

    roles = tuple(sorted(role_defs.values(), key=lambda item: (item.name, item.source_path)))
    actors = tuple(sorted(actor_defs.values(), key=lambda item: (item.name, item.source_path)))
    bindings = tuple(
        sorted(
            env_bindings,
            key=lambda item: (item.environment, item.actor, item.source_path),
        )
    )
    return roles, actors, bindings


def _parse_actor_source_tree(
    *,
    parser: Parser,
    source_text: str,
) -> Tree:
    raw_tree = parser.parse(source_text.encode("utf-8"))
    if not raw_tree.root_node.has_error:
        return raw_tree
    normalized_source = _normalize_docstring_literals_for_parser(source_text)
    if normalized_source == source_text:
        return raw_tree
    normalized_tree = parser.parse(normalized_source.encode("utf-8"))
    return normalized_tree


def _normalize_docstring_literals_for_parser(source_text: str) -> str:
    if '"""' not in source_text:
        return source_text
    chars = list(source_text)
    index = 0
    in_single_quote = False
    in_double_quote = False
    while index < len(source_text):
        token = source_text[index]
        prev = source_text[index - 1] if index > 0 else ""
        if in_single_quote:
            if token == "'" and prev != "\\":
                in_single_quote = False
            index += 1
            continue
        if in_double_quote:
            if token == '"' and prev != "\\":
                in_double_quote = False
            index += 1
            continue
        if source_text.startswith('"""', index):
            end = source_text.find('"""', index + 3)
            span_end = len(source_text) if end < 0 else end + 3
            for cursor in range(index, span_end):
                if chars[cursor] != "\n":
                    chars[cursor] = " "
            index = span_end
            continue
        if token == "'":
            in_single_quote = True
            index += 1
            continue
        if token == '"':
            in_double_quote = True
            index += 1
            continue
        index += 1
    return "".join(chars)


def _contains_actor_declaration_tokens(source_text: str) -> bool:
    for raw_line in source_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("role ") or line.startswith("actor "):
            return True
    return False


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
    raise ValueError(f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}")


__all__ = [
    "load_actor_role_ownership_from_sources",
]
