from __future__ import annotations

import importlib


def test_interface_ontology_materialization_imports_without_package_cycle() -> None:
    ontology_materialization = importlib.import_module(
        "aware_interface.ontology.materialization"
    )
    snapshot_commit = importlib.import_module(
        "aware_interface.materialization.snapshot_commit"
    )

    assert callable(ontology_materialization.materialize_interface_config_bundle)
    assert callable(snapshot_commit.commit_interface_config_snapshot)


def test_interface_package_materialization_exports_remain_available() -> None:
    package_materialization = importlib.import_module("aware_interface.materialization")

    assert callable(package_materialization.materialize_interface_package_from_manifest)
    assert callable(package_materialization.resolve_interface_package_materialization_spec)
