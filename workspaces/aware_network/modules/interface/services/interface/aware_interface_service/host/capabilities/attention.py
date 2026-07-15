from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import cast
from uuid import UUID

from aware_attention_service_api import AwareAttentionServiceApiClient
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTopologyTransitionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTopologyTransitionSectionInput,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTransitionPin,
)
from aware_attention_service_dto.attention.session.models import (
    AttentionLayoutTransitionSectionInput,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTopologyTransitionRequest,
)
from aware_attention_service_dto.attention.session.service_operation import (
    ApplyAttentionSessionLayoutTransitionRequest,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountSnapshot,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionEnvironmentRuntimeTarget,
)
from aware_attention_service_dto.attention.section.service_operation import (
    ActivateAttentionSectionObservableRequest,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountLayoutRequest,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeMountSectionRequest,
)
from aware_attention_service_dto.attention.section.models import (
    AttentionRuntimeLayoutSectionState,
)
from aware_attention_service_dto.attention.section.service_operation import (
    GetAttentionRuntimeMountRequest,
)
from aware_attention_service_dto.attention.section.service_operation import (
    WatchAttentionRuntimeMountRequest,
)
from aware_interface import (
    InterfaceAttentionFocusTargetState,
    InterfaceResolvedSectionStateAddress,
    InterfaceNavigationContextLayoutTargetState,
    InterfaceWindowLayoutSectionState,
    InterfaceWindowLayoutState,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
    InterfaceWindowConfigBundle,
    InterfaceWindowConfigLayoutBundle,
)
from aware_interface_sdk.transport import InterfaceTransportSession
from aware_service_runtime.api_ingress.host_context import (
    current_service_api_host_context,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)
from aware_types import JsonObject


_ATTENTION_SERVICE_API_PACKAGE_NAME = "attention-service-api"


@dataclass(frozen=True, slots=True)
class AttentionRuntimeMountResolution:
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress]
    window_layout_sections: tuple[InterfaceWindowLayoutSectionState, ...] = ()
    admitted_window_layout_sections: tuple[InterfaceWindowLayoutSectionState, ...] = ()
    admitted_layout_sections: tuple[AttentionRuntimeLayoutSectionState, ...] = ()
    layout_sections: tuple[AttentionRuntimeLayoutSectionState, ...] = ()
    environment_target: AttentionEnvironmentRuntimeTarget | None = None
    attention_session_id: UUID | None = None
    attention_session_layout_id: UUID | None = None
    active_layout_transition: AttentionLayoutTransitionPin | None = None
    active_layout_topology_transition: AttentionLayoutTopologyTransitionPin | None = (
        None
    )
    active_layout_config_id: UUID | None = None
    active_layout_key: str | None = None
    active_section_key: str | None = None
    active_observable_id: UUID | None = None

    @property
    def active_layout_transition_id(self) -> UUID | None:
        transition = self.active_layout_transition
        return transition.attention_layout_transition_id if transition else None

    @property
    def active_topology_transition_id(self) -> UUID | None:
        transition = self.active_layout_topology_transition
        return (
            transition.attention_layout_topology_transition_id if transition else None
        )


@dataclass(frozen=True, slots=True)
class AttentionLayoutIntentSection:
    """One renderer-neutral row in a complete Interface Host layout intent."""

    layout_config_section_config_id: UUID
    order: int
    weight_micros: int
    is_visible: bool = True
    is_collapsed: bool = False


@dataclass(frozen=True, slots=True)
class AttentionLayoutIntent:
    """
    Full-vector intent pinned to one mounted AttentionSession layout.

    Interface Host never accepts pixels or floating-point geometry here. The
    caller's expected transition id is forwarded unchanged so a stale request
    fails closed at Attention authority instead of being silently retried.
    """

    attention_session_id: UUID
    attention_session_layout_id: UUID
    client_intent_id: str
    expected_previous_layout_transition_id: UUID | None
    section_states: tuple[AttentionLayoutIntentSection, ...]
    topology_transition_id: UUID | None = None
    transition_kind: str = "layout"
    source_kind: str = "interface_host_layout_intent"
    source_ref: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AttentionLayoutIntentResult:
    """Mutation outcome plus the committed Attention reconciliation pin."""

    outcome: str
    conflict_reason: str | None = None
    transition: AttentionLayoutTransitionPin | None = None
    latest_transition: AttentionLayoutTransitionPin | None = None

    @property
    def reconciliation_transition(self) -> AttentionLayoutTransitionPin | None:
        return self.latest_transition or self.transition


@dataclass(frozen=True, slots=True)
class AttentionLayoutTopologyIntentSection:
    """One admitted config-section anchor in a complete topology intent."""

    layout_config_section_config_id: UUID
    order: int


@dataclass(frozen=True, slots=True)
class AttentionLayoutTopologyIntent:
    """Full active-membership vector over the mounted admitted catalog."""

    attention_session_id: UUID
    attention_session_layout_id: UUID
    client_intent_id: str
    expected_previous_topology_transition_id: UUID | None
    section_states: tuple[AttentionLayoutTopologyIntentSection, ...]
    transition_kind: str = "topology"
    source_kind: str = "interface_host_layout_topology_intent"
    source_ref: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AttentionLayoutTopologyIntentResult:
    """Topology mutation outcome plus the committed reconciliation pin."""

    outcome: str
    conflict_reason: str | None = None
    transition: AttentionLayoutTopologyTransitionPin | None = None
    latest_transition: AttentionLayoutTopologyTransitionPin | None = None

    @property
    def reconciliation_transition(self) -> AttentionLayoutTopologyTransitionPin | None:
        return self.latest_transition or self.transition


def attention_session_id_from_materialized_session_frames(
    pane_states: Iterable[object],
    *,
    required: bool = True,
) -> UUID | None:
    """Derive one session scope from committed Experience frame evidence."""

    session_ids: set[UUID] = set()
    for pane_state in pane_states:
        provenance = _target_value(pane_state, "provenance")
        if not isinstance(provenance, Mapping):
            continue
        frame = provenance.get("session_view_frame")
        if not isinstance(frame, Mapping):
            continue
        raw_session_id = frame.get("attention_session_id")
        if raw_session_id is None:
            raw_session_id = provenance.get("attention_session_id")
        if raw_session_id is None:
            continue
        try:
            session_ids.add(
                raw_session_id
                if isinstance(raw_session_id, UUID)
                else UUID(str(raw_session_id))
            )
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(
                "Committed session_view_frame has an invalid attention_session_id."
            ) from exc
    if len(session_ids) > 1:
        raise ValueError(
            "Committed session_view_frame evidence resolves multiple "
            "AttentionSession ids."
        )
    if session_ids:
        return next(iter(session_ids))
    if required:
        raise ValueError(
            "Committed session_view_frame evidence is missing attention_session_id."
        )
    return None


def pin_window_layout_to_runtime_mount(
    *,
    window_layout: InterfaceWindowLayoutState,
    resolution: AttentionRuntimeMountResolution,
) -> InterfaceWindowLayoutState:
    transition = (
        resolution.active_layout_transition
        or resolution.active_layout_topology_transition
    )
    return replace(
        window_layout,
        attention_session_id=resolution.attention_session_id,
        attention_session_layout_id=resolution.attention_session_layout_id,
        active_layout_transition_id=resolution.active_layout_transition_id,
        active_topology_transition_id=resolution.active_topology_transition_id,
        object_instance_graph_commit_id=(
            transition.object_instance_graph_commit_id if transition else None
        ),
        graph_hash_post=transition.graph_hash_post if transition else None,
        admitted_sections=resolution.admitted_window_layout_sections,
    )


def build_attention_environment_runtime_target(
    *,
    navigation_context_layout_target: (
        InterfaceNavigationContextLayoutTargetState | None
    ),
) -> AttentionEnvironmentRuntimeTarget | None:
    if navigation_context_layout_target is None:
        return None
    if (
        navigation_context_layout_target.environment_id is None
        or navigation_context_layout_target.thread_id is None
        or navigation_context_layout_target.thread_layout_id is None
    ):
        return None
    evidence = (
        dict(navigation_context_layout_target.evidence)
        if isinstance(navigation_context_layout_target.evidence, dict)
        else {}
    )
    return AttentionEnvironmentRuntimeTarget(
        environment_id=navigation_context_layout_target.environment_id,
        environment_experience_profile_id=_evidence_uuid(
            evidence,
            "environment_experience_profile_id",
        ),
        environment_experience_profile_mount_id=_evidence_uuid(
            evidence,
            "environment_experience_profile_mount_id",
        ),
        mount_key=_evidence_text(evidence, "mount_key"),
        topology_seed_key=_evidence_text(evidence, "topology_seed_key"),
        process_config_id=_evidence_uuid(evidence, "process_config_id"),
        process_key=_evidence_text(evidence, "process_key"),
        process_id=navigation_context_layout_target.process_id,
        thread_config_id=_evidence_uuid(evidence, "thread_config_id"),
        thread_key=_evidence_text(evidence, "thread_key"),
        thread_id=navigation_context_layout_target.thread_id,
        thread_layout_config_id=_evidence_uuid(
            evidence,
            "thread_layout_config_id",
        ),
        layout_key=(
            navigation_context_layout_target.layout_key
            or _evidence_text(evidence, "layout_key")
        ),
        layout_config_id=navigation_context_layout_target.layout_config_id,
        layout_id=navigation_context_layout_target.layout_id,
        thread_layout_id=navigation_context_layout_target.thread_layout_id,
        activate_on_seed=_evidence_bool(evidence, "runtime_mount_activate_on_seed"),
        status=_evidence_text(evidence, "runtime_mount_status"),
    )


def runtime_mount_matches_environment_target(
    *,
    runtime_mount: AttentionRuntimeMountSnapshot | object | None,
    environment_target: AttentionEnvironmentRuntimeTarget | None,
) -> bool:
    if environment_target is None:
        return True
    if runtime_mount is None:
        return False
    return environment_runtime_targets_match(
        actual=_target_value(runtime_mount, "environment_target"),
        expected=environment_target,
    )


def environment_runtime_targets_match(
    *,
    actual: object | None,
    expected: AttentionEnvironmentRuntimeTarget,
) -> bool:
    if actual is None:
        return False
    for field_name in (
        "environment_id",
        "environment_experience_profile_id",
        "environment_experience_profile_mount_id",
        "process_config_id",
        "process_id",
        "thread_config_id",
        "thread_id",
        "thread_layout_config_id",
        "layout_config_id",
        "layout_id",
        "thread_layout_id",
    ):
        expected_value = _target_uuid(expected, field_name)
        if (
            expected_value is not None
            and _target_uuid(actual, field_name) != expected_value
        ):
            return False
    for field_name in (
        "mount_key",
        "topology_seed_key",
        "process_key",
        "thread_key",
        "layout_key",
    ):
        expected_value = _target_text(expected, field_name)
        if (
            expected_value is not None
            and _target_text(actual, field_name) != expected_value
        ):
            return False
    return _target_bool(actual, "activate_on_seed") == _target_bool(
        expected, "activate_on_seed"
    )


def _attention_client(
    *,
    transport_session: InterfaceTransportSession | None,
) -> AwareAttentionServiceApiClient | None:
    if transport_session is not None:
        return AwareAttentionServiceApiClient(transport_session.client)

    host_context = current_service_api_host_context()
    if host_context is None:
        return None
    invoker = build_service_api_client_for_api_package(
        host_context.service_api_dependency_routes,
        api_package_name=_ATTENTION_SERVICE_API_PACKAGE_NAME,
        consumer_service_package_id=host_context.service_package_id,
        consumer_service_package_name=host_context.service_package_name,
        actor_id=host_context.operation_context.actor_id,
        invocation_context=cast(
            JsonObject | None,
            (
                dict(host_context.invocation_context)
                if host_context.invocation_context is not None
                else None
            ),
        ),
    )
    if invoker is None:
        return None
    return AwareAttentionServiceApiClient(invoker)


def _window_bundle(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
) -> InterfaceWindowConfigBundle | None:
    if interface_config_bundle is None:
        return None
    normalized_window_key = (bundle_window_key or "").strip().casefold()
    if normalized_window_key:
        for window in interface_config_bundle.window_configs:
            if window.key.strip().casefold() == normalized_window_key:
                return window
    return next(iter(interface_config_bundle.window_configs), None)


def _layout_bundle(
    *,
    window_bundle: InterfaceWindowConfigBundle | None,
    layout_config_id: UUID | None,
    layout_key: str | None,
    section_key: str | None = None,
) -> InterfaceWindowConfigLayoutBundle | None:
    if window_bundle is None:
        return None
    if layout_config_id is not None:
        for layout in window_bundle.layout_configs:
            if layout.layout_config_id == layout_config_id:
                return layout
    normalized_layout_key = (layout_key or "").strip().casefold()
    if normalized_layout_key:
        for layout in window_bundle.layout_configs:
            if layout.key.strip().casefold() == normalized_layout_key:
                return layout
    normalized_section_key = (section_key or "").strip().casefold()
    if normalized_section_key:
        matching_layouts = tuple(
            layout
            for layout in window_bundle.layout_configs
            if any(
                section.key.strip().casefold() == normalized_section_key
                for section in layout.sections
            )
        )
        if len(matching_layouts) == 1:
            return matching_layouts[0]
    for layout in window_bundle.layout_configs:
        if layout.is_default:
            return layout
    return next(iter(window_bundle.layout_configs), None)


def _layout_section_config_id(
    *,
    layout_bundle: InterfaceWindowConfigLayoutBundle | None,
    section_key: str | None,
) -> UUID | None:
    if layout_bundle is None or section_key is None:
        return None
    normalized_section_key = section_key.strip().casefold()
    for section in layout_bundle.sections:
        if section.key.strip().casefold() == normalized_section_key:
            return section.layout_config_section_config_id
    return None


def _resolve_focus_observable_id(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    layout_config_id: UUID | None,
    layout_key: str | None,
    section_key: str | None,
    observable_id: UUID | None,
) -> UUID | None:
    window_bundle = _window_bundle(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=bundle_window_key,
    )
    layout_bundle = _layout_bundle(
        window_bundle=window_bundle,
        layout_config_id=layout_config_id,
        layout_key=layout_key,
    )
    section_config_id = _layout_section_config_id(
        layout_bundle=layout_bundle,
        section_key=section_key,
    )
    if section_config_id is None:
        return None

    if observable_id is not None:
        return observable_id

    matches: dict[UUID, str] = {}
    for candidate_observable_id in _iter_section_observable_mounts(
        interface_config_bundle=interface_config_bundle,
        section_config_id=section_config_id,
    ):
        matches[candidate_observable_id] = str(candidate_observable_id)
    if len(matches) != 1:
        return None
    return next(iter(matches))


def _iter_section_observable_mounts(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    section_config_id: UUID,
):
    if interface_config_bundle is None:
        return
    for pane_config in interface_config_bundle.pane_configs:
        for projection_view in pane_config.projection_experience_views:
            observable_id = projection_view.object_projection_graph_observable_id
            if observable_id is None:
                continue
            for mount in projection_view.section_mounts:
                if mount.layout_config_section_config_id != section_config_id:
                    continue
                yield observable_id


def _apply_runtime_mount_to_section_state_addresses(
    *,
    runtime_mount: AttentionRuntimeMountSnapshot,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
) -> dict[str, InterfaceResolvedSectionStateAddress]:
    addresses = dict(section_state_addresses)
    for snapshot in runtime_mount.section_snapshots:
        current = addresses.get(snapshot.section_key)
        focus_target = _focus_target_state_from_attention_target(
            getattr(snapshot, "focus_target", None)
        )
        addresses[snapshot.section_key] = InterfaceResolvedSectionStateAddress(
            section_key=snapshot.section_key,
            layout_section_id=(
                current.layout_section_id if current is not None else None
            ),
            section_focus_scope_id=(
                snapshot.section_focus_scope_id
                if snapshot.section_focus_scope_id is not None
                else (current.section_focus_scope_id if current is not None else None)
            ),
            focus_scope_id=(
                snapshot.focus_scope_id
                if snapshot.focus_scope_id is not None
                else (current.focus_scope_id if current is not None else None)
            ),
            focus_id=(
                snapshot.focus_id
                if getattr(snapshot, "focus_id", None) is not None
                else (
                    focus_target.focus_id
                    if focus_target is not None and focus_target.focus_id is not None
                    else current.focus_id if current is not None else None
                )
            ),
            observable_id=(
                snapshot.observable_id
                if snapshot.exists
                else (current.observable_id if current is not None else None)
            ),
            branch_id=(
                focus_target.object_instance_graph_branch_id
                if focus_target is not None
                and focus_target.object_instance_graph_branch_id is not None
                else current.branch_id if current is not None else None
            ),
            state_projection_hash=(
                focus_target.projection_hash
                if focus_target is not None and focus_target.projection_hash is not None
                else current.state_projection_hash if current is not None else None
            ),
            focus_target=(
                focus_target
                if focus_target is not None
                else current.focus_target if current is not None else None
            ),
        )
    return addresses


def _focus_target_state_from_attention_target(
    focus_target: object | None,
) -> InterfaceAttentionFocusTargetState | None:
    if focus_target is None:
        return None
    object_projection_graph_identity_id = _target_uuid(
        focus_target,
        "object_projection_graph_identity_id",
    )
    if object_projection_graph_identity_id is None:
        return None
    kind = _target_optional_text(focus_target, "kind") or "constructor"
    return InterfaceAttentionFocusTargetState(
        kind=kind,
        focus_id=_target_uuid(focus_target, "focus_id"),
        focus_scope_id=_target_uuid(focus_target, "focus_scope_id"),
        projection_experience_graph_identity_id=_target_uuid(
            focus_target,
            "projection_experience_graph_identity_id",
        ),
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_branch_id=_target_uuid(
            focus_target,
            "object_instance_graph_branch_id",
        ),
        projection_hash=_target_optional_text(focus_target, "projection_hash"),
        target_type=_target_optional_text(focus_target, "target_type"),
        target_id=_target_uuid(focus_target, "target_id"),
        description=_target_optional_text(focus_target, "description"),
    )


def _resolution_from_runtime_mount(
    *,
    runtime_mount: AttentionRuntimeMountSnapshot,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
) -> AttentionRuntimeMountResolution:
    return AttentionRuntimeMountResolution(
        section_state_addresses=_apply_runtime_mount_to_section_state_addresses(
            runtime_mount=runtime_mount,
            section_state_addresses=section_state_addresses,
        ),
        window_layout_sections=_window_layout_sections_from_runtime_mount(
            runtime_mount=runtime_mount,
        ),
        admitted_window_layout_sections=_window_layout_sections_from_states(
            getattr(runtime_mount, "admitted_layout_sections", ()),
        ),
        layout_sections=tuple(
            sorted(
                getattr(runtime_mount, "layout_sections", ()),
                key=lambda item: (item.order, item.section_key),
            )
        ),
        admitted_layout_sections=tuple(
            sorted(
                getattr(runtime_mount, "admitted_layout_sections", ()),
                key=lambda item: (item.order, item.section_key),
            )
        ),
        environment_target=getattr(runtime_mount, "environment_target", None),
        attention_session_id=getattr(runtime_mount, "attention_session_id", None),
        attention_session_layout_id=getattr(
            runtime_mount,
            "attention_session_layout_id",
            None,
        ),
        active_layout_transition=getattr(
            runtime_mount,
            "active_layout_transition",
            None,
        ),
        active_layout_topology_transition=getattr(
            runtime_mount,
            "active_layout_topology_transition",
            None,
        ),
        active_layout_config_id=runtime_mount.layout_config_id,
        active_layout_key=runtime_mount.layout_key,
        active_section_key=runtime_mount.active_section_key,
        active_observable_id=runtime_mount.active_observable_id,
    )


def _window_layout_sections_from_runtime_mount(
    *,
    runtime_mount: AttentionRuntimeMountSnapshot,
) -> tuple[InterfaceWindowLayoutSectionState, ...]:
    return _window_layout_sections_from_states(
        getattr(runtime_mount, "layout_sections", ()),
    )


def _window_layout_sections_from_states(
    layout_sections: Iterable[object],
) -> tuple[InterfaceWindowLayoutSectionState, ...]:
    sections: list[InterfaceWindowLayoutSectionState] = []
    for index, section in enumerate(layout_sections):
        section_key = _target_optional_text(section, "section_key")
        if section_key is None:
            continue
        is_visible = _target_optional_bool(section, "is_visible")
        is_collapsed = _target_optional_bool(section, "is_collapsed") or False
        sections.append(
            InterfaceWindowLayoutSectionState(
                section_key=section_key,
                layout_config_section_config_id=_target_uuid(
                    section,
                    "layout_config_section_config_id",
                ),
                layout_section_id=_target_uuid(section, "layout_section_id"),
                attention_session_section_id=_target_uuid(
                    section,
                    "attention_session_section_id",
                ),
                title=_target_optional_text(section, "title"),
                description=_target_optional_text(section, "description"),
                order=_target_int(section, "order", fallback=index),
                flex=_target_float(section, "flex", fallback=1.0),
                weight_micros=(
                    _target_int(section, "weight_micros", fallback=0)
                    if _target_value(section, "weight_micros") is not None
                    else None
                ),
                is_visible=True if is_visible is None else is_visible,
                is_collapsed=is_collapsed,
            )
        )
    return tuple(sorted(sections, key=lambda item: (item.order, item.section_key)))


async def enrich_section_state_addresses_from_attention(
    *,
    transport_session: InterfaceTransportSession | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    window_layout: InterfaceWindowLayoutState,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
    environment_target: AttentionEnvironmentRuntimeTarget | None = None,
) -> dict[str, InterfaceResolvedSectionStateAddress]:
    _ = window_layout
    return (
        await resolve_runtime_mount_from_attention(
            transport_session=transport_session,
            interface_config_bundle=interface_config_bundle,
            bundle_window_key=bundle_window_key,
            section_state_addresses=section_state_addresses,
            environment_target=environment_target,
        )
    ).section_state_addresses


async def resolve_runtime_mount_from_attention(
    *,
    transport_session: InterfaceTransportSession | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
    environment_target: AttentionEnvironmentRuntimeTarget | None = None,
    attention_session_id: UUID | None = None,
    preferred_layout_config_id: UUID | None = None,
    preferred_section_key: str | None = None,
    preferred_observable_id: UUID | None = None,
) -> AttentionRuntimeMountResolution:
    window_bundle = _window_bundle(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=bundle_window_key,
    )
    layout_requests = _runtime_mount_layout_requests(
        interface_config_bundle=interface_config_bundle,
        window_bundle=window_bundle,
    )
    local_layout_bundle = _layout_bundle(
        window_bundle=window_bundle,
        layout_config_id=None,
        layout_key=None,
        section_key=preferred_section_key,
    )
    client = _attention_client(transport_session=transport_session)
    if client is None:
        if environment_target is not None:
            raise RuntimeError(
                "Interface runtime target resolution requires Attention service."
            )
        return AttentionRuntimeMountResolution(
            section_state_addresses=section_state_addresses,
            environment_target=environment_target,
            active_layout_config_id=(
                local_layout_bundle.layout_config_id
                if local_layout_bundle is not None
                else None
            ),
            active_layout_key=(
                local_layout_bundle.key if local_layout_bundle is not None else None
            ),
            active_section_key=preferred_section_key,
            active_observable_id=preferred_observable_id,
        )
    addresses = dict(section_state_addresses)
    try:
        response = await client.attention.get_runtime_mount.get_runtime_mount(
            GetAttentionRuntimeMountRequest(
                window_key=(
                    window_bundle.key
                    if window_bundle is not None
                    else bundle_window_key
                ),
                environment_target=environment_target,
                attention_session_id=attention_session_id,
                preferred_layout_config_id=preferred_layout_config_id,
                preferred_layout_key=None,
                preferred_section_key=preferred_section_key,
                preferred_observable_id=preferred_observable_id,
                layouts=layout_requests,
            )
        )
    except Exception:
        if environment_target is not None or attention_session_id is not None:
            raise
        return AttentionRuntimeMountResolution(
            section_state_addresses=addresses,
            environment_target=environment_target,
            active_layout_config_id=(
                local_layout_bundle.layout_config_id
                if local_layout_bundle is not None
                else None
            ),
            active_layout_key=(
                local_layout_bundle.key if local_layout_bundle is not None else None
            ),
            active_section_key=preferred_section_key,
            active_observable_id=preferred_observable_id,
        )
    runtime_mount = response.runtime_mount
    if runtime_mount is None:
        if environment_target is not None:
            raise ValueError(
                "Attention runtime mount response is missing runtime_mount."
            )
        return AttentionRuntimeMountResolution(
            section_state_addresses=addresses,
            environment_target=environment_target,
            active_layout_config_id=(
                local_layout_bundle.layout_config_id
                if local_layout_bundle is not None
                else None
            ),
            active_layout_key=(
                local_layout_bundle.key if local_layout_bundle is not None else None
            ),
            active_section_key=preferred_section_key,
            active_observable_id=preferred_observable_id,
        )
    if not runtime_mount_matches_environment_target(
        runtime_mount=runtime_mount,
        environment_target=environment_target,
    ):
        raise ValueError(
            "Attention runtime mount target did not match Environment receipt."
        )
    return _resolution_from_runtime_mount(
        runtime_mount=runtime_mount,
        section_state_addresses=addresses,
    )


def _default_section_observables_for_layout_bundle(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    layout_bundle: InterfaceWindowConfigLayoutBundle | None,
) -> dict[str, UUID]:
    if layout_bundle is None:
        return {}

    defaults: dict[str, UUID] = {}
    for section in layout_bundle.sections:
        section_candidates: dict[UUID, str] = {}
        for candidate_observable_id in _iter_section_observable_mounts(
            interface_config_bundle=interface_config_bundle,
            section_config_id=section.layout_config_section_config_id,
        ):
            section_candidates[candidate_observable_id] = str(candidate_observable_id)
        if len(section_candidates) == 1:
            defaults[section.key] = next(iter(section_candidates))
    return defaults


def _runtime_mount_layout_requests(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    window_bundle: InterfaceWindowConfigBundle | None,
) -> list[AttentionRuntimeMountLayoutRequest]:
    if window_bundle is None:
        return []
    requests: list[AttentionRuntimeMountLayoutRequest] = []
    for layout in window_bundle.layout_configs:
        defaults_by_section = _default_section_observables_for_layout_bundle(
            interface_config_bundle=interface_config_bundle,
            layout_bundle=layout,
        )
        requests.append(
            AttentionRuntimeMountLayoutRequest(
                layout_config_id=layout.layout_config_id,
                layout_key=layout.key,
                is_default=layout.is_default,
                sections=[
                    AttentionRuntimeMountSectionRequest(
                        layout_config_section_config_id=(
                            section.layout_config_section_config_id
                        ),
                        section_key=section.key,
                        order=section_index,
                        default_observable_id=defaults_by_section.get(section.key),
                        default_rationale="interface_runtime_default_section_observable",
                    )
                    for section_index, section in enumerate(layout.sections)
                ],
            )
        )
    return requests


def build_watch_runtime_mount_request(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    environment_target: AttentionEnvironmentRuntimeTarget | None = None,
    attention_session_id: UUID | None = None,
    preferred_layout_config_id: UUID | None = None,
    preferred_layout_key: str | None = None,
    preferred_section_key: str | None = None,
    preferred_observable_id: UUID | None = None,
    poll_interval_ms: int = 1000,
) -> WatchAttentionRuntimeMountRequest | None:
    window_bundle = _window_bundle(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=bundle_window_key,
    )
    if window_bundle is None:
        return None
    layout_requests = _runtime_mount_layout_requests(
        interface_config_bundle=interface_config_bundle,
        window_bundle=window_bundle,
    )
    if not layout_requests:
        return None
    return WatchAttentionRuntimeMountRequest(
        window_key=window_bundle.key,
        environment_target=environment_target,
        attention_session_id=attention_session_id,
        preferred_layout_config_id=preferred_layout_config_id,
        preferred_layout_key=preferred_layout_key,
        preferred_section_key=preferred_section_key,
        preferred_observable_id=preferred_observable_id,
        poll_interval_ms=poll_interval_ms,
        layouts=layout_requests,
    )


def runtime_mount_watch_request_signature(
    request: WatchAttentionRuntimeMountRequest | None,
) -> str | None:
    if request is None:
        return None
    payload = request.model_dump(mode="json", exclude_none=True)
    payload.pop("poll_interval_ms", None)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )


async def stream_runtime_mount_from_attention(
    *,
    transport_session: InterfaceTransportSession | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
    environment_target: AttentionEnvironmentRuntimeTarget | None = None,
    attention_session_id: UUID | None = None,
    preferred_layout_config_id: UUID | None = None,
    preferred_layout_key: str | None = None,
    preferred_section_key: str | None = None,
    preferred_observable_id: UUID | None = None,
    poll_interval_ms: int = 1000,
) -> AsyncIterator[AttentionRuntimeMountResolution]:
    client = _attention_client(transport_session=transport_session)
    request = build_watch_runtime_mount_request(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=bundle_window_key,
        environment_target=environment_target,
        attention_session_id=attention_session_id,
        preferred_layout_config_id=preferred_layout_config_id,
        preferred_layout_key=preferred_layout_key,
        preferred_section_key=preferred_section_key,
        preferred_observable_id=preferred_observable_id,
        poll_interval_ms=poll_interval_ms,
    )
    if client is None or request is None:
        if environment_target is not None:
            raise RuntimeError(
                "Interface runtime target watch requires Attention service."
            )
        return
    addresses = dict(section_state_addresses)
    async for event in client.attention.watch_runtime_mount.stream_watch_runtime_mount(
        request
    ):
        if not runtime_mount_matches_environment_target(
            runtime_mount=event.runtime_mount,
            environment_target=environment_target,
        ):
            raise ValueError(
                "Attention runtime mount target did not match Environment receipt."
            )
        resolution = _resolution_from_runtime_mount(
            runtime_mount=event.runtime_mount,
            section_state_addresses=addresses,
        )
        addresses = resolution.section_state_addresses
        yield resolution


async def apply_session_layout_intent_through_attention(
    *,
    transport_session: InterfaceTransportSession | None,
    runtime_mount: AttentionRuntimeMountResolution,
    intent: AttentionLayoutIntent,
) -> AttentionLayoutIntentResult:
    """
    Submit one complete Host intent through the generated Attention API.

    The runtime-mount snapshot supplies the authoritative mapping from stable
    Interface section-config ids to mounted AttentionSessionSection ids. This
    function performs one mutation call and never retries a conflict.
    """

    client = _attention_client(transport_session=transport_session)
    if client is None:
        raise RuntimeError("Interface layout intent requires Attention service.")
    section_states = _attention_layout_transition_inputs(
        runtime_mount=runtime_mount,
        intent=intent,
    )
    response = await client.attention.apply_session_layout_transition.apply_session_layout_transition(
        ApplyAttentionSessionLayoutTransitionRequest(
            attention_session_id=intent.attention_session_id,
            attention_session_layout_id=intent.attention_session_layout_id,
            client_intent_id=intent.client_intent_id.strip(),
            expected_previous_layout_transition_id=(
                intent.expected_previous_layout_transition_id
            ),
            topology_transition_id=intent.topology_transition_id,
            section_states=section_states,
            transition_kind=intent.transition_kind.strip(),
            source_kind=intent.source_kind.strip() or None,
            source_ref=(intent.source_ref or "").strip() or None,
            metadata_json=cast(JsonObject, dict(intent.metadata)),
        )
    )
    if response.outcome not in {"committed", "idempotent", "conflict"}:
        raise RuntimeError(
            "Attention returned an unknown layout transition outcome: "
            f"{response.outcome!r}"
        )
    return AttentionLayoutIntentResult(
        outcome=response.outcome,
        conflict_reason=response.conflict_reason,
        transition=response.transition,
        latest_transition=response.latest_transition,
    )


async def apply_session_layout_topology_intent_through_attention(
    *,
    transport_session: InterfaceTransportSession | None,
    runtime_mount: AttentionRuntimeMountResolution,
    intent: AttentionLayoutTopologyIntent,
) -> AttentionLayoutTopologyIntentResult:
    """Submit one complete topology intent once through generated Attention API."""

    client = _attention_client(transport_session=transport_session)
    if client is None:
        raise RuntimeError(
            "Interface layout topology intent requires Attention service."
        )
    section_states = _attention_layout_topology_transition_inputs(
        runtime_mount=runtime_mount,
        intent=intent,
    )
    response = await client.attention.apply_session_layout_topology_transition.apply_session_layout_topology_transition(
        ApplyAttentionSessionLayoutTopologyTransitionRequest(
            attention_session_id=intent.attention_session_id,
            attention_session_layout_id=intent.attention_session_layout_id,
            client_intent_id=intent.client_intent_id.strip(),
            expected_previous_topology_transition_id=(
                intent.expected_previous_topology_transition_id
            ),
            section_states=section_states,
            transition_kind=intent.transition_kind.strip(),
            source_kind=intent.source_kind.strip() or None,
            source_ref=(intent.source_ref or "").strip() or None,
            metadata_json=cast(JsonObject, dict(intent.metadata)),
        )
    )
    if response.outcome not in {"committed", "idempotent", "conflict"}:
        raise RuntimeError(
            "Attention returned an unknown layout topology transition outcome: "
            f"{response.outcome!r}"
        )
    return AttentionLayoutTopologyIntentResult(
        outcome=response.outcome,
        conflict_reason=response.conflict_reason,
        transition=response.transition,
        latest_transition=response.latest_transition,
    )


def _attention_layout_topology_transition_inputs(
    *,
    runtime_mount: AttentionRuntimeMountResolution,
    intent: AttentionLayoutTopologyIntent,
) -> list[AttentionLayoutTopologyTransitionSectionInput]:
    if runtime_mount.attention_session_id != intent.attention_session_id:
        raise ValueError(
            "Layout topology intent attention_session_id does not match runtime mount."
        )
    if runtime_mount.attention_session_layout_id != intent.attention_session_layout_id:
        raise ValueError(
            "Layout topology intent attention_session_layout_id does not match runtime mount."
        )
    if not intent.client_intent_id.strip():
        raise ValueError("Layout topology intent client_intent_id must be non-empty.")
    if not intent.transition_kind.strip():
        raise ValueError("Layout topology intent transition_kind must be non-empty.")
    if not intent.section_states:
        raise ValueError("Layout topology intent must contain at least one section.")

    admitted_by_section_config_id: dict[UUID, AttentionRuntimeLayoutSectionState] = {}
    for admitted in runtime_mount.admitted_layout_sections:
        section_config_id = admitted.layout_config_section_config_id
        session_section_id = admitted.attention_session_section_id
        if section_config_id is None or session_section_id is None:
            raise ValueError(
                "Admitted runtime mount section is missing stable config/session ids."
            )
        if section_config_id in admitted_by_section_config_id:
            raise ValueError(
                "Admitted runtime mount contains duplicate "
                f"layout_config_section_config_id: {section_config_id}"
            )
        admitted_by_section_config_id[section_config_id] = admitted

    seen_ids: set[UUID] = set()
    seen_orders: set[int] = set()
    inputs: list[AttentionLayoutTopologyTransitionSectionInput] = []
    for row in sorted(intent.section_states, key=lambda item: item.order):
        section_config_id = row.layout_config_section_config_id
        if section_config_id in seen_ids:
            raise ValueError(
                "Layout topology intent contains duplicate "
                f"layout_config_section_config_id: {section_config_id}"
            )
        if row.order < 0 or row.order in seen_orders:
            raise ValueError(
                "Layout topology intent section orders must be unique and non-negative."
            )
        admitted = admitted_by_section_config_id.get(section_config_id)
        if admitted is None:
            raise ValueError(
                "Layout topology intent contains a section outside the admitted catalog: "
                f"{section_config_id}"
            )
        session_section_id = admitted.attention_session_section_id
        if session_section_id is None:
            raise RuntimeError(
                "Validated admitted runtime mount lost attention_session_section_id."
            )
        inputs.append(
            AttentionLayoutTopologyTransitionSectionInput(
                attention_session_section_id=session_section_id,
                order=row.order,
            )
        )
        seen_ids.add(section_config_id)
        seen_orders.add(row.order)
    if seen_orders != set(range(len(inputs))):
        raise ValueError(
            "Layout topology intent section orders must be contiguous "
            f"0..{len(inputs) - 1}."
        )
    return inputs


def _attention_layout_transition_inputs(
    *,
    runtime_mount: AttentionRuntimeMountResolution,
    intent: AttentionLayoutIntent,
) -> list[AttentionLayoutTransitionSectionInput]:
    if runtime_mount.attention_session_id != intent.attention_session_id:
        raise ValueError(
            "Layout intent attention_session_id does not match runtime mount."
        )
    if runtime_mount.attention_session_layout_id != intent.attention_session_layout_id:
        raise ValueError(
            "Layout intent attention_session_layout_id does not match runtime mount."
        )
    if not intent.client_intent_id.strip():
        raise ValueError("Layout intent client_intent_id must be non-empty.")
    if not intent.transition_kind.strip():
        raise ValueError("Layout intent transition_kind must be non-empty.")
    if not intent.section_states:
        raise ValueError("Layout intent must contain at least one section.")

    mounted_by_section_config_id: dict[UUID, AttentionRuntimeLayoutSectionState] = {}
    for mounted in runtime_mount.layout_sections:
        section_config_id = mounted.layout_config_section_config_id
        if section_config_id is None:
            raise ValueError(
                "Runtime mount section is missing layout_config_section_config_id."
            )
        if mounted.attention_session_section_id is None:
            raise ValueError(
                "Runtime mount section is missing attention_session_section_id."
            )
        if section_config_id in mounted_by_section_config_id:
            raise ValueError(
                "Runtime mount contains duplicate layout_config_section_config_id: "
                f"{section_config_id}"
            )
        mounted_by_section_config_id[section_config_id] = mounted

    intent_by_section_config_id: dict[UUID, AttentionLayoutIntentSection] = {}
    seen_orders: set[int] = set()
    for row in intent.section_states:
        section_config_id = row.layout_config_section_config_id
        if section_config_id in intent_by_section_config_id:
            raise ValueError(
                "Layout intent contains duplicate layout_config_section_config_id: "
                f"{section_config_id}"
            )
        if row.order < 0 or row.order in seen_orders:
            raise ValueError(
                "Layout intent section orders must be unique and non-negative."
            )
        if row.weight_micros < 0:
            raise ValueError("Layout intent weight_micros must be non-negative.")
        if (not row.is_visible or row.is_collapsed) and row.weight_micros != 0:
            raise ValueError(
                "Hidden or collapsed layout intent sections must have zero weight_micros."
            )
        if row.is_visible and not row.is_collapsed and row.weight_micros <= 0:
            raise ValueError(
                "Visible non-collapsed layout intent sections require positive weight_micros."
            )
        intent_by_section_config_id[section_config_id] = row
        seen_orders.add(row.order)

    mounted_ids = set(mounted_by_section_config_id)
    intent_ids = set(intent_by_section_config_id)
    if intent_ids != mounted_ids:
        missing = sorted(str(value) for value in mounted_ids - intent_ids)
        unknown = sorted(str(value) for value in intent_ids - mounted_ids)
        raise ValueError(
            "Layout intent section membership must match runtime mount; "
            f"missing={missing} unknown={unknown}"
        )
    expected_orders = set(range(len(intent.section_states)))
    if seen_orders != expected_orders:
        raise ValueError(
            "Layout intent section orders must be contiguous "
            f"0..{len(intent.section_states) - 1}."
        )
    active_weight_sum = sum(
        row.weight_micros
        for row in intent.section_states
        if row.is_visible and not row.is_collapsed
    )
    if active_weight_sum != 1_000_000:
        raise ValueError(
            "Visible non-collapsed layout intent weight_micros must sum to "
            f"1000000; have={active_weight_sum}."
        )

    section_inputs: list[AttentionLayoutTransitionSectionInput] = []
    for row in sorted(intent.section_states, key=lambda item: item.order):
        attention_session_section_id = mounted_by_section_config_id[
            row.layout_config_section_config_id
        ].attention_session_section_id
        if attention_session_section_id is None:
            raise RuntimeError(
                "Validated runtime mount lost attention_session_section_id."
            )
        section_inputs.append(
            AttentionLayoutTransitionSectionInput(
                attention_session_section_id=attention_session_section_id,
                order=row.order,
                weight_micros=row.weight_micros,
                is_visible=row.is_visible,
                is_collapsed=row.is_collapsed,
            )
        )
    return section_inputs


def attention_managed_section_defaults(
    *,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    window_layout: InterfaceWindowLayoutState | None,
) -> dict[str, UUID]:
    if window_layout is None:
        return {}
    return _default_section_observables_for_layout_bundle(
        interface_config_bundle=interface_config_bundle,
        layout_bundle=_layout_bundle(
            window_bundle=_window_bundle(
                interface_config_bundle=interface_config_bundle,
                bundle_window_key=bundle_window_key,
            ),
            layout_config_id=window_layout.layout_config_id,
            layout_key=window_layout.layout_key,
        ),
    )


async def activate_attention_observable_for_runtime_focus(
    *,
    transport_session: InterfaceTransportSession | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    bundle_window_key: str | None,
    layout_config_id: UUID | None,
    layout_key: str | None,
    section_key: str | None,
    observable_id: UUID | None,
) -> UUID | None:
    client = _attention_client(transport_session=transport_session)
    if client is None or interface_config_bundle is None or section_key is None:
        return None
    observable_id = _resolve_focus_observable_id(
        interface_config_bundle=interface_config_bundle,
        bundle_window_key=bundle_window_key,
        layout_config_id=layout_config_id,
        layout_key=layout_key,
        section_key=section_key,
        observable_id=observable_id,
    )
    if observable_id is None:
        return None
    try:
        await client.attention.activate_section_observable.activate_section_observable(
            ActivateAttentionSectionObservableRequest(
                section_key=section_key,
                observable_id=observable_id,
                rationale="interface_runtime_focus_activation",
            )
        )
    except Exception:
        return None
    return observable_id


def _target_value(target: object, field_name: str) -> object:
    if isinstance(target, dict):
        return target.get(field_name)
    return getattr(target, field_name, None)


def _target_uuid(target: object, field_name: str) -> UUID | None:
    value = _target_value(target, field_name)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _target_text(target: object, field_name: str) -> str | None:
    value = _target_value(target, field_name)
    if value is None:
        return None
    text = str(value).strip()
    return text.casefold() if text else None


def _target_optional_text(target: object, field_name: str) -> str | None:
    value = _target_value(target, field_name)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _target_int(target: object, field_name: str, *, fallback: int) -> int:
    value = _target_value(target, field_name)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if value is not None:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            pass
    return fallback


def _target_float(target: object, field_name: str, *, fallback: float) -> float:
    value = _target_value(target, field_name)
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if value is not None:
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            pass
    return fallback


def _target_optional_bool(target: object, field_name: str) -> bool | None:
    value = _target_value(target, field_name)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    text = _target_text(target, field_name)
    if text is None:
        return None
    return text in {"true", "1", "yes", "on"}


def _target_bool(target: object, field_name: str) -> bool:
    return _target_optional_bool(target, field_name) or False


def _evidence_uuid(evidence: dict[str, object], key: str) -> UUID | None:
    value = evidence.get(key)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _evidence_text(evidence: dict[str, object], key: str) -> str | None:
    value = evidence.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _evidence_bool(evidence: dict[str, object], key: str) -> bool:
    value = evidence.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    text = _evidence_text(evidence, key)
    if text is None:
        return False
    return text.casefold() in {"true", "1", "yes", "on"}


__all__ = [
    "AttentionLayoutIntent",
    "AttentionLayoutIntentResult",
    "AttentionLayoutIntentSection",
    "AttentionRuntimeMountResolution",
    "activate_attention_observable_for_runtime_focus",
    "apply_session_layout_intent_through_attention",
    "attention_session_id_from_materialized_session_frames",
    "attention_managed_section_defaults",
    "build_attention_environment_runtime_target",
    "build_watch_runtime_mount_request",
    "enrich_section_state_addresses_from_attention",
    "environment_runtime_targets_match",
    "pin_window_layout_to_runtime_mount",
    "resolve_runtime_mount_from_attention",
    "runtime_mount_matches_environment_target",
    "runtime_mount_watch_request_signature",
    "stream_runtime_mount_from_attention",
]
