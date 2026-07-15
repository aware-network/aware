from ._experience_runtime_test_paths import EXPERIENCE_AWARE_ROOT


def _read(relative_path: str) -> str:
    return (EXPERIENCE_AWARE_ROOT / relative_path).read_text(encoding="utf-8")


def test_projection_experience_owns_dedicated_child_projection_portals() -> None:
    parent_projection = _read("projection_experience_projection.aware")

    expected_portals = {
        "projection_experience_graphs": "ProjectionExperienceGraph",
        "projection_experience_section_graph_bindings": (
            "ProjectionExperienceSectionGraphBinding"
        ),
        "projection_experience_layout_graph_bindings": (
            "ProjectionExperienceLayoutGraphBinding"
        ),
    }
    for relationship_name, target_projection in expected_portals.items():
        assert (
            "projection.ProjectionExperience::"
            f"{relationship_name} {target_projection}"
        ) in parent_projection

    assert (
        "ProjectionExperienceSectionGraphBinding::projection_experience_graph_identity"
        not in parent_projection
    )
    assert (
        "ProjectionExperienceLayoutGraphBinding::layout_config" not in parent_projection
    )


def test_dedicated_child_projections_do_not_embed_parent_collection_edges() -> None:
    child_projections = {
        "projection_experience_graph_projection.aware": (
            "projection_experience_graphs"
        ),
        "projection_experience_section_graph_binding_projection.aware": (
            "projection_experience_section_graph_bindings"
        ),
        "projection_experience_layout_graph_binding_projection.aware": (
            "projection_experience_layout_graph_bindings"
        ),
    }
    for relative_path, relationship_name in child_projections.items():
        source = _read(relative_path)
        assert "root projection.ProjectionExperience" in source
        assert f"ProjectionExperience::{relationship_name}" not in source, relative_path
