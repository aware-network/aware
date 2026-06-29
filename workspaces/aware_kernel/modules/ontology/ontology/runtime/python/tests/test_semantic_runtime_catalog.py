from __future__ import annotations

from pathlib import Path

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY,
    SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
)
from aware_ontology.semantic_runtime_catalog import (
    resolve_semantic_ontology_package_manifest_closure,
    semantic_ontology_package_names_for_projection_names,
)


def test_resolves_package_and_projection_manifest_closure(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    meta_manifest = repo_root / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml"
    conversation_manifest = (
        repo_root / "workspaces/coordination/ontologies/conversation/structure/aware.toml"
    )
    experience_manifest = repo_root / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml"
    for path in (meta_manifest, conversation_manifest, experience_manifest):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("aware = 1\n", encoding="utf-8")

    context = {
        SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
            "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
            "entries": [
                _entry("meta-ontology", meta_manifest),
                _entry(
                    "conversation-ontology",
                    conversation_manifest,
                    dependency_package_names=("meta-ontology",),
                ),
                _entry(
                    "experience-ontology",
                    experience_manifest,
                    dependency_package_names=("meta-ontology",),
                    projection_names=("ExperiencePackage",),
                ),
            ],
        }
    }

    assert resolve_semantic_ontology_package_manifest_closure(
        context=context,
        repo_root=repo_root,
        package_names=("conversation-ontology",),
        required_projection_names=("ExperiencePackage",),
    ) == (meta_manifest, conversation_manifest, experience_manifest)


def test_reports_missing_catalog_dependency(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    context = {
        SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_CONTEXT_KEY: {
            "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
            "entries": [
                _entry(
                    "conversation-ontology",
                    repo_root / "conversation" / "aware.toml",
                    dependency_package_names=("missing-ontology",),
                ),
            ],
        }
    }

    with pytest.raises(ValueError, match="missing-ontology"):
        resolve_semantic_ontology_package_manifest_closure(
            context=context,
            repo_root=repo_root,
            package_names=("conversation-ontology",),
        )


def test_resolves_projection_owners() -> None:
    entries = {
        "experience-ontology": _catalog_entry(
            package_name="experience-ontology",
            projection_names=("ExperiencePackage",),
        ),
        "conversation-ontology": _catalog_entry(
            package_name="conversation-ontology",
            projection_names=("ConversationSpace",),
        ),
    }

    assert semantic_ontology_package_names_for_projection_names(
        entries_by_package_name=entries,
        required_projection_names=("ConversationSpace",),
    ) == ("conversation-ontology",)


def _entry(
    package_name: str,
    manifest_path: Path,
    *,
    dependency_package_names: tuple[str, ...] = (),
    projection_names: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "module_id": package_name.removesuffix("-ontology"),
        "package_name": package_name,
        "fqn_prefix": package_name.replace("-", "_"),
        "manifest_path": manifest_path.as_posix(),
        "dependency_package_names": list(dependency_package_names),
        "projection_names": list(projection_names),
    }


def _catalog_entry(
    *,
    package_name: str,
    projection_names: tuple[str, ...],
):
    from aware_ontology.semantic_runtime_catalog import SemanticOntologyPackageCatalogEntry

    return SemanticOntologyPackageCatalogEntry(
        module_id=package_name.removesuffix("-ontology"),
        package_name=package_name,
        fqn_prefix=package_name.replace("-", "_"),
        manifest_path=Path(f"/tmp/{package_name}/aware.toml"),
        dependency_package_names=(),
        projection_names=projection_names,
    )
