from __future__ import annotations

from tree_sitter import Node

from aware_code.language_service.position import ByteRange

from .projection import ProjectionAddDiagnostic, ProjectionSuggestFn


def collect_environment_diagnostics(
    *,
    projection_root: Node | None,
    document_bytes: bytes,
    add: ProjectionAddDiagnostic,
    suggest: ProjectionSuggestFn,
) -> None:
    if projection_root is None:
        return
    if b"projection" not in document_bytes or b"Environment" not in document_bytes:
        return

    _add = add
    _suggest = suggest

    event_names: set[str] = set()
    action_names: set[str] = set()

    queue: list[Node] = [projection_root]
    while queue:
        node = queue.pop()
        queue.extend(node.children)
        if node.type == "event_def":
            name_node = node.child_by_field_name("name")
            if (
                name_node is not None
                and name_node.end_byte > name_node.start_byte
                and name_node.text is not None
            ):
                name = name_node.text.decode("utf-8", errors="replace").strip()
                if name:
                    event_names.add(name)
        elif node.type == "action_def":
            name_node = node.child_by_field_name("name")
            if (
                name_node is not None
                and name_node.end_byte > name_node.start_byte
                and name_node.text is not None
            ):
                name = name_node.text.decode("utf-8", errors="replace").strip()
                if name:
                    action_names.add(name)

    queue = [projection_root]
    while queue:
        node = queue.pop()
        queue.extend(node.children)
        if node.type != "environment_def":
            continue

        seen_events: set[str] = set()
        for item in node.named_children:
            if item.type != "environment_item":
                continue
            members = list(item.named_children)
            if not members:
                continue
            inner = members[0]
            if inner.type != "environment_event_stmt":
                continue

            event_node = inner.child_by_field_name("event")
            if (
                event_node is None
                or event_node.end_byte <= event_node.start_byte
                or event_node.text is None
            ):
                continue
            event_ref = event_node.text.decode("utf-8", errors="replace").strip()
            if not event_ref:
                continue
            event_key = event_ref.rsplit(".", 1)[-1]
            event_rng = ByteRange(
                start=event_node.start_byte,
                end=event_node.end_byte,
            )

            if event_key in seen_events:
                _add(
                    rng=event_rng,
                    message=(f"Duplicate environment event coupling for {event_key!r}."),
                    code="aware.environment.event_duplicate",
                )
            else:
                seen_events.add(event_key)

            if event_ref not in event_names and event_key not in event_names:
                _add(
                    rng=event_rng,
                    message=f"Environment event reference not found: {event_ref!r}",
                    code="aware.environment.event_not_found",
                    data={"suggestions": _suggest(event_key, sorted(event_names))},
                )

            seen_actions: set[str] = set()
            action_count = 0
            for action_stmt in inner.named_children:
                if action_stmt.type != "environment_event_action_stmt":
                    continue
                action_node = action_stmt.child_by_field_name("action")
                if (
                    action_node is None
                    or action_node.end_byte <= action_node.start_byte
                    or action_node.text is None
                ):
                    continue
                action_ref = action_node.text.decode("utf-8", errors="replace").strip()
                if not action_ref:
                    continue
                action_count += 1
                action_key = action_ref.rsplit(".", 1)[-1]
                action_rng = ByteRange(
                    start=action_node.start_byte,
                    end=action_node.end_byte,
                )

                if action_key in seen_actions:
                    _add(
                        rng=action_rng,
                        message=(
                            f"Duplicate action mapping {action_key!r} under "
                            f"environment event {event_key!r}."
                        ),
                        code="aware.environment.action_duplicate",
                    )
                else:
                    seen_actions.add(action_key)

                if action_ref not in action_names and action_key not in action_names:
                    _add(
                        rng=action_rng,
                        message=(f"Environment action reference not found: " f"{action_ref!r}"),
                        code="aware.environment.action_not_found",
                        data={"suggestions": _suggest(action_key, sorted(action_names))},
                    )

            if action_count == 0:
                _add(
                    rng=event_rng,
                    message=(
                        f"Environment event {event_key!r} must declare at least " "one action mapping."
                    ),
                    code="aware.environment.event_action_missing",
                )
