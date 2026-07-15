from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceEnterAppScreenResponse,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceAppScreenState,
    InterfaceBackendState,
    InterfaceCurrentScreen,
    InterfaceHostState,
    InterfaceHostViewStateCursorState,
    InterfaceRuntimeState,
    InterfaceTransportState,
)
from aware_sdk import (
    AwareAppLaunchDescriptor,
    AwareAppLaunchDescriptorError,
    AwareAppSession,
    AwareAppSessionError,
)
from aware_sdk import cli
from aware_sdk.commands import app as app_command

_APP_PACKAGE_ID = UUID("11111111-1111-4111-8111-111111111111")
_BRANCH_ID = UUID("22222222-2222-4222-8222-222222222222")
_APP_COMMIT_ID = UUID("33333333-3333-4333-8333-333333333333")
_SCREEN_ID = UUID("44444444-4444-4444-8444-444444444444")
_EXPERIENCE_ID = UUID("55555555-5555-4555-8555-555555555555")
_LAYOUT_BINDING_ID = UUID("66666666-6666-4666-8666-666666666666")


def test_launch_descriptor_validates_committed_screen_truth() -> None:
    launch = AwareAppLaunchDescriptor.from_mapping(_launch_payload())

    assert launch.app_id == "aware-home"
    assert launch.app_package.app_package_id == _APP_PACKAGE_ID
    assert launch.resolve_screen().screen_key == "home"
    assert launch.digest_sha256.startswith("sha256:")
    assert launch.to_payload() == _launch_payload()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda payload: payload.update(schema="aware.app.launch.v1"), "schema"),
        (
            lambda payload: payload.update(default_screen_key="missing"),
            "default_screen_key",
        ),
        (
            lambda payload: payload["screens"].append(dict(payload["screens"][0])),
            "Duplicate",
        ),
        (
            lambda payload: payload["app_package"].update(branch_id="not-a-uuid"),
            "must be a UUID",
        ),
    ],
)
def test_launch_descriptor_rejects_invalid_schema_or_screen_coordinates(
    mutate: Any,
    message: str,
) -> None:
    payload = _launch_payload()
    mutate(payload)

    with pytest.raises(AwareAppLaunchDescriptorError, match=message):
        AwareAppLaunchDescriptor.from_mapping(payload)


def test_home_materialized_launch_descriptor_is_directly_consumable() -> None:
    repo_root = Path(__file__).resolve().parents[8]
    launch = AwareAppLaunchDescriptor.from_path(
        repo_root
        / "workspaces/aware_home/modules/home/apps/aware_home/aware.app.launch.json"
    )

    assert launch.app_id == "aware-home"
    assert launch.app_package.package_name == "aware-home-app"
    assert [screen.screen_key for screen in launch.screens] == ["control", "home"]
    assert launch.resolve_screen().screen_key == "control"


@pytest.mark.asyncio
async def test_app_session_enters_exact_public_interface_sdk_coordinates() -> None:
    client = _FakeInterfaceClient()
    launch = AwareAppLaunchDescriptor.from_mapping(_launch_payload())

    session = await AwareAppSession.open(
        client=client,
        launch_ref=launch,
        namespace="home-agent",
    )

    assert client.entry_calls == [
        {
            "namespace": "home-agent",
            "app_package_id": _APP_PACKAGE_ID,
            "app_package_branch_id": _BRANCH_ID,
            "app_package_object_instance_graph_commit_id": _APP_COMMIT_ID,
            "app_config_screen_config_id": _SCREEN_ID,
            "reason": "aware_sdk.app.run",
            "evidence": {
                "consumer": "aware-sdk",
                "renderer_kind": "textual",
                "launch_descriptor_sha256": launch.digest_sha256,
                "screen_key": "home",
            },
        }
    ]
    receipt = session.run_receipt()
    assert receipt["status"] == "succeeded"
    assert receipt["canonical_rail"].startswith("aware-sdk -> interface-sdk")
    assert receipt["selected_screen"]["projection_experience_id"] == str(_EXPERIENCE_ID)
    assert receipt["surface"]["current_screen"]["screen_key"] == "home"


@pytest.mark.asyncio
async def test_app_session_fails_closed_on_interface_coordinate_mismatch() -> None:
    client = _FakeInterfaceClient(mismatched_projection=True)

    with pytest.raises(AwareAppSessionError, match="projection_experience_id"):
        await AwareAppSession.open(
            client=client,
            launch_ref=AwareAppLaunchDescriptor.from_mapping(_launch_payload()),
            namespace="home-agent",
        )


@pytest.mark.asyncio
async def test_app_session_actions_stay_on_interface_pane_action_rail() -> None:
    client = _FakeInterfaceClient()
    session = await AwareAppSession.open(
        client=client,
        launch_ref=AwareAppLaunchDescriptor.from_mapping(_launch_payload()),
        namespace="home-agent",
    )

    await session.act(
        pane_ref="home/main/door",
        action_ref="door.open",
        payload={"source": "agent"},
    )

    assert client.action_calls == [
        {
            "namespace": "home-agent",
            "pane_ref": "home/main/door",
            "action_ref": "door.open",
            "payload": {"source": "agent"},
            "ensure_current_surface": False,
        }
    ]


@pytest.mark.asyncio
async def test_app_session_follow_deduplicates_interface_cursor_and_digest() -> None:
    client = _FakeInterfaceClient(
        follow_states=[
            _host_state("home-agent", cursor="cursor-1", digest="digest-1"),
            _host_state("home-agent", cursor="cursor-2", digest="digest-2"),
            _host_state("home-agent", cursor="cursor-2", digest="digest-2"),
        ]
    )
    session = await AwareAppSession.open(
        client=client,
        launch_ref=AwareAppLaunchDescriptor.from_mapping(_launch_payload()),
        namespace="home-agent",
    )

    snapshots = [snapshot async for snapshot in session.follow(poll_interval_ms=25)]

    assert client.follow_calls == [{"namespace": "home-agent", "poll_interval_ms": 25}]
    assert len(snapshots) == 1
    assert snapshots[0].host_state.runtime.view_state_cursor.cursor == "cursor-2"


def test_app_run_once_emits_and_writes_canonical_receipt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    launch_ref = _write_launch(tmp_path)
    receipt_ref = tmp_path / "receipts" / "app-run.json"
    client = _FakeInterfaceClient()
    monkeypatch.setattr(app_command, "_build_client", lambda args: client)

    exit_code = cli.main(
        [
            "app",
            "run",
            "--launch-ref",
            str(launch_ref),
            "--namespace",
            "home-agent",
            "--once",
            "--no-ensure-local-host",
            "--receipt",
            str(receipt_ref),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["schema"] == "aware.app.run.v0"
    assert payload["status"] == "succeeded"
    assert payload["namespace"] == "home-agent"
    assert payload["selected_screen"]["screen_key"] == "home"
    assert json.loads(receipt_ref.read_text(encoding="utf-8")) == payload


def test_app_run_follow_emits_deduplicated_ndjson_and_terminal_receipt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    launch_ref = _write_launch(tmp_path)
    receipt_ref = tmp_path / "app-follow.json"
    client = _FakeInterfaceClient(
        follow_states=[
            _host_state("home-agent", cursor="cursor-1", digest="digest-1"),
            _host_state("home-agent", cursor="cursor-2", digest="digest-2"),
            _host_state("home-agent", cursor="cursor-2", digest="digest-2"),
        ]
    )
    monkeypatch.setattr(app_command, "_build_client", lambda args: client)

    exit_code = cli.main(
        [
            "app",
            "run",
            "--launch-ref",
            str(launch_ref),
            "--namespace",
            "home-agent",
            "--follow",
            "--poll-interval-ms",
            "10",
            "--no-ensure-local-host",
            "--receipt",
            str(receipt_ref),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    frames = [json.loads(line) for line in captured.out.splitlines()]
    assert [frame["event"] for frame in frames] == ["entered", "updated"]
    assert [frame["sequence"] for frame in frames] == [0, 1]
    receipt = json.loads(receipt_ref.read_text(encoding="utf-8"))
    assert receipt["status"] == "succeeded"
    assert receipt["phase"] == "follow_complete"
    assert receipt["update_count"] == 1


def test_app_run_follow_emits_stable_terminal_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    launch_ref = _write_launch(tmp_path)
    receipt_ref = tmp_path / "app-follow-failed.json"
    client = _FakeInterfaceClient(follow_error=RuntimeError("follow unavailable"))
    monkeypatch.setattr(app_command, "_build_client", lambda args: client)

    exit_code = cli.main(
        [
            "app",
            "run",
            "--launch-ref",
            str(launch_ref),
            "--namespace",
            "home-agent",
            "--follow",
            "--no-ensure-local-host",
            "--receipt",
            str(receipt_ref),
        ]
    )

    frames = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert exit_code == 1
    assert [frame["event"] for frame in frames] == ["entered", "stream_failed"]
    assert frames[-1]["error"] == "follow unavailable"
    receipt = json.loads(receipt_ref.read_text(encoding="utf-8"))
    assert receipt["status"] == "failed"
    assert receipt["phase"] == "follow"


def test_app_run_rejects_non_descriptor_input_before_interface_client_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    launch_ref = tmp_path / "bad-launch.json"
    launch_ref.write_text('{"schema":"not-aware"}\n', encoding="utf-8")
    built = False

    def _build_client(args: Any) -> Any:
        nonlocal built
        built = True
        return _FakeInterfaceClient()

    monkeypatch.setattr(app_command, "_build_client", _build_client)

    exit_code = cli.main(
        ["app", "run", "--launch-ref", str(launch_ref), "--namespace", "agent"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert built is False
    assert payload["schema"] == "aware.app.run.v0"
    assert payload["status"] == "failed"
    assert payload["phase"] == "descriptor_validation"


class _FakeInterfaceClient:
    def __init__(
        self,
        *,
        mismatched_projection: bool = False,
        follow_states: list[InterfaceHostState] | None = None,
        follow_error: Exception | None = None,
    ) -> None:
        self.mismatched_projection = mismatched_projection
        self._follow_states = follow_states or []
        self._follow_error = follow_error
        self.entry_calls: list[dict[str, object]] = []
        self.action_calls: list[dict[str, object]] = []
        self.follow_calls: list[dict[str, object]] = []

    async def enter_app_screen(
        self, **kwargs: object
    ) -> InterfaceEnterAppScreenResponse:
        self.entry_calls.append(dict(kwargs))
        namespace = str(kwargs["namespace"])
        host_state = _host_state(namespace, cursor="cursor-1", digest="digest-1")
        if self.mismatched_projection:
            host_state = host_state.model_copy(
                update={
                    "app_screen": host_state.app_screen.model_copy(
                        update={"projection_experience_id": uuid4()}
                    )
                }
            )
        return InterfaceEnterAppScreenResponse(
            request_id=uuid4(),
            namespace=namespace,
            app_screen=host_state.app_screen,
            host_state=host_state,
        )

    async def invoke_pane_action(self, **kwargs: object) -> Any:
        self.action_calls.append(dict(kwargs))
        return SimpleNamespace(
            host_state=_host_state(
                str(kwargs["namespace"]),
                cursor="cursor-action",
                digest="digest-action",
            )
        )

    async def follow_states(
        self, **kwargs: object
    ) -> AsyncIterator[InterfaceHostState]:
        self.follow_calls.append(dict(kwargs))
        for host_state in self._follow_states:
            yield host_state
        if self._follow_error is not None:
            raise self._follow_error


def _launch_payload() -> dict[str, Any]:
    return {
        "schema": "aware.app.launch.v0",
        "app_id": "aware-home",
        "display_name": "Aware Home",
        "app_package": {
            "package_name": "aware-home-app",
            "app_package_id": str(_APP_PACKAGE_ID),
            "branch_id": str(_BRANCH_ID),
            "object_instance_graph_commit_id": str(_APP_COMMIT_ID),
        },
        "default_screen_key": "home",
        "screens": [
            {
                "screen_key": "home",
                "app_config_screen_config_id": str(_SCREEN_ID),
                "projection_experience_id": str(_EXPERIENCE_ID),
                "projection_experience_layout_graph_binding_id": str(
                    _LAYOUT_BINDING_ID
                ),
            }
        ],
    }


def _write_launch(tmp_path: Path) -> Path:
    path = tmp_path / "aware.app.launch.json"
    path.write_text(json.dumps(_launch_payload(), indent=2) + "\n", encoding="utf-8")
    return path


def _host_state(namespace: str, *, cursor: str, digest: str) -> InterfaceHostState:
    app_screen = InterfaceAppScreenState(
        status="resolved",
        accepted=True,
        app_package_id=_APP_PACKAGE_ID,
        app_package_branch_id=_BRANCH_ID,
        app_package_object_instance_graph_commit_id=_APP_COMMIT_ID,
        app_config_screen_config_id=_SCREEN_ID,
        screen_key="home",
        projection_experience_id=_EXPERIENCE_ID,
        projection_experience_layout_graph_binding_id=_LAYOUT_BINDING_ID,
        experience_name="home_story",
        layout_binding_key="configuration_map",
    )
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="https://interface.example",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="app",
            screen_key="home",
            source_kind="committed_app_screen",
            title="Aware Home",
            pane_key="home",
        ),
        transport=InterfaceTransportState(
            available=True,
            registered=True,
            authenticated=True,
            actor_id=uuid4(),
            interface_id=uuid4(),
            interface_session_id=uuid4(),
            capabilities=["interface.enter_app_screen"],
        ),
        app_screen=app_screen,
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=True,
                database_exists=True,
                opg_count=1,
                projection_bundle_available=True,
                projection_plan_count=1,
                table_count=2,
            ),
            view_state_cursor=InterfaceHostViewStateCursorState(
                cursor=cursor,
                digest=digest,
            ),
        ),
    )
