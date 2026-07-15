from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID

from aware_environment_service_api._bindings import (
    API_INVOCATION_MANIFEST as ENVIRONMENT_API_INVOCATION_MANIFEST,
)
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_service_dto.experience.thread_layout_resolution.service_operation import (
    ResolveExperienceThreadLayoutIntentRequest,
)
from aware_interface import (
    InterfaceRuntimeState,
    InterfaceNavigationContextLayoutTargetState,
)
from aware_interface_sdk.transport import InterfaceTransportSession
from aware_utils.logging import logger

_DEFAULT_CONTROL_INTENT_KEY = "identity.admission"
_EXPERIENCE_ENDPOINT_REF = (
    "experience.resolve_experience_thread_layout_intent."
    "resolve_experience_thread_layout_intent"
)
_ENVIRONMENT_ENDPOINT_REF = "environment.experience.provision_environment_experience"
_ENVIRONMENT_UPSERT_ENDPOINT_REF = (
    "environment.experience.upsert_environment_experience"
)
_MISSING = object()


@dataclass(frozen=True, slots=True)
class ServiceApiInterfaceNavigationContextLayoutPort:
    """Resolve Interface window navigation-context layout evidence via service APIs."""

    transport_session: InterfaceTransportSession | None
    context_environment_id: UUID | None = None
    context_process_id: UUID | None = None
    context_thread_id: UUID | None = None
    context_branch_id: UUID | None = None
    context_projection_hash: str | None = None
    intent_key: str = _DEFAULT_CONTROL_INTENT_KEY
    topology_seed_key: str | None = _DEFAULT_CONTROL_INTENT_KEY
    experience_name: str | None = None
    profile_key: str | None = None
    environment_handle: str | None = None
    environment_selector: str | None = "current"

    async def resolve_navigation_context_layout_target(
        self,
        *,
        state: InterfaceRuntimeState,
    ) -> InterfaceNavigationContextLayoutTargetState | None:
        if self.transport_session is None:
            return None
        environment_id = self.context_environment_id or state.backend.environment_id
        if environment_id is None:
            return None

        try:
            experience_response = await self._resolve_experience_target(
                state=state,
                environment_id=environment_id,
            )
            if not getattr(experience_response, "success", False):
                return None
            resolution = getattr(experience_response, "resolution", None)
            target = getattr(resolution, "target", None)
            if resolution is None or target is None:
                return None

            resolved_environment_id = _resolved_environment_id(
                resolution=resolution,
                fallback_environment_id=environment_id,
            )
            if resolved_environment_id is None:
                return None
            topology_seed_key, topology_seed_source = _resolve_topology_seed_key(
                configured_topology_seed_key=self.topology_seed_key,
                resolution=resolution,
            )
            if topology_seed_key is None:
                return None

            upsert_response = await self._upsert_environment_experience(
                environment_id=resolved_environment_id,
                resolution=resolution,
            )
            if upsert_response is not None and not _environment_response_succeeded(
                upsert_response
            ):
                return None
            environment_experience_profile_id = _as_uuid(
                getattr(upsert_response, "environment_experience_profile_id", None)
                if upsert_response is not None
                else None
            )

            environment_response = await self._provision_environment_experience(
                environment_id=resolved_environment_id,
                topology_seed_key=topology_seed_key,
                environment_experience_profile_id=environment_experience_profile_id,
            )
            if not _environment_response_succeeded(environment_response):
                return None

            runtime_mounts = _runtime_mount_receipts(environment_response)
            if runtime_mounts is None:
                return None
            selected_receipt = _select_runtime_mount_receipt(
                receipts=runtime_mounts,
                environment_id=resolved_environment_id,
                topology_seed_key=topology_seed_key,
                target=target,
            )
            if selected_receipt is None:
                return None
            receipt_source = "environment_runtime_mount"
            process_id = _as_uuid(getattr(selected_receipt, "process_id", None))
            thread_id = _as_uuid(getattr(selected_receipt, "thread_id", None))
            thread_layout_id = _as_uuid(
                getattr(selected_receipt, "thread_layout_id", None)
            )
            layout_id = _as_uuid(getattr(selected_receipt, "layout_id", None))
            layout_config_id = _as_uuid(
                getattr(selected_receipt, "layout_config_id", None)
            ) or _as_uuid(getattr(target, "layout_config_id", None))
            layout_key = _as_optional_text(
                getattr(selected_receipt, "layout_key", None)
            ) or _as_optional_text(getattr(target, "layout_key", None))
            selected_receipt_count = len(runtime_mounts)

            if thread_id is None or thread_layout_id is None:
                return None

            receipt_process_key = _as_optional_text(
                getattr(selected_receipt, "process_key", None)
            ) or _as_optional_text(getattr(target, "process_key", None))
            receipt_thread_key = _as_optional_text(
                getattr(selected_receipt, "thread_key", None)
            ) or _as_optional_text(getattr(target, "thread_key", None))
            receipt_layout_key = layout_key
            window_key = (
                _as_optional_text(getattr(target, "window_key", None)) or "main"
            )

            return InterfaceNavigationContextLayoutTargetState(
                source_kind="service_api_environment_navigation_context_layout",
                environment_id=resolved_environment_id,
                process_id=process_id,
                thread_id=thread_id,
                thread_layout_id=thread_layout_id,
                layout_id=layout_id,
                layout_config_id=layout_config_id,
                layout_key=layout_key,
                window_key=window_key,
                evidence={
                    "source": "service_api",
                    "receipt_source": receipt_source,
                    "experience_endpoint_ref": _EXPERIENCE_ENDPOINT_REF,
                    "environment_endpoint_ref": _ENVIRONMENT_ENDPOINT_REF,
                    "environment_upsert_endpoint_ref": (
                        _ENVIRONMENT_UPSERT_ENDPOINT_REF
                    ),
                    "intent_key": _as_optional_text(
                        getattr(resolution, "intent_key", None)
                    )
                    or self.intent_key,
                    "experience_name": _as_optional_text(
                        getattr(resolution, "experience_name", None)
                    ),
                    "profile_key": _as_optional_text(
                        getattr(resolution, "profile_key", None)
                    ),
                    "process_key": receipt_process_key,
                    "thread_key": receipt_thread_key,
                    "layout_key": receipt_layout_key,
                    "window_key": window_key,
                    "topology_seed_key": topology_seed_key,
                    "topology_seed_source": topology_seed_source,
                    "environment_status": _as_optional_text(
                        getattr(environment_response, "status", None)
                    ),
                    "environment_experience_profile_id": _as_optional_text(
                        getattr(
                            environment_response,
                            "environment_experience_profile_id",
                            None,
                        )
                        or environment_experience_profile_id
                    ),
                    "environment_experience_profile_mount_id": _as_optional_text(
                        getattr(
                            selected_receipt,
                            "environment_experience_profile_mount_id",
                            None,
                        )
                    ),
                    "mount_key": _as_optional_text(
                        getattr(selected_receipt, "mount_key", None)
                    ),
                    "process_config_id": _as_optional_text(
                        getattr(selected_receipt, "process_config_id", None)
                    )
                    or _as_optional_text(getattr(target, "process_config_id", None)),
                    "thread_config_id": _as_optional_text(
                        getattr(selected_receipt, "thread_config_id", None)
                    )
                    or _as_optional_text(getattr(target, "thread_config_id", None)),
                    "thread_layout_config_id": _as_optional_text(
                        getattr(selected_receipt, "thread_layout_config_id", None)
                    ),
                    "sections": _resolution_section_mappings(resolution=resolution),
                    "layout_id": _as_optional_text(
                        getattr(selected_receipt, "layout_id", None)
                    ),
                    "thread_layout_id": _as_optional_text(
                        getattr(selected_receipt, "thread_layout_id", None)
                    ),
                    "runtime_mount_status": _as_optional_text(
                        getattr(selected_receipt, "status", None)
                    ),
                    "runtime_mount_receipt_count": selected_receipt_count,
                    "runtime_mount_activate_on_seed": _as_bool(
                        getattr(selected_receipt, "activate_on_seed", False)
                    ),
                    "process_receipt_count": len(
                        tuple(getattr(environment_response, "process_ids", ()))
                    ),
                    "thread_receipt_count": len(
                        tuple(getattr(environment_response, "thread_ids", ()))
                    ),
                    "thread_layout_receipt_count": len(
                        tuple(getattr(environment_response, "thread_layout_ids", ()))
                    ),
                    "experience_evidence": dict(
                        getattr(resolution, "evidence", {}) or {}
                    ),
                },
            )
        except Exception as exc:
            logger.warning(
                "aware_interface_service navigation-context layout service API "
                "resolution failed: %s",
                exc,
            )
            return None

    async def _resolve_experience_target(
        self,
        *,
        state: InterfaceRuntimeState,
        environment_id: UUID,
    ) -> object:
        assert self.transport_session is not None
        client = AwareExperienceServiceApiClient(self.transport_session.client)
        binding = getattr(self.transport_session, "binding", None)
        request_context: dict[str, object] = {
            "backend_available": state.backend.available,
        }
        for key, value in (
            ("interface_id", getattr(binding, "interface_id", None)),
            (
                "interface_session_id",
                getattr(binding, "interface_session_id", None),
            ),
            ("session_label", getattr(binding, "session_label", None)),
            ("backend_reason", state.backend.reason),
        ):
            normalized = _as_optional_text(value)
            if normalized is not None:
                request_context[key] = normalized
        resolver = client.experience.resolve_experience_thread_layout_intent
        request = ResolveExperienceThreadLayoutIntentRequest(
            intent_key=self.intent_key,
            experience_name=self.experience_name,
            profile_key=self.profile_key,
            environment_id=environment_id,
            environment_handle=self.environment_handle,
            environment_selector=self.environment_selector,
            request_context=request_context,
        )
        return await resolver.resolve_experience_thread_layout_intent(request)

    async def _provision_environment_experience(
        self,
        *,
        environment_id: UUID,
        topology_seed_key: str,
        environment_experience_profile_id: UUID | None = None,
    ) -> object:
        assert self.transport_session is not None
        binding = getattr(self.transport_session, "binding", None)
        actor_id = _as_uuid(getattr(binding, "actor_id", None))
        return await self.transport_session.client.invoke_api_endpoint(
            manifest=ENVIRONMENT_API_INVOCATION_MANIFEST,
            endpoint_ref=_ENVIRONMENT_ENDPOINT_REF,
            request_payload=SimpleNamespace(
                actor_id=actor_id,
                environment_id=environment_id,
                process_id=self.context_process_id,
                thread_id=self.context_thread_id,
                branch_id=self.context_branch_id,
                projection_hash=self.context_projection_hash,
                environment_experience_profile_id=environment_experience_profile_id,
                topology_seed_key=topology_seed_key,
            ),
        )

    async def _upsert_environment_experience(
        self,
        *,
        environment_id: UUID,
        resolution: object,
    ) -> object | None:
        activation = getattr(resolution, "environment_activation", None)
        if activation is None:
            return None
        profile = getattr(activation, "profile", None)
        if profile is None:
            return None
        topology_seeds = getattr(activation, "topology_seeds", None) or []
        assert self.transport_session is not None
        binding = getattr(self.transport_session, "binding", None)
        actor_id = _as_uuid(getattr(binding, "actor_id", None))
        return await self.transport_session.client.invoke_api_endpoint(
            manifest=ENVIRONMENT_API_INVOCATION_MANIFEST,
            endpoint_ref=_ENVIRONMENT_UPSERT_ENDPOINT_REF,
            request_payload=SimpleNamespace(
                actor_id=actor_id,
                environment_id=environment_id,
                process_id=self.context_process_id,
                thread_id=self.context_thread_id,
                branch_id=self.context_branch_id,
                projection_hash=self.context_projection_hash,
                profile=_model_payload(profile),
                topology_seeds=[
                    _model_payload(topology_seed) for topology_seed in topology_seeds
                ],
            ),
        )


def _resolved_environment_id(
    *,
    resolution: object,
    fallback_environment_id: UUID,
) -> UUID | None:
    environment_target = getattr(resolution, "environment", None)
    environment_id = _as_uuid(getattr(environment_target, "environment_id", None))
    return environment_id or fallback_environment_id


def _resolve_topology_seed_key(
    *,
    configured_topology_seed_key: str | None,
    resolution: object,
) -> tuple[str | None, str | None]:
    configured = _as_optional_text(configured_topology_seed_key)
    if configured is not None:
        return configured, "interface_service_config"
    activation = getattr(resolution, "environment_activation", None)
    activation_seed = _as_optional_text(getattr(activation, "topology_seed_key", None))
    if activation_seed is not None:
        return activation_seed, "experience_environment_activation"
    evidence = getattr(resolution, "evidence", {}) or {}
    if isinstance(evidence, dict):
        evidence_seed = _as_optional_text(evidence.get("topology_seed_key"))
        if evidence_seed is not None:
            return evidence_seed, "experience_evidence"
    intent_key = _as_optional_text(getattr(resolution, "intent_key", None))
    if intent_key is not None:
        return intent_key, "experience_intent_key"
    return None, None


def _environment_response_succeeded(response: object) -> bool:
    status = (_as_optional_text(getattr(response, "status", None)) or "").casefold()
    if status != "succeeded":
        return False
    return _as_optional_text(getattr(response, "error", None)) is None


def _runtime_mount_receipts(response: object) -> tuple[object, ...] | None:
    raw_receipts = getattr(response, "runtime_mounts", _MISSING)
    if raw_receipts is _MISSING:
        return None
    if not isinstance(raw_receipts, (list, tuple)):
        return ()
    return tuple(raw_receipts)


def _resolution_section_mappings(*, resolution: object) -> list[dict[str, object]]:
    sections = getattr(resolution, "sections", ()) or ()
    mappings: list[dict[str, object]] = []
    for section in sections:
        mapping = {
            "section_key": _as_optional_text(getattr(section, "section_key", None)),
            "layout_section_config_id": _as_optional_text(
                getattr(section, "layout_section_config_id", None)
            ),
            "projection_experience_name": _as_optional_text(
                getattr(section, "projection_experience_name", None)
            ),
            "view_key": _as_optional_text(getattr(section, "view_key", None)),
            "view_ref": _as_optional_text(getattr(section, "view_ref", None)),
            "section_graph_binding_key": _as_optional_text(
                getattr(section, "section_graph_binding_key", None)
            ),
            "observable_id": _as_optional_text(getattr(section, "observable_id", None)),
            "representation_id": _as_optional_text(
                getattr(section, "representation_id", None)
            ),
            "is_default": _as_bool(getattr(section, "is_default", False)),
            "intent": _as_optional_text(getattr(section, "intent", None)),
        }
        mappings.append(
            {key: value for key, value in mapping.items() if value is not None}
        )
    return mappings


def _select_runtime_mount_receipt(
    *,
    receipts: tuple[object, ...],
    environment_id: UUID,
    topology_seed_key: str,
    target: object,
) -> object | None:
    candidates: list[object] = []
    for receipt in receipts:
        if _as_uuid(getattr(receipt, "environment_id", None)) != environment_id:
            continue
        if not _text_matches(
            getattr(receipt, "topology_seed_key", None),
            topology_seed_key,
        ):
            continue
        if _as_uuid(getattr(receipt, "thread_id", None)) is None:
            continue
        if _as_uuid(getattr(receipt, "thread_layout_id", None)) is None:
            continue
        status = _as_optional_text(getattr(receipt, "status", None))
        if status is not None and status.casefold() != "succeeded":
            continue
        if not _target_text_matches(receipt, target, field_name="process_key"):
            continue
        if not _target_text_matches(receipt, target, field_name="thread_key"):
            continue
        if not _target_text_matches(receipt, target, field_name="layout_key"):
            continue
        target_layout_config_id = _as_uuid(getattr(target, "layout_config_id", None))
        receipt_layout_config_id = _as_uuid(getattr(receipt, "layout_config_id", None))
        if (
            target_layout_config_id is not None
            and receipt_layout_config_id is not None
            and target_layout_config_id != receipt_layout_config_id
        ):
            continue
        candidates.append(receipt)

    active_candidates = [
        receipt
        for receipt in candidates
        if _as_bool(getattr(receipt, "activate_on_seed", False))
    ]
    if len(active_candidates) == 1:
        return active_candidates[0]
    if len(candidates) == 1:
        return candidates[0]
    return None


def _single_uuid(values: object) -> UUID | None:
    if not isinstance(values, (list, tuple)):
        return None
    if len(values) != 1:
        return None
    return _as_uuid(values[0])


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
    normalized = str(value).strip()
    return normalized or None


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return bool(value)
    normalized = _as_optional_text(value)
    if normalized is None:
        return False
    return normalized.casefold() in {"true", "1", "yes", "on"}


def _model_payload(value: object) -> object:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dump(mode="json", exclude_none=True)
    return value


def _text_matches(candidate: object, expected: object) -> bool:
    candidate_text = _as_optional_text(candidate)
    expected_text = _as_optional_text(expected)
    if expected_text is None:
        return True
    return candidate_text == expected_text


def _target_text_matches(
    receipt: object,
    target: object,
    *,
    field_name: str,
) -> bool:
    target_value = _as_optional_text(getattr(target, field_name, None))
    if target_value is None:
        return True
    return _text_matches(getattr(receipt, field_name, None), target_value)


__all__ = [
    "ServiceApiInterfaceNavigationContextLayoutPort",
]
