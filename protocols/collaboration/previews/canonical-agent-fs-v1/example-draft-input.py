"""Illustrative terms only; no Issue admission or SPEC acceptance is issued."""
import sys
from aware_specification_fs_adapter import SpecificationFsSchemaResolutionContext
from aware_specification_runtime import (
    SpecificationDefinition, SpecificationInvariantDefinition,
    SpecificationPhaseDefinition, SpecificationPhaseGateDefinition,
    SpecificationSnapshot, encode_specification_snapshot, invariant_ref,
)
from aware_specification_sdk import SpecificationDraftRequest

invariant = SpecificationInvariantDefinition(
    "preserve-input", "The JSON checker never modifies its input file."
)
gate = SpecificationPhaseGateDefinition(
    "checked", "Tests cover valid and invalid inputs and unchanged input bytes.",
    "aware.specification.gate.evidence-accepted.v1", "customer.json-checker.tests.v1",
    (invariant_ref("customer.json-checker", invariant.invariant_key),),
)
definition = SpecificationDefinition(
    key="customer.json-checker", title="JSON checker", version_number=1,
    semantic_resolution_digest=SpecificationFsSchemaResolutionContext().semantic_resolution_digest,
    invariants=(invariant,),
    phases=(SpecificationPhaseDefinition(
        "checker", "Checker", 0, gate,
        description="Report whether one input file is valid JSON without modifying it.",
    ),),
    description="A reproducible non-mutating JSON validity check.",
)
request = SpecificationDraftRequest(definition, "customer-author", "customer-intent:draft-1")
sys.stdout.buffer.write(encode_specification_snapshot(SpecificationSnapshot((request.definition,))))
