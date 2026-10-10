import subprocess
import sys
from dataclasses import replace

import pytest
from aware_issue_sdk import (
    IssueSdkOperationClient,
    IssueSpecificationIterationBindingError,
    IssueSpecificationIterationBindingObservation,
    IssueSpecificationIterationBindingObserveRequest,
    SpecificationIterationBindingOutcome,
)


def request():
    return IssueSpecificationIterationBindingObserveRequest(
        "fb/2026-10-05/example",
        "specification:example.spec/phase:first/iteration:proof",
        1,
        *(["sha256:" + "a" * 64] * 4),
        "b" * 40,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("plan_revision", True),
        ("plan_revision", 0),
        ("plan_digest", "a" * 64),
        ("expected_head", "no-epoch"),
        ("issue_ref", ""),
        ("iteration_ref", "x\n"),
    ],
)
def test_request_contract_rejects_malformed_coordinates(field, value):
    with pytest.raises(IssueSpecificationIterationBindingError):
        replace(request(), **{field: value})


def test_absent_service_port_is_unavailable_without_fs_fallback():
    with pytest.raises(
        IssueSpecificationIterationBindingError, match="pairing_authority_unavailable"
    ):
        IssueSdkOperationClient(object()).observe_specification_iteration_binding(
            request()
        )


@pytest.mark.parametrize(
    "kind", ["object", "incomplete", "uncorrelated", "authorizing"]
)
def test_sdk_validates_typed_provider_result(kind):
    req = request()
    result = IssueSpecificationIterationBindingObservation(
        req,
        SpecificationIterationBindingOutcome.REFUSED,
        "test.provider",
        diagnostics=("refused",),
    )
    if kind == "object":
        result = object()
    elif kind == "incomplete":
        result = object.__new__(IssueSpecificationIterationBindingObservation)
    elif kind == "uncorrelated":
        result = replace(result, request=replace(req, issue_ref="fb/2026-10-05/other"))
    else:
        object.__setattr__(result, "approval_verified", True)

    class Provider:
        def observe_specification_iteration_binding(self, request):
            return result

    with pytest.raises(
        IssueSpecificationIterationBindingError, match="pairing_result_invalid"
    ):
        IssueSdkOperationClient(Provider()).observe_specification_iteration_binding(req)


def test_refusal_freezes_lists_and_has_no_approval_or_binding_claim():
    diagnostics = ["unavailable"]
    result = IssueSpecificationIterationBindingObservation(
        request(),
        SpecificationIterationBindingOutcome.UNAVAILABLE,
        "test.provider",
        diagnostics=diagnostics,
    )
    diagnostics.append("caller changed")
    assert result.diagnostics == ("unavailable",)
    assert result.to_wire()["binding_persisted"] is False
    assert result.to_wire()["approval_verified"] is False


def test_neutral_contract_imports_no_specification_or_service_dependencies():
    from aware_issue_sdk import specification_iteration

    assert (
        specification_iteration.OPERATION_REF
        == "issue_sdk.observe_specification_iteration_binding"
    )
    # Imports in this module are stdlib and the already neutral Issue runtime;
    # test process may separately load integration packages, so inspect source.
    import ast
    from pathlib import Path

    tree = ast.parse(Path(specification_iteration.__file__).read_text())
    imports = {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert imports <= {"dataclasses", "enum", "aware_issue_runtime"}
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import sys; sys.path.insert(0, sys.argv[1]); "
                "from aware_issue_sdk import IssueSpecificationIterationBindingObserveRequest, IssueSdkOperationClient; "
                "assert not any(name.startswith(('aware_specification', 'aware_issue_service', 'aware_content_service')) for name in sys.modules)"
            ),
            str(Path(specification_iteration.__file__).parents[1]),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
