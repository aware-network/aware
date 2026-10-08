"""Typed fixtures prove carriage, not physical publication or owner admission."""

import ast
import json
import os
import subprocess
import sys
import tomllib
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path

import pytest
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationPhaseDefinition,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
)
from aware_specification_sdk import (
    SPECIFICATION_DRAFT_EVIDENCE_PROFILE,
    SpecificationDraftEvidence,
    SpecificationDraftMemberBinding,
    SpecificationDraftPhysicalEffect,
    SpecificationDraftRequest,
    SpecificationDraftResult,
    SpecificationObservation,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)

SHA = "sha256:" + "1" * 64
KINDS = (
    "directory",
    "file",
    "file_write",
    "package_publication",
    "package_postimage",
    "cleanup_file",
    "cleanup_directory",
)


def effect(kind="file_write", **changes):
    return replace(
        SpecificationDraftPhysicalEffect(
            "plans/.aware-spec-draft-" + "a" * 32 + "/a",
            kind,
            "unknown",
            None,
            None,
            None,
            None,
            None,
            False,
        ),
        **changes,
    )


def evidence(**changes):
    return replace(
        SpecificationDraftEvidence(
            SPECIFICATION_DRAFT_EVIDENCE_PROFILE,
            "attempt:one",
            "issue:one",
            "execution:one",
            "client-intent:one",
            "intent",
            SHA,
            "plans/demo",
            "plans/.aware-spec-draft-" + "a" * 32,
            (SpecificationDraftMemberBinding("a", 1, SHA),),
            "none",
            (),
            (),
            (),
            True,
            False,
            False,
        ),
        **changes,
    )


def request():
    gate = SpecificationPhaseGateDefinition("g", "Promise", "contract", "evidence")
    phase = SpecificationPhaseDefinition("p", "Phase", 0, gate, description="Purpose")
    definition = SpecificationDefinition(
        "example",
        "Example",
        1,
        SHA,
        (SpecificationInvariantDefinition("safe", "Stay safe"),),
        (phase,),
        "Purpose",
    )
    return SpecificationDraftRequest(definition, "author", "intent")


def result(req):
    observation = SpecificationObservation(
        SpecificationSnapshot((req.definition,)),
        SHA,
        "fixture",
        "filesystem",
        "local_structural_observation",
        SHA,
        (),
    )
    return SpecificationDraftResult(observation, ("plans/demo/a",), "intent")


class Reader:
    def __init__(self, current=None):
        self.current = evidence() if current is None else current
        self.calls = 0

    def observe_draft_evidence(self):
        self.calls += 1
        if isinstance(self.current, BaseException):
            raise self.current
        return self.current


class Provider:
    def __init__(self, reader, *, failure=None, transform=lambda value: value):
        self.reader = reader
        self.failure = failure
        self.transform = transform
        self.calls = 0

    def observe(self, req):
        return result(request()).observation

    def create_draft(self, req):
        self.calls += 1
        self.reader.current = evidence(
            package_outcome="published",
            completion_verified=True,
            effects=(effect("package_publication", state="applied"),),
        )
        if self.failure is not None:
            raise self.failure
        return self.transform(result(req))


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("state", ["none", "applied", "unknown"])
def test_every_exact_kind_and_state_roundtrips(kind, state):
    value = effect(kind, state=state)
    encoded = asdict(value)
    assert SpecificationDraftPhysicalEffect(**encoded) == value
    assert value.before_identity is None


def test_order_repeated_paths_absence_and_both_durability_flags_are_lossless():
    events = tuple(effect(k) for k in KINDS) + (effect("file_write", state="applied"),)
    value = evidence(effects=events, durability_confirmed=True)
    assert tuple(e.kind for e in value.effects) == KINDS + ("file_write",)
    assert all(e.mode is None and e.after_digest is None for e in value.effects)
    assert value.durability_confirmed and not any(
        e.durability_confirmed for e in events
    )
    assert json.loads(json.dumps(asdict(value)))["package_outcome"] == "none"
    with pytest.raises(FrozenInstanceError):
        value.package_outcome = "published"
    with pytest.raises(FrozenInstanceError):
        value.effects[0].state = "none"


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "cleanup"},
        {"kind": []},
        {"state": "success"},
        {"mode": True},
        {"mode": -1},
        {"mode": 0o10000},
        {"before_digest": "sha256:" + "A" * 64},
        {"after_digest": "bad"},
        {"before_identity": [1, 2]},
        {"after_identity": (True, 2)},
        {"after_identity": (1,)},
        {"durability_confirmed": 1},
    ],
)
def test_invalid_effect_fields_refuse(changes):
    with pytest.raises(ValueError):
        effect(**changes)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/a",
        "../a",
        "a/../b",
        "a//b",
        "a/./b",
        "a\\b",
        "a/",
        "e\u0301/a",
        "a\x00b",
        "a\u0080b",
        "a" * 1025,
        "\ud800",
    ],
)
def test_noncanonical_member_paths_refuse(path):
    with pytest.raises(ValueError):
        SpecificationDraftMemberBinding(path, 0, SHA)


@pytest.mark.parametrize(
    "changes",
    [
        {"profile": "future"},
        {"attempt_ref": ""},
        {"issue_ref": None},
        {"protocol_manifest_sha256": "bad"},
        {"members": []},
        {"members": (object(),)},
        {"members": ()},
        {"effects": []},
        {"effects": (object(),)},
        {"package_outcome": "success"},
        {"residual_scratch_paths": []},
        {"cleanup_diagnostics": ["fault"]},
        {"cleanup_diagnostics": (None,)},
        {"ledger_complete": 1},
        {"completion_verified": 1},
        {"durability_confirmed": 1},
        {"target_locator": "../a"},
    ],
)
def test_invalid_evidence_fields_refuse(changes):
    with pytest.raises(ValueError):
        evidence(**changes)


def test_member_conflicts_duplicates_order_and_size_refuse():
    for members in (
        (SpecificationDraftMemberBinding("a", 0, SHA),) * 2,
        (
            SpecificationDraftMemberBinding("b", 0, SHA),
            SpecificationDraftMemberBinding("a", 0, SHA),
        ),
        (
            SpecificationDraftMemberBinding("a", 0, SHA),
            SpecificationDraftMemberBinding("a/b", 0, SHA),
        ),
    ):
        with pytest.raises(ValueError):
            evidence(members=members)
    for size in (-1, True, 2 * 1024**2 + 1):
        with pytest.raises(ValueError):
            SpecificationDraftMemberBinding("a", size, SHA)


def test_invalid_request_does_not_call_reader_or_provider():
    reader = Reader()
    provider = Provider(reader)
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(provider, draft_evidence_reader=reader).create_draft(
            object()
        )
    assert error.value.effect == "none" and error.value.evidence is None
    assert reader.calls == provider.calls == 0


def test_reader_success_attaches_original_evidence_without_authorizing_owners():
    reader = Reader()
    provider = Provider(reader)
    sdk = SpecificationSdkClient(provider, draft_evidence_reader=reader)
    observed = sdk.create_draft(request())
    assert observed.evidence == reader.current
    assert observed.evidence is not reader.current
    assert observed.evidence.effects[0] is not reader.current.effects[0]
    assert reader.calls == 2
    assert sdk.observe(SpecificationObserveRequest()) == result(request()).observation


@pytest.mark.parametrize(
    "transform",
    [
        lambda r: None,
        lambda r: object.__new__(SpecificationDraftResult),
        lambda r: replace(r, created_paths=("plans/demo/other",)),
        lambda r: replace(r, evidence=evidence()),
    ],
)
def test_malformed_result_retains_original_known_publication(transform):
    reader = Reader()
    provider = Provider(reader, transform=transform)
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(provider, draft_evidence_reader=reader).create_draft(
            request()
        )
    assert error.value.effect == "unknown"
    assert error.value.evidence.package_outcome == "published"
    assert provider.calls == 1


def test_nested_result_validation_happens_after_original_reader():
    reader = Reader()

    def incomplete(value):
        object.__delattr__(value.observation, "snapshot")
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=incomplete), draft_evidence_reader=reader
        ).create_draft(request())
    assert reader.calls == 2
    assert error.value.evidence.package_outcome == "published"
    assert error.value.effect == "unknown"


@pytest.mark.parametrize(
    "failure",
    [OSError("reader failed"), {}, object.__new__(SpecificationDraftEvidence)],
)
def test_postinvocation_reader_failure_keeps_incomplete_history_not_zero_effects(
    failure,
):
    reader = Reader(evidence(effects=(effect(),)))

    def unavailable(value):
        reader.current = failure
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=unavailable), draft_evidence_reader=reader
        ).create_draft(request())
    value = error.value.evidence
    assert error.value.code == "draft_evidence_unavailable"
    assert error.value.effect == "unknown"
    assert value.effects == (effect(),)
    assert value.package_outcome == "unknown"
    assert not value.ledger_complete and not value.completion_verified
    assert error.value.evidence_diagnostics == ("draft_evidence_unavailable",)


def test_unavailable_reader_before_invocation_does_not_invent_empty_ledger():
    reader = Reader(OSError("unavailable"))
    provider = Provider(reader)
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(provider, draft_evidence_reader=reader).create_draft(
            request()
        )
    assert provider.calls == 0
    assert error.value.evidence is None and error.value.effect == "unknown"


def test_known_publication_snapshot_survives_subsequent_reader_failure():
    reader = Reader(evidence(package_outcome="published", completion_verified=True))

    def unavailable(value):
        reader.current = OSError("reader failed")
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=unavailable), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.evidence.package_outcome == "published"
    assert not error.value.evidence.ledger_complete
    assert error.value.effect == "unknown"


@pytest.mark.parametrize("outcome", ["none", "unknown"])
def test_known_publication_cannot_regress_to_same_attempt_no_publication(outcome):
    original = evidence(package_outcome="published", completion_verified=True)
    reader = Reader(original)

    class Refuse:
        def create_draft(self, req):
            reader.current = evidence(package_outcome=outcome)
            raise SpecificationOperationError("owner_refused", effect="none")

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(Refuse(), draft_evidence_reader=reader).create_draft(
            request()
        )
    assert error.value.code == "owner_refused"
    assert error.value.effect == "unknown"
    assert error.value.evidence.package_outcome == "published"
    assert not error.value.evidence.ledger_complete
    assert not error.value.evidence.completion_verified
    assert error.value.evidence_diagnostics == ("draft_evidence_unavailable",)


@pytest.mark.parametrize("change", ["drop", "rewrite", "reorder"])
def test_later_complete_snapshot_cannot_discard_or_rewrite_original_events(change):
    history = (effect("directory"), effect("file"))
    original = evidence(effects=history)
    reader = Reader(original)
    published = effect("package_publication", state="applied")
    later_effects = {
        "drop": (published,),
        "rewrite": (replace(history[0], state="applied"), history[1], published),
        "reorder": (history[1], history[0], published),
    }[change]

    def inconsistent(value):
        reader.current = evidence(
            effects=later_effects,
            package_outcome="published",
            completion_verified=True,
        )
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=inconsistent), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.code == "draft_evidence_unavailable"
    assert error.value.effect == "unknown"
    assert error.value.evidence.effects == history
    assert error.value.evidence.package_outcome == "unknown"
    assert not error.value.evidence.ledger_complete
    assert not error.value.evidence.completion_verified
    assert error.value.evidence_diagnostics == ("draft_evidence_unavailable",)


def test_history_can_extend_while_residual_scratch_paths_shrink_during_cleanup():
    history = (effect("directory"), effect("file"))
    original = evidence(
        effects=history,
        residual_scratch_paths=("plans/scratch/a", "plans/scratch"),
    )
    reader = Reader(original)
    later = evidence(
        effects=history
        + (
            effect("package_publication", state="applied"),
            effect("cleanup_file", state="applied"),
            effect("cleanup_directory", state="applied"),
        ),
        package_outcome="published",
        completion_verified=True,
    )

    def cleaned(value):
        reader.current = later
        return value

    observed = SpecificationSdkClient(
        Provider(reader, transform=cleaned), draft_evidence_reader=reader
    ).create_draft(request())
    assert observed.evidence == later
    assert observed.evidence.effects[: len(history)] == history
    assert not observed.evidence.residual_scratch_paths
    assert observed.evidence.ledger_complete and observed.evidence.completion_verified


@pytest.mark.parametrize(
    "changes",
    [
        {"attempt_ref": "other"},
        {"issue_ref": "other"},
        {"execution_ref": "other"},
        {"client_intent_id": "other"},
        {"authoring_intent_ref": "other"},
        {"protocol_manifest_sha256": "sha256:" + "2" * 64},
        {"target_locator": "plans/other"},
        {"scratch_locator": "plans/.aware-spec-draft-" + "b" * 32},
        {"members": (SpecificationDraftMemberBinding("b", 1, SHA),)},
    ],
)
def test_cross_attempt_substitution_cannot_replace_original_history(changes):
    original = evidence(effects=(effect(),))
    reader = Reader(original)

    def substituted(value):
        reader.current = evidence(**changes)
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=substituted), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.evidence.attempt_ref == original.attempt_ref
    assert error.value.evidence.effects == original.effects
    assert error.value.evidence.package_outcome == "unknown"
    assert not error.value.evidence.ledger_complete


def test_defensive_capture_survives_provider_mutation_of_initial_value():
    initial = evidence(effects=(effect(),))
    reader = Reader(initial)

    def mutate(value):
        object.__setattr__(initial.effects[0], "state", "none")
        reader.current = OSError("unavailable")
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=mutate), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.evidence.effects[0].state == "unknown"


@pytest.mark.parametrize(
    "changes",
    [
        {"ledger_complete": False},
        {"completion_verified": False},
        {"package_outcome": "none"},
        {"package_outcome": "unknown"},
        {"residual_scratch_paths": ("plans/scratch",)},
        {"cleanup_diagnostics": ("descriptor_close:OSError",)},
    ],
)
def test_completion_requires_full_original_evidence(changes):
    reader = Reader()

    def unfinished(value):
        reader.current = replace(reader.current, **changes)
        return value

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=unfinished), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.effect == "unknown"
    assert error.value.evidence == reader.current


def test_provider_refusal_keeps_code_and_original_known_publication():
    reader = Reader()
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, failure=SpecificationOperationError("owner_refused")),
            draft_evidence_reader=reader,
        ).create_draft(request())
    assert error.value.code == "owner_refused"
    assert error.value.effect == "published"
    assert error.value.evidence.package_outcome == "published"


def test_provider_primary_refusal_survives_reader_failure():
    reader = Reader()

    class Refuse:
        def create_draft(self, req):
            reader.current = OSError("evidence failed")
            raise SpecificationOperationError("owner_refused")

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(Refuse(), draft_evidence_reader=reader).create_draft(
            request()
        )
    assert error.value.code == "owner_refused"
    assert error.value.effect == "unknown"
    assert not error.value.evidence.ledger_complete
    assert error.value.evidence_diagnostics == ("draft_evidence_unavailable",)


@pytest.mark.parametrize("failure", [OSError("provider failed"), KeyboardInterrupt()])
def test_untyped_provider_failures_preserve_evidence_and_unknown_effect(failure):
    reader = Reader()
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, failure=failure), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.effect == "unknown"
    assert error.value.evidence.package_outcome == "published"


def test_no_reader_is_explicit_compatibility_and_error_evidence_is_detached():
    reader = Reader()
    value = SpecificationSdkClient(Provider(reader)).create_draft(request())
    assert value.evidence is None
    source = evidence(effects=(effect(),))
    error = SpecificationOperationError("refused", evidence=source)
    object.__setattr__(source.effects[0], "state", "applied")
    assert error.evidence.effects[0].state == "unknown"


def test_package_metadata_and_imports_are_dependency_neutral():
    base = Path(__file__).parents[1]
    metadata = tomllib.loads((base / "pyproject.toml").read_text())["project"]
    assert metadata["version"] == "0.3.1"
    assert metadata["dependencies"] == ["aware-specification-runtime>=0.1.0,<0.2.0"]
    code = """
import sys
sys.path[:0] = sys.argv[1:]
import aware_specification_sdk as sdk
assert hasattr(sdk, 'SpecificationDraftEvidenceReader')
assert not any(n.startswith(('aware_issue', 'aware_protocol', 'aware_file_system', 'aware_specification_fs', 'aware_service', 'aware_command')) for n in sys.modules)
"""
    runtime = base.parents[3] / "libs/runtime/python"
    probe = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, str(base), str(runtime)],
        check=False,
        capture_output=True,
        text=True,
        env={"PATH": os.environ.get("PATH", "")},
        timeout=10,
    )
    assert probe.returncode == 0, probe.stderr
    for path in (base / "aware_specification_sdk").glob("*.py"):
        ast.parse(path.read_text())


@pytest.mark.parametrize("field", ["author_ref", "authoring_intent_ref", "definition"])
def test_provider_cannot_change_the_validated_request_and_manufacture_success(field):
    reader = Reader()
    req = request()

    def mutate(value):
        if field == "definition":
            object.__setattr__(req.definition, "title", "Different meaning")
        else:
            object.__setattr__(req, field, "different")
        return result(req)

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, transform=mutate), draft_evidence_reader=reader
        ).create_draft(req)
    assert error.value.effect == "unknown"
    assert error.value.evidence.package_outcome == "published"


@pytest.mark.parametrize("outcome", ["none", "unknown"])
def test_provider_publication_claim_cannot_override_original_reader(outcome):
    reader = Reader()

    class Claimed:
        def create_draft(self, req):
            reader.current = evidence(package_outcome=outcome)
            raise SpecificationOperationError("claimed", effect="published")

    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(Claimed(), draft_evidence_reader=reader).create_draft(
            request()
        )
    assert error.value.effect == "unknown"
    assert error.value.evidence.package_outcome == outcome


def test_malformed_provider_error_preserves_original_evidence():
    reader = Reader()
    malformed = SpecificationOperationError("refused")
    del malformed.code
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, failure=malformed), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.code == "draft_provider_error_invalid"
    assert error.value.effect == "unknown"
    assert error.value.evidence.package_outcome == "published"


def test_value_and_typed_reader_handling_performs_no_source_io(monkeypatch):
    import builtins

    req = request()
    reader = Reader()
    provider = Provider(reader)

    def forbidden(*args, **kwargs):
        raise AssertionError("public SDK attempted source IO")

    monkeypatch.setattr(builtins, "open", forbidden)
    for name in ("open", "mkdir", "write", "rename"):
        monkeypatch.setattr(os, name, forbidden)
    value = SpecificationSdkClient(provider, draft_evidence_reader=reader).create_draft(
        req
    )
    assert value.evidence.completion_verified


def test_older_same_attempt_error_snapshot_does_not_replace_final_reader_history():
    reader = Reader()
    original = reader.current
    refusal = SpecificationOperationError("owner_refused", evidence=original)
    with pytest.raises(SpecificationOperationError) as error:
        SpecificationSdkClient(
            Provider(reader, failure=refusal), draft_evidence_reader=reader
        ).create_draft(request())
    assert error.value.code == "owner_refused"
    assert error.value.effect == "published"
    assert error.value.evidence == reader.current
    assert error.value.evidence.effects != original.effects
