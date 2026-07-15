from __future__ import annotations

from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest

from _interface_runtime_test_paths import REPO_ROOT
from _meta_proof_support import (
    build_interface_meta_proof_runtime,
    isolated_meta_aware_root,
    rehydrate_lane_root_from_head,
)
from aware_interface_ontology.stable_ids import (
    stable_interface_session_experience_session_id,
)


@pytest.mark.asyncio
async def test_interface_session_public_mount_supports_many_experience_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_interface.handlers.impl.interface import (
        interface_session as interface_session_handler,
    )
    from aware_interface_ontology.interface.interface_enums import (
        InterfaceSessionState,
    )
    from aware_interface_ontology.interface.interface_session import (
        InterfaceSession,
    )
    from aware_interface_ontology.interface.interface_session_experience_session import (
        InterfaceSessionExperienceSession,
    )

    interface_session_id = uuid4()
    session = InterfaceSession(
        id=interface_session_id,
        interface_id=uuid4(),
        identity_session_id=uuid4(),
        experience_sessions=[],
        name="shared-home",
        state=InterfaceSessionState.active,
    )

    async def _build(*, experience_session_id: UUID, **_kwargs: object) -> InterfaceSessionExperienceSession:
        return InterfaceSessionExperienceSession(
            id=stable_interface_session_experience_session_id(
                interface_session_id=interface_session_id,
                experience_session_id=experience_session_id,
            ),
            interface_session_id=interface_session_id,
            experience_session_id=experience_session_id,
            status="active",
        )

    monkeypatch.setattr(
        InterfaceSessionExperienceSession,
        "build_via_interface_session",
        _build,
    )
    first_experience_session_id = uuid4()
    second_experience_session_id = uuid4()
    first = await interface_session_handler.mount_experience_session(
        interface_session=session,
        experience_session_id=first_experience_session_id,
    )
    repeated = await interface_session_handler.mount_experience_session(
        interface_session=session,
        experience_session_id=first_experience_session_id,
    )
    second = await interface_session_handler.mount_experience_session(
        interface_session=session,
        experience_session_id=second_experience_session_id,
    )

    assert first is repeated
    assert first.id != second.id
    assert [mount.experience_session_id for mount in session.experience_sessions] == [
        first_experience_session_id,
        second_experience_session_id,
    ]


@pytest.mark.asyncio
async def test_interface_experience_session_portals_commit_and_rehydrate(
    tmp_path: Path,
) -> None:
    with isolated_meta_aware_root(tmp_path / "aware_root") as aware_root:
        runtime = build_interface_meta_proof_runtime(
            repo_root=REPO_ROOT,
            aware_root=aware_root,
        )

        from aware_interface_ontology.interface.interface_session import (
            InterfaceSession,
        )
        from aware_interface_ontology.interface.interface_session_experience_session import (
            InterfaceSessionExperienceSession,
        )

        interface_session_id = uuid4()
        actor_id = uuid4()
        experience_session_ids = (uuid4(), uuid4())
        committed_mounts: list[InterfaceSessionExperienceSession] = []
        for index, experience_session_id in enumerate(experience_session_ids):
            mount_id = stable_interface_session_experience_session_id(
                interface_session_id=interface_session_id,
                experience_session_id=experience_session_id,
            )
            lane = runtime.bind(
                branch_id=mount_id,
                projection="InterfaceSessionExperienceSession",
                actor_id=actor_id,
            )
            with lane.activate(commit=True, publish=False):
                mounted = await InterfaceSessionExperienceSession.build_via_interface_session(
                    interface_session_id=interface_session_id,
                    experience_session_id=experience_session_id,
                    metadata_json={"order": index},
                )
                repeated = await InterfaceSessionExperienceSession.build_via_interface_session(
                    interface_session_id=interface_session_id,
                    experience_session_id=experience_session_id,
                    metadata_json={"order": index},
                )
            assert mounted.id == repeated.id == mount_id
            committed_mounts.append(
                await rehydrate_lane_root_from_head(
                    runtime=runtime,
                    aware_root=aware_root,
                    branch_id=mount_id,
                    projection_name="InterfaceSessionExperienceSession",
                    root_id=mount_id,
                    root_type=InterfaceSessionExperienceSession,
                )
            )

        assert {mount.experience_session_id for mount in committed_mounts} == set(experience_session_ids)
        assert all(mount.interface_session_id == interface_session_id for mount in committed_mounts)
        assert [cast(dict, mount.metadata_json)["order"] for mount in committed_mounts] == [
            0,
            1,
        ]
        assert "active_experience_session_id" not in InterfaceSession.model_fields


def test_interface_experience_session_mount_identity_is_pair_scoped() -> None:
    interface_session_id = uuid4()
    first = stable_interface_session_experience_session_id(
        interface_session_id=interface_session_id,
        experience_session_id=uuid4(),
    )
    second = stable_interface_session_experience_session_id(
        interface_session_id=interface_session_id,
        experience_session_id=uuid4(),
    )
    assert first != second
