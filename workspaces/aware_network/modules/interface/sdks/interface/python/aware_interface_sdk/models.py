from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceHostState,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceResolvedPaneDescriptor,
)


@dataclass(frozen=True, slots=True)
class InterfaceSurfacePane:
    descriptor: InterfaceResolvedPaneDescriptor

    @property
    def pane_ref(self) -> str:
        return "/".join(
            _required_text(getattr(self.descriptor, attr, None), attr)
            for attr in ("window_key", "layout_key", "section_key")
        )

    @property
    def aliases(self) -> tuple[str, ...]:
        aliases = (
            _optional_str(self.descriptor.section_key),
            _optional_str(self.descriptor.pane_kind),
            _optional_str(self.descriptor.pane_config_id),
            _optional_str(self.descriptor.pane_package_name),
        )
        unique_aliases: list[str] = []
        for alias in aliases:
            if alias is not None and alias not in unique_aliases:
                unique_aliases.append(alias)
        return tuple(unique_aliases)

    @property
    def api_capability_endpoint_ids(self) -> tuple[str, ...]:
        return tuple(
            str(item)
            for item in _value_sequence(
                _field(self.descriptor, "api_capability_endpoint_ids")
            )
        )

    @property
    def surface_affordance_keys(self) -> tuple[str, ...]:
        return tuple(self.descriptor.action_keys)

    def resolve_action_ref(self, action_ref: str) -> str:
        action_keys = self.surface_affordance_keys
        if action_ref in action_keys:
            return action_ref
        if action_ref.isdigit():
            index = int(action_ref) - 1
            if 0 <= index < len(action_keys):
                return action_keys[index]
        raise ValueError(
            f"Action {action_ref!r} is not exposed by pane {self.pane_ref!r}."
        )

    def resolve_capability_ref(self, capability_ref: str) -> str:
        endpoint_ids = self.api_capability_endpoint_ids
        if capability_ref in endpoint_ids:
            return capability_ref
        if capability_ref.isdigit():
            index = int(capability_ref) - 1
            if 0 <= index < len(endpoint_ids):
                return endpoint_ids[index]
        raise ValueError(
            f"Capability {capability_ref!r} is not exposed by pane {self.pane_ref!r}."
        )

    def to_payload(self) -> dict[str, Any]:
        pane = self.descriptor
        return {
            "pane_ref": self.pane_ref,
            "aliases": list(self.aliases),
            "window_key": pane.window_key,
            "layout_key": pane.layout_key,
            "section_key": pane.section_key,
            "layout_config_section_config_id": _optional_str(
                pane.layout_config_section_config_id
            ),
            "layout_section_id": _optional_str(pane.layout_section_id),
            "section_focus_scope_id": _optional_str(pane.section_focus_scope_id),
            "focus_scope_id": _optional_str(pane.focus_scope_id),
            "branch_id": _optional_str(pane.branch_id),
            "pane_kind": pane.pane_kind,
            "pane_config_id": _optional_str(pane.pane_config_id),
            "pane_package_id": _optional_str(pane.pane_package_id),
            "pane_package_name": pane.pane_package_name,
            "object_projection_graph_observable_id": _optional_str(
                pane.object_projection_graph_observable_id
            ),
            "title": pane.title,
            "summary": pane.summary,
            "narrative_key": pane.narrative_key,
            "projection_view_id": pane.projection_view_id,
            "state_source_kind": pane.state_source_kind,
            "state_projection_hash": pane.state_projection_hash,
            "api_capability_endpoint_ids": list(self.api_capability_endpoint_ids),
            "surface_affordance_keys": list(self.surface_affordance_keys),
        }


@dataclass(frozen=True, slots=True)
class InterfaceSurfaceSnapshot:
    namespace: str
    host_state: InterfaceHostState

    @property
    def panes(self) -> tuple[InterfaceSurfacePane, ...]:
        current_gate = self._current_gate_pane_descriptor()
        if current_gate is not None:
            return (InterfaceSurfacePane(descriptor=current_gate),)
        runtime = self.host_state.runtime
        if runtime is None:
            return ()
        return tuple(
            InterfaceSurfacePane(descriptor=pane)
            for pane in (runtime.resolved_panes or ())
        )

    def _current_gate_pane_descriptor(self) -> InterfaceResolvedPaneDescriptor | None:
        current_screen = self.host_state.current_screen
        if current_screen is None:
            return None
        if getattr(current_screen, "source_kind", None) != "gate":
            return None
        pane_key = _optional_str(getattr(current_screen, "pane_key", None))
        if pane_key is None:
            return None
        runtime = self.host_state.runtime
        for pane in getattr(runtime, "resolved_panes", ()) or ():
            if pane.section_key == pane_key or pane.pane_kind == pane_key:
                return pane
        action_keys = [
            action.action_key
            for action in self.host_state.allowed_actions or ()
            if _optional_str(action.action_key) is not None
        ]
        return InterfaceResolvedPaneDescriptor(
            window_key="bootstrap",
            layout_key="bootstrap.panes",
            section_key=pane_key,
            pane_kind=pane_key,
            title=getattr(current_screen, "title", None),
            summary=getattr(current_screen, "message", None),
            narrative_key=f"bootstrap.panes.{pane_key}",
            projection_view_id=getattr(current_screen, "projection_view_id", None),
            state_source_kind="host_pane_contribution",
            state_projection_hash=f"section:bootstrap.panes:{pane_key}",
            action_keys=action_keys,
        )

    @property
    def experience_session_narration(
        self,
    ) -> "InterfaceExperienceSessionNarrationSnapshot":
        return InterfaceExperienceSessionNarrationSnapshot.from_host_state(
            self.host_state,
            namespace=self.namespace,
        )

    @property
    def pane_api_capability_endpoint_count(self) -> int:
        return sum(len(pane.api_capability_endpoint_ids) for pane in self.panes)

    def resolve_pane(self, pane_ref: str) -> InterfaceSurfacePane:
        candidates: list[InterfaceSurfacePane] = [
            pane
            for pane in self.panes
            if pane_ref == pane.pane_ref or pane_ref in pane.aliases
        ]
        if not candidates:
            raise ValueError(
                f"Pane {pane_ref!r} is not mounted in the current Interface surface."
            )
        if len(candidates) > 1:
            refs = ", ".join(pane.pane_ref for pane in candidates)
            raise ValueError(f"Pane ref {pane_ref!r} is ambiguous; use one of: {refs}.")
        return candidates[0]

    def status_payload(self) -> dict[str, Any]:
        host_state = self.host_state
        transport = host_state.transport
        runtime = host_state.runtime
        return {
            "namespace": self.namespace,
            "host_label": host_state.host_label,
            "endpoint": getattr(host_state, "endpoint", None),
            "started": host_state.started,
            "connected": bool(transport.available),
            "interface": {
                "registered": transport.registered,
                "admitted": bool(
                    transport.registered
                    and transport.interface_id is not None
                    and transport.interface_session_id is not None
                ),
                "interface_id": _optional_str(transport.interface_id),
                "interface_session_id": _optional_str(transport.interface_session_id),
                "session_label": transport.session_label,
                "capabilities": list(transport.capabilities or ()),
            },
            "actor": {
                "registered": transport.registered,
                "authenticated": transport.authenticated,
                "actor_id": _optional_str(transport.actor_id),
                "interface_id": _optional_str(transport.interface_id),
                "interface_session_id": _optional_str(transport.interface_session_id),
            },
            "environment_admission": _jsonable(host_state.environment_admission),
            "environment_admission_receipt": _jsonable(
                host_state.environment_admission_receipt
            ),
            "environment_navigation": _jsonable(host_state.environment_navigation),
            "experience_session_narration": _jsonable(
                self.experience_session_narration,
            ),
            "current_screen": _screen_payload(host_state.current_screen),
            "pane_count": len(self.panes),
            "pane_api_capability_endpoint_count": self.pane_api_capability_endpoint_count,
            "surface_affordance_count": len(host_state.allowed_actions or ()),
            "runtime_available": runtime is not None,
            "warnings": list(host_state.warnings or ()),
        }

    def render_payload(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "host_label": self.host_state.host_label,
            "current_screen": _screen_payload(self.host_state.current_screen),
            "runtime": _runtime_payload(self.host_state.runtime),
            "panes": self.panes_payload()["panes"],
            "warnings": list(self.host_state.warnings or ()),
        }

    def panes_payload(self) -> dict[str, Any]:
        panes = [pane.to_payload() for pane in self.panes]
        return {
            "namespace": self.namespace,
            "pane_count": len(panes),
            "pane_api_capability_endpoint_count": sum(
                len(pane["api_capability_endpoint_ids"]) for pane in panes
            ),
            "panes": panes,
        }

    def capabilities_payload(self) -> dict[str, Any]:
        transport = self.host_state.transport
        return {
            "namespace": self.namespace,
            "transport": {
                "available": transport.available,
                "registered": transport.registered,
                "authenticated": transport.authenticated,
                "capabilities": list(transport.capabilities or ()),
            },
            "local_service_host": _jsonable(self.host_state.local_service_host),
            "local_node_runtime": _jsonable(self.host_state.local_node_runtime),
            "pane_api_capability_endpoint_count": self.pane_api_capability_endpoint_count,
            "panes": self.panes_payload()["panes"],
            "surface_affordances": _jsonable(self.host_state.allowed_actions or ()),
        }

    def surface_affordances_payload(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "status": "transitional_surface_affordances",
            "note": (
                "Product renderers should prefer pane-scoped `aware panes` and "
                "`aware invoke <pane-ref> <capability-ref>`."
            ),
            "affordances": _jsonable(self.host_state.allowed_actions or ()),
        }


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionNarrationEvent:
    commit_id: UUID | None = None
    branch_id: UUID | None = None
    projection_hash: str | None = None
    narration_lines: tuple[str, ...] = ()
    operation_label: str | None = None
    graph_hash_post: str | None = None
    object_instance_graph_identity_id: UUID | None = None
    object_instance_graph_branch_id: UUID | None = None
    object_instance_graph_commit_id: UUID | None = None
    projection_experience_graph_identity_id: UUID | None = None
    object_projection_graph_identity_id: UUID | None = None
    semantics: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None

    @property
    def text(self) -> str:
        lines = tuple(line for line in self.narration_lines if line.strip())
        if lines:
            return "\n".join(lines)
        if self.operation_label:
            return self.operation_label
        if self.commit_id is not None:
            return f"Experience OIG commit {self.commit_id}"
        return "Experience session change"

    @classmethod
    def from_value(
        cls,
        value: object,
    ) -> "InterfaceExperienceSessionNarrationEvent":
        return cls(
            commit_id=_uuid_value(_field(value, "commit_id")),
            branch_id=_uuid_value(_field(value, "branch_id")),
            projection_hash=_optional_str(_field(value, "projection_hash")),
            narration_lines=_text_sequence(_field(value, "narration_lines")),
            operation_label=_optional_str(_field(value, "operation_label")),
            graph_hash_post=_optional_str(_field(value, "graph_hash_post")),
            object_instance_graph_identity_id=_uuid_value(
                _field(value, "object_instance_graph_identity_id")
            ),
            object_instance_graph_branch_id=_uuid_value(
                _field(value, "object_instance_graph_branch_id")
            ),
            object_instance_graph_commit_id=_uuid_value(
                _field(value, "object_instance_graph_commit_id")
            ),
            projection_experience_graph_identity_id=_uuid_value(
                _field(value, "projection_experience_graph_identity_id")
            ),
            object_projection_graph_identity_id=_uuid_value(
                _field(value, "object_projection_graph_identity_id")
            ),
            semantics=_object_mapping(_field(value, "semantics")),
            evidence=_object_mapping(_field(value, "evidence")),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "commit_id": _optional_str(self.commit_id),
            "branch_id": _optional_str(self.branch_id),
            "projection_hash": self.projection_hash,
            "narration_lines": list(self.narration_lines),
            "operation_label": self.operation_label,
            "graph_hash_post": self.graph_hash_post,
            "object_instance_graph_identity_id": _optional_str(
                self.object_instance_graph_identity_id
            ),
            "object_instance_graph_branch_id": _optional_str(
                self.object_instance_graph_branch_id
            ),
            "object_instance_graph_commit_id": _optional_str(
                self.object_instance_graph_commit_id
            ),
            "projection_experience_graph_identity_id": _optional_str(
                self.projection_experience_graph_identity_id
            ),
            "object_projection_graph_identity_id": _optional_str(
                self.object_projection_graph_identity_id
            ),
            "semantics": self.semantics or {},
            "evidence": self.evidence or {},
        }


@dataclass(frozen=True, slots=True)
class InterfaceExperienceSessionNarrationSnapshot:
    namespace: str
    status: str = "inactive"
    feature_key: str | None = None
    experience_name: str | None = None
    view_ref: str | None = None
    actor_id: UUID | None = None
    feature_lease_id: str | None = None
    event_count: int = 0
    last_commit_id: UUID | None = None
    events: tuple[InterfaceExperienceSessionNarrationEvent, ...] = ()
    error: str | None = None
    evidence: dict[str, Any] | None = None

    @property
    def active(self) -> bool:
        return self.status in {"active", "enabled", "ready"} and self.error is None

    @classmethod
    def from_surface(
        cls,
        surface: InterfaceSurfaceSnapshot,
    ) -> "InterfaceExperienceSessionNarrationSnapshot":
        return cls.from_host_state(surface.host_state, namespace=surface.namespace)

    @classmethod
    def from_host_state(
        cls,
        host_state: object,
        *,
        namespace: str,
    ) -> "InterfaceExperienceSessionNarrationSnapshot":
        value = _field(host_state, "experience_session_narration")
        if value is None:
            return cls(namespace=namespace)
        events = tuple(
            InterfaceExperienceSessionNarrationEvent.from_value(item)
            for item in _value_sequence(_field(value, "events"))
        )
        event_count = _int_value(_field(value, "event_count"))
        return cls(
            namespace=namespace,
            status=_optional_str(_field(value, "status")) or "inactive",
            feature_key=_optional_str(_field(value, "feature_key")),
            experience_name=_optional_str(_field(value, "experience_name")),
            view_ref=_optional_str(_field(value, "view_ref")),
            actor_id=_uuid_value(_field(value, "actor_id")),
            feature_lease_id=_optional_str(_field(value, "feature_lease_id")),
            event_count=event_count if event_count is not None else len(events),
            last_commit_id=_uuid_value(_field(value, "last_commit_id")),
            events=events,
            error=_optional_str(_field(value, "error")),
            evidence=_object_mapping(_field(value, "evidence")),
        )

    def events_after_commit(
        self,
        commit_id: UUID | str | None,
        *,
        limit: int | None = None,
    ) -> tuple[InterfaceExperienceSessionNarrationEvent, ...]:
        events = self.events
        resolved_commit_id = _uuid_value(commit_id)
        if resolved_commit_id is not None:
            for index, event in enumerate(events):
                if event.commit_id == resolved_commit_id:
                    events = events[index + 1 :]
                    break
        if limit is not None and limit >= 0:
            events = events[-limit:] if limit else ()
        return events

    def to_payload(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "status": self.status,
            "feature_key": self.feature_key,
            "experience_name": self.experience_name,
            "view_ref": self.view_ref,
            "actor_id": _optional_str(self.actor_id),
            "feature_lease_id": self.feature_lease_id,
            "event_count": self.event_count,
            "last_commit_id": _optional_str(self.last_commit_id),
            "events": [event.to_payload() for event in self.events],
            "error": self.error,
            "evidence": self.evidence or {},
        }


def _screen_payload(current_screen: Any) -> dict[str, Any] | None:
    if current_screen is None:
        return None
    return {
        "screen_kind": getattr(current_screen, "screen_kind", None),
        "screen_key": getattr(current_screen, "screen_key", None),
        "source_kind": getattr(current_screen, "source_kind", None),
        "title": getattr(current_screen, "title", None),
        "message": getattr(current_screen, "message", None),
        "pane_key": getattr(current_screen, "pane_key", None),
        "projection_view_id": getattr(current_screen, "projection_view_id", None),
    }


def _runtime_payload(runtime: Any) -> dict[str, Any] | None:
    if runtime is None:
        return None
    return {
        "active_layout_config_id": _optional_str(
            getattr(runtime, "active_layout_config_id", None)
        ),
        "active_focus": _jsonable(getattr(runtime, "active_focus", None)),
        "resolved_view": _jsonable(getattr(runtime, "resolved_view", None)),
        "layout_states": _jsonable(getattr(runtime, "layout_states", ()) or ()),
        "section_representations": _jsonable(
            getattr(runtime, "section_representations", ()) or ()
        ),
        "warnings": list(getattr(runtime, "warnings", ()) or ()),
    }


def _jsonable(value: Any) -> Any:
    to_payload = getattr(value, "to_payload", None)
    if callable(to_payload):
        return to_payload()
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Missing required Interface surface value: {label}.")
    return text


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _field(value: object, name: str, default: object | None = None) -> object | None:
    if value is None:
        return default
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _uuid_value(value: object | None) -> UUID | None:
    if isinstance(value, UUID):
        return value
    text = _optional_str(value)
    if text is None:
        return None
    try:
        return UUID(text)
    except ValueError:
        return None


def _int_value(value: object | None) -> int | None:
    if isinstance(value, int):
        return value
    text = _optional_str(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _text_sequence(value: object | None) -> tuple[str, ...]:
    return tuple(
        text
        for text in (_optional_str(item) for item in _value_sequence(value))
        if text is not None
    )


def _value_sequence(value: object | None) -> tuple[object, ...]:
    if value is None or isinstance(value, str | bytes | Mapping):
        return ()
    if isinstance(value, Sequence):
        return tuple(value)
    return ()


def _object_mapping(value: object | None) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    payload = _jsonable(value)
    if isinstance(payload, Mapping):
        return {str(key): _jsonable(item) for key, item in payload.items()}
    return {"value": payload}


__all__ = [
    "InterfaceExperienceSessionNarrationEvent",
    "InterfaceExperienceSessionNarrationSnapshot",
    "InterfaceSurfacePane",
    "InterfaceSurfaceSnapshot",
]
