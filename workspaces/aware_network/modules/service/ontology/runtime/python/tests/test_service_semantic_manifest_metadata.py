from __future__ import annotations

from pathlib import Path

from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.semantic_manifest_metadata import (
    resolve_service_manifest_semantic_package_metadata,
)
from aware_service_ontology.stable_ids import stable_service_config_id


def _write_service_toml(root: Path) -> Path:
    toml_path = root / "aware.service.toml"
    toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "home-story-service"',
                'fqn_prefix = "aware_home_story_service"',
                "",
                "[build]",
                'sources_dir = "bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "service_ontology"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return toml_path


def _write_service_source(root: Path) -> None:
    bindings = root / "bindings"
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / "home.services.aware").write_text(
        "\n".join(
            [
                "service home_story {",
                "    api home_story_api;",
                "",
                "    operation status {",
                "        endpoint home_story_api.status.status;",
                "        receipt read_model;",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_service_semantic_manifest_metadata_publishes_service_config_root(
    tmp_path: Path,
) -> None:
    toml_path = _write_service_toml(tmp_path)
    _write_service_source(tmp_path)

    metadata = resolve_service_manifest_semantic_package_metadata(
        workspace_root=tmp_path,
        package_root=tmp_path,
        manifest_path=toml_path,
        manifest_spec=load_aware_service_toml_spec(toml_path=toml_path),
        descriptor=object(),
        metadata={},
    )

    expected_id = str(stable_service_config_id(name="home_story"))
    assert metadata["service_name"] == "home_story"
    assert metadata["service_names"] == ("home_story",)
    assert metadata["semantic_root_name"] == "home_story"
    assert metadata["semantic_root_id"] == expected_id
    assert metadata["semantic_root_ids"] == (expected_id,)
