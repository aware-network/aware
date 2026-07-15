from __future__ import annotations

from aware_experience.compiler.models import (
    ExperienceGraphEdgeOwnership,
    ExperienceGraphOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionNodeIdentityOwnership,
    ExperienceProjectionNodeOwnership,
)
from aware_experience.graph.ontology import (
    build_graph_ontology_plans,
    decode_graph_ontology_plan_payload,
    encode_graph_ontology_plan_payload,
)


def _projection_ownership() -> tuple[ExperienceProjectionExperienceOwnership, ...]:
    return (
        ExperienceProjectionExperienceOwnership(
            name="home_story",
            projection="Home",
            source_path="experiences.aware",
            branches=(),
            observables=(),
            nodes=(
                ExperienceProjectionNodeOwnership(
                    name="home.Home",
                    node_ref="home.Home",
                    source_path="experiences.aware",
                    params=(),
                    identities=(
                        ExperienceProjectionNodeIdentityOwnership(
                            key="home", source_path="experiences.aware"
                        ),
                    ),
                ),
                ExperienceProjectionNodeOwnership(
                    name="home.Home::doors",
                    node_ref="home.Home::doors",
                    source_path="experiences.aware",
                    params=(),
                    identities=(
                        ExperienceProjectionNodeIdentityOwnership(
                            key="front_door", source_path="experiences.aware"
                        ),
                    ),
                ),
                ExperienceProjectionNodeOwnership(
                    name="home.Home::tvs",
                    node_ref="home.Home::tvs",
                    source_path="experiences.aware",
                    params=(),
                    identities=(
                        ExperienceProjectionNodeIdentityOwnership(
                            key="living_room_tv",
                            source_path="experiences.aware",
                        ),
                    ),
                ),
                ExperienceProjectionNodeOwnership(
                    name="home.Tv::channels",
                    node_ref="home.Tv::channels",
                    source_path="experiences.aware",
                    params=(),
                    identities=(
                        ExperienceProjectionNodeIdentityOwnership(
                            key="news_channel", source_path="experiences.aware"
                        ),
                    ),
                ),
            ),
        ),
    )


def test_build_graph_ontology_plans_maps_tree_to_deterministic_keys() -> None:
    graph_ownership = (
        ExperienceGraphOwnership(
            name="home_default",
            experience="home_story",
            source_path="graphs.aware",
            root="home",
            edges=(
                ExperienceGraphEdgeOwnership(
                    parent="home",
                    child="front_door",
                    source_path="graphs.aware",
                ),
                ExperienceGraphEdgeOwnership(
                    parent="home",
                    child="living_room_tv",
                    source_path="graphs.aware",
                ),
                ExperienceGraphEdgeOwnership(
                    parent="living_room_tv",
                    child="news_channel",
                    source_path="graphs.aware",
                ),
            ),
        ),
    )
    plans = build_graph_ontology_plans(
        projection_experience_ownership=_projection_ownership(),
        graph_ownership=graph_ownership,
    )
    assert len(plans) == 1
    plan = plans[0]
    assert plan.graph.graph_name == "home_default"
    assert plan.graph.root_ref == "home"
    assert {item.ref: item.key for item in plan.identities} == {
        "home": "home",
        "front_door": "home.front_door",
        "living_room_tv": "home.living_room_tv",
        "news_channel": "home.living_room_tv.news_channel",
    }
    assert {
        (edge.parent_ref, edge.child_ref, edge.key) for edge in plan.node_identity_edges
    } == {
        ("home", "front_door", "home.front_door"),
        ("home", "living_room_tv", "home.living_room_tv"),
        (
            "living_room_tv",
            "news_channel",
            "home.living_room_tv.news_channel",
        ),
    }
    assert {
        (edge.parent_ref, edge.child_ref, edge.key)
        for edge in plan.graph_identity_edges
    } == {
        ("home", "front_door", "home.front_door"),
        ("home", "living_room_tv", "home.living_room_tv"),
        (
            "living_room_tv",
            "news_channel",
            "home.living_room_tv.news_channel",
        ),
    }


def test_graph_ontology_payload_roundtrip_decodes_typed_contract() -> None:
    graph_ownership = (
        ExperienceGraphOwnership(
            name="home_default",
            experience="home_story",
            source_path="graphs.aware",
            root="home",
            edges=(
                ExperienceGraphEdgeOwnership(
                    parent="home",
                    child="front_door",
                    source_path="graphs.aware",
                ),
            ),
        ),
    )
    plans = build_graph_ontology_plans(
        projection_experience_ownership=_projection_ownership(),
        graph_ownership=graph_ownership,
    )

    payload = encode_graph_ontology_plan_payload(plans=plans)
    decoded = decode_graph_ontology_plan_payload(payload=payload)

    assert decoded == plans


def test_build_graph_ontology_plans_fails_on_unknown_node_identity_ref() -> None:
    graph_ownership = (
        ExperienceGraphOwnership(
            name="home_default",
            experience="home_story",
            source_path="graphs.aware",
            root="home",
            edges=(
                ExperienceGraphEdgeOwnership(
                    parent="home",
                    child="unknown_channel",
                    source_path="graphs.aware",
                ),
            ),
        ),
    )
    try:
        _ = build_graph_ontology_plans(
            projection_experience_ownership=_projection_ownership(),
            graph_ownership=graph_ownership,
        )
    except ValueError as exc:
        assert "known node identity ref" in str(exc)
        assert "unknown_channel" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError(
            "Expected graph ontology mapping failure for unknown node identity ref"
        )


def test_decode_graph_ontology_payload_fails_on_unknown_edge_ref() -> None:
    payload = [
        {
            "graph": {
                "name": "home_default",
                "experience": "home_story",
                "root_ref": "home",
                "source_path": "graphs.aware",
            },
            "identities": [
                {
                    "ref": "home",
                    "node_name": "home.Home",
                    "identity_key": "home",
                    "key": "home",
                    "is_root": True,
                    "source_path": "graphs.aware",
                }
            ],
            "node_identity_edges": [
                {
                    "parent_ref": "home",
                    "child_ref": "front_door",
                    "parent_key": "home",
                    "child_key": "home.front_door",
                    "key": "home.front_door",
                    "source_path": "graphs.aware",
                }
            ],
            "graph_identity_edges": [],
        }
    ]

    try:
        _ = decode_graph_ontology_plan_payload(payload=payload)
    except ValueError as exc:
        assert "refs must exist in graph identities" in str(exc)
        assert "front_door" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError(
            "Expected graph ontology decode failure for unknown edge ref"
        )
