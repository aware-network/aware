from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_sdk import ExperienceSdkClient, build_experience_sdk_client
from aware_experience_service_dto.experience.section_graph_binding.models import (
    ExperienceSectionFocusTarget,
    ExperienceSectionGraphBindingDescriptor,
)
from aware_experience_service_dto.experience.section_graph_binding.service_operation import (
    ActivateExperienceSectionGraphBindingRequest,
    ExperienceSectionGraphBindingActivationScope,
    GetExperienceSectionGraphBindingCatalogRequest,
)
from aware_interface import (
    InterfaceAttentionFocusTargetState,
    InterfaceResolvedSectionStateAddress,
    InterfaceRuntimeSectionRepresentationState,
    InterfaceNavigationContextLayoutTargetState,
)
from aware_interface_service_dto.comms.models.interface_config_bundle import (
    InterfaceConfigBundle,
)
from aware_interface_sdk.transport import InterfaceTransportSession


@dataclass(frozen=True, slots=True)
class ExperienceSectionViewActionResolution:
    action_key: str
    view_invocation_action_config_id: UUID
    action_kind: str | None = None
    target_ref: str | None = None


@dataclass(frozen=True, slots=True)
class ExperienceSectionGraphBindingActivationResolution:
    experience_name: str
    binding_key: str
    section_key: str
    projection_observable_id: UUID
    projection_experience_graph_identity_id: UUID
    object_projection_graph_identity_id: UUID
    projection_experience_view_instance_id: UUID | None = None
    view_actions: tuple[ExperienceSectionViewActionResolution, ...] = ()
    focus_target: InterfaceAttentionFocusTargetState | None = None


async def activate_experience_section_graph_binding_for_runtime_focus(
    *,
    transport_session: InterfaceTransportSession | None,
    interface_config_bundle: InterfaceConfigBundle | None,
    navigation_context_layout_target: InterfaceNavigationContextLayoutTargetState | None,
    section_state_addresses: dict[str, InterfaceResolvedSectionStateAddress],
    window_key: str | None,
    layout_key: str | None,
    section_key: str | None,
    observable_id: UUID | None,
    representation: InterfaceRuntimeSectionRepresentationState | None = None,
) -> ExperienceSectionGraphBindingActivationResolution | None:
    client = _experience_client(transport_session=transport_session)
    if (
        client is None
        or interface_config_bundle is None
        or section_key is None
        or observable_id is None
    ):
        return None

    view_ref = _representation_view_ref(representation) or _bundle_view_ref_for_focus(
        interface_config_bundle=interface_config_bundle,
        section_key=section_key,
        observable_id=observable_id,
    )
    experience_name = _experience_name_from_view_ref(view_ref)
    if experience_name is None:
        return None

    binding_key = _representation_binding_key(representation) or _mapped_binding_key(
        navigation_context_layout_target=navigation_context_layout_target,
        section_key=section_key,
        observable_id=observable_id,
        view_ref=view_ref,
    )
    descriptor = await _resolve_binding_descriptor(
        client=client,
        experience_name=experience_name,
        section_key=section_key,
        observable_id=observable_id,
        view_ref=view_ref,
        binding_key=binding_key,
    )
    if descriptor is None:
        return None

    object_projection_graph_identity_id = _as_uuid(
        getattr(descriptor, "object_projection_graph_identity_id", None)
    )
    projection_experience_graph_identity_id = _as_uuid(
        getattr(descriptor, "projection_experience_graph_identity_id", None)
    )
    projection_observable_id = _as_uuid(
        getattr(descriptor, "projection_observable_id", None)
    )
    resolved_binding_key = _as_optional_text(getattr(descriptor, "binding_key", None))
    resolved_section_key = _as_optional_text(getattr(descriptor, "section_key", None))
    if (
        object_projection_graph_identity_id is None
        or projection_experience_graph_identity_id is None
        or projection_observable_id is None
        or resolved_binding_key is None
        or resolved_section_key is None
    ):
        return None

    address = section_state_addresses.get(section_key)
    focus_target = ExperienceSectionFocusTarget(
        kind="constructor",
        focus_scope_id=address.focus_scope_id if address is not None else None,
        projection_experience_graph_identity_id=(
            projection_experience_graph_identity_id
        ),
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        projection_hash=None,
        target_type="projection_experience_graph_identity",
        target_id=projection_experience_graph_identity_id,
        description=_as_optional_text(getattr(descriptor, "graph_identity_ref", None)),
    )
    activation_scope = ExperienceSectionGraphBindingActivationScope(
        window_key=window_key,
        layout_key=layout_key,
        section_key=resolved_section_key,
        layout_section_id=address.layout_section_id if address is not None else None,
        section_focus_scope_id=(
            address.section_focus_scope_id if address is not None else None
        ),
        focus_scope_id=address.focus_scope_id if address is not None else None,
        observable_id=projection_observable_id,
        focus_target=focus_target,
    )
    response = await client.activate_section_graph_binding(
        ActivateExperienceSectionGraphBindingRequest(
            experience_name=experience_name,
            binding_key=resolved_binding_key,
            activation_scope=activation_scope,
            rationale="interface_runtime_focus_activation",
        )
    )
    if not getattr(response, "success", False):
        return None
    state = getattr(response, "state", None)
    section_view = getattr(state, "section_view", None) if state is not None else None
    returned_focus_target = (
        _interface_focus_target_from_experience_target(
            getattr(state, "focus_target", None)
        )
        if state is not None
        else None
    )
    return ExperienceSectionGraphBindingActivationResolution(
        experience_name=experience_name,
        binding_key=resolved_binding_key,
        section_key=resolved_section_key,
        projection_observable_id=projection_observable_id,
        projection_experience_graph_identity_id=projection_experience_graph_identity_id,
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        projection_experience_view_instance_id=_as_uuid(
            getattr(section_view, "projection_experience_view_instance_id", None)
        ),
        view_actions=_view_action_resolutions(section_view),
        focus_target=returned_focus_target,
    )


def _experience_client(
    *,
    transport_session: InterfaceTransportSession | None,
) -> ExperienceSdkClient | None:
    if transport_session is None:
        return None
    return build_experience_sdk_client(AwareExperienceServiceApiClient(transport_session.client))


async def _resolve_binding_descriptor(
    *,
    client: ExperienceSdkClient,
    experience_name: str,
    section_key: str,
    observable_id: UUID,
    view_ref: str | None,
    binding_key: str | None,
) -> ExperienceSectionGraphBindingDescriptor | None:
    try:
        response = await client.get_section_graph_binding_catalog(
            GetExperienceSectionGraphBindingCatalogRequest(
                experience_name=experience_name,
                section_keys=[] if binding_key is not None else [section_key],
                binding_keys=[binding_key] if binding_key is not None else [],
            )
        )
    except Exception:
        return None
    if not getattr(response, "success", False):
        return None
    bindings = tuple(getattr(response, "bindings", ()) or ())
    if binding_key is not None:
        return next(
            (
                descriptor
                for descriptor in bindings
                if _text_matches(getattr(descriptor, "binding_key", None), binding_key)
            ),
            None,
        )
    candidates = [
        descriptor
        for descriptor in bindings
        if _text_matches(getattr(descriptor, "section_key", None), section_key)
        and _as_uuid(getattr(descriptor, "projection_observable_id", None))
        == observable_id
        and (
            view_ref is None
            or _text_matches(getattr(descriptor, "view_ref", None), view_ref)
        )
    ]
    if len(candidates) != 1:
        candidates = [
            descriptor
            for descriptor in bindings
            if _text_matches(getattr(descriptor, "section_key", None), section_key)
            and view_ref is not None
            and _text_matches(getattr(descriptor, "view_ref", None), view_ref)
        ]
    if len(candidates) != 1:
        return None
    return candidates[0]


def _bundle_view_ref_for_focus(
    *,
    interface_config_bundle: InterfaceConfigBundle,
    section_key: str,
    observable_id: UUID,
) -> str | None:
    section_config_ids = {
        section.layout_config_section_config_id
        for window in interface_config_bundle.window_configs
        for layout in window.layout_configs
        for section in layout.sections
        if section.key.strip().casefold() == section_key.strip().casefold()
    }
    for pane_config in interface_config_bundle.pane_configs:
        for projection_view in pane_config.projection_experience_views:
            if projection_view.object_projection_graph_observable_id != observable_id:
                continue
            for mount in projection_view.section_mounts:
                if mount.layout_config_section_config_id in section_config_ids:
                    return projection_view.view_ref
    return None


def _mapped_binding_key(
    *,
    navigation_context_layout_target: InterfaceNavigationContextLayoutTargetState | None,
    section_key: str,
    observable_id: UUID,
    view_ref: str | None,
) -> str | None:
    if navigation_context_layout_target is None:
        return None
    evidence = (
        navigation_context_layout_target.evidence
        if isinstance(navigation_context_layout_target.evidence, dict)
        else {}
    )
    for mapping in evidence.get("sections", ()) or ():
        if not isinstance(mapping, dict):
            continue
        if not _section_mapping_matches(
            mapping=mapping,
            section_key=section_key,
            observable_id=observable_id,
            view_ref=view_ref,
        ):
            continue
        return _as_optional_text(mapping.get("section_graph_binding_key"))
    return None


def _section_mapping_matches(
    *,
    mapping: dict[str, object],
    section_key: str,
    observable_id: UUID,
    view_ref: str | None,
) -> bool:
    mapped_section_key = _as_optional_text(mapping.get("section_key"))
    if mapped_section_key is not None and not _text_matches(
        mapped_section_key,
        section_key,
    ):
        return False
    mapped_view_ref = _as_optional_text(mapping.get("view_ref"))
    if view_ref is not None and mapped_view_ref is not None:
        return _text_matches(mapped_view_ref, view_ref)
    mapped_observable_id = _as_uuid(mapping.get("observable_id"))
    return mapped_observable_id is None or mapped_observable_id == observable_id


def _representation_view_ref(
    representation: InterfaceRuntimeSectionRepresentationState | None,
) -> str | None:
    if representation is None:
        return None
    return _as_optional_text(representation.view_ref)


def _representation_binding_key(
    representation: InterfaceRuntimeSectionRepresentationState | None,
) -> str | None:
    if representation is None:
        return None
    return _as_optional_text(representation.section_graph_binding_key)


def _experience_name_from_view_ref(view_ref: str | None) -> str | None:
    normalized = _as_optional_text(view_ref)
    if normalized is None:
        return None
    experience_name = normalized.split(".", 1)[0].strip()
    return experience_name or None


def _view_action_resolutions(
    section_view: object | None,
) -> tuple[ExperienceSectionViewActionResolution, ...]:
    if section_view is None:
        return ()
    resolutions: list[ExperienceSectionViewActionResolution] = []
    for action in tuple(getattr(section_view, "actions", ()) or ()):
        action_key = _as_optional_text(getattr(action, "action_key", None))
        view_invocation_action_config_id = _as_uuid(
            getattr(action, "view_invocation_action_config_id", None)
            or getattr(action, "action_id", None)
        )
        if action_key is None or view_invocation_action_config_id is None:
            continue
        resolutions.append(
            ExperienceSectionViewActionResolution(
                action_key=action_key,
                view_invocation_action_config_id=view_invocation_action_config_id,
                action_kind=_as_optional_text(getattr(action, "action_kind", None)),
                target_ref=_as_optional_text(getattr(action, "target_ref", None)),
            )
        )
    return tuple(resolutions)


def _interface_focus_target_from_experience_target(
    focus_target: object | None,
) -> InterfaceAttentionFocusTargetState | None:
    object_projection_graph_identity_id = _as_uuid(
        getattr(focus_target, "object_projection_graph_identity_id", None)
    )
    if object_projection_graph_identity_id is None:
        return None
    return InterfaceAttentionFocusTargetState(
        kind=_as_optional_text(getattr(focus_target, "kind", None)) or "constructor",
        focus_id=_as_uuid(getattr(focus_target, "focus_id", None)),
        focus_scope_id=_as_uuid(getattr(focus_target, "focus_scope_id", None)),
        projection_experience_graph_identity_id=_as_uuid(
            getattr(focus_target, "projection_experience_graph_identity_id", None)
        ),
        object_projection_graph_identity_id=object_projection_graph_identity_id,
        object_instance_graph_branch_id=_as_uuid(
            getattr(focus_target, "object_instance_graph_branch_id", None)
        ),
        projection_hash=_as_optional_text(
            getattr(focus_target, "projection_hash", None)
        ),
        target_type=_as_optional_text(getattr(focus_target, "target_type", None)),
        target_id=_as_uuid(getattr(focus_target, "target_id", None)),
        description=_as_optional_text(getattr(focus_target, "description", None)),
    )


def _text_matches(left: object, right: object) -> bool:
    left_text = _as_optional_text(left)
    right_text = _as_optional_text(right)
    return left_text is not None and right_text is not None and (
        left_text.casefold() == right_text.casefold()
    )


def _as_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return None


def _as_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ExperienceSectionGraphBindingActivationResolution",
    "ExperienceSectionViewActionResolution",
    "activate_experience_section_graph_binding_for_runtime_focus",
]
