from __future__ import annotations

import copy
import json

import pytest
from aware_workspace_runtime import (
    RepositoryEvidencePosture,
    RepositoryMutationKind,
    RepositoryMutationOutcome,
    WorkspaceRepositoryAuthorizedMutation,
    WorkspaceRepositoryEvidenceCheckpoint,
    WorkspaceRepositoryMutationReceipt,
    WorkspaceRepositoryMutationRequest,
    repository_authorized_mutation_from_payload,
    repository_authorized_mutation_payload,
    repository_change_evidence_from_payload,
    repository_content_delta_from_payload,
    repository_delta_capture_from_payload,
    repository_diff_page_from_payload,
    repository_diff_request_from_payload,
    repository_evidence_checkpoint_from_payload,
    repository_external_evidence_from_payload,
    repository_mutation_receipt_from_payload,
    repository_mutation_receipt_ref,
    repository_mutation_request_from_payload,
    repository_mutation_request_payload,
    workspace_repository_value_from_payload,
    workspace_repository_value_payload,
)
from test_change_evidence import (
    BINDING,
    NOW,
    _diff_values,
    _evidence,
    _external,
    _observation,
)
from test_repository_delta import capture, content_delta


def _mutation_receipt() -> WorkspaceRepositoryMutationReceipt:
    return WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=repository_mutation_receipt_ref(
            repository_binding_ref=BINDING,
            operation_ref="operation:codec",
            idempotency_key="request:codec",
        ),
        repository_binding_ref=BINDING,
        operation_ref="operation:codec",
        idempotency_key="request:codec",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="new.txt",
        expected_exists=False,
        expected_content_digest=None,
        outcome=RepositoryMutationOutcome.APPLIED,
        context_refs=("opaque:caller",),
        result_coordinate=_observation(6),
        result_entry_ref="entry:new",
        result_content_digest="content:new",
        result_size_bytes=8,
        request_body_evidence_ref="body:request",
        result_body_evidence_ref="body:result",
        delta_evidence_ref="delta:create",
    )


def _checkpoint() -> WorkspaceRepositoryEvidenceCheckpoint:
    return WorkspaceRepositoryEvidenceCheckpoint(
        consumer_key="coordination-issue-reader",
        repository_binding_ref=BINDING,
        observer_epoch="observer-epoch-1",
        accepted_cursor=6,
        evidence_revision=4,
        projection_digest="projection:4",
        accepted_at=NOW,
    )


@pytest.mark.parametrize(
    ("value", "decoder"),
    [
        (
            _evidence(RepositoryEvidencePosture.PROVIDER_CORRELATED),
            repository_change_evidence_from_payload,
        ),
        (_external(), repository_external_evidence_from_payload),
        (_mutation_receipt(), repository_mutation_receipt_from_payload),
        (_diff_values()[0], repository_diff_request_from_payload),
        (_diff_values()[1], repository_diff_page_from_payload),
        (_checkpoint(), repository_evidence_checkpoint_from_payload),
        (capture(), repository_delta_capture_from_payload),
        (content_delta(capture()), repository_content_delta_from_payload),
    ],
)
def test_every_top_level_value_round_trips_through_json(
    value: object, decoder: object
) -> None:
    payload = workspace_repository_value_payload(value)  # type: ignore[arg-type]
    transported = json.loads(json.dumps(payload))
    assert decoder(transported) == value  # type: ignore[operator]
    assert workspace_repository_value_from_payload(transported) == value


@pytest.mark.parametrize(
    ("field", "replacement", "match"),
    [
        ("contract_ref", "wrong-contract", "contract ref"),
        ("contract_version", "99", "contract version"),
        ("value_kind", "unknown", "value kind"),
    ],
)
def test_envelope_rejects_unknown_contract_and_kind(
    field: str, replacement: str, match: str
) -> None:
    payload = workspace_repository_value_payload(_external())
    payload[field] = replacement
    with pytest.raises(ValueError, match=match):
        workspace_repository_value_from_payload(payload)


def test_codec_rejects_missing_unknown_and_wrong_typed_fields() -> None:
    payload = workspace_repository_value_payload(_external())
    missing = copy.deepcopy(payload)
    del missing["value"]["observed_at"]  # type: ignore[index]
    with pytest.raises(ValueError, match="missing: observed_at"):
        workspace_repository_value_from_payload(missing)

    unknown = copy.deepcopy(payload)
    unknown["value"]["provider_payload"] = {"trusted": True}  # type: ignore[index]
    with pytest.raises(ValueError, match="unknown: provider_payload"):
        workspace_repository_value_from_payload(unknown)

    wrong_type = copy.deepcopy(payload)
    wrong_type["value"]["complete"] = 1  # type: ignore[index]
    with pytest.raises(ValueError, match="must be a boolean"):
        workspace_repository_value_from_payload(wrong_type)


def test_codec_revalidates_derived_refs_and_provenance_after_transport() -> None:
    evidence = _evidence(RepositoryEvidencePosture.WORKSPACE_OBSERVED)
    payload = workspace_repository_value_payload(evidence)
    tampered = copy.deepcopy(payload)
    tampered["value"]["evidence_ref"] = "tampered"  # type: ignore[index]
    with pytest.raises(ValueError, match="not deterministic"):
        workspace_repository_value_from_payload(tampered)

    posture = copy.deepcopy(payload)
    posture["value"]["posture"] = "workspace_authorized"  # type: ignore[index]
    posture["value"]["changed_entries"][0]["posture"] = "workspace_authorized"  # type: ignore[index]
    with pytest.raises(ValueError, match="mutation receipt"):
        workspace_repository_value_from_payload(posture)


def test_codec_preserves_opaque_context_ref_order_without_interpretation() -> None:
    payload = workspace_repository_value_payload(_external())
    restored = repository_external_evidence_from_payload(
        json.loads(json.dumps(payload))
    )
    assert restored.context_refs == ("agent-session:1", "issue:42")


def test_specific_decoder_rejects_a_different_valid_value_kind() -> None:
    payload = workspace_repository_value_payload(_checkpoint())
    with pytest.raises(ValueError, match="Expected repository evidence value kind"):
        repository_diff_page_from_payload(payload)


def test_mutation_operation_request_and_result_are_strict_and_lossless() -> None:
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:transport",
        idempotency_key="request:transport",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="src/new.txt",
        expected_exists=False,
        expected_content_digest=None,
        content=b"hello\x00aware",
        context_refs=("issue:42",),
    )
    request_payload = json.loads(
        json.dumps(repository_mutation_request_payload(request))
    )
    assert repository_mutation_request_from_payload(request_payload) == request

    failed_receipt = WorkspaceRepositoryMutationReceipt(
        mutation_receipt_ref=repository_mutation_receipt_ref(
            repository_binding_ref=BINDING,
            operation_ref="operation:transport",
            idempotency_key="request:transport",
        ),
        repository_binding_ref=BINDING,
        operation_ref="operation:transport",
        idempotency_key="request:transport",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="src/new.txt",
        expected_exists=False,
        expected_content_digest=None,
        outcome=RepositoryMutationOutcome.CONFLICT,
        context_refs=("issue:42",),
        error_code="snapshot_existence_mismatch",
    )
    result = WorkspaceRepositoryAuthorizedMutation(failed_receipt, None)
    result_payload = json.loads(
        json.dumps(repository_authorized_mutation_payload(result))
    )
    assert repository_authorized_mutation_from_payload(result_payload) == result


def test_mutation_operation_codec_preserves_exact_text_replacements() -> None:
    from aware_workspace_runtime import WorkspaceRepositoryTextReplacement

    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:replace",
        idempotency_key="request:replace",
        mutation_kind=RepositoryMutationKind.UPDATE,
        expected_coordinate=_observation(6),
        target_path="src/existing.txt",
        expected_exists=True,
        expected_content_digest="sha256:" + "a" * 64,
        text_replacements=(
            WorkspaceRepositoryTextReplacement(
                old_text="before",
                new_text="after",
            ),
        ),
        context_refs=("work-context:42",),
    )

    payload = json.loads(json.dumps(repository_mutation_request_payload(request)))

    assert payload["value"]["text_replacements"] == [  # type: ignore[index]
        {"old_text": "before", "new_text": "after"}
    ]
    assert repository_mutation_request_from_payload(payload) == request


def test_mutation_operation_codec_rejects_noncanonical_content_and_tampering() -> None:
    request = WorkspaceRepositoryMutationRequest(
        operation_ref="operation:transport",
        idempotency_key="request:transport",
        mutation_kind=RepositoryMutationKind.CREATE,
        expected_coordinate=_observation(5),
        target_path="new.txt",
        expected_exists=False,
        expected_content_digest=None,
        content=b"aware",
    )
    payload = repository_mutation_request_payload(request)
    invalid_content = copy.deepcopy(payload)
    invalid_content["value"]["content_base64"] = "not base64"  # type: ignore[index]
    with pytest.raises(ValueError, match="canonical base64"):
        repository_mutation_request_from_payload(invalid_content)

    unknown = copy.deepcopy(payload)
    unknown["value"]["provider"] = "filesystem"  # type: ignore[index]
    with pytest.raises(ValueError, match="unknown: provider"):
        repository_mutation_request_from_payload(unknown)


@pytest.fixture(scope="module")
def receipt_encoding_predecessor():
    import hashlib
    import importlib.util
    import subprocess
    from pathlib import Path

    root = next(p for p in Path(__file__).parents if (p / "aware.repo.toml").exists())
    packet = json.loads(
        (
            root
            / "docs/reports/workspace-tree-receipt-index-encoding-performance-inputs-20261013.json"
        ).read_text()
    )
    pin = next(
        row
        for row in packet["preimages"]
        if row["path"].endswith("/change_evidence_codec.py")
    )
    body = subprocess.check_output(
        ["git", "show", packet["capture_revision"] + ":" + pin["path"]], cwd=root
    )
    assert hashlib.sha256(body).hexdigest() == pin["sha256"]
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(
            "aware_workspace_runtime._receipt_encoding_predecessor", loader=None
        )
    )
    exec(compile(body, pin["path"], "exec"), module.__dict__)  # noqa: S102 -- hash-verified committed source
    return module


@pytest.mark.parametrize(
    "value",
    [
        _external(),
        _mutation_receipt(),
        _diff_values()[0],
        _diff_values()[1],
        _checkpoint(),
        capture(),
        content_delta(capture()),
        _evidence(RepositoryEvidencePosture.PROVIDER_CORRELATED),
    ],
)
def test_receipt_encoding_preserves_predecessor_payload_and_every_fresh_field(
    value, receipt_encoding_predecessor
):
    import dataclasses

    from aware_workspace_runtime import change_evidence_codec as current

    expected = receipt_encoding_predecessor.workspace_repository_value_payload(value)
    assert current.workspace_repository_value_payload(value) == expected
    assert json.dumps(
        current.workspace_repository_value_payload(value),
        sort_keys=True,
        separators=(",", ":"),
    ) == json.dumps(expected, sort_keys=True, separators=(",", ":"))
    # Compare each mutation with the actual original encoder rather than
    # adding new coercions or acceptance rules to these established codecs.
    for field in dataclasses.fields(value):
        changed = copy.copy(value)
        object.__setattr__(changed, field.name, None)
        outcomes = []
        for module in (receipt_encoding_predecessor, current):
            try:
                outcomes.append(
                    ("value", module.workspace_repository_value_payload(changed))
                )
            except (ValueError, TypeError, AttributeError) as error:
                outcomes.append((type(error).__name__, str(error)))
        assert outcomes[0] == outcomes[1], field.name
    assert current.workspace_repository_value_payload(value) == expected


def test_receipt_encoding_reflects_changes_after_prior_success(
    receipt_encoding_predecessor,
):
    from aware_workspace_runtime import change_evidence_codec as current

    value = _mutation_receipt()
    first = current.workspace_repository_value_payload(value)
    object.__setattr__(value, "target_path", "changed-after-first-encoding.txt")
    successor = current.workspace_repository_value_payload(value)
    assert successor == receipt_encoding_predecessor.workspace_repository_value_payload(
        value
    )
    assert first["value"]["target_path"] == "new.txt"
    assert successor["value"]["target_path"] == "changed-after-first-encoding.txt"


@pytest.fixture(scope="module")
def closed_receipt_predecessor():
    import hashlib
    import importlib.util
    import subprocess
    from pathlib import Path

    root = next(
        path for path in Path(__file__).parents if (path / "aware.repo.toml").exists()
    )
    packet = json.loads(
        (
            root
            / "docs/reports/workspace-receipt-closed-schema-conversion-performance-inputs-20261014.json"
        ).read_text()
    )
    pin = packet["preimages"][0]
    body = subprocess.check_output(
        ["git", "show", packet["capture_revision"] + ":" + pin["path"]], cwd=root
    )
    assert hashlib.sha256(body).hexdigest() == pin["sha256"]
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(
            "aware_workspace_runtime._closed_receipt_predecessor", loader=None
        )
    )
    exec(compile(body, pin["path"], "exec"), vars(module))  # noqa: S102 -- digest-verified committed source
    return module


@pytest.mark.parametrize(
    "value",
    [
        _external(),
        _mutation_receipt(),
        *_diff_values(),
        _checkpoint(),
        capture(),
        content_delta(capture()),
        _evidence(RepositoryEvidencePosture.PROVIDER_CORRELATED),
    ],
)
def test_closed_receipt_every_field_fresh_and_literal_wire_parity(
    closed_receipt_predecessor, value
):
    from dataclasses import fields

    from aware_workspace_runtime import change_evidence_codec as current

    old = closed_receipt_predecessor
    original = current.workspace_repository_value_payload(value)
    assert original == old.workspace_repository_value_payload(value)
    for field in fields(value):
        for changed in (None, "changed after prior conversion", True):
            member = copy.copy(value)
            object.__setattr__(member, field.name, changed)
            results = []
            for module in (old, current):
                try:
                    results.append(
                        ("value", module.workspace_repository_value_payload(member))
                    )
                except (ValueError, TypeError, AttributeError, KeyError) as error:
                    results.append((type(error).__name__, str(error)))
            assert results[0] == results[1], (type(value).__name__, field.name, changed)
    assert current.workspace_repository_value_payload(value) == original
    assert json.dumps(original, sort_keys=True, separators=(",", ":")) == json.dumps(
        old.workspace_repository_value_payload(value),
        sort_keys=True,
        separators=(",", ":"),
    )


@pytest.mark.parametrize(
    "mode",
    [
        "code",
        "defaults",
        "keyword_defaults",
        "copy",
        "entry",
        "registry",
        "original_map",
    ],
)
def test_closed_receipt_authenticates_dispatch_before_foreign_calls(monkeypatch, mode):
    import types

    from aware_workspace_runtime import change_evidence_codec as current

    value = _mutation_receipt()
    entry = current._RECEIPT_FIELDS_BY_ID[id(type(value))]
    converter, code = entry[2]
    calls = []

    def foreign(*args, **kwargs):
        raise AssertionError("foreign receipt converter must not execute")

    class Foreign:
        def get(self, *args):
            calls.append(True)
            raise AssertionError("foreign registry must not execute")

        def __getitem__(self, key):
            calls.append(True)
            raise AssertionError("foreign entry must not execute")

    with monkeypatch.context() as patch:
        if mode == "code":
            patch.setattr(converter, "__code__", foreign.__code__)
        elif mode == "defaults":
            patch.setattr(converter, "__defaults__", (foreign,))
        elif mode == "keyword_defaults":
            patch.setattr(converter, "__kwdefaults__", {"guard": foreign})
        elif mode == "copy":
            copied = types.FunctionType(code, converter.__globals__)
            patch.setitem(
                current._RECEIPT_FIELDS_BY_ID,
                id(type(value)),
                (entry[0], entry[1], (copied, code), *entry[3:]),
            )
        elif mode == "entry":
            patch.setitem(current._RECEIPT_FIELDS_BY_ID, id(type(value)), Foreign())
        elif mode == "original_map":
            patch.setattr(current, "_RECEIPT_ORIGINAL_ENTRIES", Foreign())
        else:
            patch.setattr(current, "_RECEIPT_FIELDS_BY_ID", Foreign())
        with pytest.raises(TypeError, match="Original receipt compiler"):
            current.repository_mutation_receipt_payload(value)
        assert calls == []
    assert current.repository_mutation_receipt_payload(value)


@pytest.mark.parametrize(
    "mutation", ["field_name", "field_kind", "reorder", "hint", "metadata_copy"]
)
def test_closed_receipt_schema_changes_use_original_generic_behavior(
    monkeypatch, mutation, closed_receipt_predecessor
):
    import dataclasses

    from aware_workspace_runtime import change_evidence_codec as current

    value = _mutation_receipt()
    cls = type(value)
    metadata = vars(cls)["__dataclass_fields__"]
    hints = current._type_hints(cls)
    old_hints = closed_receipt_predecessor._type_hints(cls)
    with monkeypatch.context() as patch:
        if mutation == "field_name":
            patch.setattr(metadata["target_path"], "name", "context_refs")
        elif mutation == "field_kind":
            patch.setattr(
                metadata["target_path"], "_field_type", dataclasses._FIELD_CLASSVAR
            )
        elif mutation == "reorder":
            patch.setattr(
                cls, "__dataclass_fields__", dict(reversed(tuple(metadata.items())))
            )
        elif mutation == "metadata_copy":
            patch.setattr(cls, "__dataclass_fields__", metadata.copy())
        else:
            patch.setitem(hints, "target_path", tuple[str, ...])
            patch.setitem(old_hints, "target_path", tuple[str, ...])
        expected = closed_receipt_predecessor.repository_mutation_receipt_payload(value)
        actual = current.repository_mutation_receipt_payload(value)
        assert actual == expected
        assert json.dumps(actual, separators=(",", ":")) == json.dumps(
            expected, separators=(",", ":")
        )


def test_closed_receipt_unsupported_and_subclass_fallback(closed_receipt_predecessor):
    from dataclasses import dataclass

    from aware_workspace_runtime import change_evidence_codec as current

    @dataclass
    class Extra:
        label: str
        count: int | None

    class SubReceipt(WorkspaceRepositoryMutationReceipt):
        pass

    value = _mutation_receipt()
    sub = SubReceipt(
        **{name: getattr(value, name) for name in value.__dataclass_fields__}
    )
    for member, annotation in (
        (Extra("new", None), Extra),
        (sub, WorkspaceRepositoryMutationReceipt),
        (value, WorkspaceRepositoryMutationReceipt),
        (42, str),
    ):
        assert current._encode(
            member, annotation
        ) == closed_receipt_predecessor._encode(member, annotation)


def test_closed_receipt_preserves_omission_double_read_and_error_order(
    closed_receipt_predecessor,
):
    from aware_workspace_runtime import change_evidence_codec as current

    value = _mutation_receipt()
    cls = type(value)
    names = tuple(value.__dataclass_fields__)

    # Noneligible duck values keep all the original property behavior and order.
    class Duck:
        def __init__(self):
            self.calls = []

        def __getattr__(self, name):
            self.calls.append(name)
            return getattr(value, name)

    observed = []
    for module in (closed_receipt_predecessor, current):
        member = Duck()
        payload = module._encode(member, cls)
        observed.append((payload, member.calls))
    assert observed[0] == observed[1]
    assert observed[0][1] == list(names)


def test_closed_receipt_conserves_all_frozen_functions_and_prior_tests():
    import ast
    import hashlib
    from pathlib import Path

    root = next(
        path for path in Path(__file__).parents if (path / "aware.repo.toml").exists()
    )
    packet = json.loads(
        (
            root
            / "docs/reports/workspace-receipt-closed-schema-conversion-performance-inputs-20261014.json"
        ).read_text()
    )
    for index, pin in enumerate(packet["preimages"]):
        current = {
            node.name: hashlib.sha256(
                ast.dump(node, include_attributes=False).encode()
            ).hexdigest()
            for node in ast.parse((root / pin["path"]).read_bytes()).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        names = packet["frozen_functions"] if index == 0 else pin["declarations"]
        for name in names:
            assert current[name] == pin["declarations"][name], name
        if index == 0:
            assert set(current) - set(pin["declarations"]) == {
                "_compile_receipt_fields"
            }


@pytest.mark.parametrize("behavior", ("return", "raise", "restore"))
def test_closed_receipt_code_poison_variants_never_enter(monkeypatch, behavior):
    from aware_workspace_runtime import change_evidence_codec as current

    value = _mutation_receipt()
    entry = current._RECEIPT_FIELDS_BY_ID[id(type(value))]
    function, code = entry[2]
    calls = []
    namespace = {}
    body = "def foreign(*args, **kwargs):\n    _poison_calls.append(True)\n"
    if behavior == "restore":
        body += "    _poison_function.__code__ = _poison_code\n"
    body += (
        "    raise RuntimeError('foreign poison')\n"
        if behavior == "raise"
        else "    return {}\n"
    )
    exec(body, namespace)  # noqa: S102 -- fixed diagnostic branches only
    with monkeypatch.context() as patch:
        patch.setitem(current.__dict__, "_poison_calls", calls)
        patch.setitem(current.__dict__, "_poison_function", function)
        patch.setitem(current.__dict__, "_poison_code", code)
        patch.setattr(function, "__code__", namespace["foreign"].__code__)
        with pytest.raises(TypeError, match="Original receipt compiler"):
            current.repository_mutation_receipt_payload(value)
        assert calls == []


@pytest.mark.parametrize("change", ("code", "registry"))
def test_closed_receipt_reauthenticates_after_metadata_return(monkeypatch, change):
    from aware_workspace_runtime import change_evidence_codec as current

    value = _mutation_receipt()
    entry = current._RECEIPT_FIELDS_BY_ID[id(type(value))]
    function = entry[2][0]
    original = current._type_hints

    def foreign(*args, **kwargs):
        raise AssertionError("changed compiler must never execute")

    def hints(cls):
        if change == "code":
            monkeypatch.setattr(function, "__code__", foreign.__code__)
        else:
            monkeypatch.setattr(current, "_RECEIPT_FIELDS_BY_ID", {})
        return original(cls)

    monkeypatch.setattr(current, "_type_hints", hints)
    with pytest.raises(TypeError, match="Original receipt compiler"):
        current.repository_mutation_receipt_payload(value)


@pytest.fixture
def cold_receipt_predecessor(closed_receipt_predecessor):
    closed_receipt_predecessor._type_hints.cache_clear()
    try:
        yield closed_receipt_predecessor
    finally:
        closed_receipt_predecessor._type_hints.cache_clear()


@pytest.fixture
def cold_receipt_candidate():
    import importlib.util
    from pathlib import Path

    from aware_workspace_runtime import change_evidence_codec as current

    path = Path(current.__file__)
    module = importlib.util.module_from_spec(
        importlib.util.spec_from_loader(
            "aware_workspace_runtime._cold_receipt_candidate", loader=None
        )
    )
    exec(compile(path.read_bytes(), str(path), "exec"), vars(module))  # noqa: S102 -- exact current authored codec, isolated lazy cache
    assert module._type_hints.cache_info().currsize == 0
    return module


def test_closed_receipt_compilation_preserves_lazy_shared_cache(
    cold_receipt_candidate, cold_receipt_predecessor
):
    for module in (cold_receipt_predecessor, cold_receipt_candidate):
        assert module._type_hints.cache_info().currsize == 0
    before = cold_receipt_candidate._type_hints.cache_info()
    assert len(cold_receipt_candidate._compile_receipt_fields()) == 20
    assert cold_receipt_candidate._type_hints.cache_info() == before


def test_closed_receipt_cold_encoder_annotation_parity(
    monkeypatch, cold_receipt_candidate, cold_receipt_predecessor
):
    value = _mutation_receipt()
    monkeypatch.setitem(type(value).__annotations__, "target_path", tuple[str, ...])
    expected = cold_receipt_predecessor.repository_mutation_receipt_payload(value)
    actual = cold_receipt_candidate.repository_mutation_receipt_payload(value)
    assert actual == expected
    assert actual["value"]["target_path"] == list(value.target_path)
    assert json.dumps(actual, sort_keys=True, separators=(",", ":")) == json.dumps(
        expected, sort_keys=True, separators=(",", ":")
    )


def test_closed_receipt_cold_decoder_annotation_parity(
    monkeypatch, cold_receipt_candidate, cold_receipt_predecessor
):
    payload = workspace_repository_value_payload(_mutation_receipt())
    monkeypatch.setitem(
        WorkspaceRepositoryMutationReceipt.__annotations__,
        "target_path",
        tuple[str, ...],
    )
    outcomes = []
    for module in (cold_receipt_predecessor, cold_receipt_candidate):
        assert module._type_hints.cache_info().currsize == 0
        with pytest.raises(ValueError) as refusal:
            module.repository_mutation_receipt_from_payload(payload)
        outcomes.append((type(refusal.value), str(refusal.value)))
    assert outcomes[0] == outcomes[1]
    assert "target_path must be an array" in outcomes[0][1]


@pytest.mark.parametrize("change", ("replace", "remove_in_place"))
def test_closed_receipt_hint_return_schema_membership_parity(
    monkeypatch, change, cold_receipt_candidate, cold_receipt_predecessor
):
    value = _mutation_receipt()
    cls = type(value)
    original_metadata = vars(cls)["__dataclass_fields__"]
    original_rows = tuple(original_metadata.items())
    reduced = dict(original_rows)
    del reduced["target_path"]
    outcomes = []
    for module in (cold_receipt_predecessor, cold_receipt_candidate):
        original_hints = module._type_hints
        calls = []
        try:
            with monkeypatch.context() as patch:

                def hint_return(
                    annotation, _calls=calls, _original_hints=original_hints
                ):
                    if annotation is cls:
                        _calls.append(annotation)
                        if change == "replace":
                            patch.setattr(cls, "__dataclass_fields__", reduced)
                        else:
                            original_metadata.pop("target_path", None)
                    return _original_hints(annotation)

                patch.setattr(module, "_type_hints", hint_return)
                outcomes.append(module.repository_mutation_receipt_payload(value))
                assert calls == [cls]
        finally:
            original_metadata.clear()
            original_metadata.update(original_rows)
        assert vars(cls)["__dataclass_fields__"] is original_metadata
    assert outcomes[0] == outcomes[1]
    assert "target_path" not in outcomes[0]["value"]


@pytest.mark.parametrize("change", ("replace", "reorder_in_place"))
def test_closed_receipt_hint_return_schema_error_order_parity(
    monkeypatch, change, cold_receipt_candidate, cold_receipt_predecessor
):
    value = _mutation_receipt()
    cls = type(value)
    original_metadata = vars(cls)["__dataclass_fields__"]
    original_rows = tuple(original_metadata.items())
    reordered = dict(reversed(original_rows))
    outcomes = []
    for module in (cold_receipt_predecessor, cold_receipt_candidate):
        original_hints = module._type_hints
        calls = []
        reads = []
        try:
            with monkeypatch.context() as patch:

                def hint_return(
                    annotation, _calls=calls, _original_hints=original_hints
                ):
                    if annotation is cls:
                        _calls.append(annotation)
                        if change == "replace":
                            patch.setattr(cls, "__dataclass_fields__", reordered)
                        else:
                            original_metadata.clear()
                            original_metadata.update(reordered)
                    return _original_hints(annotation)

                def read(member, name, _reads=reads):
                    if name in ("target_path", "context_refs"):
                        _reads.append(name)
                        raise RuntimeError(name)
                    return object.__getattribute__(member, name)

                patch.setattr(module, "_type_hints", hint_return)
                patch.setattr(cls, "__getattribute__", read)
                with pytest.raises(RuntimeError) as refusal:
                    module.repository_mutation_receipt_payload(value)
                outcomes.append((str(refusal.value), reads))
                assert calls == [cls]
        finally:
            original_metadata.clear()
            original_metadata.update(original_rows)
    assert outcomes[0] == outcomes[1] == ("context_refs", ["context_refs"])


def test_closed_receipt_warm_decoder_preserves_predecessor_cache_history(
    monkeypatch, cold_receipt_candidate, cold_receipt_predecessor
):
    outcomes = []
    value = _mutation_receipt()
    for module in (cold_receipt_predecessor, cold_receipt_candidate):
        assert module._type_hints.cache_info().currsize == 0
        payload = module.repository_mutation_receipt_payload(value)
        assert module._type_hints.cache_info().currsize > 0
        with monkeypatch.context() as patch:
            patch.setitem(type(value).__annotations__, "target_path", tuple[str, ...])
            decoded = module.repository_mutation_receipt_from_payload(payload)
            outcomes.append(decoded.target_path)
    assert outcomes == [value.target_path, value.target_path]


def _nullable_codec_specimen(module, scalar):
    from dataclasses import fields
    from types import UnionType

    # Descriptive codec values only: this never constructs an authority handle.
    for entry in module._RECEIPT_FIELDS_BY_ID.values():
        cls = entry[0]
        for _, name, hint, _, _ in entry[1]:
            if type(hint) is not UnionType or len(hint.__args__) != 2:
                continue
            if not any(arg is scalar for arg in hint.__args__) or not any(
                arg is type(None) for arg in hint.__args__
            ):
                continue
            value = object.__new__(cls)
            for field in fields(cls):
                object.__setattr__(value, field.name, None)
            return value, cls, name
    raise AssertionError("Declared nullable primitive required")


@pytest.mark.parametrize("scalar,member", [(str, "value"), (int, 7)])
@pytest.mark.parametrize("reverse", [False, True])
def test_closed_receipt_exact_nullable_members_use_fast_leaf(
    monkeypatch, scalar, member, reverse, cold_receipt_predecessor
):
    from aware_workspace_runtime import change_evidence_codec as current

    value, cls, name = _nullable_codec_specimen(current, scalar)
    hint = type(None) | scalar if reverse else scalar | type(None)
    assert hint is not next(
        row[2] for row in current._RECEIPT_FIELDS_BY_ID[id(cls)][1] if row[1] == name
    )
    for module in (cold_receipt_predecessor, current):
        monkeypatch.setitem(module._type_hints(cls), name, hint)
    calls = []

    def union_dispatch(*args):
        calls.append(args)
        raise AssertionError("Exact primitive nullable must not use union dispatch")

    with monkeypatch.context() as patch:
        patch.setattr(current, "_encode_union", union_dispatch)
        for replacement in (None, member, object()):
            object.__setattr__(value, name, replacement)
            outcomes = []
            for module in (cold_receipt_predecessor, current):
                try:
                    outcomes.append(("value", module._encode(value, cls)))
                except TypeError as error:
                    outcomes.append((type(error), str(error)))
            assert outcomes[0] == outcomes[1]
        assert calls == []


@pytest.mark.parametrize(
    "shape",
    [
        "other_scalar",
        "other_boolean",
        "extra_argument",
        "class_argument",
        "lookalike",
        "typing_union",
    ],
)
def test_closed_receipt_other_nullable_shapes_keep_literal_fallback(
    monkeypatch, shape, cold_receipt_predecessor
):
    import typing

    from aware_workspace_runtime import change_evidence_codec as current

    value, cls, name = _nullable_codec_specimen(current, str)
    calls = []

    class EqualityPoison(type):
        __hash__ = type.__hash__

        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("Hint recognition must not call class equality")

    class Other(metaclass=EqualityPoison):
        pass

    class Lookalike:
        def __eq__(self, other):
            calls.append("equality")
            raise AssertionError("Hint recognition must not call object equality")

        @property
        def __args__(self):
            calls.append("arguments")
            raise AssertionError("Lookalike union arguments must not be read")

    if shape == "other_scalar":
        hint, member = int | None, 7
    elif shape == "other_boolean":
        hint, member = bool | None, "value"
    elif shape == "extra_argument":
        hint, member = str | int | None, 7
    elif shape == "class_argument":
        hint, member = Other | None, "value"
    elif shape == "lookalike":
        hint, member = Lookalike(), "value"
    else:
        hint, member = typing.Optional[str], "value"  # noqa: UP045 -- original unsupported typing union fallback control
    for module in (cold_receipt_predecessor, current):
        monkeypatch.setitem(module._type_hints(cls), name, hint)
    object.__setattr__(value, name, member)
    outcomes = []
    for module in (cold_receipt_predecessor, current):
        try:
            outcomes.append(("value", module._encode(value, cls)))
        except TypeError as error:
            outcomes.append((type(error), str(error)))
    assert outcomes[0] == outcomes[1]
    assert calls == []


def test_closed_receipt_none_still_reads_hint_before_omission(
    monkeypatch, cold_receipt_predecessor
):
    from aware_workspace_runtime import change_evidence_codec as current

    value, cls, name = _nullable_codec_specimen(current, str)
    outcomes = []
    for module in (cold_receipt_predecessor, current):
        monkeypatch.delitem(module._type_hints(cls), name)
        with pytest.raises(KeyError) as error:
            module._encode(value, cls)
        outcomes.append(error.value.args)
    assert outcomes == [(name,), (name,)]
