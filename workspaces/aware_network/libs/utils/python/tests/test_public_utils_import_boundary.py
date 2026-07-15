from __future__ import annotations

from pathlib import Path

import aware_utils


def test_aware_utils_does_not_ship_import_grouper() -> None:
    utils_root = Path(aware_utils.__file__).parent

    assert not (utils_root / "import_grouper.py").exists()
    assert not hasattr(aware_utils, "ImportGrouper")


def test_aware_utils_does_not_ship_dynamic_import_discovery_rail() -> None:
    utils_root = Path(aware_utils.__file__).parent
    dynamic_import_exports = (
        "import_class_from_file_path",
        "try_import_module_class",
        "generate_import_strategies",
        "import_class_with_fallback_strategies",
        "import_enum_with_fallback_strategies",
    )

    assert not (utils_root / "dynamic_import.py").exists()
    for export_name in dynamic_import_exports:
        assert not hasattr(aware_utils, export_name)


def test_aware_utils_has_no_import_grouping_semantic_package_hardcodes() -> None:
    utils_root = Path(aware_utils.__file__).parent
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(utils_root.rglob("*.py"))
        if "__pycache__" not in path.parts
    )

    forbidden_fragments = (
        "tool.poetry",
        "pyproject.toml",
        "aware_agent",
        "aware_economy",
        "aware_identity",
        "aware_interface",
        "aware_network",
        "aware_environment",
        "aware_space",
        "aware_tests",
        'startswith("aware_',
        "startswith('aware_",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_pydantic_package_bootstrap_has_no_package_name_dependency_policy() -> None:
    utils_root = Path(aware_utils.__file__).parent
    source = (utils_root / "pydantic" / "package_bootstrap.py").read_text(
        encoding="utf-8"
    )

    forbidden_fragments = (
        'endswith("_ontology',
        "endswith('_ontology",
        'startswith("aware_',
        "startswith('aware_",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source
