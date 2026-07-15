"""Actor-facing committed App session ergonomics over Interface SDK."""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_interface_sdk import InterfaceSdkClient, InterfaceSurfaceSnapshot


APP_LAUNCH_SCHEMA = "aware.app.launch.v0"
APP_RUN_SCHEMA = "aware.app.run.v0"
APP_UPDATE_SCHEMA = "aware.app.update.v0"
CANONICAL_RAIL = "aware-sdk -> interface-sdk -> Interface -> Experience -> API/Services"


class AwareAppSessionError(RuntimeError):
    """Raised when committed App entry or session evidence fails closed."""


class AwareAppLaunchDescriptorError(AwareAppSessionError):
    """Raised when an ``aware.app.launch.v0`` payload is invalid."""


@dataclass(frozen=True, slots=True)
class AwareAppPackageReference:
    package_name: str
    app_package_id: UUID
    branch_id: UUID
    object_instance_graph_commit_id: UUID

    def to_payload(self) -> dict[str, str]:
        return {
            "package_name": self.package_name,
            "app_package_id": str(self.app_package_id),
            "branch_id": str(self.branch_id),
            "object_instance_graph_commit_id": str(
                self.object_instance_graph_commit_id
            ),
        }


@dataclass(frozen=True, slots=True)
class AwareAppScreenReference:
    screen_key: str
    app_config_screen_config_id: UUID
    projection_experience_id: UUID
    projection_experience_layout_graph_binding_id: UUID

    def to_payload(self) -> dict[str, str]:
        return {
            "screen_key": self.screen_key,
            "app_config_screen_config_id": str(self.app_config_screen_config_id),
            "projection_experience_id": str(self.projection_experience_id),
            "projection_experience_layout_graph_binding_id": str(
                self.projection_experience_layout_graph_binding_id
            ),
        }


@dataclass(frozen=True, slots=True)
class AwareAppLaunchDescriptor:
    app_id: str
    display_name: str
    app_package: AwareAppPackageReference
    default_screen_key: str
    screens: tuple[AwareAppScreenReference, ...]
    digest_sha256: str
    _payload: dict[str, object] = field(repr=False)

    @classmethod
    def from_path(cls, path: str | Path) -> "AwareAppLaunchDescriptor":
        descriptor_path = Path(path).expanduser().resolve()
        if not descriptor_path.is_file():
            raise AwareAppLaunchDescriptorError(
                f"App launch descriptor not found: {descriptor_path}"
            )
        try:
            decoded = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AwareAppLaunchDescriptorError(
                f"App launch descriptor is not valid JSON: {descriptor_path}: {exc}"
            ) from exc
        if not isinstance(decoded, Mapping):
            raise AwareAppLaunchDescriptorError(
                "App launch descriptor root must be a JSON object."
            )
        return cls.from_mapping(decoded)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object],
    ) -> "AwareAppLaunchDescriptor":
        schema = _required_text(payload.get("schema"), "schema")
        if schema != APP_LAUNCH_SCHEMA:
            raise AwareAppLaunchDescriptorError(
                f"Unsupported App launch descriptor schema: {schema!r}; "
                f"expected {APP_LAUNCH_SCHEMA!r}."
            )

        app_package_payload = _required_mapping(
            payload.get("app_package"), "app_package"
        )
        app_package = AwareAppPackageReference(
            package_name=_required_text(
                app_package_payload.get("package_name"),
                "app_package.package_name",
            ),
            app_package_id=_required_uuid(
                app_package_payload.get("app_package_id"),
                "app_package.app_package_id",
            ),
            branch_id=_required_uuid(
                app_package_payload.get("branch_id"),
                "app_package.branch_id",
            ),
            object_instance_graph_commit_id=_required_uuid(
                app_package_payload.get("object_instance_graph_commit_id"),
                "app_package.object_instance_graph_commit_id",
            ),
        )

        raw_screens = payload.get("screens")
        if not isinstance(raw_screens, list) or not raw_screens:
            raise AwareAppLaunchDescriptorError(
                "App launch descriptor screens must be a non-empty array."
            )
        screens: list[AwareAppScreenReference] = []
        screen_keys: set[str] = set()
        for index, raw_screen in enumerate(raw_screens):
            screen_payload = _required_mapping(raw_screen, f"screens[{index}]")
            screen_key = _required_text(
                screen_payload.get("screen_key"), f"screens[{index}].screen_key"
            )
            if screen_key in screen_keys:
                raise AwareAppLaunchDescriptorError(
                    f"Duplicate App launch screen key: {screen_key!r}."
                )
            screen_keys.add(screen_key)
            screens.append(
                AwareAppScreenReference(
                    screen_key=screen_key,
                    app_config_screen_config_id=_required_uuid(
                        screen_payload.get("app_config_screen_config_id"),
                        f"screens[{index}].app_config_screen_config_id",
                    ),
                    projection_experience_id=_required_uuid(
                        screen_payload.get("projection_experience_id"),
                        f"screens[{index}].projection_experience_id",
                    ),
                    projection_experience_layout_graph_binding_id=_required_uuid(
                        screen_payload.get(
                            "projection_experience_layout_graph_binding_id"
                        ),
                        (
                            f"screens[{index}]."
                            "projection_experience_layout_graph_binding_id"
                        ),
                    ),
                )
            )

        default_screen_key = _required_text(
            payload.get("default_screen_key"), "default_screen_key"
        )
        if default_screen_key not in screen_keys:
            raise AwareAppLaunchDescriptorError(
                "App launch default_screen_key does not name a committed screen: "
                f"{default_screen_key!r}."
            )

        app_id = _required_text(payload.get("app_id"), "app_id")
        display_name = _required_text(payload.get("display_name"), "display_name")
        normalized_payload: dict[str, object] = {
            "schema": APP_LAUNCH_SCHEMA,
            "app_id": app_id,
            "display_name": display_name,
            "app_package": app_package.to_payload(),
            "default_screen_key": default_screen_key,
            "screens": [screen.to_payload() for screen in screens],
        }
        digest = hashlib.sha256(
            json.dumps(
                normalized_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        return cls(
            app_id=app_id,
            display_name=display_name,
            app_package=app_package,
            default_screen_key=default_screen_key,
            screens=tuple(screens),
            digest_sha256=f"sha256:{digest}",
            _payload=normalized_payload,
        )

    def resolve_screen(self, screen_key: str | None = None) -> AwareAppScreenReference:
        selected_key = (
            _required_text(screen_key, "screen_key")
            if screen_key is not None
            else self.default_screen_key
        )
        matches = tuple(
            screen for screen in self.screens if screen.screen_key == selected_key
        )
        if not matches:
            available = ", ".join(screen.screen_key for screen in self.screens)
            raise AwareAppLaunchDescriptorError(
                f"App launch screen {selected_key!r} is not committed; "
                f"available screens: {available}."
            )
        if len(matches) != 1:  # Defensive; descriptor construction rejects this.
            raise AwareAppLaunchDescriptorError(
                f"App launch screen {selected_key!r} is ambiguous."
            )
        return matches[0]

    def to_payload(self) -> dict[str, object]:
        return dict(self._payload)


@dataclass(slots=True)
class AwareAppSession:
    client: InterfaceSdkClient
    launch: AwareAppLaunchDescriptor
    selected_screen: AwareAppScreenReference
    namespace: str
    entry_response: Any
    snapshot: InterfaceSurfaceSnapshot

    @classmethod
    async def open(
        cls,
        *,
        launch_ref: AwareAppLaunchDescriptor | str | Path,
        screen_key: str | None = None,
        namespace: str,
        client: InterfaceSdkClient | None = None,
    ) -> "AwareAppSession":
        launch = (
            launch_ref
            if isinstance(launch_ref, AwareAppLaunchDescriptor)
            else AwareAppLaunchDescriptor.from_path(launch_ref)
        )
        selected_screen = launch.resolve_screen(screen_key)
        resolved_namespace = _required_session_text(namespace, "namespace")
        resolved_client = client or InterfaceSdkClient.from_local_service_host()
        response = await resolved_client.enter_app_screen(
            namespace=resolved_namespace,
            app_package_id=launch.app_package.app_package_id,
            app_package_branch_id=launch.app_package.branch_id,
            app_package_object_instance_graph_commit_id=(
                launch.app_package.object_instance_graph_commit_id
            ),
            app_config_screen_config_id=(selected_screen.app_config_screen_config_id),
            reason="aware_sdk.app.run",
            evidence={
                "consumer": "aware-sdk",
                "renderer_kind": "textual",
                "launch_descriptor_sha256": launch.digest_sha256,
                "screen_key": selected_screen.screen_key,
            },
        )
        _validate_entry_response(
            response=response,
            launch=launch,
            selected_screen=selected_screen,
            namespace=resolved_namespace,
        )
        snapshot = InterfaceSurfaceSnapshot(
            namespace=resolved_namespace,
            host_state=response.host_state,
        )
        return cls(
            client=resolved_client,
            launch=launch,
            selected_screen=selected_screen,
            namespace=resolved_namespace,
            entry_response=response,
            snapshot=snapshot,
        )

    async def act(
        self,
        *,
        pane_ref: str,
        action_ref: str,
        payload: Mapping[str, object] | None = None,
    ) -> Any:
        response = await self.client.invoke_pane_action(
            namespace=self.namespace,
            pane_ref=_required_session_text(pane_ref, "pane_ref"),
            action_ref=_required_session_text(action_ref, "action_ref"),
            payload=dict(payload or {}),
            ensure_current_surface=False,
        )
        host_state = getattr(response, "host_state", None)
        if host_state is None:
            raise AwareAppSessionError(
                "Interface pane action response is missing host_state."
            )
        _validate_host_namespace(host_state, self.namespace)
        self.snapshot = InterfaceSurfaceSnapshot(
            namespace=self.namespace,
            host_state=host_state,
        )
        return response

    async def follow(
        self,
        *,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[InterfaceSurfaceSnapshot]:
        if poll_interval_ms <= 0:
            raise AwareAppSessionError("poll_interval_ms must be greater than zero.")
        last_cursor_key = _view_state_cursor_key(self.snapshot)
        async for host_state in self.client.follow_states(
            namespace=self.namespace,
            poll_interval_ms=poll_interval_ms,
        ):
            _validate_host_namespace(host_state, self.namespace)
            snapshot = InterfaceSurfaceSnapshot(
                namespace=self.namespace,
                host_state=host_state,
            )
            cursor_key = _view_state_cursor_key(snapshot)
            if cursor_key is not None and cursor_key == last_cursor_key:
                continue
            self.snapshot = snapshot
            last_cursor_key = cursor_key
            yield snapshot

    def run_receipt(
        self,
        *,
        status: str = "succeeded",
        phase: str = "entered",
        update_count: int = 0,
        error: str | None = None,
    ) -> dict[str, object]:
        host_state = self.snapshot.host_state
        transport = host_state.transport
        app_screen = getattr(host_state, "app_screen", None)
        runtime = host_state.runtime
        payload: dict[str, object] = {
            "schema": APP_RUN_SCHEMA,
            "status": status,
            "phase": phase,
            "canonical_rail": CANONICAL_RAIL,
            "renderer_kind": "textual",
            "namespace": self.namespace,
            "launch_descriptor_sha256": self.launch.digest_sha256,
            "app_id": self.launch.app_id,
            "display_name": self.launch.display_name,
            "app_package": self.launch.app_package.to_payload(),
            "selected_screen": self.selected_screen.to_payload(),
            "interface": {
                "host_label": host_state.host_label,
                "interface_id": _optional_text(transport.interface_id),
                "interface_session_id": _optional_text(transport.interface_session_id),
                "actor_id": _optional_text(transport.actor_id),
                "connected": bool(transport.available),
                "authenticated": bool(transport.authenticated),
            },
            "app_screen": _jsonable(app_screen),
            "view_state_cursor": _jsonable(getattr(runtime, "view_state_cursor", None)),
            "surface": self.snapshot.render_payload(),
            "update_count": update_count,
            "warnings": list(host_state.warnings or ()),
            "next_actions": {
                "act": (
                    f"aware act --namespace {self.namespace} " "<pane-ref> <action-ref>"
                ),
                "follow": (
                    "aware app run --launch-ref <descriptor> "
                    f"--screen {self.selected_screen.screen_key} "
                    f"--namespace {self.namespace} --follow"
                ),
            },
        }
        if error is not None:
            payload["error"] = error
        return payload

    def update_frame(
        self,
        *,
        sequence: int,
        event: str,
        status: str = "succeeded",
        error: str | None = None,
    ) -> dict[str, object]:
        runtime = self.snapshot.host_state.runtime
        payload: dict[str, object] = {
            "schema": APP_UPDATE_SCHEMA,
            "status": status,
            "event": event,
            "sequence": sequence,
            "namespace": self.namespace,
            "launch_descriptor_sha256": self.launch.digest_sha256,
            "app_package": self.launch.app_package.to_payload(),
            "selected_screen": self.selected_screen.to_payload(),
            "app_screen": _jsonable(self.snapshot.host_state.app_screen),
            "view_state_cursor": _jsonable(getattr(runtime, "view_state_cursor", None)),
            "surface": self.snapshot.render_payload(),
        }
        if error is not None:
            payload["error"] = error
        return payload


def failed_run_receipt(
    *,
    namespace: str,
    phase: str,
    error: BaseException,
    launch: AwareAppLaunchDescriptor | None = None,
    screen_key: str | None = None,
) -> dict[str, object]:
    return {
        "schema": APP_RUN_SCHEMA,
        "status": "failed",
        "phase": phase,
        "canonical_rail": CANONICAL_RAIL,
        "renderer_kind": "textual",
        "namespace": namespace,
        "launch_descriptor_sha256": (
            launch.digest_sha256 if launch is not None else None
        ),
        "app_package": (
            launch.app_package.to_payload() if launch is not None else None
        ),
        "screen_key": screen_key,
        "error": str(error) or type(error).__name__,
        "error_type": type(error).__name__,
        "next_action": "inspect_app_launch_or_interface_host_receipt",
    }


def failed_update_frame(
    *,
    receipt: Mapping[str, object],
    sequence: int,
) -> dict[str, object]:
    return {
        "schema": APP_UPDATE_SCHEMA,
        "status": "failed",
        "event": "stream_failed",
        "sequence": sequence,
        "namespace": receipt.get("namespace"),
        "launch_descriptor_sha256": receipt.get("launch_descriptor_sha256"),
        "app_package": receipt.get("app_package"),
        "error": receipt.get("error"),
        "error_type": receipt.get("error_type"),
        "next_action": receipt.get("next_action"),
    }


def _validate_entry_response(
    *,
    response: Any,
    launch: AwareAppLaunchDescriptor,
    selected_screen: AwareAppScreenReference,
    namespace: str,
) -> None:
    if _optional_text(getattr(response, "namespace", None)) != namespace:
        raise AwareAppSessionError(
            "Interface App entry response namespace does not match the requested "
            f"namespace {namespace!r}."
        )
    host_state = getattr(response, "host_state", None)
    if host_state is None:
        raise AwareAppSessionError(
            "Interface App entry response is missing host_state."
        )
    _validate_host_namespace(host_state, namespace)
    app_screen = getattr(response, "app_screen", None)
    host_app_screen = getattr(host_state, "app_screen", None)
    if app_screen is None or host_app_screen is None:
        raise AwareAppSessionError(
            "Interface App entry response is missing committed app_screen evidence."
        )
    _validate_app_screen(
        app_screen,
        launch=launch,
        selected_screen=selected_screen,
        label="response.app_screen",
    )
    _validate_app_screen(
        host_app_screen,
        launch=launch,
        selected_screen=selected_screen,
        label="host_state.app_screen",
    )
    if getattr(host_state, "runtime", None) is None:
        raise AwareAppSessionError(
            "Interface App entry succeeded without a resolved Interface runtime surface."
        )


def _validate_app_screen(
    app_screen: Any,
    *,
    launch: AwareAppLaunchDescriptor,
    selected_screen: AwareAppScreenReference,
    label: str,
) -> None:
    if getattr(app_screen, "accepted", False) is not True:
        blockers = ", ".join(str(item) for item in getattr(app_screen, "blockers", ()))
        reason = _optional_text(getattr(app_screen, "error", None)) or _optional_text(
            getattr(app_screen, "reason", None)
        )
        detail = reason or blockers or "entry was not accepted"
        raise AwareAppSessionError(f"{label} rejected committed App entry: {detail}.")
    expected = {
        "app_package_id": launch.app_package.app_package_id,
        "app_package_branch_id": launch.app_package.branch_id,
        "app_package_object_instance_graph_commit_id": (
            launch.app_package.object_instance_graph_commit_id
        ),
        "app_config_screen_config_id": (selected_screen.app_config_screen_config_id),
        "projection_experience_id": selected_screen.projection_experience_id,
        "projection_experience_layout_graph_binding_id": (
            selected_screen.projection_experience_layout_graph_binding_id
        ),
    }
    for field_name, expected_value in expected.items():
        actual = getattr(app_screen, field_name, None)
        if actual != expected_value:
            raise AwareAppSessionError(
                f"{label}.{field_name} does not match committed launch truth: "
                f"expected {expected_value}, got {actual}."
            )
    if _optional_text(getattr(app_screen, "screen_key", None)) != (
        selected_screen.screen_key
    ):
        raise AwareAppSessionError(
            f"{label}.screen_key does not match committed launch truth: "
            f"expected {selected_screen.screen_key!r}, got "
            f"{getattr(app_screen, 'screen_key', None)!r}."
        )


def _validate_host_namespace(host_state: Any, namespace: str) -> None:
    actual = _optional_text(getattr(host_state, "namespace", None))
    if actual != namespace:
        raise AwareAppSessionError(
            "Interface host_state namespace does not match the app session: "
            f"expected {namespace!r}, got {actual!r}."
        )


def _view_state_cursor_key(
    snapshot: InterfaceSurfaceSnapshot,
) -> tuple[str | None, str | None] | None:
    runtime = snapshot.host_state.runtime
    cursor_state = getattr(runtime, "view_state_cursor", None)
    if cursor_state is None:
        return None
    cursor = _optional_text(getattr(cursor_state, "cursor", None))
    digest = _optional_text(getattr(cursor_state, "digest", None))
    if cursor is None and digest is None:
        return None
    return cursor, digest


def _required_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise AwareAppLaunchDescriptorError(f"{label} must be a JSON object.")
    return value


def _required_text(value: object, label: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise AwareAppLaunchDescriptorError(
            f"App launch descriptor field {label!r} must be non-empty."
        )
    return text


def _required_uuid(value: object, label: str) -> UUID:
    text = _required_text(value, label)
    try:
        return UUID(text)
    except ValueError as exc:
        raise AwareAppLaunchDescriptorError(
            f"App launch descriptor field {label!r} must be a UUID: {text!r}."
        ) from exc


def _required_session_text(value: object, label: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise AwareAppSessionError(f"{label} must be non-empty.")
    return text


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _jsonable(value: object) -> object:
    if value is None:
        return None
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


__all__ = [
    "APP_LAUNCH_SCHEMA",
    "APP_RUN_SCHEMA",
    "APP_UPDATE_SCHEMA",
    "AwareAppLaunchDescriptor",
    "AwareAppLaunchDescriptorError",
    "AwareAppPackageReference",
    "AwareAppScreenReference",
    "AwareAppSession",
    "AwareAppSessionError",
    "CANONICAL_RAIL",
    "failed_run_receipt",
    "failed_update_frame",
]
