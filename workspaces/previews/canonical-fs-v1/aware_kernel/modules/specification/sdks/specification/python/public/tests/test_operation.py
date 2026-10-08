from dataclasses import replace

import pytest
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationPlan,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObservation,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)


def test_invalid_request_never_invokes_selected_provider():
    class Never:
        def observe(self, request):
            raise AssertionError("provider invoked")

        def create_draft(self, request):
            raise AssertionError("provider invoked")

    with pytest.raises(SpecificationOperationError):
        SpecificationSdkClient(Never()).observe(object())
    with pytest.raises(SpecificationOperationError):
        SpecificationSdkClient(Never()).create_draft(object())


def test_wrong_result_type_is_refused():
    class Wrong:
        def observe(self, request):
            return {}

    with pytest.raises(SpecificationOperationError, match="invalid_observation"):
        SpecificationSdkClient(Wrong()).observe(SpecificationObserveRequest())


def test_incomplete_typed_observation_is_a_structural_refusal():
    class Incomplete:
        def observe(self, request):
            return object.__new__(SpecificationObservation)

    with pytest.raises(SpecificationOperationError) as caught:
        SpecificationSdkClient(Incomplete()).observe(SpecificationObserveRequest())
    assert caught.value.code == "invalid_observation"
    assert caught.value.effect == "none"
    assert isinstance(caught.value.__cause__, AttributeError)


def test_draft_cannot_invent_approved_iteration():
    gate = SpecificationPhaseGateDefinition("g", "Promise", "contract", "evidence")
    phase = SpecificationPhaseDefinition(
        "p", "Phase", 0, gate, description="Phase goal"
    )
    definition = SpecificationDefinition(
        "example",
        "Example",
        1,
        "sha256:" + "1" * 64,
        (SpecificationInvariantDefinition("safe", "Stay safe"),),
        (phase,),
        "Purpose",
    )
    SpecificationDraftRequest(definition, "author", "intent")
    phase = replace(
        phase, iterations=(SpecificationIterationPlan("i", "Iteration", "Objective"),)
    )
    with pytest.raises(
        SpecificationOperationError, match="iteration_approval_writer_unavailable"
    ):
        SpecificationDraftRequest(
            replace(definition, phases=(phase,)), "author", "intent"
        )


def test_public_sdk_import_boundary():
    import ast
    from pathlib import Path

    package = Path(__file__).parents[1] / "aware_specification_sdk"
    imports = set()
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imports.add(node.module.split(".")[0])
    assert imports <= {
        "dataclasses",
        "pathlib",
        "typing",
        "unicodedata",
        "aware_specification_runtime",
    }
