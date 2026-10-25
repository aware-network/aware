"""Illustrative public-type recipe; replace meaning with customer-approved terms.

Prints canonical bytes only. Never run customer Python from create-draft.
This example is source-qualified; installed preparation remains Bundle-owned.
"""

import sys

from aware_specification_fs_adapter import SpecificationFsSchemaResolutionContext
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    encode_specification_snapshot,
    invariant_ref,
)
from aware_specification_sdk import SpecificationDraftRequest


def prepare() -> bytes:
    invariant = SpecificationInvariantDefinition(
        "preserve-input", "The JSON checker never modifies its input file."
    )
    gate = SpecificationPhaseGateDefinition(
        "checked",
        "Tests demonstrate valid and invalid inputs and unchanged input bytes.",
        "aware.specification.gate.evidence-accepted.v1",
        "customer.json-checker.tests.v1",
        (invariant_ref("customer.json-checker", invariant.invariant_key),),
    )
    definition = SpecificationDefinition(
        key="customer.json-checker",
        title="JSON checker",
        version_number=1,
        semantic_resolution_digest=SpecificationFsSchemaResolutionContext().semantic_resolution_digest,
        invariants=(invariant,),
        phases=(
            SpecificationPhaseDefinition(
                "checker",
                "Checker",
                0,
                gate,
                description="Deliver a command that reports whether one input file is valid JSON.",
            ),
        ),
        description="Provide a non-mutating JSON validity check with reproducible test evidence.",
    )
    request = SpecificationDraftRequest(
        definition, "customer-author", "customer-intent:json-checker-draft-1"
    )
    return encode_specification_snapshot(SpecificationSnapshot((request.definition,)))


if __name__ == "__main__":
    sys.stdout.buffer.write(prepare())
