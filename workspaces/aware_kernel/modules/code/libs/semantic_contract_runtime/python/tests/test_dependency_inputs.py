import ast
from copy import copy
from dataclasses import replace
from pathlib import Path

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticBody,
    SemanticDependencyCoordinate,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
    SemanticDependencyProduct,
    SemanticDependencyProductInput,
    SemanticDependencyTarget,
)
from test_materialization_planning import _demand_set, _digest, _intent


def product_input():
    demands = _demand_set()
    demand = demands.demands[0]
    target = SemanticPackageCoordinate("package:api", "api", _digest("api-source"))
    wire = b'{"meaning":"portable"}'
    value = SemanticValueCoordinate(
        demand.required_result_role,
        demand.result_product_contract,
        "result:api",
        ContentDigest.of_bytes(wire),
        len(wire),
    )
    product = SemanticDependencyProduct(
        demand.demand_digest,
        SemanticDependencyCoordinate(
            target, value.contract, value.value_ref, value.digest
        ),
        SemanticBody(value, wire),
        _digest("provenance"),
    )
    return SemanticDependencyProductInput(
        demands.package,
        _digest("source"),
        ((demand.authored_dependency_kind, demand.authored_dependency_ref),),
        demands,
        (product,),
        _intent(),
    )


def test_product_uses_existing_code_coordinates_and_retains_provenance():
    inputs = product_input()
    inputs.__post_init__()
    assert inputs.products[0].coordinate.package.package_ref == "package:api"
    assert inputs.products[0].provenance_digest == _digest("provenance")


@pytest.mark.parametrize("change", ["missing", "duplicate", "undeclared", "package"])
def test_product_closure_rejects_invalid_correspondence(change):
    inputs = product_input()
    changes = {
        "missing": {"products": ()},
        "duplicate": {"products": inputs.products * 2},
        "undeclared": {"declared_dependencies": ()},
        "package": {"package": inputs.products[0].coordinate.package},
    }
    with pytest.raises(ValueError):
        replace(inputs, **changes[change])


def test_changed_body_rejected_on_revalidation():
    inputs = product_input()
    body = copy(inputs.products[0].body)
    object.__setattr__(body, "canonical_body", b"changed")
    product = copy(inputs.products[0])
    object.__setattr__(product, "body", body)
    with pytest.raises(ValueError):
        replace(inputs, products=(product,))


def test_planning_context_is_generic_and_rejects_duplicate_declarations():
    inputs = product_input()
    target = SemanticDependencyTarget(
        inputs.products[0].coordinate.package, ("api.public",)
    )
    dependency = SemanticAuthoredDependency("api_package", "sdk.api", (target,))
    context = SemanticDependencyPlanningInput(
        inputs.package, inputs.source_identity_digest, (dependency,)
    )
    context.__post_init__()
    with pytest.raises(ValueError):
        replace(context, dependencies=(dependency, dependency))


def test_code_contract_has_no_domain_or_workspace_imports():
    path = (
        Path(__file__).resolve().parents[1]
        / "aware_code_semantic_contract_runtime/dependency_inputs.py"
    )
    imports = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "dataclasses", "typing"}
