from __future__ import annotations

import json
from pathlib import Path

from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes

FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "docs/specs/semantic-contract-runtime/fixtures/canonical-adapter-golden-v1.json"
)


def _all_keys(value: object) -> set[str]:
    if type(value) is dict:
        return set(value) | {key for item in value.values() for key in _all_keys(item)}
    if type(value) is list:
        return {key for item in value for key in _all_keys(item)}
    return set()


def test_golden_neutral_bodies_and_meta_adapter_boundary() -> None:
    root = json.loads(FIXTURE.read_text(encoding="utf-8"))
    neutral = root["neutral"]
    expectations = root["canonical_adapter_expectations"]
    for body_key, digest_key in (
        ("result_body", "result_body_digest"),
        ("transition_body", "transition_body_digest"),
        ("prepared_effect_body", "prepared_effect_body_digest"),
    ):
        assert (
            ContentDigest.of_bytes(canonical_json_bytes(neutral[body_key])).value
            == neutral[digest_key]
        )
    assert (
        neutral["transition_body_digest"]
        == expectations["semantic_transition_digest_must_equal"]
    )
    assert (
        neutral["prepared_effect_body_digest"]
        == expectations["semantic_effect_digest_must_equal"]
    )
    assert not (_all_keys(neutral) & set(root["neutral_forbidden_fields"]))
    assert expectations == {
        "accepts_caller_effect_as_authority": False,
        "committed_reread_required": True,
        "graph_anchor_binding_external": True,
        "head_cas_required": True,
        "independent_execution_required": True,
        "local_receipt_promotable": False,
        "reconciliation_outcomes": ["admit", "rebase", "reject"],
        "semantic_effect_digest_must_equal": neutral["prepared_effect_body_digest"],
        "semantic_transition_digest_must_equal": neutral["transition_body_digest"],
    }
