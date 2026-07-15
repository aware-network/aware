from __future__ import annotations

import pytest

from aware_experience.program.language import (
    ProgramCompileError,
    ProgramConfigReferenceCatalog,
    compile_program_config_apply_calls,
    compile_program_config_plans,
)


def _home_story_contract_program() -> str:
    return """\
program home_story_scene_config(
    channel_number Int
) {
    port main home_story {
        node home home.Home.home
        node door home.Home::doors.front_door
        node tv home.Home::tvs.living_room_tv
        node channel home.Tv::channels.news_channel
    }
}

program home_story_scene impl home_story_scene_config {
    bind main home_story.entertainment.home
}
"""


def test_home_story_program_port_node_contract_shapes() -> None:
    source = _home_story_contract_program()
    plans = compile_program_config_plans(source)
    assert len(plans) == 1

    plan = plans[0]
    assert len(plan.ports) == 1
    port = plan.ports[0]
    assert port.key == "main"
    assert port.projection == "home_story"

    nodes_by_key = {node.key: node for node in port.projection_node_identities}
    assert set(nodes_by_key.keys()) == {"home", "door", "tv", "channel"}

    home = nodes_by_key["home"]
    assert home.node == "home.Home"
    assert home.identity == "home"
    assert home.args == ()

    door = nodes_by_key["door"]
    assert door.node == "home.Home::doors"
    assert door.identity == "front_door"
    assert door.args == ()

    tv = nodes_by_key["tv"]
    assert tv.node == "home.Home::tvs"
    assert tv.identity == "living_room_tv"
    assert tv.args == ()

    channel = nodes_by_key["channel"]
    assert channel.node == "home.Tv::channels"
    assert channel.identity == "news_channel"
    assert channel.args == ()

    for node in port.projection_node_identities:
        has_identity = bool((node.identity or "").strip())
        has_keys = bool(node.args)
        assert has_identity != has_keys


def test_home_story_program_port_node_contract_rejects_bare_node_ref() -> None:
    source = _home_story_contract_program()
    invalid = source.replace(
        "        node door home.Home::doors.front_door\n",
        "        node door home.Home::doors\n",
    )

    with pytest.raises(
        ProgramCompileError,
        match=r"port node ref must use `<opg-node>\.<identity>` or provide resolver keys via `<opg-node>\(<keys\.\.\.>\)`",
    ):
        _ = compile_program_config_plans(invalid)


def test_home_story_program_apply_calls_require_projection_node_identity_resolution() -> (
    None
):
    source = _home_story_contract_program()
    plan = compile_program_config_plans(source)[0]

    calls = compile_program_config_apply_calls(
        plan,
        references=ProgramConfigReferenceCatalog(
            attribute_config_ids={
                "program.input.channel_number": "attr-channel-number",
            },
            projection_ids={
                "program.port.main.projection": "projection-id",
            },
            projection_node_ids={
                "program.port.main.projection_node.home": "projection-node-home-struct",
                "program.port.main.projection_node.door": "projection-node-door-struct",
                "program.port.main.projection_node.tv": "projection-node-tv-struct",
                "program.port.main.projection_node.channel": "projection-node-channel-struct",
            },
            projection_node_identity_ids={
                "program.port.main.projection_node_identity.home": "projection-node-home-id",
                "program.port.main.projection_node_identity.door": "projection-node-door-id",
                "program.port.main.projection_node_identity.tv": "projection-node-tv-id",
                "program.port.main.projection_node_identity.channel": "projection-node-channel-id",
            },
        ),
        strict_resolution=True,
    )

    identity_calls = [call for call in calls if call.function_name == "create_identity"]
    assert len(identity_calls) == 4

    resolved_by_alias = {
        str(call.args[1]): str(call.args[0]) for call in identity_calls
    }
    assert resolved_by_alias == {
        "home": "projection-node-home-id",
        "door": "projection-node-door-id",
        "tv": "projection-node-tv-id",
        "channel": "projection-node-channel-id",
    }


def test_home_story_program_config_surface_rejects_executable_without_impl() -> None:
    with pytest.raises(
        ProgramCompileError,
        match=r"config declarations cannot include executable statements",
    ):
        _ = compile_program_config_plans(
            """\
program home_story_scene_config(
    channel_number Int
) {
    port main home_story {
        node home home.Home.home
    }
    bind main home_story.entertainment.home
}
""",
            require_config_contract_surface=True,
        )


def test_home_story_program_config_surface_allows_contract_only_without_impl() -> None:
    plans = compile_program_config_plans(
        """\
program home_story_scene_config(
    channel_number Int
) {
    actor ai_assistant assistant
    port main home_story {
        node home home.Home.home
        node channel home.Tv::channels(number=channel_number)
    }
}
""",
        require_config_contract_surface=True,
    )
    assert len(plans) == 1
    plan = plans[0]
    assert plan.key == "home_story_scene_config"
    assert len(plan.actors) == 1
    assert plan.actors[0].key == "ai_assistant"
    assert len(plan.ports) == 1
    assert plan.ports[0].key == "main"
    assert len(plan.instructions) == 1
    assert plan.instructions[0].type == "input"
