from __future__ import annotations

import json
from pathlib import Path

from aware_issue_runtime import (
    build_issue_development_read_payload_v2,
    normalize_issue_activity_kind_payload_v1,
    normalize_issue_lifecycle_payload_v1,
)

_ROOT = Path(__file__).resolve().parents[7]
_FIXTURE = (
    _ROOT
    / "workspaces/aware_coordination/modules/workflow/sdks/issue/python/contracts"
    / "development_read_projection/v2"
    / "issue-development-read-projection-v2-fixtures.json"
)


def test_runtime_payload_matches_the_sealed_development_v2_fixture() -> None:
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    for case in fixture["cases"]:
        assert (
            build_issue_development_read_payload_v2(**case["input"])
            == case["expected_projection"]
        )


def test_runtime_owns_the_closed_normalization_vocabulary() -> None:
    assert normalize_issue_lifecycle_payload_v1("Resolved") == {
        "value": "closed",
        "raw_value": "Resolved",
        "classification": "normalized_alias",
    }
    assert normalize_issue_activity_kind_payload_v1("implementation-ready") == {
        "value": "implementation_ready",
        "raw_value": "implementation-ready",
        "classification": "normalized_alias",
    }
    assert (
        normalize_issue_activity_kind_payload_v1("new-tail-value")["classification"]
        == "unknown"
    )
