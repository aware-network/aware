from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceExperienceSessionMountResponse,
    InterfaceSessionDescribeResponse,
    InterfaceSessionStartResponse,
    InterfaceSessionView,
)
from aware_interface_sdk import InterfaceSdkClient


class _StartCapability:
    def __init__(self, response: InterfaceSessionStartResponse) -> None:
        self.response = response
        self.request = None

    async def start_interface_session(self, request):  # type: ignore[no-untyped-def]
        self.request = request
        return self.response


class _MountCapability:
    def __init__(self, response: InterfaceExperienceSessionMountResponse) -> None:
        self.response = response
        self.request = None

    async def mount_interface_experience_session(
        self, request
    ):  # type: ignore[no-untyped-def]
        self.request = request
        return self.response


class _DescribeCapability:
    def __init__(self, response: InterfaceSessionDescribeResponse) -> None:
        self.response = response
        self.request = None

    async def describe_interface_session(self, request):  # type: ignore[no-untyped-def]
        self.request = request
        return self.response


@pytest.mark.asyncio
async def test_interface_sdk_starts_commit_backed_session_through_api() -> None:
    interface_id = uuid4()
    identity_session_id = uuid4()
    interface_session_id = uuid4()
    commit_id = uuid4()
    capability = _StartCapability(
        InterfaceSessionStartResponse(
            interface_session_id=interface_session_id,
            interface_id=interface_id,
            identity_session_id=identity_session_id,
            name="shared-home",
            state="active",
            object_instance_graph_commit_id=commit_id,
            graph_hash_post="sha256:session",
        )
    )
    client = InterfaceSdkClient.from_service_api(
        SimpleNamespace(
            interface=SimpleNamespace(start_interface_session=capability)
        )  # type: ignore[arg-type]
    )

    response = await client.start_interface_session(
        interface_id=interface_id,
        identity_session_id=identity_session_id,
        name="shared-home",
    )

    assert response.interface_session_id == interface_session_id
    assert response.object_instance_graph_commit_id == commit_id
    assert capability.request.interface_id == interface_id
    assert capability.request.identity_session_id == identity_session_id
    assert capability.request.name == "shared-home"


@pytest.mark.asyncio
async def test_interface_sdk_mounts_committed_experience_session_portal() -> None:
    interface_session_id = uuid4()
    experience_session_id = uuid4()
    mount_id = uuid4()
    commit_id = uuid4()
    capability = _MountCapability(
        InterfaceExperienceSessionMountResponse(
            interface_session_experience_session_id=mount_id,
            interface_session_id=interface_session_id,
            experience_session_id=experience_session_id,
            status="active",
            metadata_json={"source": "shared-door"},
            object_instance_graph_commit_id=commit_id,
            graph_hash_post="sha256:mount",
        )
    )
    client = InterfaceSdkClient.from_service_api(
        SimpleNamespace(
            interface=SimpleNamespace(mount_interface_experience_session=capability)
        )  # type: ignore[arg-type]
    )

    response = await client.mount_interface_experience_session(
        interface_session_id=interface_session_id,
        experience_session_id=experience_session_id,
        metadata_json={"source": "shared-door"},
    )

    assert response.interface_session_experience_session_id == mount_id
    assert response.object_instance_graph_commit_id == commit_id
    assert capability.request.interface_session_id == interface_session_id
    assert capability.request.experience_session_id == experience_session_id
    assert capability.request.status == "active"
    assert capability.request.metadata_json == {"source": "shared-door"}


@pytest.mark.asyncio
async def test_interface_sdk_describes_committed_session_projection() -> None:
    interface_session_id = uuid4()
    identity_session_id = uuid4()
    capability = _DescribeCapability(
        InterfaceSessionDescribeResponse(
            status="found",
            session=InterfaceSessionView(
                interface_session_id=interface_session_id,
                interface_id=uuid4(),
                identity_session_id=identity_session_id,
                name="shared-home",
                state="active",
                domain_commit_id=uuid4(),
            ),
        )
    )
    client = InterfaceSdkClient.from_service_api(
        SimpleNamespace(
            interface=SimpleNamespace(describe_interface_session=capability)
        )  # type: ignore[arg-type]
    )

    response = await client.describe_interface_session(
        interface_session_id=interface_session_id,
    )

    assert response.status == "found"
    assert response.session is not None
    assert response.session.identity_session_id == identity_session_id
    assert capability.request.interface_session_id == interface_session_id
