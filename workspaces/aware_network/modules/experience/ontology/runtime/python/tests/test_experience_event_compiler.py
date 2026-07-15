from __future__ import annotations

from pathlib import Path

from aware_experience.event.compiler import load_event_ownership_from_sources


def test_event_compiler_parses_experience_owned_event_nodes(tmp_path: Path) -> None:
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "home_events.aware").write_text(
        "\n".join(
            [
                'event HomeDoorStateChanged name "home.door.state.changed" renderer "home.door.state.changed" title "Door Changed" description "Door state changed." {',
                "  bind home home.Door update is_locked",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ownership = load_event_ownership_from_sources(
        package_root=tmp_path,
        source_files=(Path("events/home_events.aware"),),
        package_name="home_story",
        fqn_prefix="home_story",
    )

    assert len(ownership) == 1
    event = ownership[0]
    assert event.symbol == "HomeDoorStateChanged"
    assert event.event_name == "home.door.state.changed"
    assert event.renderer_key == "home.door.state.changed"
    assert event.title == "Door Changed"
    assert event.description == "Door state changed."
    assert event.package_name == "home_story"
    assert event.fqn_prefix == "home_story"
    assert event.bindings[0].projection == "home"
    assert event.bindings[0].type_ref == "home.Door"
    assert event.bindings[0].operation == "update"
    assert event.bindings[0].attribute == "is_locked"


def test_event_compiler_does_not_depend_on_code_section_event_adapter() -> None:
    source = Path("workspaces/aware_network/modules/experience/ontology/runtime/python/aware_experience/event/compiler.py").read_text(
        encoding="utf-8"
    )

    assert "aware_grammar.adapters.event_adapter" not in source
    assert "CodeSectionEvent" not in source
    assert "CodeSectionType.event" not in source
