"""V5 envelope consistency only: no installed store or owner authority."""

import copy
import hashlib
import json
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticPackageCoordinate,
    SemanticValueCoordinate,
    canonical_json_bytes,
)
from aware_workspace_runtime import materialization_head_v5 as wire
from aware_workspace_runtime.semantic_materialization_publication import (
    WorkspaceSemanticMaterializationHeadV3,
    WorkspaceSemanticMaterializationOutputStateBindingV4,
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationRequestV3,
)


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _restamp(value):
    payload = {k: v for k, v in value.items() if k != "head_digest"}
    value["head_digest"] = _digest(
        canonical_json_bytes(
            {
                "contract": wire.HEAD_CONTRACT,
                "value": payload,
            }
        )
    )
    return value


def _binding(role, owner, coordinate, body):
    digest = _digest(body)
    return {
        "contract": wire.BINDING_CONTRACT,
        "role": role,
        "owner_contract": owner,
        "coordinate_digest": _digest(canonical_json_bytes(coordinate)),
        "body_ref": "cas://workspace-semantic-materialization/body/" + digest[7:],
        "body_digest": digest,
        "body_size": len(body),
    }


def _head(*, expected_revision=7):
    body = canonical_json_bytes({"result": "fixture construction"})
    contract = SemanticContractRef(
        "test.construction.v2", "2", ContentDigest.of_bytes(b"schema")
    )
    coordinate = SemanticValueCoordinate(
        "selected_result",
        contract,
        "test:construction",
        ContentDigest.of_bytes(body),
        len(body),
    )
    source = ContentDigest.of_bytes(b"source")
    request = WorkspaceSemanticMaterializationRequestV3.create(
        package=SemanticPackageCoordinate(
            "test.package", "ontology", ContentDigest.of_bytes(b"manifest")
        ),
        result_coordinate=coordinate,
        source_identity_digest=source,
        code_intent_digest=ContentDigest.of_bytes(b"intent"),
        code_match_digest=ContentDigest.of_bytes(b"match"),
        planning_input_digest=ContentDigest.of_bytes(b"planning"),
        execution_input_closure_digest=ContentDigest.of_bytes(b"inputs"),
        operation_result_digest=ContentDigest.of_bytes(b"result"),
        expected_head_revision=expected_revision,
    )
    pair_body = canonical_json_bytes({"source_epoch": source.value, "pair": 1})
    pair_coordinate = {"pair_digest": _digest(pair_body), "target": "test:lineage"}
    head = _restamp(
        {
            "contract": wire.HEAD_CONTRACT,
            "base_head": WorkspaceSemanticMaterializationHeadV3.create(
                request=request
            ).to_wire(),
            "package_occurrence": {
                "repository_ref": "repo",
                "workspace_ref": "workspace",
                "module_ref": "module",
                "package_id": "package",
                "package_root": "modules/module/package",
                "manifest_relative_path": "modules/module/package/aware.ontology.toml",
            },
            "incarnation_ref": "lineage:original",
            "source_epoch_digest": source.value,
            "meta_pair_binding": _binding(
                "meta_committed_pair", "test.pair.v2", pair_coordinate, pair_body
            ),
            "ontology_product_binding": _binding(
                "ontology_terminal_product", contract.key, coordinate.to_wire(), body
            ),
            "predecessor_head_digest": None,
            "operation_ref": "command:one",
            "operation_digest": _digest(b"operation"),
            "output_state_bindings": [],
        }
    )
    return head, pair_coordinate, pair_body, body


def test_exact_head_roundtrip_matches_independent_hash_and_is_detached():
    value, pair, pair_body, product_body = _head()
    body = wire.encode_head(value, expected_output_roles=())
    result = wire.decode_head(body, expected_output_roles=())
    assert result == value and result is not value
    assert result["base_head"] is not value["base_head"]
    wire.verify_retained_owner_body(
        result["meta_pair_binding"], coordinate_wire=pair, body=pair_body
    )
    wire.verify_retained_owner_body(
        result["ontology_product_binding"],
        coordinate_wire=result["base_head"]["result_coordinate"],
        body=product_body,
    )
    result["base_head"]["package"]["package_ref"] = "changed"
    assert (
        wire.decode_head(body, expected_output_roles=())["base_head"]["package"][
            "package_ref"
        ]
        == "test.package"
    )


def test_fresh_command_preserves_the_operation_independent_pair_and_nonzero_genesis_revision():
    left, _, _, _ = _head()
    right = copy.deepcopy(left)
    right["operation_ref"] = "command:two"
    right["operation_digest"] = _digest(b"operation:two")
    _restamp(right)
    assert wire.encode_head(left, expected_output_roles=()) != wire.encode_head(
        right, expected_output_roles=()
    )
    assert left["meta_pair_binding"] == right["meta_pair_binding"]
    assert right["base_head"]["request"]["expected_head_revision"] == 7


@pytest.mark.parametrize("field", sorted(wire._HEAD_FIELDS))
def test_missing_head_fields_refuse(field):
    value, _, _, _ = _head()
    del value[field]
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        wire.encode_head(value, expected_output_roles=())


@pytest.mark.parametrize(
    "fault",
    [
        "source",
        "result_coordinate",
        "result_body",
        "result_size",
        "owner_contract",
        "body_ref",
        "pair_role",
        "base_digest",
        "base_v4",
        "extra_field",
        "boolean_size",
        "zero_size",
        "oversized_body",
        "operation_nfc",
        "unknown_version",
    ],
)
def test_coherently_restamped_inconsistent_heads_refuse(fault):
    value, _, _, _ = _head()
    product = value["ontology_product_binding"]
    if fault == "source":
        value["source_epoch_digest"] = _digest(b"other source")
    elif fault == "result_coordinate":
        product["coordinate_digest"] = _digest(b"other coordinate")
    elif fault == "result_body":
        product["body_digest"] = _digest(b"other body")
        product["body_ref"] = (
            "cas://workspace-semantic-materialization/body/"
            + product["body_digest"][7:]
        )
    elif fault == "result_size":
        product["body_size"] += 1
    elif fault == "owner_contract":
        product["owner_contract"] = "other.owner"
    elif fault == "body_ref":
        product["body_ref"] += "0"
    elif fault == "pair_role":
        value["meta_pair_binding"]["role"] = "public_v5_head"
    elif fault == "base_digest":
        value["base_head"]["head_digest"] = _digest(b"wrong base")
    elif fault == "base_v4":
        value["base_head"]["contract"] = (
            "aware.workspace.semantic-materialization-head.v4"
        )
    elif fault == "extra_field":
        product["extra"] = 1
    elif fault == "boolean_size":
        product["body_size"] = True
    elif fault == "zero_size":
        product["body_size"] = 0
    elif fault == "oversized_body":
        product["body_size"] = 67_108_865
    elif fault == "operation_nfc":
        value["operation_ref"] = "command:e\u0301"
    elif fault == "unknown_version":
        value["contract"] = "aware.workspace.semantic-materialization-head.v6"
    _restamp(value)
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        wire.encode_head(value, expected_output_roles=())


@pytest.mark.parametrize("fault", ["body", "coordinate", "size"])
def test_owner_body_checks_preserve_complete_bytes(fault):
    value, coordinate, body, _ = _head()
    if fault == "body":
        body = body[:-1] + b" "
    elif fault == "coordinate":
        coordinate["target"] = "other:lineage"
    else:
        body += b" "
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        wire.verify_retained_owner_body(
            value["meta_pair_binding"], coordinate_wire=coordinate, body=body
        )


def test_canonical_and_duplicate_json_rejection():
    value, _, _, _ = _head()
    body = wire.encode_head(value, expected_output_roles=())
    for invalid in (
        body + b"\n",
        json.dumps(value).encode(),
        body[:-1] + b',"head_digest":"duplicate"}',
        b"[" * 1100,
    ):
        with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
            wire.decode_head(invalid, expected_output_roles=())


def test_declared_output_state_roles_require_complete_v4_bindings():
    value, _, _, _ = _head()
    base = wire.publication._parse_publication_head_v2_wire(value["base_head"])
    output = replace(base.result_coordinate, role="generated_output")
    prior, current = (
        ContentDigest.of_bytes(b"prior"),
        ContentDigest.of_bytes(b"current"),
    )
    binding = WorkspaceSemanticMaterializationOutputStateBindingV4(
        output,
        "test_output",
        wire.publication._body_ref(prior.value),
        prior,
        5,
        prior,
        wire.publication._body_ref(current.value),
        current,
        7,
        current,
    ).to_wire()
    value["output_state_bindings"] = [binding]
    _restamp(value)
    body = wire.encode_head(value, expected_output_roles=("generated_output",))
    assert wire.decode_head(body, expected_output_roles=("generated_output",)) == value
    for roles in ((), ("other_output",), ("generated_output", "generated_output")):
        with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
            wire.encode_head(value, expected_output_roles=roles)
    value["output_state_bindings"].append(binding)
    _restamp(value)
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        wire.encode_head(value, expected_output_roles=("generated_output",))


class _Hostile:
    calls = 0

    def __getattribute__(self, name):
        _Hostile.calls += 1
        raise AssertionError("foreign attribute call")

    def __eq__(self, other):
        _Hostile.calls += 1
        raise AssertionError("foreign equality call")


@pytest.mark.parametrize(
    "field",
    ["base_head", "meta_pair_binding", "operation_ref", "output_state_bindings"],
)
def test_hostile_values_reject_without_behavior(field):
    value, _, _, _ = _head()
    value[field] = _Hostile()
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        wire.encode_head(value, expected_output_roles=())
    assert _Hostile.calls == 0


def test_cyclic_and_overdeep_metadata_refuse_without_unbounded_serialization():
    value, _, _, _ = _head()
    cycle = []
    cycle.append(cycle)
    value["base_head"] = cycle
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError, match="traversal bound"
    ):
        wire.encode_head(value, expected_output_roles=())


def test_original_code_completion_result_coordinate_is_preserved():
    from test_semantic_materialization_publication import _graph_v2_fixture

    _runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=3, marker="a"
    )
    value, _, _, _ = _head()
    value["base_head"] = WorkspaceSemanticMaterializationHeadV3.create(
        request=request
    ).to_wire()
    value["source_epoch_digest"] = request.source_identity_digest.value
    coordinate = request.result_coordinate
    # Exact complete result bytes were emitted by the original Code runtime.
    body = snapshot.body_for(coordinate)
    value["ontology_product_binding"] = _binding(
        "ontology_terminal_product",
        coordinate.contract.key,
        coordinate.to_wire(),
        body.canonical_body,
    )
    _restamp(value)
    encoded = wire.encode_head(value, expected_output_roles=())
    assert (
        wire.decode_head(encoded, expected_output_roles=())["base_head"][
            "result_coordinate"
        ]
        == coordinate.to_wire()
    )
    assert invocation.target_package == request.package


def test_owner_coordinate_scalars_are_not_reinterpreted_as_workspace_tokens():
    coordinate = {"label": "", "ratio": 0.5, "optional": None}
    body = b"complete owner body"
    binding = _binding("meta_committed_pair", "test.owner", coordinate, body)
    wire.verify_retained_owner_body(binding, coordinate_wire=coordinate, body=body)
    for number in (float("nan"), float("inf"), -0.0):
        with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
            wire.verify_retained_owner_body(
                binding, coordinate_wire={"value": number}, body=body
            )


def test_v3_coordinate_ref_is_preserved_without_an_invented_4096_byte_limit():
    value, _, _, body = _head()
    base = wire.publication._parse_publication_head_v2_wire(value["base_head"])
    request = WorkspaceSemanticMaterializationRequestV3.create(
        package=base.package,
        result_coordinate=replace(
            base.result_coordinate, value_ref="test:" + "r" * 5000
        ),
        source_identity_digest=base.source_identity_digest,
        code_intent_digest=base.code_intent_digest,
        code_match_digest=base.code_match_digest,
        planning_input_digest=base.planning_input_digest,
        execution_input_closure_digest=base.execution_input_closure_digest,
        operation_result_digest=base.operation_result_digest,
        expected_head_revision=base.request.expected_head_revision,
    )
    value["base_head"] = WorkspaceSemanticMaterializationHeadV3.create(
        request=request
    ).to_wire()
    value["ontology_product_binding"] = _binding(
        "ontology_terminal_product",
        request.result_coordinate.contract.key,
        request.result_coordinate.to_wire(),
        body,
    )
    _restamp(value)
    encoded = wire.encode_head(value, expected_output_roles=())
    assert wire.decode_head(encoded, expected_output_roles=())["base_head"][
        "result_coordinate"
    ]["value_ref"].endswith("r" * 5000)


def test_head_and_declared_role_byte_count_bounds():
    value, _, _, _ = _head()
    for invalid in (b" " * 262_145, b"", bytearray(b"{}")):
        with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
            wire.decode_head(invalid, expected_output_roles=())
    for roles in (tuple(f"role_{n}" for n in range(65)), [], (_Hostile(),)):
        with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
            wire.encode_head(value, expected_output_roles=roles)
    assert _Hostile.calls == 0


@pytest.mark.parametrize("role", ["public_v5_head", "lineage_checkpoint"])
def test_private_workspace_domain_bindings_cannot_use_the_owner_coordinate_verifier(
    role,
):
    value, coordinate, body, _ = _head()
    binding = value["meta_pair_binding"]
    binding["role"] = role
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="semantic-owner body role",
    ):
        wire.verify_retained_owner_body(binding, coordinate_wire=coordinate, body=body)


def test_prior_record_revision_uses_the_v5_store_integer_domain():
    value, _, _, _ = _head(expected_revision=2**63)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="prior record revision bound",
    ):
        wire.encode_head(value, expected_output_roles=())
    value, _, _, _ = _head(expected_revision=2**63 - 1)
    assert (
        wire.decode_head(
            wire.encode_head(value, expected_output_roles=()), expected_output_roles=()
        )
        == value
    )
