from ._experience_runtime_test_paths import EXPERIENCE_AWARE_ROOT


def _read(relative_path: str) -> str:
    return (EXPERIENCE_AWARE_ROOT / relative_path).read_text(encoding="utf-8")


def test_projection_experience_owns_oigi_child_portal() -> None:
    parent_projection = _read("projection_experience_projection.aware")
    child_projection = _read("projection_experience_oigi_projection.aware")

    portal = (
        "projection.ProjectionExperience::projection_experience_oigis "
        "ProjectionExperienceOIGI"
    )
    assert portal in parent_projection
    assert "root projection.ProjectionExperienceOIGI" in child_projection
    assert "ProjectionExperience::projection_experience_oigis" not in child_projection
    assert (
        "projection.ProjectionExperienceOIGI::object_instance_graph_identity "
        "aware_meta.ObjectInstanceGraphIdentity"
    ) in child_projection
