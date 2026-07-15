from __future__ import annotations

from tree_sitter import Node

from aware_meta.fqn_resolver import FqnScope

from aware_code.language_service.position import ByteRange

from .projection import ProjectionAddDiagnostic, ProjectionSuggestFn


def collect_role_actor_diagnostics(
    *,
    projection_root: Node | None,
    document_bytes: bytes,
    scope: FqnScope,
    class_candidates: list[str],
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
    enabled_groups: frozenset[str] | None = None,
) -> None:
    if projection_root is None:
        return
    if b"role" not in document_bytes and b"actor" not in document_bytes and b"environment" not in document_bytes:
        return

    _add = add
    _suggest = suggest
    _is_enabled = lambda group: enabled_groups is None or group in enabled_groups  # noqa: E731

    class_name_candidates = class_candidates

    def _function_names_for_owner(owner_ref: str) -> list[str]:
        resolved = scope.try_resolve_class_with_fqn(owner_ref)
        if resolved is None:
            return []
        _fqn, class_cfg = resolved
        cls = class_cfg.code_section_class
        if cls is None:
            return []
        out: list[str] = []
        for fn in cls.code_section_functions:
            fn_name = (fn.name or "").strip()
            if fn_name:
                out.append(fn_name)
        return out

    def _tree_node_text(node: Node | None) -> str:
        if node is None or node.text is None:
            return ""
        return node.text.decode("utf-8", errors="replace").strip()

    def _symbol_key(raw: str) -> str:
        token = (raw or "").strip()
        if not token:
            return ""
        if "." in token:
            token = token.rsplit(".", 1)[-1]
        return token.strip()

    role_names: set[str] = set()
    queue: list[Node] = [projection_root]
    while queue:
        node = queue.pop()
        queue.extend(node.children)
        if node.type != "role_def":
            continue

        name_node = node.child_by_field_name("name")
        if name_node is None or name_node.end_byte <= name_node.start_byte:
            continue
        role_name = _tree_node_text(name_node)
        role_rng = ByteRange(
            start=name_node.start_byte,
            end=name_node.end_byte,
        )
        if not role_name:
            continue

        if role_name in role_names and _is_enabled("role"):
            _add(
                rng=role_rng,
                message=f"Duplicate role declaration: {role_name!r}",
                code="aware.role.duplicate",
            )
        elif role_name not in role_names:
            role_names.add(role_name)

        if not _is_enabled("role"):
            continue
        for child in node.named_children:
            if child.type != "role_capability_stmt":
                continue
            target_node = child.child_by_field_name("target")
            if (
                target_node is None
                or target_node.end_byte <= target_node.start_byte
            ):
                continue
            target_ref = _tree_node_text(target_node)
            if not target_ref:
                continue
            if "." not in target_ref:
                _add(
                    rng=ByteRange(
                        start=target_node.start_byte,
                        end=target_node.end_byte,
                    ),
                    message=(
                        "Role capability target must be `Class.Function` or "
                        "`package.schema.Class.Function`."
                    ),
                    code="aware.role.target_invalid",
                )
                continue
            owner_ref, fn_name = target_ref.rsplit(".", 1)
            owner_ref = owner_ref.strip()
            fn_name = fn_name.strip()
            if not owner_ref or not fn_name:
                _add(
                    rng=ByteRange(
                        start=target_node.start_byte,
                        end=target_node.end_byte,
                    ),
                    message=("Role capability target must include both class owner and function name."),
                    code="aware.role.target_invalid",
                )
                continue
            resolved_owner = scope.try_resolve_class_with_fqn(owner_ref)
            if resolved_owner is None:
                _add(
                    rng=ByteRange(
                        start=target_node.start_byte,
                        end=target_node.end_byte,
                    ),
                    message=f"Class not found for role target: {owner_ref}",
                    code="aware.role.class_not_found",
                    data={"suggestions": _suggest(owner_ref, class_name_candidates)},
                )
                continue
            fn_candidates = _function_names_for_owner(owner_ref)
            if fn_name not in fn_candidates:
                _add(
                    rng=ByteRange(
                        start=target_node.start_byte,
                        end=target_node.end_byte,
                    ),
                    message=(
                        f"Function {fn_name!r} not found on class {owner_ref!r} "
                        "(role capability target)."
                    ),
                    code="aware.role.function_not_found",
                    data={"suggestions": _suggest(fn_name, fn_candidates)},
                )

    actor_names: set[str] = set()
    queue = [projection_root]
    while queue:
        node = queue.pop()
        queue.extend(node.children)
        if node.type != "actor_def":
            continue

        name_node = node.child_by_field_name("name")
        if name_node is None or name_node.end_byte <= name_node.start_byte:
            continue
        actor_name = _tree_node_text(name_node)
        actor_rng = ByteRange(
            start=name_node.start_byte,
            end=name_node.end_byte,
        )
        if not actor_name:
            continue
        if actor_name in actor_names and _is_enabled("actor"):
            _add(
                rng=actor_rng,
                message=f"Duplicate actor declaration: {actor_name!r}",
                code="aware.actor.duplicate",
            )
        elif actor_name not in actor_names:
            actor_names.add(actor_name)

        if not _is_enabled("actor"):
            continue
        for child in node.named_children:
            if child.type != "actor_role_stmt":
                continue
            role_node = child.child_by_field_name("role")
            if role_node is None or role_node.end_byte <= role_node.start_byte:
                continue
            role_ref = _tree_node_text(role_node)
            if not role_ref:
                continue
            _add(
                rng=ByteRange(
                    start=role_node.start_byte,
                    end=role_node.end_byte,
                ),
                message=(
                    f"Actor declaration {actor_name!r} cannot assign roles inline; "
                    "assign roles in `environment { actor ... { role ... } }`."
                ),
                code="aware.actor.role_assignment_invalid",
            )

    if not _is_enabled("actor"):
        return

    queue = [projection_root]
    while queue:
        node = queue.pop()
        queue.extend(node.children)
        if node.type != "environment_def":
            continue
        environment_name = _tree_node_text(node.child_by_field_name("name"))
        for item in node.named_children:
            if item.type != "environment_item":
                continue
            members = list(item.named_children)
            if not members:
                continue
            actor_stmt = members[0]
            if actor_stmt.type != "environment_actor_stmt":
                continue

            actor_node = actor_stmt.child_by_field_name("actor")
            actor_ref = _tree_node_text(actor_node)
            actor_key = _symbol_key(actor_ref)
            if actor_node is not None and actor_node.end_byte > actor_node.start_byte and actor_key not in actor_names:
                _add(
                    rng=ByteRange(
                        start=actor_node.start_byte,
                        end=actor_node.end_byte,
                    ),
                    message=(
                        f"Environment {environment_name!r} references unknown actor "
                        f"{actor_ref!r}."
                    ),
                    code="aware.actor.binding_actor_not_found",
                    data={"suggestions": _suggest(actor_key, sorted(actor_names))},
                )

            body = actor_stmt.child_by_field_name("body")
            if body is None:
                continue
            for body_child in body.named_children:
                if body_child.type != "environment_actor_role_stmt":
                    continue
                role_node = body_child.child_by_field_name("role")
                role_ref = _tree_node_text(role_node)
                role_key = _symbol_key(role_ref)
                if role_node is None or role_node.end_byte <= role_node.start_byte or role_key in role_names:
                    continue
                _add(
                    rng=ByteRange(
                        start=role_node.start_byte,
                        end=role_node.end_byte,
                    ),
                    message=(
                        f"Environment {environment_name!r} actor {actor_ref!r} references "
                        f"unknown role {role_ref!r}."
                    ),
                    code="aware.actor.binding_role_not_found",
                    data={"suggestions": _suggest(role_key, sorted(role_names))},
                )
