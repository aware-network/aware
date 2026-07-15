from __future__ import annotations

from pathlib import Path

_CONTENT_ROOT = Path(__file__).resolve().parents[1] / "structure" / "aware"
_PACKAGE_ROOT = _CONTENT_ROOT / "package"


def test_content_package_sources_are_content_owned_and_generic() -> None:
    sources = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_PACKAGE_ROOT.glob("content_package*.aware"))
    }

    assert set(sources) == {
        "content_package.aware",
        "content_package_artifact.aware",
        "content_package_content.aware",
        "content_package_enums.aware",
        "content_package_projection.aware",
    }

    combined = "\n".join(sources.values())
    assert "class ContentPackage" in sources["content_package.aware"]
    assert "edge ContentPackageContent" in sources["content_package_content.aware"]
    assert "class ContentPackageArtifact" in sources["content_package_artifact.aware"]
    assert "class ContentPackageArtifactRef : inline_value" in sources[
        "content_package_artifact.aware"
    ]
    assert "projection ContentPackage is_branchable" in sources[
        "content_package_projection.aware"
    ]
    assert "aware_content.package.ContentPackage" in sources[
        "content_package_projection.aware"
    ]
    assert "aware_content.package.ContentPackageContent::content Content" in sources[
        "content_package_projection.aware"
    ]

    forbidden_tokens = (
        "aware_code",
        "aware_workspace",
        "workspace.",
        "GoalContent",
        "Goal service",
        "aware_goal",
    )
    for token in forbidden_tokens:
        assert token not in combined


def test_content_package_classes_stay_one_class_per_file() -> None:
    class_lines_by_file = {
        path.name: [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith(("class ", "edge ", "enum ", "projection "))
        ]
        for path in sorted(_PACKAGE_ROOT.glob("content_package*.aware"))
    }

    assert class_lines_by_file == {
        "content_package.aware": ["class ContentPackage {"],
        "content_package_artifact.aware": [
            "class ContentPackageArtifact {",
            "class ContentPackageArtifactRef : inline_value {",
        ],
        "content_package_content.aware": ["edge ContentPackageContent {"],
        "content_package_enums.aware": ["enum ContentPackageArtifactStatus {"],
        "content_package_projection.aware": [
            "projection ContentPackage is_branchable {"
        ],
    }
