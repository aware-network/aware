from dataclasses import replace

import pytest
from aware_specification_runtime import (
    SpecificationContractError,
    SpecificationIterationIdentity,
    SpecificationIterationPlan,
    SpecificationSnapshot,
    iteration_ref,
    resolve_iteration_identity,
)

from .test_values import specification_fixture


def test_same_plan_key_under_different_phases_has_different_identity():
    plan = SpecificationIterationPlan("first", "First", "Do the first cut")
    left = SpecificationIterationIdentity("specification:example/phase:left", plan)
    right = SpecificationIterationIdentity("specification:example/phase:right", plan)
    assert left.plan_digest != right.plan_digest
    assert left.iteration_ref == "specification:example/phase:left/iteration:first"


@pytest.mark.parametrize(
    "field,value",
    [("title", "Revised"), ("objective", "New scope"), ("plan_revision", 2)],
)
def test_plan_meaning_changes_digest(field, value):
    plan = SpecificationIterationPlan("first", "First", "Do first")
    before = SpecificationIterationIdentity("specification:example/phase:first", plan)
    after = SpecificationIterationIdentity(
        before.phase_ref, replace(plan, **{field: value})
    )
    assert before.plan_digest != after.plan_digest


def test_resolution_uses_exact_snapshot_and_coordinates():
    snapshot = SpecificationSnapshot((specification_fixture(),))
    wanted = iteration_ref("specification:recovery/phase:artifact", "artifact-r1")
    identity = resolve_iteration_identity(snapshot, wanted)
    assert identity.plan.plan_revision == 1
    with pytest.raises(SpecificationContractError, match="unavailable"):
        resolve_iteration_identity(
            snapshot, "specification:recovery/phase:other/iteration:artifact-r1"
        )
    object.__setattr__(identity, "plan_digest", "sha256:" + "0" * 64)
    with pytest.raises(SpecificationContractError, match="mismatch"):
        identity.__post_init__()


def test_foreign_plan_refuses_before_behavior():
    class Foreign:
        def __getattribute__(self, name):
            raise AssertionError("foreign behavior invoked")

    with pytest.raises(SpecificationContractError, match="exact"):
        SpecificationIterationIdentity("specification:example/phase:first", Foreign())
