from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest

from aware_interface import (
    InterfaceActionReceipt,
    InterfaceActionRequest,
    InterfaceGateState,
    InterfaceGateStep,
    InterfaceHostRuntime,
    InterfaceLaneSyncService,
    InterfaceNavigationContextLayoutTargetState,
    InterfaceResolvedView,
    EnvironmentInterfaceGatePort,
    describe_interface_backend_state,
)
from aware_interface.runtime_artifact_refs import runtime_artifact_refs_from_payload
from aware_interface.session_port import FocusScopeLane, SectionFocusScopeLane
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)


_REPO_ROOT = Path(__file__).resolve().parents[8]
_INTERFACE_DB_SQL_ROOT = _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "services" / "interface" / "db" / "sqlite"


def _write_service_registry(*, runtime_dir: Path, environment_id: UUID) -> Path:
    registry_path = runtime_dir / "db.schema.registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    entry = build_db_schema_registry_entry(
        package_kind="state",
        backend_targets=("sqlite",),
        sql_root=_INTERFACE_DB_SQL_ROOT,
        source_label="interface-db",
        relative_to=runtime_dir,
    )
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(environment_id=environment_id, entries=[entry]),
    )
    return registry_path


def _ontology_runtime_artifact_ref() -> dict[str, object]:
    artifact_set = {
        "artifact_set_id": "ontology-runtime-artifact-set:test",
        "package_name": "aware-test-ontology",
        "fqn_prefix": "aware_test",
        "runtime_contract_version": "aware.ontology.runtime_artifact_set.v1",
        "runtime_projection_descriptors": [
            {
                "projection_name": "FocusScope",
                "projection_hash": "focus-scope-hash",
            }
        ],
    }
    return {
        "artifact_family": "ontology_runtime_artifact_set",
        "artifact_key": "ontology-runtime-artifact-set:test",
        "artifact_role": "runtime_artifact_set",
        "required_for": ["service_boot"],
        "status": "available",
        "package_name": "aware-test-ontology",
        "runtime_contract_version": "aware.ontology.runtime_artifact_set.v1",
        "receipt": {"ontology_runtime_artifact_set": artifact_set},
    }


def _build_host_runtime(
    *,
    tmp_path: Path,
    environment_id: UUID,
) -> InterfaceHostRuntime:
    registry_path = _write_service_registry(
        runtime_dir=tmp_path / "state" / "interface-service-local-state",
        environment_id=environment_id,
    )
    return InterfaceHostRuntime.from_runtime_artifact_refs(
        repository_root=tmp_path / "repo",
        state_home=tmp_path,
        namespace="cli",
        environment_id=environment_id,
        runtime_artifact_refs=runtime_artifact_refs_from_payload(
            [_ontology_runtime_artifact_ref()]
        ),
        db_schema_registry_path=registry_path,
    )


class _FakeLaneSyncSource:
    async def load_latest(self, *, branch_id: str, projection_hash: str):  # type: ignore[no-untyped-def]
        return None

    async def load_commit(  # type: ignore[no-untyped-def]
        self,
        *,
        branch_id: str,
        projection_hash: str,
        commit_id: str,
    ):
        return None

    async def _watch(self):  # type: ignore[no-untyped-def]
        if False:
            yield None

    def watch_lane(  # type: ignore[no-untyped-def]
        self,
        *,
        branch_id: str,
        projection_hash: str,
        include_initial: bool = True,
    ):
        return self._watch()


class _FakeSessionPort:
    async def ensure_boot_interface_graph(self):  # type: ignore[no-untyped-def]
        return uuid4()

    async def resolve_focus_scope_lane(self, *, window_key: str) -> FocusScopeLane:
        return FocusScopeLane(
            interface_id=uuid4(),
            window_key=window_key,
            window_id=uuid4(),
            focus_scope_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="sha256:test:focus",
        )

    async def resolve_section_focus_scope_lane(
        self,
        *,
        window_key: str,
        layout_key: str,
        section_key: str,
    ) -> SectionFocusScopeLane:
        return SectionFocusScopeLane(
            interface_id=uuid4(),
            window_key=window_key,
            layout_key=layout_key,
            section_key=section_key,
            window_id=uuid4(),
            layout_id=uuid4(),
            section_id=uuid4(),
            layout_section_id=uuid4(),
            section_focus_scope_id=uuid4(),
            focus_scope_id=uuid4(),
            branch_id=uuid4(),
            projection_hash="sha256:test:section",
        )

    def lane_sync_source(
        self, *, include_commit_payload: bool = True
    ) -> _FakeLaneSyncSource:
        return _FakeLaneSyncSource()

    def context_ids(self) -> tuple[UUID | None, UUID | None]:
        return (uuid4(), uuid4())


class _FakeGatePort:
    async def load_gate_state(self, *, backend=None) -> InterfaceGateState:
        return InterfaceGateState(
            destination_key="studio",
            active_step_key="ready",
            blocked=False,
            steps=(InterfaceGateStep(key="ready", status="active", title="Ready"),),
        )


class _FakeExperiencePort:
    async def resolve_view(self, *, state):  # type: ignore[no-untyped-def]
        return InterfaceResolvedView(
            experience_key="aware.home",
            projection_view_id="aware.home.default",
            host_payload={"backend_available": state.backend.available},
        )


class _FakeThreadLayoutPort:
    def __init__(self) -> None:
        self.states = []
        self.target = InterfaceNavigationContextLayoutTargetState(
            source_kind="environment_activation",
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            thread_layout_id=uuid4(),
            layout_config_id=uuid4(),
            layout_key="configuration_map",
            window_key="main",
        )

    async def resolve_navigation_context_layout_target(self, *, state):  # type: ignore[no-untyped-def]
        self.states.append(state)
        return self.target


class _FakeActionPort:
    async def perform_action(
        self, request: InterfaceActionRequest
    ) -> InterfaceActionReceipt:
        return InterfaceActionReceipt(
            status="succeeded",
            receipt_id="receipt-1",
            payload={"action_key": request.action_key},
        )


@pytest.mark.asyncio
async def test_host_runtime_coordinator_bootstraps_backend_and_snapshot(
    tmp_path: Path,
) -> None:
    environment_id = uuid4()
    runtime = _build_host_runtime(tmp_path=tmp_path, environment_id=environment_id)

    backend = await runtime.describe_backend_state()
    assert backend.available is True
    assert backend.manifest_path is None
    assert backend.environment_id == environment_id
    assert backend.database_path == (tmp_path / "cli" / "interface.sqlite").resolve()
    assert backend.table_count > 0

    coordinator = runtime.build_coordinator(
        session_port=_FakeSessionPort(),
        gate_port=_FakeGatePort(),
        experience_port=_FakeExperiencePort(),
        navigation_context_layout_port=_FakeThreadLayoutPort(),
        action_port=_FakeActionPort(),
    )

    snapshot = await coordinator.snapshot()
    assert snapshot.backend.available is True
    assert snapshot.gate_state is not None
    assert snapshot.gate_state.destination_key == "studio"
    assert snapshot.resolved_view is not None
    assert snapshot.resolved_view.experience_key == "aware.home"
    assert snapshot.resolved_view.host_payload["backend_available"] is True
    assert snapshot.navigation_context_layout_target is not None
    assert snapshot.navigation_context_layout_target.layout_key == "configuration_map"
    assert snapshot.warnings == ()

    sync_service = coordinator.build_lane_sync_service()
    assert isinstance(sync_service, InterfaceLaneSyncService)

    interface_id = await coordinator.ensure_boot_interface_graph()
    assert isinstance(interface_id, UUID)

    focus_lane = await coordinator.resolve_focus_scope_lane(window_key="execution")
    assert focus_lane.window_key == "execution"

    section_lane = await coordinator.resolve_section_focus_scope_lane(
        window_key="execution",
        layout_key="mobile-conversation-workspace",
        section_key="workspace",
    )
    assert section_lane.section_key == "workspace"

    process_id, thread_id = coordinator.context_ids()
    assert isinstance(process_id, UUID)
    assert isinstance(thread_id, UUID)

    receipt = await coordinator.perform_action(
        InterfaceActionRequest(action_key="noop")
    )
    assert receipt.status == "succeeded"
    assert receipt.payload["action_key"] == "noop"


@pytest.mark.asyncio
async def test_host_runtime_accepts_service_owned_db_schema_registry(
    tmp_path: Path,
) -> None:
    environment_id = uuid4()
    service_registry_path = _write_service_registry(
        runtime_dir=tmp_path / "state" / "interface-service-local-state",
        environment_id=environment_id,
    )

    runtime = InterfaceHostRuntime.from_runtime_artifact_refs(
        repository_root=tmp_path / "repo",
        state_home=tmp_path,
        namespace="cli",
        environment_id=environment_id,
        runtime_artifact_refs=runtime_artifact_refs_from_payload(
            [_ontology_runtime_artifact_ref()]
        ),
        db_schema_registry_path=service_registry_path,
    )
    backend = await runtime.describe_backend_state()

    assert runtime.registry_path == service_registry_path.resolve()
    assert backend.available is True
    assert backend.registry_path == service_registry_path.resolve()
    assert backend.environment_id == environment_id


@pytest.mark.asyncio
async def test_environment_interface_gate_port_composes_boot_gated_flow(
    tmp_path: Path,
) -> None:
    environment_id = uuid4()
    runtime = _build_host_runtime(tmp_path=tmp_path, environment_id=environment_id)
    backend = await runtime.describe_backend_state()
    actor_id = uuid4()

    gate_port = EnvironmentInterfaceGatePort(
        repository_root=tmp_path / "repo",
        state_home=tmp_path,
        namespace="cli",
        endpoint="wss://node.aware.run",
        actor_id=actor_id,
        environment_config_id=environment_id,
        auth_session_available=True,
        auth_actor_id=actor_id,
    )

    gate_state = await gate_port.load_gate_state(backend=backend)
    assert gate_state is not None
    assert gate_state.destination_key == "identityGate"
    assert gate_state.active_step_key == "identity"
    assert tuple(step.status for step in gate_state.steps) == (
        "crossed",
        "active",
        "locked",
    )
    assert (
        gate_state.reason
        == "Bootstrap authority for the selected environment before crossing Boot."
    )


@pytest.mark.asyncio
async def test_describe_interface_backend_state_reports_retired_manifest_boot(
    tmp_path: Path,
) -> None:
    state = await describe_interface_backend_state(
        repository_root=tmp_path / "repo",
        state_home=tmp_path,
        namespace="cli",
    )

    assert state.available is False
    assert state.manifest_path is None
    assert state.registry_path is None
    assert state.database_path == (tmp_path / "cli" / "interface.sqlite").resolve()
    assert state.database_exists is False
    assert state.reason is not None
    assert "Environment runtime manifest boot is retired" in state.reason
