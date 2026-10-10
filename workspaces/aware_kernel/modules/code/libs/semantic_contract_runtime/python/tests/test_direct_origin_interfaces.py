from dataclasses import replace
from typing import cast

import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticImplementationCoordinate,
)
from aware_code_semantic_contract_runtime.direct_origin_interfaces import (
    RESOURCE_ROLES,
    TWO_STAGE_RESOURCE_ROLES,
    DirectCommandExpectedContext,
    DirectCommandResourceBinding,
    DirectWorkspaceOriginProduct,
    RetainedSemanticStageRuntimeExpectation,
)
from aware_code_semantic_contract_runtime.materialization_catalog import (
    AdmittedCodeSemanticContractCatalog,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime


def context():
    # Deliberately inert identity markers: constructing expectations is not
    # original runtime/catalog admission, and these fixtures claim neither.
    runtime = cast(SemanticContractRuntime, object())
    catalog = cast(AdmittedCodeSemanticContractCatalog, object())
    objects = {role: object() for role in RESOURCE_ROLES}
    objects.update(code_runtime=runtime, catalog=catalog)
    digest = ContentDigest.of_bytes(b"fixture")
    return DirectCommandExpectedContext(
        object(),
        object(),
        1,
        runtime,
        catalog,
        SemanticImplementationCoordinate("composition", digest),
        SemanticConfigurationCoordinate("composition", digest),
        SemanticImplementationCoordinate("policy", digest),
        SemanticConfigurationCoordinate("policy", digest),
        tuple(
            DirectCommandResourceBinding(role, objects[role], "borrowed")
            for role in RESOURCE_ROLES
        ),
    )


def test_expectations_and_products_are_not_nominal_admissions():
    expected = context()
    assert replace(expected) != expected
    assert all(
        a.resource is b.resource
        for a, b in zip(expected.resources, replace(expected).resources)
    )
    product = DirectWorkspaceOriginProduct(object(), expected)
    assert replace(product) != product
    assert not hasattr(product, "validate_command_lifetime")
    assert not hasattr(product, "acquire_command_publication_guard")


@pytest.mark.parametrize("pid", [True, 0, -1, "1"])
def test_exact_process_id_required(pid):
    with pytest.raises(ContractViolation):
        replace(context(), process_id=pid)


@pytest.mark.parametrize(
    "change", ["missing", "reordered", "duplicate", "list", "runtime", "catalog"]
)
def test_resource_identity_and_disposition_closure(change):
    expected = context()
    resources = expected.resources
    with pytest.raises(ContractViolation):
        if change == "missing":
            replace(expected, resources=resources[:-1])
        elif change == "reordered":
            replace(expected, resources=tuple(reversed(resources)))
        elif change == "duplicate":
            replace(expected, resources=(resources[0],) + resources[:-1])
        elif change == "list":
            replace(expected, resources=list(resources))
        elif change == "runtime":
            replace(expected, runtime=object())
        else:
            replace(expected, catalog=object())


@pytest.mark.parametrize(
    "role,resource,disposition",
    [
        ("unknown", object(), "owned"),
        ("catalog", None, "borrowed"),
        ("catalog", object(), "inferred"),
    ],
)
def test_unavailable_resource_or_implicit_disposition_rejects(
    role, resource, disposition
):
    with pytest.raises(ContractViolation):
        DirectCommandResourceBinding(role, resource, disposition)


def two_stage_context():
    expected = context()
    authority_runtime = object()
    # Inert expected references, deliberately not real Code registrations.
    stages = (
        RetainedSemanticStageRuntimeExpectation(
            "source_planning", expected.runtime, object()
        ),
        RetainedSemanticStageRuntimeExpectation(
            "authority_derivation", authority_runtime, object()
        ),
    )
    return replace(
        expected,
        stage_runtime_bindings=stages,
        resources=(
            DirectCommandResourceBinding(
                "authority_code_runtime", authority_runtime, "owned"
            ),
            *expected.resources,
        ),
    )


def test_source_only_shape_is_preserved_and_two_stage_is_expected_data():
    assert context().stage_runtime_bindings == ()
    expected = two_stage_context()
    assert tuple(b.role for b in expected.resources) == TWO_STAGE_RESOURCE_ROLES
    assert expected.stage_runtime_bindings[0].runtime is expected.runtime
    assert expected.resources[0].resource is expected.stage_runtime_bindings[1].runtime
    assert (
        replace(expected.stage_runtime_bindings[0])
        != expected.stage_runtime_bindings[0]
    )
    assert not hasattr(expected.stage_runtime_bindings[1], "validate_registration")


@pytest.mark.parametrize(
    "change",
    [
        "one",
        "three",
        "list",
        "reordered",
        "duplicate",
        "foreign_shape",
        "planning_runtime",
        "same_runtime",
        "same_registration",
        "missing_resource",
        "foreign_resource",
        "resource_without_stages",
    ],
)
def test_incomplete_or_substituted_stage_resource_shape_rejects(change):
    expected = two_stage_context()
    planning, authority = expected.stage_runtime_bindings
    with pytest.raises(ContractViolation):
        if change == "one":
            replace(expected, stage_runtime_bindings=(planning,))
        elif change == "three":
            replace(expected, stage_runtime_bindings=(planning, authority, authority))
        elif change == "list":
            replace(expected, stage_runtime_bindings=[planning, authority])
        elif change == "reordered":
            replace(expected, stage_runtime_bindings=(authority, planning))
        elif change == "duplicate":
            replace(expected, stage_runtime_bindings=(planning, planning))
        elif change == "foreign_shape":
            replace(expected, stage_runtime_bindings=(object(), authority))
        elif change == "planning_runtime":
            replace(
                expected,
                stage_runtime_bindings=(replace(planning, runtime=object()), authority),
            )
        elif change == "same_runtime":
            replace(
                expected,
                stage_runtime_bindings=(
                    planning,
                    replace(authority, runtime=planning.runtime),
                ),
            )
        elif change == "same_registration":
            replace(
                expected,
                stage_runtime_bindings=(
                    planning,
                    replace(authority, registration=planning.registration),
                ),
            )
        elif change == "missing_resource":
            replace(expected, resources=expected.resources[1:])
        elif change == "foreign_resource":
            replace(
                expected,
                resources=(
                    replace(expected.resources[0], resource=object()),
                    *expected.resources[1:],
                ),
            )
        else:
            replace(expected, stage_runtime_bindings=())


@pytest.mark.parametrize(
    "field,value",
    [
        ("stage", "authority"),
        ("stage", True),
        ("runtime", None),
        ("registration", None),
    ],
)
def test_stage_discriminator_and_available_identity_references(field, value):
    with pytest.raises(ContractViolation):
        replace(two_stage_context().stage_runtime_bindings[1], **{field: value})


def test_revalidation_detects_changed_nested_stage_shape():
    expected = two_stage_context()
    object.__setattr__(expected.stage_runtime_bindings[1], "runtime", object())
    with pytest.raises(ContractViolation, match="authority runtime resource"):
        expected.__post_init__()
