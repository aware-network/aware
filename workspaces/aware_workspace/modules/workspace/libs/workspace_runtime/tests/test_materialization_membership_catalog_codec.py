from __future__ import annotations

import json

import pytest
from aware_code_semantic_contract_runtime import ContractViolation, canonical_json_bytes
from aware_workspace_runtime import (
    decode_workspace_semantic_authored_dependency,
    decode_workspace_semantic_materialization_membership_catalog,
    decode_workspace_semantic_materialization_package_entry,
    encode_workspace_semantic_authored_dependency,
    encode_workspace_semantic_materialization_membership_catalog,
    encode_workspace_semantic_materialization_package_entry,
)
from test_materialization_membership_catalog import _catalog  # pyright: ignore[reportMissingImports]


def test_membership_values_round_trip_against_exact_context() -> None:
    catalog = _catalog()
    entry = catalog.entries[1]
    dependency = entry.authored_dependencies[0]
    assert (
        decode_workspace_semantic_authored_dependency(
            encode_workspace_semantic_authored_dependency(dependency),
            expected=dependency,
        )
        == dependency
    )
    assert (
        decode_workspace_semantic_materialization_package_entry(
            encode_workspace_semantic_materialization_package_entry(entry),
            expected=entry,
        )
        == entry
    )
    assert (
        decode_workspace_semantic_materialization_membership_catalog(
            encode_workspace_semantic_materialization_membership_catalog(catalog),
            catalog_ref=catalog.catalog_ref,
            catalog_generation=catalog.catalog_generation,
            entries=catalog.entries,
        )
        == catalog
    )


def test_catalog_generation_and_source_substitution_fail() -> None:
    catalog = _catalog()
    payload = json.loads(
        encode_workspace_semantic_materialization_membership_catalog(catalog)
    )
    payload["catalog_generation"] += 1
    with pytest.raises(ContractViolation, match="exact Workspace context"):
        decode_workspace_semantic_materialization_membership_catalog(
            canonical_json_bytes(payload),
            catalog_ref=catalog.catalog_ref,
            catalog_generation=catalog.catalog_generation,
            entries=catalog.entries,
        )

    entry = catalog.entries[0]
    payload = json.loads(encode_workspace_semantic_materialization_package_entry(entry))
    payload["source_authority_ref"] = "forged"
    with pytest.raises(ContractViolation, match="exact Workspace context"):
        decode_workspace_semantic_materialization_package_entry(
            canonical_json_bytes(payload), expected=entry
        )
