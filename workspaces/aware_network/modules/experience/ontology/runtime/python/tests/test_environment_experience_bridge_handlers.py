from __future__ import annotations

from uuid import uuid4

import pytest

from aware_orm.session.session import Session


@pytest.mark.asyncio
async def test_environment_experience_bridge_constructors_use_new_parent_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.handlers.impl.action import (
        action_experience as action_handler,
    )
    from aware_experience.handlers.impl.environment import (
        environment_experience_process_config as process_handler,
    )
    from aware_experience.handlers.impl.environment import (
        environment_experience_program as program_handler,
    )
    from aware_experience.handlers.impl.environment import (
        environment_experience_program_apply as apply_handler,
    )
    from aware_experience.handlers.impl.environment import (
        environment_experience_thread_config as thread_handler,
    )
    from aware_experience.stable_ids import (
        stable_action_experience_id,
        stable_environment_experience_process_config_id,
        stable_environment_experience_program_apply_id,
        stable_environment_experience_program_id,
        stable_environment_experience_thread_config_id,
    )

    session = Session(branch_id=uuid4(), skip_db=True)
    for module in (
        action_handler,
        process_handler,
        thread_handler,
        program_handler,
        apply_handler,
    ):
        monkeypatch.setattr(module, "current_handler_session", lambda: session)

    environment_experience_profile_config_id = uuid4()
    process_config_id = uuid4()
    thread_config_id = uuid4()
    program_config_id = uuid4()
    action_config_id = uuid4()

    process_bridge = await process_handler.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        process_config_id=process_config_id,
        key="ops",
        title="Ops",
        position=1,
    )
    assert process_bridge.id == stable_environment_experience_process_config_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        process_config_id=process_config_id,
        key="ops",
    )
    assert process_bridge.process_config_id == process_config_id

    thread_bridge = (
        await thread_handler.build_via_environment_experience_process_config(
            environment_experience_process_config_id=process_bridge.id,
            thread_config_id=thread_config_id,
            key="ops.main",
            title="Ops Main",
            position=0,
        )
    )
    assert thread_bridge.id == stable_environment_experience_thread_config_id(
        environment_experience_process_config_id=process_bridge.id,
        thread_config_id=thread_config_id,
        key="ops.main",
    )
    assert thread_bridge.thread_config_id == thread_config_id

    program = await program_handler.build_via_environment_experience_thread_config(
        environment_experience_thread_config_id=thread_bridge.id,
        program_config_id=program_config_id,
    )
    assert program.id == stable_environment_experience_program_id(
        environment_experience_thread_config_id=thread_bridge.id,
        program_config_id=program_config_id,
    )

    program_apply = await apply_handler.build_via_environment_experience_thread_config(
        environment_experience_thread_config_id=thread_bridge.id,
        program_config_id=program_config_id,
        key="bootstrap",
    )
    assert program_apply.id == stable_environment_experience_program_apply_id(
        environment_experience_thread_config_id=thread_bridge.id,
        key="bootstrap",
    )
    assert program_apply.program_config_id == program_config_id

    action = await action_handler.build(action_config_id=action_config_id)
    assert action.id == stable_action_experience_id(action_config_id=action_config_id)
    assert action.action_config_id == action_config_id
    assert not hasattr(action, "thread_config_program_config_graph_id")


@pytest.mark.asyncio
async def test_environment_experience_profile_update_title_replaces_and_clears_only_title() -> None:
    from aware_experience.handlers._generated.meta_handlers import (
        AWARE_META_GRAPH_INVOCATION_HANDLERS,
    )
    from aware_experience.handlers.impl.environment import (
        environment_experience_profile_config as profile_config_handler,
    )
    from aware_experience_ontology.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )

    profile_config = EnvironmentExperienceProfileConfig(
        id=uuid4(),
        environment_experience_id=uuid4(),
        environment_profile_config_id=uuid4(),
        key="os.default",
        title="Home Story OS",
        description="Profile description",
        narrative="Profile narrative",
    )
    assert hasattr(profile_config, "update_title")
    assert any(
        key.owner_class_name == "EnvironmentExperienceProfileConfig"
        and key.function_name == "update_title"
        for key in AWARE_META_GRAPH_INVOCATION_HANDLERS
    )

    await profile_config_handler.update_title(
        environment_experience_profile_config=profile_config,
        title="Aware Home OS",
    )
    assert profile_config.title == "Aware Home OS"
    assert profile_config.description == "Profile description"
    assert profile_config.narrative == "Profile narrative"
    assert profile_config.key == "os.default"

    await profile_config_handler.update_title(
        environment_experience_profile_config=profile_config,
        title=None,
    )
    assert profile_config.title is None
    assert profile_config.description == "Profile description"
    assert profile_config.narrative == "Profile narrative"
    assert profile_config.key == "os.default"


@pytest.mark.asyncio
async def test_environment_experience_profile_add_process_config_attaches_direct_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.handlers.impl.environment import (
        environment_experience_profile_config as profile_config_handler,
    )
    from aware_experience.stable_ids import (
        stable_environment_experience_process_config_id,
    )
    from aware_experience_ontology.environment.environment_experience_process_config import (
        EnvironmentExperienceProcessConfig,
    )
    from aware_experience_ontology.environment.environment_experience_profile_config import (
        EnvironmentExperienceProfileConfig,
    )

    environment_experience_profile_config_id = uuid4()
    process_config_id = uuid4()
    process_bridge_id = stable_environment_experience_process_config_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        process_config_id=process_config_id,
        key="control",
    )
    created = EnvironmentExperienceProcessConfig(
        id=process_bridge_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        process_config_id=process_config_id,
        key="control",
        title="Control",
        description="Control process",
        position=0,
        narrative="Control narrative",
        intent="Control intent",
    )
    calls: list[dict[str, object]] = []

    async def _build_process_config(
        **kwargs: object,
    ) -> EnvironmentExperienceProcessConfig:
        calls.append(dict(kwargs))
        return created

    monkeypatch.setattr(
        profile_config_handler.EnvironmentExperienceProcessConfig,
        "build_via_environment_experience_profile_config",
        staticmethod(_build_process_config),
    )
    profile_config = EnvironmentExperienceProfileConfig(
        id=environment_experience_profile_config_id,
        environment_experience_id=uuid4(),
        environment_profile_config_id=uuid4(),
        key="os.default",
    )

    first = await profile_config_handler.add_process_config(
        environment_experience_profile_config=profile_config,
        process_config_id=process_config_id,
        key=" control ",
        title="Control",
        description="Control process",
        position=0,
        narrative="Control narrative",
        intent="Control intent",
    )
    second = await profile_config_handler.add_process_config(
        environment_experience_profile_config=profile_config,
        process_config_id=process_config_id,
        key="control",
        title="Control",
        description="Control process",
        position=0,
        narrative="Control narrative",
        intent="Control intent",
    )

    assert first is created
    assert second is created
    assert profile_config.process_configs == [created]
    assert calls[0] == {
        "environment_experience_profile_config_id": environment_experience_profile_config_id,
        "process_config_id": process_config_id,
        "key": "control",
        "title": "Control",
        "description": "Control process",
        "position": 0,
        "narrative": "Control narrative",
        "intent": "Control intent",
    }


@pytest.mark.asyncio
async def test_environment_experience_profile_identity_uses_environment_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.handlers.impl.environment import (
        environment_experience_profile as profile_handler,
    )
    from aware_experience.stable_ids import stable_environment_experience_profile_id

    session = Session(branch_id=uuid4(), skip_db=True)
    monkeypatch.setattr(profile_handler, "current_handler_session", lambda: session)

    environment_experience_id = uuid4()
    profile_config_id = uuid4()
    environment_profile_id = uuid4()
    other_environment_profile_id = uuid4()

    profile = await profile_handler.build_via_environment_experience(
        environment_experience_id=environment_experience_id,
        profile_config_id=profile_config_id,
        environment_profile_id=environment_profile_id,
        title="Default",
    )

    assert profile.id == stable_environment_experience_profile_id(
        environment_experience_id=environment_experience_id,
        profile_config_id=profile_config_id,
        environment_profile_id=environment_profile_id,
    )
    assert profile.id != stable_environment_experience_profile_id(
        environment_experience_id=environment_experience_id,
        profile_config_id=profile_config_id,
        environment_profile_id=other_environment_profile_id,
    )
    assert profile.environment_profile_id == environment_profile_id
