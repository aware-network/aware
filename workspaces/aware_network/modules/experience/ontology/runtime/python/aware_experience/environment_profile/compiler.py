from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from tree_sitter import Node, Parser

from aware_experience.compiler.models import (
    ExperienceEnvironmentProfileOwnership,
    ExperienceEnvironmentProfileThreadLayoutSectionOwnership,
    ExperienceEnvironmentProfileProcessOwnership,
    ExperienceEnvironmentProfileThreadLayoutOwnership,
    ExperienceEnvironmentProfileThreadOwnership,
    ExperienceEnvironmentProfileThreadProjectionOwnership,
    ExperienceEnvironmentProfileViewEventTransitionOwnership,
    ExperienceEventOwnership,
    ExperienceProjectionExperienceOwnership,
)
from tree_sitter_aware.tree_sitter_language import AWARE_LANGUAGE


def load_environment_profile_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    projection_experience_ownership: tuple[
        ExperienceProjectionExperienceOwnership, ...
    ],
    event_ownership: tuple[ExperienceEventOwnership, ...] | None = None,
    external_projection_experience_prefixes: tuple[str, ...] = (),
) -> tuple[ExperienceEnvironmentProfileOwnership, ...]:
    parser = Parser(language=AWARE_LANGUAGE)
    profile_ownership_by_key: dict[str, ExperienceEnvironmentProfileOwnership] = {}
    scope_name: str | None = None
    known_projection_experiences = {
        _normalize_symbol(item.name): item.name
        for item in projection_experience_ownership
        if _normalize_symbol(item.name)
    }
    known_projection_view_refs_by_experience = {
        item.name.casefold(): frozenset(
            f"{observable.key}.{view.key}".casefold()
            for observable in item.observables
            for view in observable.views
        )
        for item in projection_experience_ownership
    }
    external_projection_prefixes = tuple(
        _normalize_external_projection_prefix(item)
        for item in external_projection_experience_prefixes
        if _normalize_external_projection_prefix(item)
    )

    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(
            base=package_root, candidate=source_path, label="environment profile source"
        )
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        tree = parser.parse(source_text.encode("utf-8"))

        for node in tree.root_node.named_children:
            if node.type != "experience_profile_scope_def":
                continue

            scope_name_raw = _field_text(node, "name")
            normalized_scope_name = _normalize_symbol(scope_name_raw)
            if not normalized_scope_name:
                raise ValueError(
                    f"Environment profile scope in {source_path} requires a non-empty experience name"
                )
            if normalized_scope_name not in known_projection_experiences:
                raise ValueError(
                    "Environment profile scope references unknown projection experience "
                    f"{scope_name_raw!r} (source={source_path})"
                )
            if scope_name is None:
                scope_name = known_projection_experiences[normalized_scope_name]
            elif _normalize_symbol(scope_name) != normalized_scope_name:
                raise ValueError(
                    "Experience package currently allows exactly one environment profile scope across authored "
                    f"sources; already saw {scope_name!r}, found {scope_name_raw!r} in {source_path}"
                )

            for scope_child in node.named_children:
                if scope_child.type != "experience_profile_scope_item":
                    continue
                for profile_node in scope_child.named_children:
                    if profile_node.type != "experience_profile_def":
                        continue
                    profile = _load_profile_definition(
                        node=profile_node,
                        experience_name=scope_name,
                        source_path=source_path,
                        source_rel=source_rel,
                        known_projection_experiences=known_projection_experiences,
                        known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
                        external_projection_experience_prefixes=external_projection_prefixes,
                    )
                    profile_key = profile.key.casefold()
                    if profile_key in profile_ownership_by_key:
                        raise ValueError(
                            f"Duplicate profile declaration {profile.key!r} across environment profile sources"
                        )
                    profile_ownership_by_key[profile_key] = profile

    profiles = tuple(
        sorted(
            profile_ownership_by_key.values(),
            key=lambda item: (
                item.experience_name.casefold(),
                item.key.casefold(),
                item.source_path,
            ),
        )
    )
    if event_ownership is None:
        return profiles
    return publish_environment_profile_transition_event_refs(
        environment_profile_ownership=profiles,
        event_ownership=event_ownership,
    )


def publish_environment_profile_transition_event_refs(
    *,
    environment_profile_ownership: tuple[ExperienceEnvironmentProfileOwnership, ...],
    event_ownership: tuple[ExperienceEventOwnership, ...],
) -> tuple[ExperienceEnvironmentProfileOwnership, ...]:
    event_catalog: dict[str, ExperienceEventOwnership] = {}
    for event in event_ownership:
        if not event.is_dependency:
            _register_event_reference(
                reference=event.symbol, owner=event, catalog=event_catalog
            )
            _register_event_reference(
                reference=event.event_name, owner=event, catalog=event_catalog
            )
        for reference in _qualified_event_references(event):
            _register_event_reference(
                reference=reference,
                owner=event,
                catalog=event_catalog,
            )

    resolved_profiles: list[ExperienceEnvironmentProfileOwnership] = []
    for profile in environment_profile_ownership:
        transitions: list[ExperienceEnvironmentProfileViewEventTransitionOwnership] = []
        for transition in profile.view_event_transitions:
            event_key = _event_reference_key(transition.trigger_event_ref)
            event = event_catalog.get(event_key)
            if event is None:
                raise ValueError(
                    f"Environment profile {profile.key!r} transition {transition.key!r} "
                    f"references unknown event {transition.trigger_event_ref!r} "
                    f"(source={transition.source_path})"
                )
            transitions.append(
                replace(
                    transition,
                    trigger_event_config_ref=event.event_name,
                )
            )
        resolved_profiles.append(
            replace(profile, view_event_transitions=tuple(transitions))
        )
    return tuple(resolved_profiles)


def _load_profile_definition(
    *,
    node: Node,
    experience_name: str,
    source_path: Path,
    source_rel: str,
    known_projection_experiences: dict[str, str],
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    external_projection_experience_prefixes: tuple[str, ...],
) -> ExperienceEnvironmentProfileOwnership:
    profile_key = _normalize_view_token(_field_text(node, "key"))
    if not profile_key:
        raise ValueError(
            f"Environment profile declaration in {source_path} requires a non-empty profile key"
        )

    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    processes_by_key: dict[str, ExperienceEnvironmentProfileProcessOwnership] = {}
    transitions_by_key: dict[
        str, ExperienceEnvironmentProfileViewEventTransitionOwnership
    ] = {}

    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Environment profile {profile_key!r} in {source_path} is missing a body"
        )

    for child in _iter_profile_children(body):
        if child.type == "experience_profile_title_stmt":
            title = _decode_string_field(child, "title")
            continue
        if child.type == "experience_profile_description_stmt":
            description = _decode_string_field(child, "description")
            continue
        if child.type == "experience_profile_narrative_stmt":
            narrative = _decode_string_field(child, "narrative")
            continue
        if child.type == "experience_profile_transition_def":
            transition = _load_transition_definition(
                node=child,
                profile_key=profile_key,
                source_path=source_path,
                source_rel=source_rel,
                known_projection_experiences=known_projection_experiences,
                known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
                external_projection_experience_prefixes=external_projection_experience_prefixes,
            )
            transition_key = transition.key.casefold()
            if transition_key in transitions_by_key:
                raise ValueError(
                    f"Environment profile {profile_key!r} duplicates transition "
                    f"{transition.key!r} in {source_path}"
                )
            transitions_by_key[transition_key] = transition
            continue
        if child.type != "experience_profile_process_def":
            continue

        process = _load_process_definition(
            node=child,
            source_path=source_path,
            source_rel=source_rel,
            known_projection_experiences=known_projection_experiences,
            known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
            external_projection_experience_prefixes=external_projection_experience_prefixes,
        )
        process_key = process.key.casefold()
        if process_key in processes_by_key:
            raise ValueError(
                f"Environment profile {profile_key!r} duplicates process declaration {process.key!r} in {source_path}"
            )
        processes_by_key[process_key] = process

    default_process_count = sum(
        1 for item in processes_by_key.values() if item.is_bootstrap_default
    )
    if default_process_count > 1:
        raise ValueError(
            f"Environment profile {profile_key!r} allows at most one default process in {source_path}"
        )

    process_configs = tuple(
        sorted(
            processes_by_key.values(),
            key=lambda item: (item.key.casefold(), item.source_path),
        )
    )
    view_event_transitions = tuple(
        sorted(
            transitions_by_key.values(),
            key=lambda item: (item.key.casefold(), item.source_path),
        )
    )
    _assert_profile_transition_refs_known(
        profile_key=profile_key,
        process_configs=process_configs,
        transitions=view_event_transitions,
        source_path=source_path,
        external_projection_experience_prefixes=external_projection_experience_prefixes,
    )

    return ExperienceEnvironmentProfileOwnership(
        experience_name=experience_name,
        key=profile_key,
        source_path=source_rel,
        title=title,
        description=description,
        narrative=narrative,
        process_configs=process_configs,
        view_event_transitions=view_event_transitions,
    )


def _load_transition_definition(
    *,
    node: Node,
    profile_key: str,
    source_path: Path,
    source_rel: str,
    known_projection_experiences: dict[str, str],
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    external_projection_experience_prefixes: tuple[str, ...],
) -> ExperienceEnvironmentProfileViewEventTransitionOwnership:
    key = _normalize_view_token(_field_text(node, "key"))
    if not key:
        raise ValueError(
            f"Environment profile {profile_key!r} has transition declaration with empty key in {source_path}"
        )

    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Environment profile {profile_key!r} transition {key!r} in {source_path} is missing a body"
        )

    source_projection_experience_name: str | None = None
    source_view_key: str | None = None
    trigger_event_ref: str | None = None
    target_projection_experience_name: str | None = None
    target_section_graph_binding_key: str | None = None
    name: str | None = None
    rationale: str | None = None
    idempotency_policy: str | None = None

    for child in _iter_transition_children(body):
        if child.type == "experience_profile_transition_source_stmt":
            if source_projection_experience_name is not None:
                raise ValueError(
                    f"Environment profile {profile_key!r} transition {key!r} duplicates source in {source_path}"
                )
            source_projection_experience_name = _resolve_projection_experience_name(
                raw=_field_text(child, "experience"),
                known_projection_experiences=known_projection_experiences,
                source_path=source_path,
                label=(
                    f"Environment profile {profile_key!r} transition {key!r} source"
                ),
                external_projection_experience_prefixes=external_projection_experience_prefixes,
                allow_external=True,
            )
            source_view_key = _normalize_view_token(_field_text(child, "view_key"))
            if not source_view_key:
                raise ValueError(
                    f"Environment profile {profile_key!r} transition {key!r} source requires view in {source_path}"
                )
            _assert_projection_view_ref_known(
                projection_experience_name=source_projection_experience_name,
                view_key=source_view_key,
                known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
                source_path=source_path,
                label=(
                    f"Environment profile {profile_key!r} transition {key!r} source"
                ),
                external_projection_experience_prefixes=external_projection_experience_prefixes,
                allow_external=True,
            )
            continue
        if child.type == "experience_profile_transition_trigger_stmt":
            if trigger_event_ref is not None:
                raise ValueError(
                    f"Environment profile {profile_key!r} transition {key!r} duplicates trigger in {source_path}"
                )
            trigger_event_ref = _normalize_view_token(_field_text(child, "event"))
            if not trigger_event_ref:
                raise ValueError(
                    f"Environment profile {profile_key!r} transition {key!r} trigger requires event in {source_path}"
                )
            continue
        if child.type == "experience_profile_transition_target_stmt":
            if target_projection_experience_name is not None:
                raise ValueError(
                    f"Environment profile {profile_key!r} transition {key!r} duplicates target in {source_path}"
                )
            target_projection_experience_name = _resolve_projection_experience_name(
                raw=_field_text(child, "experience"),
                known_projection_experiences=known_projection_experiences,
                source_path=source_path,
                label=(
                    f"Environment profile {profile_key!r} transition {key!r} target"
                ),
                external_projection_experience_prefixes=(),
                allow_external=False,
            )
            target_section_graph_binding_key = _normalize_view_token(
                _field_text(child, "binding_key")
            )
            if not target_section_graph_binding_key:
                raise ValueError(
                    f"Environment profile {profile_key!r} transition {key!r} target requires binding in {source_path}"
                )
            continue
        if child.type == "experience_profile_transition_name_stmt":
            name = _decode_string_field(child, "name")
            continue
        if child.type == "experience_profile_transition_rationale_stmt":
            rationale = _decode_string_field(child, "rationale")
            continue
        if child.type == "experience_profile_transition_idempotency_policy_stmt":
            idempotency_policy = _decode_string_field(child, "idempotency_policy")
            continue

    missing: list[str] = []
    if source_projection_experience_name is None or source_view_key is None:
        missing.append("source")
    if trigger_event_ref is None:
        missing.append("trigger")
    if (
        target_projection_experience_name is None
        or target_section_graph_binding_key is None
    ):
        missing.append("target")
    if missing:
        raise ValueError(
            f"Environment profile {profile_key!r} transition {key!r} is missing "
            + ", ".join(missing)
            + f" in {source_path}"
        )

    return ExperienceEnvironmentProfileViewEventTransitionOwnership(
        key=key,
        source_projection_experience_name=source_projection_experience_name,
        source_view_key=source_view_key,
        trigger_event_ref=trigger_event_ref,
        target_projection_experience_name=target_projection_experience_name,
        target_section_graph_binding_key=target_section_graph_binding_key,
        source_path=source_rel,
        name=name,
        rationale=rationale,
        idempotency_policy=idempotency_policy,
    )


def _load_process_definition(
    *,
    node: Node,
    source_path: Path,
    source_rel: str,
    known_projection_experiences: dict[str, str],
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    external_projection_experience_prefixes: tuple[str, ...],
) -> ExperienceEnvironmentProfileProcessOwnership:
    process_type = _normalize_view_token(_field_text(node, "type"))
    if not process_type:
        raise ValueError(
            f"Environment profile process declaration in {source_path} requires a non-empty type"
        )

    key = _normalize_view_token(_field_text(node, "key"))
    if not key:
        raise ValueError(
            f"Environment profile process declaration in {source_path} requires a non-empty key"
        )

    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    intent: str | None = None
    shape: str | None = None
    position: int | None = None
    threads_by_key: dict[str, ExperienceEnvironmentProfileThreadOwnership] = {}

    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Environment profile process {key!r} in {source_path} is missing a body"
        )

    for child in _iter_process_children(body):
        if child.type == "experience_profile_process_title_stmt":
            title = _decode_string_field(child, "title")
            continue
        if child.type == "experience_profile_process_description_stmt":
            description = _decode_string_field(child, "description")
            continue
        if child.type == "experience_profile_process_narrative_stmt":
            narrative = _decode_string_field(child, "narrative")
            continue
        if child.type == "experience_profile_process_intent_stmt":
            intent = _normalize_view_token(_field_text(child, "intent")) or None
            continue
        if child.type == "experience_profile_process_shape_stmt":
            shape = _normalize_view_token(_field_text(child, "shape")) or None
            continue
        if child.type == "experience_profile_process_position_stmt":
            position = _parse_int_field(child, "position", source_path=source_path)
            continue
        if child.type != "experience_profile_thread_def":
            continue

        thread = _load_thread_definition(
            node=child,
            source_path=source_path,
            source_rel=source_rel,
            known_projection_experiences=known_projection_experiences,
            known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
            external_projection_experience_prefixes=external_projection_experience_prefixes,
        )
        thread_key = thread.key.casefold()
        if thread_key in threads_by_key:
            raise ValueError(
                f"Environment profile process {key!r} duplicates thread declaration {thread.key!r} in {source_path}"
            )
        threads_by_key[thread_key] = thread

    default_thread_count = sum(1 for item in threads_by_key.values() if item.is_default)
    if default_thread_count > 1:
        raise ValueError(
            f"Environment profile process {key!r} allows at most one default thread in {source_path}"
        )

    return ExperienceEnvironmentProfileProcessOwnership(
        type=process_type,
        key=key,
        process_key=key,
        source_path=source_rel,
        title=title,
        description=description,
        shape=shape,
        position=position,
        is_bootstrap_default=_has_default_token(node),
        narrative=narrative,
        intent=intent,
        thread_configs=tuple(
            sorted(
                threads_by_key.values(),
                key=lambda item: (item.key.casefold(), item.source_path),
            )
        ),
    )


def _load_thread_definition(
    *,
    node: Node,
    source_path: Path,
    source_rel: str,
    known_projection_experiences: dict[str, str],
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    external_projection_experience_prefixes: tuple[str, ...],
) -> ExperienceEnvironmentProfileThreadOwnership:
    key = _normalize_view_token(_field_text(node, "key"))
    if not key:
        raise ValueError(
            f"Environment profile thread declaration in {source_path} requires a non-empty key"
        )

    title: str | None = None
    description: str | None = None
    narrative: str | None = None
    intent: str | None = None
    workspace_view_key: str | None = None
    position: int | None = None
    state_prompt_template: str | None = None
    declared_projection_experiences: list[
        ExperienceEnvironmentProfileThreadProjectionOwnership
    ] = []
    projection_contract_keys_seen: set[str] = set()
    layout_configs: list[ExperienceEnvironmentProfileThreadLayoutOwnership] = []
    layout_keys_seen: set[str] = set()

    body = node.child_by_field_name("body")
    if body is None:
        raise ValueError(
            f"Environment profile thread {key!r} in {source_path} is missing a body"
        )

    for child in _iter_thread_children(body):
        if child.type == "experience_profile_thread_title_stmt":
            title = _decode_string_field(child, "title")
            continue
        if child.type == "experience_profile_thread_description_stmt":
            description = _decode_string_field(child, "description")
            continue
        if child.type == "experience_profile_thread_narrative_stmt":
            narrative = _decode_string_field(child, "narrative")
            continue
        if child.type == "experience_profile_thread_intent_stmt":
            intent = _normalize_view_token(_field_text(child, "intent")) or None
            continue
        if child.type == "experience_profile_thread_workspace_view_stmt":
            workspace_view_key = (
                _normalize_view_token(_field_text(child, "workspace_view")) or None
            )
            continue
        if child.type == "experience_profile_thread_position_stmt":
            position = _parse_int_field(child, "position", source_path=source_path)
            continue
        if child.type == "experience_profile_thread_state_prompt_template_stmt":
            state_prompt_template = _decode_string_field(child, "state_prompt_template")
            continue
        if child.type == "experience_profile_thread_layout_def":
            layout = _load_layout_definition(
                node=child,
                thread_key=key,
                source_path=source_path,
                source_rel=source_rel,
                known_projection_experiences=known_projection_experiences,
                known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
                external_projection_experience_prefixes=external_projection_experience_prefixes,
            )
            layout_key_casefolded = layout.layout_key.casefold()
            if layout_key_casefolded in layout_keys_seen:
                raise ValueError(
                    f"Environment profile thread {key!r} duplicates layout {layout.layout_key!r} in {source_path}"
                )
            layout_keys_seen.add(layout_key_casefolded)
            layout_configs.append(layout)
            continue
        if child.type != "experience_profile_thread_projection_def":
            continue

        projection_experience_name_raw = _field_text(child, "experience")
        resolved_projection_experience_name = _resolve_projection_experience_name(
            raw=projection_experience_name_raw,
            known_projection_experiences=known_projection_experiences,
            source_path=source_path,
            label=f"Environment profile thread {key!r}",
            external_projection_experience_prefixes=external_projection_experience_prefixes,
            allow_external=True,
        )
        view_key = _normalize_view_token(_field_text(child, "view_key")) or None
        _assert_projection_view_ref_known(
            projection_experience_name=projection_experience_name_raw,
            view_key=view_key,
            known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
            source_path=source_path,
            label=f"Environment profile thread {key!r} projection declaration",
            external_projection_experience_prefixes=external_projection_experience_prefixes,
            allow_external=True,
        )
        projection_contract_key = _thread_projection_contract_key(
            projection_experience_name=resolved_projection_experience_name,
            view_key=view_key,
        )
        if projection_contract_key in projection_contract_keys_seen:
            raise ValueError(
                f"Environment profile thread {key!r} duplicates projection experience "
                f"{resolved_projection_experience_name!r} view {view_key!r} in {source_path}"
            )
        projection_contract_keys_seen.add(projection_contract_key)
        declared_projection_experiences.append(
            ExperienceEnvironmentProfileThreadProjectionOwnership(
                projection_experience_name=resolved_projection_experience_name,
                source_path=source_rel,
                view_key=view_key,
                is_default=_has_default_token(child),
            )
        )

    projection_contract_keys = {
        _thread_projection_contract_key(
            projection_experience_name=item.projection_experience_name,
            view_key=item.view_key,
        )
        for item in declared_projection_experiences
    }
    for layout in layout_configs:
        for section in layout.sections:
            if _thread_projection_contract_has_view(
                projection_contract_keys=projection_contract_keys,
                projection_experience_name=section.projection_experience_name,
                view_key=section.view_key,
            ):
                continue
            raise ValueError(
                f"Environment profile thread {key!r} layout {layout.layout_key!r} section "
                f"{section.section_key!r} references projection experience "
                f"{section.projection_experience_name!r} view {section.view_key!r}, but that exact "
                f"projection/view is not declared on the thread in {source_path}"
            )

    default_projection_count = sum(
        1 for item in declared_projection_experiences if item.is_default
    )
    if default_projection_count > 1:
        raise ValueError(
            f"Environment profile thread {key!r} allows at most one default projection in {source_path}"
        )
    default_layout_count = sum(1 for item in layout_configs if item.is_default)
    if default_layout_count > 1:
        raise ValueError(
            f"Environment profile thread {key!r} allows at most one default layout in {source_path}"
        )

    return ExperienceEnvironmentProfileThreadOwnership(
        key=key,
        thread_key=key,
        source_path=source_rel,
        title=title,
        description=description,
        workspace_view_key=workspace_view_key,
        position=position,
        is_default=_has_default_token(node),
        narrative=narrative,
        intent=intent,
        state_prompt_template=state_prompt_template,
        projection_experiences=tuple(
            sorted(
                _collapse_thread_projection_experience_ownership(
                    declarations=declared_projection_experiences
                ),
                key=lambda item: (
                    item.projection_experience_name.casefold(),
                    (item.view_key or "").casefold(),
                ),
            )
        ),
        layout_configs=tuple(
            sorted(
                layout_configs,
                key=lambda item: (
                    item.position is None,
                    item.position or 0,
                    item.layout_key.casefold(),
                ),
            )
        ),
    )


def _load_layout_definition(
    *,
    node: Node,
    thread_key: str,
    source_path: Path,
    source_rel: str,
    known_projection_experiences: dict[str, str],
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    external_projection_experience_prefixes: tuple[str, ...],
) -> ExperienceEnvironmentProfileThreadLayoutOwnership:
    layout_key = _normalize_view_token(_field_text(node, "layout_key"))
    if not layout_key:
        raise ValueError(
            f"Environment profile thread {thread_key!r} has layout declaration with empty key in {source_path}"
        )

    sections_by_key: dict[
        str, ExperienceEnvironmentProfileThreadLayoutSectionOwnership
    ] = {}
    body = node.child_by_field_name("body")
    if body is not None:
        for child in _iter_layout_children(body):
            if child.type != "experience_profile_thread_layout_section_def":
                continue
            section = _load_layout_section_definition(
                node=child,
                thread_key=thread_key,
                layout_key=layout_key,
                source_path=source_path,
                source_rel=source_rel,
                known_projection_experiences=known_projection_experiences,
                known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
                external_projection_experience_prefixes=external_projection_experience_prefixes,
            )
            section_key_casefolded = section.section_key.casefold()
            if section_key_casefolded in sections_by_key:
                raise ValueError(
                    f"Environment profile thread {thread_key!r} layout {layout_key!r} duplicates "
                    f"section {section.section_key!r} in {source_path}"
                )
            sections_by_key[section_key_casefolded] = section

    return ExperienceEnvironmentProfileThreadLayoutOwnership(
        layout_key=layout_key,
        source_path=source_rel,
        key=layout_key,
        is_default=_has_default_token(node),
        sections=tuple(
            sorted(
                sections_by_key.values(),
                key=lambda item: (
                    item.position is None,
                    item.position or 0,
                    item.section_key.casefold(),
                ),
            )
        ),
    )


def _load_layout_section_definition(
    *,
    node: Node,
    thread_key: str,
    layout_key: str,
    source_path: Path,
    source_rel: str,
    known_projection_experiences: dict[str, str],
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    external_projection_experience_prefixes: tuple[str, ...],
) -> ExperienceEnvironmentProfileThreadLayoutSectionOwnership:
    section_key = _normalize_view_token(_field_text(node, "section_key"))
    if not section_key:
        raise ValueError(
            f"Environment profile thread {thread_key!r} layout {layout_key!r} has empty section key in {source_path}"
        )

    projection_experience_name_raw = _field_text(node, "experience")
    resolved_projection_experience_name = _resolve_projection_experience_name(
        raw=projection_experience_name_raw,
        known_projection_experiences=known_projection_experiences,
        source_path=source_path,
        label=(
            f"Environment profile thread {thread_key!r} layout {layout_key!r} "
            f"section {section_key!r}"
        ),
        external_projection_experience_prefixes=external_projection_experience_prefixes,
        allow_external=True,
    )

    view_key = _normalize_view_token(_field_text(node, "view_key"))
    if not view_key:
        raise ValueError(
            f"Environment profile thread {thread_key!r} layout {layout_key!r} section "
            f"{section_key!r} requires an explicit view in {source_path}"
        )
    _assert_projection_view_ref_known(
        projection_experience_name=projection_experience_name_raw,
        view_key=view_key,
        known_projection_view_refs_by_experience=known_projection_view_refs_by_experience,
        source_path=source_path,
        label=(
            f"Environment profile thread {thread_key!r} layout {layout_key!r} "
            f"section {section_key!r}"
        ),
        external_projection_experience_prefixes=external_projection_experience_prefixes,
        allow_external=True,
    )

    return ExperienceEnvironmentProfileThreadLayoutSectionOwnership(
        section_key=section_key,
        projection_experience_name=resolved_projection_experience_name,
        view_key=view_key,
        source_path=source_rel,
        key=section_key,
        section_graph_binding_key=_normalize_view_token(
            _field_text(node, "binding_key")
        )
        or None,
        is_default=_has_default_token(node),
    )


def _assert_profile_transition_refs_known(
    *,
    profile_key: str,
    process_configs: tuple[ExperienceEnvironmentProfileProcessOwnership, ...],
    transitions: tuple[ExperienceEnvironmentProfileViewEventTransitionOwnership, ...],
    source_path: Path,
    external_projection_experience_prefixes: tuple[str, ...],
) -> None:
    if not transitions:
        return

    profile_projection_contract_keys: set[str] = set()
    binding_keys: set[tuple[str, str]] = set()
    for process in process_configs:
        for thread in process.thread_configs:
            for projection in thread.projection_experiences:
                profile_projection_contract_keys.add(
                    _thread_projection_contract_key(
                        projection_experience_name=projection.projection_experience_name,
                        view_key=projection.view_key,
                    )
                )
            for layout in thread.layout_configs:
                for section in layout.sections:
                    profile_projection_contract_keys.add(
                        _thread_projection_contract_key(
                            projection_experience_name=section.projection_experience_name,
                            view_key=section.view_key,
                        )
                    )
                    binding_key = (section.section_graph_binding_key or "").strip()
                    if binding_key:
                        binding_keys.add(
                            (
                                section.projection_experience_name.casefold(),
                                binding_key.casefold(),
                            )
                        )

    for transition in transitions:
        source_is_external = _matches_external_projection_prefix(
            projection_experience_name=transition.source_projection_experience_name,
            external_projection_experience_prefixes=external_projection_experience_prefixes,
        )
        if not source_is_external and not _thread_projection_contract_has_view(
            projection_contract_keys=profile_projection_contract_keys,
            projection_experience_name=transition.source_projection_experience_name,
            view_key=transition.source_view_key,
        ):
            raise ValueError(
                f"Environment profile {profile_key!r} transition {transition.key!r} "
                f"source projection/view is not declared on the profile: "
                f"projection={transition.source_projection_experience_name!r} "
                f"view={transition.source_view_key!r} (source={source_path})"
            )
        target_binding_key = (
            transition.target_projection_experience_name.casefold(),
            transition.target_section_graph_binding_key.casefold(),
        )
        if target_binding_key not in binding_keys:
            raise ValueError(
                f"Environment profile {profile_key!r} transition {transition.key!r} "
                f"target binding is not declared on a profile layout section: "
                f"projection={transition.target_projection_experience_name!r} "
                f"binding={transition.target_section_graph_binding_key!r} "
                f"(source={source_path})"
            )


def _resolve_projection_experience_name(
    *,
    raw: str,
    known_projection_experiences: dict[str, str],
    source_path: Path,
    label: str,
    external_projection_experience_prefixes: tuple[str, ...],
    allow_external: bool,
) -> str:
    projection_experience_name_key = _normalize_symbol(raw)
    if not projection_experience_name_key:
        raise ValueError(
            f"{label} references empty projection experience in {source_path}"
        )
    resolved_projection_experience_name = known_projection_experiences.get(
        projection_experience_name_key
    )
    if resolved_projection_experience_name is None:
        if allow_external and _matches_external_projection_prefix(
            projection_experience_name=raw,
            external_projection_experience_prefixes=external_projection_experience_prefixes,
        ):
            return projection_experience_name_key
        raise ValueError(
            f"{label} references unknown projection experience {raw!r} in {source_path}"
        )
    return resolved_projection_experience_name


def _field_text(node: Node, field: str) -> str:
    target = node.child_by_field_name(field)
    return _node_text(target)


def _node_text(node: Node | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.decode("utf-8").strip()


def _decode_string_field(node: Node, field: str) -> str | None:
    raw = _field_text(node, field)
    if not raw:
        return None
    try:
        value = ast.literal_eval(raw)
    except Exception as exc:
        raise ValueError(f"Unable to decode string literal {raw!r}") from exc
    if not isinstance(value, str):
        raise ValueError(f"Expected string literal, received {type(value).__name__}")
    return value.strip() or None


def _parse_int_field(node: Node, field: str, *, source_path: Path) -> int:
    raw = _field_text(node, field)
    if not raw:
        raise ValueError(
            f"Environment profile numeric field {field!r} is required in {source_path}"
        )
    if "." in raw:
        raise ValueError(
            f"Environment profile numeric field {field!r} must be an integer in {source_path}"
        )
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(
            f"Environment profile numeric field {field!r} is invalid in {source_path}: {raw!r}"
        ) from exc


def _has_default_token(node: Node) -> bool:
    return any(child.type == "default" for child in node.children)


def _iter_profile_children(node: Node) -> tuple[Node, ...]:
    return _iter_wrapped_children(node=node, wrapper_type="experience_profile_item")


def _iter_process_children(node: Node) -> tuple[Node, ...]:
    return _iter_wrapped_children(
        node=node, wrapper_type="experience_profile_process_item"
    )


def _iter_thread_children(node: Node) -> tuple[Node, ...]:
    return _iter_wrapped_children(
        node=node, wrapper_type="experience_profile_thread_item"
    )


def _iter_layout_children(node: Node) -> tuple[Node, ...]:
    return _iter_wrapped_children(
        node=node, wrapper_type="experience_profile_thread_layout_item"
    )


def _iter_transition_children(node: Node) -> tuple[Node, ...]:
    return _iter_wrapped_children(
        node=node, wrapper_type="experience_profile_transition_item"
    )


def _iter_wrapped_children(*, node: Node, wrapper_type: str) -> tuple[Node, ...]:
    rows: list[Node] = []
    for child in node.named_children:
        if child.type != wrapper_type:
            rows.append(child)
            continue
        rows.extend(child.named_children)
    return tuple(rows)


def _normalize_symbol(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_view_token(raw: str) -> str:
    return (raw or "").strip()


def _event_reference_key(raw: str) -> str:
    return (raw or "").strip().casefold()


def _register_event_reference(
    *,
    reference: str,
    owner: ExperienceEventOwnership,
    catalog: dict[str, ExperienceEventOwnership],
) -> None:
    key = _event_reference_key(reference)
    if not key:
        return
    existing = catalog.get(key)
    if existing is not None and existing != owner:
        raise ValueError(
            "Ambiguous event reference in environment profile transition catalog: "
            f"{reference!r}"
        )
    catalog[key] = owner


def _qualified_event_references(owner: ExperienceEventOwnership) -> tuple[str, ...]:
    prefixes = _event_owner_prefixes(owner)
    references: list[str] = []
    for prefix in prefixes:
        references.append(f"{prefix}.{owner.symbol}")
        references.append(f"{prefix}.{owner.event_name}")
    return tuple(dict.fromkeys(references))


def _event_owner_prefixes(owner: ExperienceEventOwnership) -> tuple[str, ...]:
    prefixes: list[str] = []
    for raw in (owner.fqn_prefix, owner.package_name):
        token = _event_owner_prefix(raw)
        if token:
            prefixes.append(token)
    return tuple(dict.fromkeys(prefixes))


def _event_owner_prefix(raw: str | None) -> str:
    token = (raw or "").strip().replace("-", "_")
    return token


def _thread_projection_contract_key(
    *, projection_experience_name: str, view_key: str | None
) -> str:
    return f"{projection_experience_name.casefold()}::{(view_key or '').casefold()}"


def _thread_projection_contract_has_view(
    *,
    projection_contract_keys: set[str],
    projection_experience_name: str,
    view_key: str | None,
) -> bool:
    exact_key = _thread_projection_contract_key(
        projection_experience_name=projection_experience_name,
        view_key=view_key,
    )
    family_key = _thread_projection_contract_key(
        projection_experience_name=projection_experience_name,
        view_key=None,
    )
    return (
        exact_key in projection_contract_keys or family_key in projection_contract_keys
    )


def _collapse_thread_projection_experience_ownership(
    *,
    declarations: list[ExperienceEnvironmentProfileThreadProjectionOwnership],
) -> list[ExperienceEnvironmentProfileThreadProjectionOwnership]:
    selected_by_projection: dict[
        str, ExperienceEnvironmentProfileThreadProjectionOwnership
    ] = {}
    for declaration in declarations:
        projection_key = declaration.projection_experience_name.casefold()
        selected = selected_by_projection.get(projection_key)
        if selected is None or (declaration.is_default and not selected.is_default):
            selected_by_projection[projection_key] = declaration
    return list(selected_by_projection.values())


def _assert_projection_view_ref_known(
    *,
    projection_experience_name: str,
    view_key: str | None,
    known_projection_view_refs_by_experience: dict[str, frozenset[str]],
    source_path: Path,
    label: str,
    external_projection_experience_prefixes: tuple[str, ...] = (),
    allow_external: bool = False,
) -> None:
    normalized_view_key = (view_key or "").strip()
    if not normalized_view_key:
        return
    known_view_refs = known_projection_view_refs_by_experience.get(
        projection_experience_name.casefold(),
        frozenset(),
    )
    if normalized_view_key.casefold() in known_view_refs:
        return
    if allow_external and _matches_external_projection_prefix(
        projection_experience_name=projection_experience_name,
        external_projection_experience_prefixes=external_projection_experience_prefixes,
    ):
        return
    raise ValueError(
        f"{label} references unknown view {normalized_view_key!r} for projection experience "
        f"{projection_experience_name!r} in {source_path}"
    )


def _normalize_external_projection_prefix(raw: str) -> str:
    token = _normalize_symbol(raw).replace("-", "_").replace(".", "_")
    return token.strip().casefold()


def _matches_external_projection_prefix(
    *,
    projection_experience_name: str,
    external_projection_experience_prefixes: tuple[str, ...],
) -> bool:
    normalized = _normalize_external_projection_prefix(projection_experience_name)
    if not normalized:
        return False
    raw_reference = (projection_experience_name or "").strip()
    qualifier = raw_reference.rpartition(".")[0]
    normalized_qualifier = qualifier.replace("-", "_").replace(".", "_").casefold()
    for prefix in external_projection_experience_prefixes:
        normalized_prefix = _normalize_external_projection_prefix(prefix)
        if not normalized_prefix:
            continue
        if normalized_qualifier and normalized_qualifier == normalized_prefix:
            return True
        if normalized == normalized_prefix or normalized.startswith(
            f"{normalized_prefix}_"
        ):
            return True
    return False


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
    "load_environment_profile_ownership_from_sources",
    "publish_environment_profile_transition_event_refs",
]
