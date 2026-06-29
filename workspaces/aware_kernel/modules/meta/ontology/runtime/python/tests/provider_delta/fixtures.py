from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_workspace.features.semantic_materialization.delta_contract import (
    WorkspaceSemanticMaterializationProviderDeltaRequest,
)


def provider_delta_uuid(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware:test:meta-provider-delta:{key}")


def write_meta_delta_fixture(workspace_root: Path) -> Path:
    manifest_path = workspace_root / "aware.toml"
    _write(
        manifest_path,
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
                "[build.namespace]",
                '"home/**/*.aware" = "default.home"',
                "",
            ]
        ),
    )
    _write(
        workspace_root / "aware" / "home" / "model.aware",
        "\n".join(
            [
                "enum RoomState {",
                "    ready",
                "    offline",
                "}",
                "",
                "class Door {",
                "    label String",
                "}",
                "",
                "class Room {",
                "    name String",
                "    state RoomState?",
                "    doors Door[]",
                "",
                "    fn create construct (",
                "        name String key",
                "    ) -> Room {",
                '        """',
                "        Create deterministic room.",
                '        """',
                "    }",
                "}",
                "",
            ]
        ),
    )
    return manifest_path


def provider_delta_request(
    *,
    manifest_path: Path,
    change_kind: str = "update",
    include_baseline_refs: bool = False,
    include_code_package_delta: bool = True,
    include_code_delta_content: bool = True,
    code_delta_content_text: str | None = None,
) -> WorkspaceSemanticMaterializationProviderDeltaRequest:
    source_relative_path = "aware/home/model.aware"
    source_text = (
        code_delta_content_text
        if code_delta_content_text is not None
        else (manifest_path.parent / source_relative_path).read_text(encoding="utf-8")
    )
    payload: dict[str, object] = {
        "package": {
            "package_name": "demo-ontology",
            "workspace_manifest_kind": "aware_toml",
            "manifest_path": manifest_path.as_posix(),
            "source_code_package_id": "source-code-package-id",
        },
        "semantic_contract": {
            "module": "aware_meta.semantic_contract",
            "provider_key": "aware_meta",
            "role": "aware_meta.provider",
            "name": "aware.semantic_provider",
        },
        "current_delta_fingerprint": "sha256:current",
        "delta_cause_hints": {
            "changed_path_count": 1,
            "source_owned_path_count": 1,
            "generated_fallout_path_count": 0,
            "changed_path_classifications": {"source_owned": 1},
            "top_changed_path_limit": 8,
            "top_changed_paths": [
                {
                    "path": "aware/home/model.aware",
                    "change_kind": change_kind,
                    "classification": "source_owned",
                    "package_relative_path": "aware/home/model.aware",
                    "language": "aware",
                    "is_structural": True,
                }
            ],
            "current_delta_fingerprint_available": True,
            "previous_delta_fingerprint_available": True,
        },
    }
    if include_code_package_delta:
        delta_path: dict[str, object] = {
            "relative_path": source_relative_path,
            "kind": change_kind,
            "language": "aware",
            "is_structural": True,
            "path_role": "authored_source",
        }
        if include_code_delta_content and change_kind != "delete":
            delta_path["content_text"] = source_text
        payload["code_package_delta"] = {
            "package_name": "demo-ontology",
            "package_root": ".",
            "sources_root": "aware",
            "manifest_relative_path": manifest_path.name,
            "authority_kind": "local_fs_view",
            "source_revision_id": "test-current",
            "paths": [delta_path],
        }
    if include_baseline_refs:
        payload["baseline_ref"] = baseline_ref_payload(
            manifest_path=manifest_path,
        )
        payload["previous_materialization_evidence"] = {
            "available": True,
            "evidence_source": "reused_workspace_materialization_receipt",
            "commit_refs": {
                "source_object_instance_graph_commit_id": "source-oig-commit",
                "semantic_object_instance_graph_commit_id": (
                    "semantic-package-oig-commit"
                ),
                "semantic_root_object_instance_graph_commit_id": (
                    "semantic-root-oig-commit"
                ),
            },
        }
    return WorkspaceSemanticMaterializationProviderDeltaRequest.model_validate(payload)


def baseline_ref_payload(*, manifest_path: Path) -> dict[str, object]:
    return {
        "workspace_revision_id": "workspace-revision-id",
        "workspace_materialization_id": "workspace-materialization-id",
        "workspace_materialization_index": 3,
        "revision_code_package_id": "revision-code-package-id",
        "source_code_package_id": "source-code-package-id",
        "source_object_instance_graph_commit_id": "source-oig-commit",
        "revision_code_package_object_instance_graph_commit_id": "source-oig-commit",
        "semantic_package_commit_id": "semantic-package-commit-id",
        "semantic_owner_module": "aware_meta",
        "semantic_package_kind": "object_config_graph_package",
        "semantic_package_id": "semantic-package-id",
        "semantic_package_name": "demo-ontology",
        "semantic_contract_module": "aware_meta.semantic_contract",
        "semantic_contract_name": "aware.semantic_provider",
        "semantic_contract_role": "aware_meta.provider",
        "semantic_contract_provider_key": "aware_meta",
        "semantic_projection_name": "ObjectConfigGraphPackage",
        "semantic_branch_id": "semantic-branch-id",
        "semantic_object_instance_graph_commit_id": "semantic-package-oig-commit",
        "semantic_root_kind": "object_config_graph",
        "semantic_root_id": "semantic-root-id",
        "semantic_root_object_instance_graph_commit_id": "semantic-root-oig-commit",
        "manifest_path": manifest_path.as_posix(),
        "manifest_toml_path": manifest_path.as_posix(),
    }


def baseline_semantic_object_index_payload() -> dict[str, dict[str, object]]:
    return {
        "ocg_package:demo-ontology": {
            "object_id": "baseline-package-object-id",
            "object_kind": "object_config_graph_package",
            "source_refs": ("aware.toml",),
        },
        "ocg:aware_demo": {
            "object_id": "baseline-graph-object-id",
            "object_kind": "object_config_graph",
            "source_refs": ("home/model.aware",),
        },
        "ocg:aware_demo/node:aware_demo.default.home.Room": {
            "object_id": "baseline-room-class-object-id",
            "object_kind": "class",
            "source_refs": ("home/model.aware",),
        },
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:name": {
            "object_id": "baseline-room-name-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": "ocg:aware_demo/node:aware_demo.default.home.Room",
            "attribute_name": "name",
            "source_refs": ("home/model.aware",),
        },
        "ocg:aware_demo/node:aware_demo.default.home.Room/attribute:state": {
            "object_id": "baseline-room-state-attribute-object-id",
            "object_kind": "attribute",
            "owner_semantic_key": "ocg:aware_demo/node:aware_demo.default.home.Room",
            "attribute_name": "state",
            "source_refs": ("home/model.aware",),
        },
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")
