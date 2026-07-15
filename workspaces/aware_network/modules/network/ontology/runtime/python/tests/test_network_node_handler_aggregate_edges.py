from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

import pytest

from aware_network.handlers.impl.network.network_node import (
    attach_service,
    register,
    upsert_environment,
)
from aware_network.handlers.impl.network.network_node_environment import (
    create_via_network_node,
)
from aware_network.handlers.impl.network.network_node_peer_fanout_rule import (
    create_via_network_node_peer,
)
from aware_network.handlers.impl.network.network_node_service import (
    build_via_network_node,
)
from aware_network_ontology.network.network_enums import NetworkEnvironmentRole
from aware_network_ontology.network.network_enums import NetworkFanoutMode
from aware_network_ontology.network.network_node_environment import (
    NetworkNodeEnvironment,
)
from aware_network_ontology.network.network_node_peer_fanout_rule import (
    NetworkNodePeerFanoutRule,
)
from aware_network_ontology.network.network_node_service import NetworkNodeService
from aware_network_ontology.stable_ids import (
    stable_network_node_id,
    stable_network_node_environment_id,
    stable_network_node_peer_fanout_rule_id,
    stable_network_node_service_id,
)
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import (
    has_invocation_provider,
    reset_invocation_provider,
    set_invocation_provider,
)


class _RecordingInvocationProvider:
    def __init__(self) -> None:
        self.constructor_calls: list[dict[str, Any]] = []

    async def invoke_instance(self, *, orm_model: ORMModel, function_name: str, payload: Mapping[str, Any]) -> Any:
        raise AssertionError(f"unexpected instance invocation: {function_name}")

    async def invoke_constructor(
        self,
        *,
        orm_class: type[ORMModel],
        function_name: str,
        payload: Mapping[str, Any],
    ) -> Any:
        self.constructor_calls.append(
            {
                "orm_class": orm_class,
                "function_name": function_name,
                "payload": dict(payload),
            }
        )
        if orm_class is NetworkNodeEnvironment:
            return await create_via_network_node(**dict(payload))
        if orm_class is NetworkNodeService:
            return await build_via_network_node(**dict(payload))
        raise AssertionError(f"unexpected constructor invocation: {function_name}")


@pytest.mark.asyncio
async def test_network_node_register_rejects_non_semantic_node_id() -> None:
    with pytest.raises(ValueError, match="public_key semantic identity"):
        await register(
            public_key="test-node-key",
            hostname="127.0.0.1",
            port=8991,
            node_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_network_node_upsert_environment_requires_invocation_provider() -> None:
    assert not has_invocation_provider()
    environment_id = uuid4()
    node = await register(
        public_key="test-node-key",
        hostname="127.0.0.1",
        port=8991,
    )

    with pytest.raises(RuntimeError, match="No invocation provider set"):
        await upsert_environment(
            network_node=node,
            environment_id=environment_id,
            role=NetworkEnvironmentRole.owner,
            is_active=True,
            priority=100,
        )
    assert node.environments == []


@pytest.mark.asyncio
async def test_network_node_attach_service_requires_invocation_provider() -> None:
    assert not has_invocation_provider()
    service_package_id = uuid4()
    service_id = uuid4()
    node = await register(
        public_key="test-node-key",
        hostname="127.0.0.1",
        port=8991,
    )

    with pytest.raises(RuntimeError, match="No invocation provider set"):
        await attach_service(
            network_node=node,
            service_package_id=service_package_id,
            service_id=service_id,
            host_id="kernel-services-node",
            protocol_version="workspace-revision",
            service_name="aware-meta-service",
            endpoint_refs=["meta.graph.invoke_function"],
            stream_endpoint_refs=[],
            host_version="1.0.0",
            supports_stream_events=True,
        )
    assert node.services == []


@pytest.mark.asyncio
async def test_network_node_parent_aggregate_edges_use_generated_child_constructors() -> None:
    node_id = stable_network_node_id(public_key="provider-node-key")
    environment_id = uuid4()
    service_package_id = uuid4()
    service_id = uuid4()
    node = await register(
        public_key="provider-node-key",
        hostname="127.0.0.1",
        port=8991,
    )

    provider = _RecordingInvocationProvider()
    token = set_invocation_provider(provider)
    try:
        assert has_invocation_provider()
        updated = await upsert_environment(
            network_node=node,
            environment_id=environment_id,
            role=NetworkEnvironmentRole.owner,
            is_active=True,
            priority=100,
        )
        binding = await attach_service(
            network_node=node,
            service_package_id=service_package_id,
            service_id=service_id,
            host_id="kernel-environment-node",
            protocol_version="workspace-revision",
            service_name="aware-environment",
            endpoint_refs=["environment.ready.ensure_ready"],
            stream_endpoint_refs=[],
            host_version="1.0.0",
            supports_stream_events=False,
        )
    finally:
        reset_invocation_provider(token)

    assert updated is node
    assert node.environments[0].id == stable_network_node_environment_id(
        network_node_id=node_id,
        environment_id=environment_id,
    )
    assert binding.id == stable_network_node_service_id(
        network_node_id=node_id,
        service_package_id=service_package_id,
    )
    assert node.services == [binding]
    assert provider.constructor_calls == [
        {
            "orm_class": NetworkNodeEnvironment,
            "function_name": "create_via_network_node",
            "payload": {
                "network_node_id": node_id,
                "environment_id": environment_id,
                "role": NetworkEnvironmentRole.owner,
                "is_active": True,
                "priority": 100,
            },
        },
        {
            "orm_class": NetworkNodeService,
            "function_name": "build_via_network_node",
            "payload": {
                "network_node_id": node_id,
                "service_package_id": service_package_id,
                "service_id": service_id,
                "host_id": "kernel-environment-node",
                "protocol_version": "workspace-revision",
                "service_name": "aware-environment",
                "endpoint_refs": ["environment.ready.ensure_ready"],
                "stream_endpoint_refs": [],
                "host_version": "1.0.0",
                "supports_stream_events": False,
            },
        },
    ]


@pytest.mark.asyncio
async def test_network_child_constructors_do_not_require_legacy_runtime_context() -> None:
    assert not has_invocation_provider()
    node_id = uuid4()
    peer_id = uuid4()
    environment_id = uuid4()
    service_package_id = uuid4()
    service_id = uuid4()
    lane_branch_id = uuid4()
    lane_projection_hash = "sha256:network-lane"

    assoc = await create_via_network_node(
        network_node_id=node_id,
        environment_id=environment_id,
        role=NetworkEnvironmentRole.owner,
        is_active=True,
        priority=10,
    )
    binding = await build_via_network_node(
        network_node_id=node_id,
        service_package_id=service_package_id,
        service_id=service_id,
        host_id="kernel-environment-node",
        protocol_version="workspace-revision",
        service_name="aware-environment-service",
        endpoint_refs=["environment.ready.ensure_ready"],
        stream_endpoint_refs=[],
        host_version="1.0.0",
        supports_stream_events=False,
    )
    fanout = await create_via_network_node_peer(
        network_node_peer_id=peer_id,
        lane_branch_id=lane_branch_id,
        lane_projection_hash=lane_projection_hash,
        enabled=True,
        mode=NetworkFanoutMode.notify_pull,
    )

    assert isinstance(assoc, NetworkNodeEnvironment)
    assert assoc.id == stable_network_node_environment_id(
        network_node_id=node_id,
        environment_id=environment_id,
    )
    assert isinstance(binding, NetworkNodeService)
    assert binding.id == stable_network_node_service_id(
        network_node_id=node_id,
        service_package_id=service_package_id,
    )
    assert isinstance(fanout, NetworkNodePeerFanoutRule)
    assert fanout.id == stable_network_node_peer_fanout_rule_id(
        network_node_peer_id=peer_id,
        lane_branch_id=lane_branch_id,
        lane_projection_hash=lane_projection_hash,
    )


@pytest.mark.asyncio
async def test_network_node_attach_service_reuses_existing_committed_advertisement() -> None:
    node_id = stable_network_node_id(public_key="test-node-key")
    service_package_id = uuid4()
    service_id = uuid4()
    node = await register(
        public_key="test-node-key",
        hostname="127.0.0.1",
        port=8991,
    )

    provider = _RecordingInvocationProvider()
    token = set_invocation_provider(provider)
    try:
        binding = await attach_service(
            network_node=node,
            service_package_id=service_package_id,
            service_id=service_id,
            host_id="kernel-services-node",
            protocol_version="workspace-revision",
            service_name="aware-meta-service",
            endpoint_refs=["meta.graph.invoke_function"],
            stream_endpoint_refs=["meta.graph.events"],
            host_version="1.0.0",
            supports_stream_events=True,
        )
        updated = await attach_service(
            network_node=node,
            service_package_id=service_package_id,
            service_id=service_id,
            host_id="kernel-services-node",
            protocol_version="workspace-revision",
            service_name="aware-meta-service-v2",
            endpoint_refs=["meta.graph.invoke_function"],
            stream_endpoint_refs=["meta.graph.events"],
            host_version="1.0.1",
            supports_stream_events=True,
        )
    finally:
        reset_invocation_provider(token)

    assert updated is binding
    assert binding.id == stable_network_node_service_id(
        network_node_id=node_id,
        service_package_id=service_package_id,
    )
    assert binding.service_package_id == service_package_id
    assert binding.service_id == service_id
    assert binding.service_name == "aware-meta-service"
    assert binding.endpoint_refs == ["meta.graph.invoke_function"]
    assert binding.stream_endpoint_refs == ["meta.graph.events"]
    assert binding.host_id == "kernel-services-node"
    assert binding.host_version == "1.0.0"
    assert binding.protocol_version == "workspace-revision"
    assert binding.supports_stream_events is True
    assert len(provider.constructor_calls) == 1
