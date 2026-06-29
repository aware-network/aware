from __future__ import annotations

from pathlib import Path

import pytest


_TEST_FILE = Path(__file__).resolve()
_KERNEL_WORKSPACE_ROOT = _TEST_FILE.parents[6]
_KERNEL_MODULES_ROOT = _KERNEL_WORKSPACE_ROOT / "modules"


def _prepend_runtime_roots(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for module_id in ("code", "meta", "ontology"):
        monkeypatch.syspath_prepend(
            str(_KERNEL_MODULES_ROOT / module_id / "ontology" / "runtime" / "python")
        )


def _base_ontology_toml(*, layout_text: str = "") -> str:
    return "\n".join(
        (
            "aware_ontology = 1",
            "",
            "[ontology]",
            'package_name = "demo-ontology"',
            'fqn_prefix = "aware_demo"',
            'source_manifest = "structure/ontology/aware.toml"',
            "",
            layout_text,
        )
    )


def _target_roles(spec: object) -> set[str]:
    return {target.role for target in getattr(spec, "language_materialization_targets")}


def _target_package_names_by_role(spec: object) -> dict[str, str]:
    return {
        target.role: target.package_name
        for target in getattr(spec, "language_materialization_targets")
    }


def test_default_layout_does_not_enable_dart_materialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(toml_text=_base_ontology_toml())

    roles = _target_roles(spec)
    assert "python_ontology" in roles
    assert "python_orm_models" in roles
    assert "sql_ontology" in roles
    assert "python_runtime_handlers_meta" in roles
    assert "dart_ontology" not in roles
    assert "dart_dto" not in roles
    assert spec.layout is None


def test_default_python_targets_declare_generated_code_package_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(toml_text=_base_ontology_toml())

    package_names = _target_package_names_by_role(spec)
    assert package_names["python_ontology"] == "aware-demo-ontology"
    assert package_names["python_orm_models"] == ("aware-demo-ontology-orm-models")


def test_ontology_manifest_defaults_to_class_strict_stable_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(toml_text=_base_ontology_toml())

    assert spec.ontology.stable_ids_resolution_policy == "class_strict"


def test_ontology_manifest_rejects_compat_stable_ids_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        AwareOntologyTomlError,
        load_aware_ontology_toml_spec_from_text,
    )

    with pytest.raises(
        AwareOntologyTomlError,
        match=r"\[ontology\]\.stable_ids_resolution_policy must be one of",
    ):
        load_aware_ontology_toml_spec_from_text(
            toml_text=_base_ontology_toml(
                layout_text='stable_ids_resolution_policy = "compat"'
            )
        )


def test_module_structure_layout_does_not_enable_dart_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(
        toml_text=_base_ontology_toml(
            layout_text="\n".join(
                (
                    "[layout]",
                    'profile = "module_structure_ontology_v1"',
                )
            )
        )
    )

    assert spec.layout is not None
    assert spec.layout.profile == "module_structure_ontology_v1"
    assert "dart" not in spec.layout.output_dirs
    roles = _target_roles(spec)
    assert "dart_ontology" not in roles
    assert "dart_dto" not in roles


def test_module_structure_layout_explicit_dart_outputs_are_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(
        toml_text=_base_ontology_toml(
            layout_text="\n".join(
                (
                    "[layout]",
                    'profile = "module_structure_ontology_v1"',
                    "",
                    "[layout.outputs.dart]",
                    'ontology = "structure/ontology/dart"',
                    'dto = "structure/ontology_dto/dart"',
                )
            )
        )
    )

    assert spec.layout is not None
    assert spec.layout.profile == "module_structure_ontology_v1"
    assert spec.layout.output_dirs["dart"] == {
        "ontology": "structure/ontology/dart",
        "dto": "structure/ontology_dto/dart",
    }
    roles = _target_roles(spec)
    assert "dart_ontology" in roles
    assert "dart_dto" in roles


def test_module_structure_layout_explicit_python_dto_output_is_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(
        toml_text=_base_ontology_toml(
            layout_text="\n".join(
                (
                    "[layout]",
                    'profile = "module_structure_ontology_v1"',
                    "",
                    "[layout.outputs.python]",
                    'dto = "structure/ontology_dto/python"',
                )
            )
        )
    )

    assert spec.layout is not None
    assert spec.layout.profile == "module_structure_ontology_v1"
    assert spec.layout.output_dirs["python"]["dto"] == ("structure/ontology_dto/python")
    roles = _target_roles(spec)
    assert "python_dto" in roles


def test_ontology_structure_layout_does_not_enable_dart_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(
        toml_text=_base_ontology_toml(
            layout_text="\n".join(
                (
                    "[layout]",
                    'profile = "ontology_structure_v1"',
                )
            )
        )
    )

    assert spec.layout is not None
    assert spec.layout.profile == "ontology_structure_v1"
    assert "dart" not in spec.layout.output_dirs
    roles = _target_roles(spec)
    assert "python_dto" in roles
    assert "dart_ontology" not in roles
    assert "dart_dto" not in roles


def test_ontology_structure_layout_explicit_dart_outputs_are_opt_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import (
        load_aware_ontology_toml_spec_from_text,
    )

    spec = load_aware_ontology_toml_spec_from_text(
        toml_text=_base_ontology_toml(
            layout_text="\n".join(
                (
                    "[layout]",
                    'profile = "ontology_structure_v1"',
                    "",
                    "[layout.outputs.dart]",
                    'ontology = "structure/dart/models"',
                    'dto = "structure/dart/dto"',
                )
            )
        )
    )

    assert spec.layout is not None
    assert spec.layout.profile == "ontology_structure_v1"
    assert spec.layout.output_dirs["dart"] == {
        "ontology": "structure/dart/models",
        "dto": "structure/dart/dto",
    }
    roles = _target_roles(spec)
    assert "dart_ontology" in roles
    assert "dart_dto" in roles


def test_kernel_ontology_manifest_uses_ontology_layout_without_dart_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepend_runtime_roots(monkeypatch=monkeypatch)

    from aware_ontology.manifest.loader import load_aware_ontology_toml_spec

    spec = load_aware_ontology_toml_spec(
        toml_path=(
            _KERNEL_WORKSPACE_ROOT
            / "modules"
            / "ontology"
            / "ontology"
            / "aware.ontology.toml"
        )
    )

    assert spec.layout is not None
    assert spec.layout.profile == "ontology_structure_v1"
    assert "dart" not in spec.layout.output_dirs
    roles = _target_roles(spec)
    assert "python_dto" in roles
    assert "dart_ontology" not in roles
    assert "dart_dto" not in roles
