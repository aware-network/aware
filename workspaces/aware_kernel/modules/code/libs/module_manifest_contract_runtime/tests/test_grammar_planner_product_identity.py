"""Original per-product planner configuration, not a shared planner cache."""

import asyncio
from contextlib import contextmanager

import pytest
from aware_code_module_manifest_contract_runtime import grammar_factory as factory
from aware_code_semantic_contract_runtime import product_contribution as products
from aware_code_semantic_contract_runtime import selected_provider
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    canonical_json_bytes,
)


@pytest.fixture(scope="module")
def admissions():
    return tuple(
        selected_provider._admit_selected_provider_factory(
            factory_ref=fn.__module__ + ":" + fn.__name__,
            provider_key=fn().binding.provider_key,
            selection_factory=fn,
        )
        for fn in (
            factory.construct_grammar_profile_selection_product,
            factory.construct_grammar_syntax_binding_product,
        )
    )


@contextmanager
def catalogs(admissions):
    originals = []
    try:
        for admission in admissions:
            original = products.issue_selected_provider_product_contribution(admission)
            originals.append(original)
        rows = tuple(
            products.produce_selected_provider_product_catalog_contribution(x)
            for x in originals
        )
        yield originals, rows
    finally:
        for original in reversed(originals):
            products.close_selected_provider_product_contribution(original)


def test_distinct_original_planners_have_distinct_bound_configuration(admissions):
    with catalogs(admissions) as (originals, rows):
        left, right = (x.entries[0] for x in rows)
        assert rows[0].planner is not rows[1].planner
        assert (
            left.dependency_planner_implementation
            == right.dependency_planner_implementation
        )
        assert (
            left.dependency_planner_configuration
            != right.dependency_planner_configuration
        )
        for original, row in zip(originals, rows, strict=True):
            value = products.read_selected_provider_product_contribution(original)
            expected = canonical_json_bytes(
                {
                    "contract": "aware.code.grammar-source-role-planner-configuration.v2",
                    "product_binding": value.binding.to_wire(),
                    "profile": value.profile.to_wire(),
                    "options": {},
                }
            )
            configuration = row.entries[0].dependency_planner_configuration
            assert (
                configuration.configuration_ref
                == "aware.code.grammar-source-role-planner.bound-product.v2"
            )
            assert configuration.digest == ContentDigest.of_bytes(expected)
            assert (
                products.read_selected_provider_product_catalog_contribution(
                    original
                ).planner
                is row.planner
            )


def test_original_owner_coordinate_map_no_longer_aliases_products(admissions):
    with catalogs(admissions) as (_, rows):
        owners = {}
        for row in rows:
            entry = row.entries[0]
            coordinate = (
                entry.dependency_planner_implementation,
                entry.dependency_planner_configuration,
            )
            previous = owners.setdefault(coordinate, row.planner)
            assert previous is row.planner
        assert len(owners) == 2


@pytest.mark.parametrize("index", (0, 1))
def test_bound_configuration_does_not_enable_graph_execution(admissions, index):
    with catalogs(admissions) as (_, rows):
        with pytest.raises(TypeError, match="exact grammar planner input"):
            asyncio.run(
                rows[index].planner.plan(
                    package=object(),
                    intent=object(),
                    selected_match=object(),
                    planning_input=object(),
                )
            )


@pytest.mark.parametrize("index", (0, 1))
def test_configuration_cannot_renew_retired_original_product(admissions, index):
    with catalogs(admissions) as (originals, rows):
        products.close_selected_provider_product_contribution(originals.pop(index))
        with pytest.raises(ContractViolation):
            asyncio.run(
                rows[index].planner.plan(
                    package=object(),
                    intent=object(),
                    selected_match=object(),
                    planning_input=object(),
                )
            )
