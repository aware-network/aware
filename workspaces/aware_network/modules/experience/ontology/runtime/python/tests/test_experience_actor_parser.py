from __future__ import annotations

import json
from pathlib import Path

import pytest

from aware_experience.actor.compiler import (
    load_actor_role_ownership_from_sources,
)
from aware_experience.actor.contracts import (
    load_actor_role_contract,
    load_actor_role_contract_from_runtime_manifests,
)


def _write_composition_manifest_for_class_fqns(
    *, root: Path, class_fqns: tuple[str, ...]
) -> Path:
    module_runtime_dir = (
        root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "experience"
        / "ontology"
        / "structure"
        / ".aware"
        / "environment"
        / "runtime"
    )
    module_runtime_dir.mkdir(parents=True, exist_ok=True)
    _ = (module_runtime_dir / "environment.manifest.json").write_text(
        json.dumps({"bindings": {"file": "bindings.manifest.json"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    _ = (module_runtime_dir / "bindings.manifest.json").write_text(
        json.dumps(
            {
                "bindings": [
                    {
                        "class_fqn": class_fqn,
                    }
                    for class_fqn in class_fqns
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    composition_path = root / ".aware" / "tmp" / "environment.composition.manifest.json"
    composition_path.parent.mkdir(parents=True, exist_ok=True)
    _ = composition_path.write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "manifest_path": (
                            "workspaces/aware_network/modules/experience/ontology/structure/.aware/environment/runtime/environment.manifest.json"
                        )
                    }
                ]
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return composition_path


def _runtime_manifest_path(root: Path) -> Path:
    return (
        root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "experience"
        / "ontology"
        / "structure"
        / ".aware"
        / "environment"
        / "runtime"
        / "environment.manifest.json"
    )


def test_load_actor_role_ownership_from_sources_parses_docstring_declarations(
    tmp_path: Path,
) -> None:
    source = "\n".join(
        [
            "role home_resident {",
            '  """Resident role."""',
            "  aware_home.home.Door.unlock",
            "}",
            "",
            "actor resident Human {",
            '  """Resident actor."""',
            "}",
            "",
            "environment home_story {",
            "  actor resident {",
            '    """Binding doc."""',
            "    role home_resident",
            "  }",
            "}",
            "",
        ]
    )
    _ = (tmp_path / "actors.aware").write_text(source, encoding="utf-8")

    roles, actors, bindings = load_actor_role_ownership_from_sources(
        package_root=tmp_path,
        source_files=(Path("actors.aware"),),
    )

    assert len(roles) == 1
    assert roles[0].name == "home_resident"
    assert roles[0].capabilities == ("aware_home.home.Door.unlock",)
    assert len(actors) == 1
    assert actors[0].name == "resident"
    assert actors[0].kind == "Human"
    assert actors[0].roles == ()
    assert len(bindings) == 1
    assert bindings[0].environment == "home_story"
    assert bindings[0].actor == "resident"
    assert bindings[0].roles == ("home_resident",)


def test_load_actor_role_ownership_from_sources_fails_on_unparsed_actor_declaration(
    tmp_path: Path,
) -> None:
    _ = (tmp_path / "actors.aware").write_text(
        "\n".join(
            [
                "actor resident Human {",
                '  """Unclosed actor block"""',
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="could not be parsed by tree-sitter"):
        _ = load_actor_role_ownership_from_sources(
            package_root=tmp_path,
            source_files=(Path("actors.aware"),),
        )


def test_load_actor_role_contract_returns_composed_actor_role_contract(
    tmp_path: Path,
) -> None:
    composition_path = _write_composition_manifest_for_class_fqns(
        root=tmp_path,
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
        ),
    )

    contract = load_actor_role_contract(
        composition_manifest_path=composition_path,
        repo_root=tmp_path,
    )

    assert contract is not None
    assert (
        contract.actor_config_class_fqn
        == "aware_identity_ontology.actor.actor_config.ActorConfig"
    )
    assert (
        contract.role_config_class_fqn
        == "aware_identity_ontology.role.role_config.RoleConfig"
    )


def test_load_actor_role_contract_accepts_runtime_manifests(
    tmp_path: Path,
) -> None:
    _ = _write_composition_manifest_for_class_fqns(
        root=tmp_path,
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
        ),
    )

    contract = load_actor_role_contract_from_runtime_manifests(
        environment_runtime_manifest_paths=(_runtime_manifest_path(tmp_path),),
        repo_root=tmp_path,
    )

    assert contract is not None
    assert (
        contract.actor_config_class_fqn
        == "aware_identity_ontology.actor.actor_config.ActorConfig"
    )
    assert (
        contract.role_config_class_fqn
        == "aware_identity_ontology.role.role_config.RoleConfig"
    )


def test_load_actor_role_contract_rejects_incomplete_contract(tmp_path: Path) -> None:
    composition_path = _write_composition_manifest_for_class_fqns(
        root=tmp_path,
        class_fqns=("aware_identity_ontology.actor.actor_config.ActorConfig",),
    )

    with pytest.raises(ValueError, match="Incomplete actor-role contract"):
        _ = load_actor_role_contract(
            composition_manifest_path=composition_path,
            repo_root=tmp_path,
        )
