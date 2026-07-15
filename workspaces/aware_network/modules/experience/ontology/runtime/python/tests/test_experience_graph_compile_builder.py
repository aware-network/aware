from __future__ import annotations

import json
from pathlib import Path

from aware_experience.compiler.builder import (
    build_experience_compile_plan,
    emit_experience_compile_plan_artifact,
)
from aware_experience.compiler.workspace import ExperienceWorkspace


def _write_experience_toml(*, root: Path) -> Path:
    content = "\n".join(
        [
            "aware_experience = 1",
            "",
            "[experience]",
            'package_name = "home_story"',
            'fqn_prefix = "home_story"',
            "",
            "[build]",
            'environment_handle = "kernel"',
            'sources_dir = "."',
            'include_paths = ["**/*.aware"]',
            "exclude_paths = []",
            "force_fresh_scan = true",
            "",
        ]
    )
    target = root / "aware.experience.toml"
    target.write_text(content, encoding="utf-8")
    return target


def _write_composition_truth(*, root: Path) -> Path:
    runtime_dir = (
        root
        / "modules"
        / "home"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
    )
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "environment.manifest.json").write_text(
        json.dumps(
            {
                "opg_index": {"file": "opg.index.json"},
                "bindings": {"file": "bindings.manifest.json"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_dir / "opg.index.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "model": "home",
                        "projection_hash": "h",
                        "file": "opgs/h.json",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    opg_dir = runtime_dir / "opgs"
    opg_dir.mkdir(parents=True, exist_ok=True)
    (opg_dir / "h.json").write_text(
        json.dumps(
            {
                "object_projection_graph_nodes": [
                    {"class_config_id": "class-home", "is_root": True},
                    {"class_config_id": "class-door"},
                    {"class_config_id": "class-tv"},
                    {"class_config_id": "class-channel"},
                ],
                "object_projection_graph_identity": {
                    "object_projection_graph_observables": [
                        {"observable_key": "security"},
                        {"observable_key": "entertainment"},
                    ]
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (runtime_dir / "bindings.manifest.json").write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "class_fqn": "aware_home_ontology.home.home.Home",
                        "canonical_class_config_id": "class-home",
                        "sql_mapping": [{"attribute_name": "id"}],
                    },
                    {
                        "class_fqn": "aware_home_ontology.home.home.Door",
                        "canonical_class_config_id": "class-door",
                        "sql_mapping": [{"attribute_name": "id"}],
                    },
                    {
                        "class_fqn": "aware_home_ontology.home.home.Tv",
                        "canonical_class_config_id": "class-tv",
                        "sql_mapping": [{"attribute_name": "id"}],
                    },
                    {
                        "class_fqn": "aware_home_ontology.home.home.TvChannel",
                        "canonical_class_config_id": "class-channel",
                        "sql_mapping": [{"attribute_name": "id"}],
                    },
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    composition_path = root / ".aware" / "tmp" / "environment.composition.manifest.json"
    composition_path.parent.mkdir(parents=True, exist_ok=True)
    composition_path.write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "module_id": "home",
                        "manifest_path": "modules/home/structure/ontology/.aware/environment/runtime/environment.manifest.json",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return composition_path


def _write_projection_experience_source(*, root: Path) -> None:
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "    observable security {",
                "        view door default api_view home.door {",
                '            """Door state view."""',
                "        }",
                "    }",
                "",
                "    observable entertainment {",
                "        view tv default api_view home.tv {",
                '            """Tv and channel state view."""',
                "        }",
                "    }",
                "",
                "    node home.Home {",
                "        id home",
                "    }",
                "",
                "    node home.Home::doors {",
                "        id front_door",
                "    }",
                "",
                "    node home.Home::tvs {",
                "        id living_room_tv",
                "    }",
                "",
                "    node home.Tv::channels {",
                "        id news_channel",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _build_plan_with_graph(
    *,
    root: Path,
    graph_source: str,
    projection_experience_source: str | None = None,
) -> None:
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(root=root)
    if projection_experience_source is None:
        _write_projection_experience_source(root=root)
    else:
        (root / "experiences.aware").write_text(
            projection_experience_source, encoding="utf-8"
        )
    (root / "graphs.aware").write_text(graph_source, encoding="utf-8")
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    _ = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )


def test_build_experience_compile_plan_graph_ownership_valid(tmp_path: Path) -> None:
    root = tmp_path
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(root=root)
    _write_projection_experience_source(root=root)
    (root / "graphs.aware").write_text(
        "\n".join(
            [
                "graph home_default on home_story {",
                "    root home",
                "    node home front_door",
                "    node home living_room_tv",
                "    node living_room_tv news_channel",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.graph_ownership) == 1
    graph = plan.graph_ownership[0]
    assert graph.name == "home_default"
    assert graph.experience == "home_story"
    assert graph.root == "home"
    assert {(edge.parent, edge.child) for edge in graph.edges} == {
        ("home", "front_door"),
        ("home", "living_room_tv"),
        ("living_room_tv", "news_channel"),
    }

    emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root,
        repo_root=root,
    )
    payload = json.loads(
        (root / "experience.compile_plan.json").read_text(encoding="utf-8")
    )
    graph_rows = payload.get("graph_ownership")
    assert isinstance(graph_rows, list)
    assert len(graph_rows) == 1
    assert graph_rows[0]["name"] == "home_default"
    assert graph_rows[0]["root"] == "home"
    graph_ontology_rows = payload.get("graph_ontology")
    assert isinstance(graph_ontology_rows, list)
    assert len(graph_ontology_rows) == 1
    graph_ontology = graph_ontology_rows[0]
    assert graph_ontology["graph"]["name"] == "home_default"
    assert graph_ontology["graph"]["root_ref"] == "home"
    identity_keys_by_ref = {
        row["ref"]: row["key"] for row in graph_ontology["identities"]
    }
    assert identity_keys_by_ref == {
        "home": "home",
        "front_door": "home.front_door",
        "living_room_tv": "home.living_room_tv",
        "news_channel": "home.living_room_tv.news_channel",
    }
    node_edges = graph_ontology["node_identity_edges"]
    graph_edges = graph_ontology["graph_identity_edges"]
    assert len(node_edges) == 3
    assert len(graph_edges) == 3


def test_build_experience_compile_plan_graph_ownership_fails_unknown_identity(
    tmp_path: Path,
) -> None:
    root = tmp_path
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(root=root)
    _write_projection_experience_source(root=root)
    (root / "graphs.aware").write_text(
        "\n".join(
            [
                "graph home_default on home_story {",
                "    root home",
                "    node home front_door",
                "    node home living_room_tv",
                "    node living_room_tv unknown_channel",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown node identity" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError("Expected graph compile failure for unknown node identity")


def test_build_experience_compile_plan_graph_ownership_fails_multiple_roots(
    tmp_path: Path,
) -> None:
    root = tmp_path
    try:
        _build_plan_with_graph(
            root=root,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    root front_door",
                    "    node home front_door",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        assert "multiple root declarations" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError("Expected graph compile failure for multiple roots")


def test_build_experience_compile_plan_graph_ownership_fails_duplicate_edge(
    tmp_path: Path,
) -> None:
    root = tmp_path
    try:
        _build_plan_with_graph(
            root=root,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    node home front_door",
                    "    node home front_door",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        assert "duplicate edge" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError("Expected graph compile failure for duplicate edge")


def test_build_experience_compile_plan_graph_ownership_fails_multiple_parents(
    tmp_path: Path,
) -> None:
    root = tmp_path
    try:
        _build_plan_with_graph(
            root=root,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    node home front_door",
                    "    node home living_room_tv",
                    "    node living_room_tv front_door",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        assert "multiple parents" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError(
            "Expected graph compile failure for child with multiple parents"
        )


def test_build_experience_compile_plan_graph_ownership_fails_root_as_child(
    tmp_path: Path,
) -> None:
    root = tmp_path
    try:
        _build_plan_with_graph(
            root=root,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    node front_door home",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        assert "cannot appear as a child edge target" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError(
            "Expected graph compile failure when root is child edge target"
        )


def test_build_experience_compile_plan_graph_ownership_fails_attempted_cycle(
    tmp_path: Path,
) -> None:
    root = tmp_path
    try:
        _build_plan_with_graph(
            root=root,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    node home front_door",
                    "    node front_door home",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        message = str(exc)
        assert (
            "cannot appear as a child edge target" in message
            or "multiple parents" in message
            or "contains a cycle" in message
        )
    else:  # pragma: no cover - fail closed
        raise AssertionError("Expected graph compile failure for cycle")


def test_build_experience_compile_plan_graph_ownership_fails_disconnected_node(
    tmp_path: Path,
) -> None:
    root = tmp_path
    try:
        _build_plan_with_graph(
            root=root,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    node home front_door",
                    "    node living_room_tv news_channel",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        assert "contains disconnected node identity" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError("Expected graph compile failure for disconnected node")


def test_build_experience_compile_plan_graph_ownership_scopes_refs_to_target_experience(
    tmp_path: Path,
) -> None:
    root = tmp_path
    projection_source = "\n".join(
        [
            "experience home_story on aware_home.home.Home {",
            "    node home.Home {",
            "        id home",
            "    }",
            "}",
            "",
            "experience home_alt on aware_home.home.Home {",
            "    node home.Home {",
            "        id alt_home",
            "    }",
            "}",
            "",
        ]
    )
    try:
        _build_plan_with_graph(
            root=root,
            projection_experience_source=projection_source,
            graph_source="\n".join(
                [
                    "graph home_default on home_story {",
                    "    root home",
                    "    node home alt_home",
                    "}",
                    "",
                ]
            ),
        )
    except ValueError as exc:
        assert "unknown node identity" in str(exc)
        assert "alt_home" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError(
            "Expected graph compile failure for cross-experience node identity reference"
        )
