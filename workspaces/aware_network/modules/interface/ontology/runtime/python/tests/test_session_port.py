from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_interface.session_port import InterfaceRuntimeSessionPort
from aware_interface.session_state import (
    InterfaceRuntimeSessionStateStore,
    PersistedEnvironmentSession,
)


@pytest.mark.asyncio
async def test_session_port_reuses_persisted_environment_for_matching_config(
    tmp_path,
) -> None:
    actor_id = uuid4()
    endpoint = "ws://localhost:8912"
    interface_id = uuid4()
    environment_id = uuid4()
    environment_config_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()
    state_store = InterfaceRuntimeSessionStateStore(
        state_root=tmp_path,
        namespace="flutter-aware-control",
    )
    await state_store.asave(
        PersistedEnvironmentSession(
            actor_id=actor_id,
            endpoint=endpoint,
            environment_id=environment_id,
            environment_config_id=environment_config_id,
        )
    )
    client = _FakeClient(
        actor_id=actor_id,
        endpoint=endpoint,
        environment_id=environment_id,
        environment_config_id=environment_config_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
    )
    port = InterfaceRuntimeSessionPort(
        client=client,
        interface_id=interface_id,
        endpoint=endpoint,
        state_store=state_store,
    )

    result = await port.bootstrap(environment_config_id=environment_config_id)

    assert result.environment_id == environment_id
    assert result.environment_config_id == environment_config_id
    assert client.provision_calls == 0
    assert client.status_calls == [environment_id]
    assert client.context.environment_id == environment_id


@pytest.mark.asyncio
async def test_session_port_reuses_bootstrap_describe_and_topology_cache(
    tmp_path,
) -> None:
    actor_id = uuid4()
    endpoint = "ws://localhost:8912"
    interface_id = uuid4()
    environment_id = uuid4()
    environment_config_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()
    lane_hash = "focus-scope-lane-hash"
    opg_hash = "focus-scope-opg-hash"
    state_store = InterfaceRuntimeSessionStateStore(
        state_root=tmp_path,
        namespace="flutter-aware-control",
    )
    topology = SimpleNamespace(
        processes=(
            SimpleNamespace(
                process_id=process_id,
                threads=(
                    SimpleNamespace(
                        thread_id=thread_id,
                        attachments=(
                            SimpleNamespace(
                                is_active=True,
                                domain_branch_id=branch_id,
                                lanes=(
                                    SimpleNamespace(
                                        opg_name="FocusScope",
                                        lane_hash=lane_hash,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    client = _FakeClient(
        actor_id=actor_id,
        endpoint=endpoint,
        environment_id=environment_id,
        environment_config_id=environment_config_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        describe_opgs=(
            SimpleNamespace(name="FocusScope", projection_hash=opg_hash),
        ),
        topology=topology,
    )
    port = InterfaceRuntimeSessionPort(
        client=client,
        interface_id=interface_id,
        endpoint=endpoint,
        state_store=state_store,
    )

    await port.bootstrap(environment_config_id=environment_config_id)
    describe_calls_after_bootstrap = client.describe_config_calls

    assert await port.resolve_projection_hash(opg_name="FocusScope") == opg_hash
    assert await port.resolve_projection_hash(opg_name="focus_scope") == opg_hash
    assert client.describe_config_calls == describe_calls_after_bootstrap
    assert await port.resolve_topology_focus_scope_lane() == (branch_id, lane_hash)
    assert await port.resolve_topology_focus_scope_lane() == (branch_id, lane_hash)
    assert client.topology_calls == [(None, None)]


@pytest.mark.asyncio
async def test_session_port_persists_environment_before_describe_hydration(
    tmp_path,
) -> None:
    actor_id = uuid4()
    endpoint = "ws://localhost:8912"
    interface_id = uuid4()
    environment_config_id = uuid4()
    environment_id = uuid4()
    state_store = InterfaceRuntimeSessionStateStore(
        state_root=tmp_path,
        namespace="flutter-aware-control",
    )
    client = _FakeClient(
        actor_id=actor_id,
        endpoint=endpoint,
        environment_id=environment_id,
        environment_config_id=environment_config_id,
        process_id=uuid4(),
        thread_id=uuid4(),
        branch_id=uuid4(),
        fail_describe_config=True,
    )
    port = InterfaceRuntimeSessionPort(
        client=client,
        interface_id=interface_id,
        endpoint=endpoint,
        state_store=state_store,
    )

    with pytest.raises(RuntimeError, match="describe failed"):
        await port.bootstrap(environment_config_id=environment_config_id)

    persisted = await state_store.aload(actor_id=actor_id, endpoint=endpoint)
    assert persisted is not None
    assert persisted.environment_id == environment_id
    assert persisted.environment_config_id == environment_config_id


class _FakeClient:
    def __init__(
        self,
        *,
        actor_id,
        endpoint,
        environment_id,
        environment_config_id,
        process_id,
        thread_id,
        branch_id,
        fail_describe_config=False,
        describe_opgs=(),
        topology=None,
    ) -> None:
        self.config = SimpleNamespace(actor_id=actor_id, endpoint=endpoint)
        self.environment_id = environment_id
        self.environment_config_id = environment_config_id
        self.process_id = process_id
        self.thread_id = thread_id
        self.branch_id = branch_id
        self.context = None
        self.provision_calls = 0
        self.status_calls = []
        self.fail_describe_config = fail_describe_config
        self.describe_opgs = describe_opgs
        self.describe_config_calls = 0
        self.topology = topology
        self.topology_calls = []

    async def discover_environment_configs(self):
        return SimpleNamespace(configs=())

    async def provision_environment(self, *, environment_config_id, eager_ready):
        _ = environment_config_id
        _ = eager_ready
        self.provision_calls += 1
        return SimpleNamespace(
            environment_id=self.environment_id,
            environment_config_id=self.environment_config_id,
            process_id=self.process_id,
            thread_id=self.thread_id,
            branch_id=self.branch_id,
        )

    async def get_environment_status(self, *, environment_id):
        self.status_calls.append(environment_id)
        return SimpleNamespace(
            environment_id=environment_id,
            environment_config_id=self.environment_config_id,
            process_id=self.process_id,
            thread_id=self.thread_id,
            branch_id=self.branch_id,
        )

    def set_context(self, context):
        self.context = context

    def get_context(self):
        return self.context

    async def describe_environment_config(self):
        self.describe_config_calls += 1
        if self.fail_describe_config:
            raise RuntimeError("describe failed")
        return _FakeDescribeConfig(ocg_id=uuid4(), opgs=self.describe_opgs)

    async def describe_environment(self):
        return {"environment_id": str(self.environment_id)}

    async def fetch_capabilities(self):
        return {"capabilities": []}

    async def describe_environment_topology(self, *, process_key=None, thread_key=None):
        self.topology_calls.append((process_key, thread_key))
        return self.topology or SimpleNamespace(processes=())


class _FakeDescribeConfig:
    def __init__(self, *, ocg_id, opgs=()) -> None:
        self.ocg_id = ocg_id
        self.opgs = opgs

    def model_dump(self, *, mode: str = "python"):
        _ = mode
        return {"ocg_id": str(self.ocg_id), "opgs": []}
