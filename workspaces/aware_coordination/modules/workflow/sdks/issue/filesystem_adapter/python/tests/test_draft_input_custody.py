"""Genuine Issue/Protocol/FileSystem custody loops, not installed SPEC/CLI."""

import copy
import gc
import os
import pickle
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from aware_file_system import retained_package as fs
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter import draft_package as issue
from aware_issue_sdk import IssueDraftInputCustodyRefusal, IssueDraftPackageRefusal
from aware_protocol_fs_adapter import specification_draft_target as protocol
from test_draft_package_admission import real_locator_context


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    values = real_locator_context(
        tmp_path,
        monkeypatch,
        target_locator="aware.protocol.toml",
        request_locator="aware.protocol.toml",
    )
    yield values
    _, _, target, plan, _, _ = values
    # Test-owned teardown of genuine originals, never a production fallback.
    for custody in list(issue._CUSTODIES.values()) + list(issue._CONTEXTS.values()):
        if custody.physical is plan:
            issue._release_custody(custody)
    if not plan.observe_cleanup().attempted:
        plan.release()
    if target.phase != "released":
        protocol.release_specification_draft_target(target)


def reserve(inputs, attempt="custody-attempt"):
    _, _, target, plan, request, provider = inputs
    return provider.retain_draft_inputs(
        protocol_target=target,
        physical_plan=plan,
        attempt_ref=attempt,
        client_intent_id=request.client_intent_id,
    )


def associate(inputs, guard, context="spec-context"):
    _, _, target, plan, request, provider = inputs
    return provider.claim_draft_input_custody(
        guard,
        protocol_target=target,
        physical_plan=plan,
        client_intent_id=request.client_intent_id,
        context_ref=context,
    )


def admit(inputs, context=None, request=None):
    _, _, target, plan, original_request, provider = inputs
    return provider.admit_draft_package(
        request or original_request,
        protocol_target=target,
        physical_plan=plan,
        input_custody=context,
    )


def stage(handle):
    while handle.phase != "staged":
        handle.stage_next_effect()


@pytest.mark.parametrize("explicit", [True, False])
def test_genuine_success_and_read_survives_writer_cleanup(inputs, explicit):
    guard = reserve(inputs) if explicit else None
    context = associate(inputs, guard) if explicit else None
    handle = admit(inputs, context)
    assert handle.phase == "issued"
    observed = handle.observe_input_custody()
    assert observed.physical.transfer == observed.protocol.transfer == "completed"
    assert observed.physical.responsibility == "admission"
    for resource in (inputs[3], inputs[2]):
        with pytest.raises(
            (
                fs.PackageInputCustodyRefusal,
                protocol.SpecificationDraftInputCustodyRefusal,
            )
        ):
            resource.revalidate() if resource is inputs[
                2
            ] else resource.validate_current()
    stage(handle)
    lens = handle.lend_staged_source()
    descriptor = lens.duplicate_parent_descriptor()
    os.close(descriptor)
    image = handle.publish_package()
    selection = handle.admit_published_read(physical_postimage=image)
    handle.validate_published_read(selection)
    receipt = handle.finish(physical_postimage=image, read_selection=selection)
    assert receipt.evidence.package_outcome == "published"
    handle.validate_completed_current()
    handle.release()
    observation = handle.observe_input_custody()
    assert observation.physical.owner_cleanup_outcome == "completed"
    assert observation.protocol.owner_cleanup_outcome == "unknown"
    assert observation.protocol.owner_cleanup_attempted is None
    assert observation.protocol.release_invocation == "returned"
    handle.validate_published_read(selection)
    handle.release_published_read(selection)
    assert (inputs[0] / "customer/specs/widget/README.md").read_bytes() == b"draft"
    if explicit:
        for old in (guard, context):
            with pytest.raises(IssueDraftInputCustodyRefusal):
                old.release()


def test_reserve_and_historical_input_binding_do_not_call_freshness(
    inputs, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Freshness before transfer")

    monkeypatch.setattr(fs, "require_retained_package_plan", forbidden)
    monkeypatch.setattr(protocol, "require_specification_draft_target", forbidden)
    guard = reserve(inputs)
    context = associate(inputs, guard)
    binding = context.observe_inputs()
    assert (
        binding.attempt_ref == "custody-attempt"
        and binding.context_ref == "spec-context"
    )
    assert binding.ordered_members == inputs[4].ordered_members
    assert guard.observe_cleanup().physical.owner_cleanup_attempted is False
    context.release()


@pytest.mark.parametrize("failure", ["issue_digest", "members", "manifest", "scope"])
def test_authorization_binding_failure_disposes_own_inputs_before_effects(
    inputs, failure
):
    guard = reserve(inputs)
    context = associate(inputs, guard)
    request = inputs[4]
    if failure == "issue_digest":
        request = replace(request, expected_issue_sha256="sha256:" + "0" * 64)
    elif failure == "members":
        request = replace(request, ordered_members=(("README.md", b"other"),))
    elif failure == "manifest":
        request = replace(request, expected_manifest_sha256="sha256:" + "0" * 64)
    else:
        source = next((inputs[0] / "work/issues").rglob("*.md"))
        source.write_text(source.read_text().replace("`customer/specs`", "`other`"))
        request = replace(
            request,
            expected_issue_sha256="sha256:"
            + __import__("hashlib").sha256(source.read_bytes()).hexdigest(),
        )
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        admit(inputs, context, request)
    observation = caught.value.input_custody
    assert observation.physical.owner_cleanup_outcome == "completed"
    assert observation.custody_state == "released"
    assert not (inputs[0] / "customer/specs/widget").exists()
    assert inputs[3].evidence.effects == ()


@pytest.mark.parametrize(
    "failure", ["physical_transfer", "protocol_transfer", "freshness", "activation"]
)
def test_partial_transfer_or_freshness_failure_disables_and_disposes_independently(
    inputs, monkeypatch, failure
):
    guard = reserve(inputs)
    context = associate(inputs, guard)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("qualified owner entrance fault")

    if failure == "physical_transfer":
        monkeypatch.setattr(fs, "transfer_package_input", interrupt)
    elif failure == "protocol_transfer":
        monkeypatch.setattr(protocol, "transfer_specification_draft_input", interrupt)
    elif failure == "freshness":
        monkeypatch.setattr(
            protocol, "bind_specification_draft_physical_plan", interrupt
        )
    else:
        monkeypatch.setattr(issue, "finalize", interrupt)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        admit(inputs, context)
    observation = caught.value.input_custody
    assert observation.physical.owner_cleanup_outcome == "completed"
    assert observation.protocol.release_invocation == "returned"
    assert observation.custody_state == "released"
    assert inputs[3].phase == "released"
    assert not (inputs[0] / "customer/specs/widget").exists()
    assert not fs._HANDLES[inputs[3]].fds


def test_competing_attempt_preserves_first_owner_and_disposes_new_unreserved_plan(
    inputs,
):
    guard = reserve(inputs)
    before = guard.observe_cleanup()
    new_plan = fs.retain_package_publication(
        root=inputs[0],
        target_path="customer/specs/other",
        scratch_path="customer/specs/.aware-spec-draft-" + "b" * 32,
        ordered_members=(("README.md", b"other"),),
    )
    descriptors = tuple(fs._HANDLES[new_plan].fds.values())
    assert len(descriptors) == 3
    with pytest.raises(IssueDraftInputCustodyRefusal):
        inputs[5].retain_draft_inputs(
            protocol_target=inputs[2],
            physical_plan=new_plan,
            attempt_ref="other-attempt",
            client_intent_id="other-intent",
        )
    assert guard.observe_cleanup() == before
    new_plan.release(input_claim=None)
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert guard.observe_cleanup() == before
    guard.release()


@pytest.mark.parametrize("wrong", ["provider", "plan", "intent", "execution"])
def test_foreign_association_or_admission_never_cleans_original(
    inputs, monkeypatch, wrong
):
    guard = reserve(inputs)
    context = associate(inputs, guard)
    before = guard.observe_cleanup()
    _, _, target, plan, request, provider = inputs
    if wrong == "provider":
        provider = FilesystemIssueOperationProvider(repository_root=inputs[0])
    elif wrong == "plan":
        plan = object()
    elif wrong == "intent":
        request = replace(request, client_intent_id="foreign-intent")
    else:
        monkeypatch.setenv("CODEX_THREAD_ID", "other-execution")
    with pytest.raises(IssueDraftPackageRefusal):
        provider.admit_draft_package(
            request, protocol_target=target, physical_plan=plan, input_custody=context
        )
    assert guard.observe_cleanup() == before
    context.release()


@pytest.mark.parametrize("kind", ["bare", "context"])
@pytest.mark.parametrize(
    "operation", ["copy", "deepcopy", "pickle", "construct", "subclass"]
)
def test_original_handles_not_reconstructible(inputs, kind, operation):
    guard = reserve(inputs)
    capability = guard if kind == "bare" else associate(inputs, guard)
    calls = {
        "copy": lambda: copy.copy(capability),
        "deepcopy": lambda: copy.deepcopy(capability),
        "pickle": lambda: pickle.dumps(capability),
        "construct": type(capability),
        "subclass": lambda: type("Forgery", (type(capability),), {}),
    }
    with pytest.raises(TypeError):
        calls[operation]()
    capability.release()


@pytest.mark.parametrize("count", range(10))
def test_real_association_vs_disposal_race_has_one_owner(inputs, count):
    guard = reserve(inputs)
    barrier = threading.Barrier(2)

    def run(index):
        barrier.wait(timeout=5)
        try:
            return associate(inputs, guard) if index == 0 else guard.release()
        except IssueDraftInputCustodyRefusal:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        values = list(pool.map(run, (0, 1)))
    assert sum(value is not None for value in values) == 1
    if values[0] is not None:
        assert not inputs[3].observe_cleanup().attempted
        values[0].release()
    assert inputs[3].observe_cleanup().outcome == "completed"


@pytest.mark.parametrize("kind", ["bare", "context", "admission"])
def test_collected_owner_disposes_without_retaining_registry_cycle(inputs, kind):
    guard = reserve(inputs)
    if kind == "bare":
        capability = guard
        del guard
    else:
        context = associate(inputs, guard)
        del guard
        gc.collect()
        assert not inputs[3].observe_cleanup().attempted
        if kind == "context":
            capability = context
            del context
        else:
            capability = admit(inputs, context)
            del context
            gc.collect()
            assert not inputs[3].observe_cleanup().attempted
    reference = weakref.ref(capability)
    del capability
    gc.collect()
    assert reference() is None
    assert inputs[3].observe_cleanup().outcome == "completed"


def test_genuine_fork_refuses_without_owner_effects(inputs):
    guard = reserve(inputs)
    before = guard.observe_cleanup()
    pid = os.fork()
    if pid == 0:
        try:
            try:
                guard.release()
            except IssueDraftInputCustodyRefusal:
                os._exit(0 if not inputs[3].observe_cleanup().attempted else 11)
            os._exit(12)
        except BaseException:  # noqa: BLE001 - exit the fork probe, never enter pytest
            # Physical historical observation itself rejects a foreign fork.
            os._exit(0 if not fs._HANDLES[inputs[3]].cleanup_attempted else 13)
    _, status = os.waitpid(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    assert guard.observe_cleanup() == before
    guard.release()


def test_manifest_freshness_follows_both_transfers_and_preparing_is_disabled(
    inputs, monkeypatch
):
    guard = reserve(inputs)
    context = associate(inputs, guard)
    custody = issue._CONTEXTS[context]
    original_read = issue._read_issue
    original_transfer = protocol.transfer_specification_draft_input
    calls = []

    def transfer(*args, **kwargs):
        preparing = custody.admission()
        assert preparing.phase == "preparing"
        assert preparing.physical_claim is not None
        assert preparing.protocol_claim is None
        calls.append("protocol_transfer")
        for handle, state in issue._ADMISSIONS.items():
            if state is preparing:
                with pytest.raises(IssueDraftPackageRefusal, match="terminal"):
                    handle.stage_next_effect()
        return original_transfer(*args, **kwargs)

    def read(root, path):
        if path == inputs[4].manifest_locator:
            assert custody.physical_claim is not None
            assert custody.protocol_claim is not None
            assert custody.phase == "transferred"
            calls.append("manifest_read")
        return original_read(root, path)

    monkeypatch.setattr(protocol, "transfer_specification_draft_input", transfer)
    monkeypatch.setattr(issue, "_read_issue", read)
    handle = admit(inputs, context)
    assert calls.index("protocol_transfer") < calls.index("manifest_read")
    handle.release()


@pytest.mark.parametrize("entrance", ["reserve", "context"])
def test_issue_capability_issuance_interruption_disposes_owned_originals(
    inputs, monkeypatch, entrance
):
    guard = reserve(inputs) if entrance == "context" else None

    def interrupt(*args, **kwargs):
        raise SystemExit("original issuer return interrupted")

    monkeypatch.setattr(issue, "finalize", interrupt)
    with pytest.raises(IssueDraftInputCustodyRefusal) as caught:
        reserve(inputs) if entrance == "reserve" else associate(inputs, guard)
    assert caught.value.input_custody.physical.owner_cleanup_outcome == "completed"
    assert caught.value.input_custody.protocol.release_invocation == "returned"
    assert caught.value.input_custody.custody_state == "released"


def test_unavailable_observation_retains_known_transfer_publication_and_cleanup(
    inputs, monkeypatch
):
    guard = reserve(inputs)
    context = associate(inputs, guard)
    handle = admit(inputs, context)
    stage(handle)
    image = handle.publish_package()
    before = handle.observe_input_custody()
    assert before.physical_evidence.package_outcome == "published"

    def unavailable(*args):
        raise OSError("historical owner observation unavailable")

    monkeypatch.setattr(fs, "observe_package_input", unavailable)
    monkeypatch.setattr(protocol, "observe_specification_draft_input", unavailable)
    missing = handle.observe_input_custody()
    assert missing.physical.transfer == missing.protocol.transfer == "completed"
    assert missing.physical_evidence.package_outcome == "published"
    handle.release()
    released = handle.observe_input_custody()
    assert released.physical.owner_cleanup_outcome == "completed"
    assert released.protocol.release_invocation == "returned"
    assert released.protocol.owner_cleanup_outcome == "unknown"
    assert released.physical_evidence.package_outcome == "published"
    assert image is not None


@pytest.mark.parametrize("kind", ["physical", "protocol"])
@pytest.mark.parametrize("checkpoint", ["publication", "cleanup"])
def test_replayed_owner_history_preserves_genuine_publication_and_cleanup(
    inputs, monkeypatch, kind, checkpoint
):
    guard = reserve(inputs)
    record = issue._CUSTODIES[guard]
    reserved = getattr(record, kind + "_observation")
    handle = admit(inputs, associate(inputs, guard))
    stage(handle)
    handle.publish_package()
    published = handle.observe_input_custody()
    assert published.physical_evidence.package_outcome == "published"
    assert published.physical_evidence.effects
    if checkpoint == "cleanup":
        handle.release()
    before = handle.observe_input_custody()
    latest = getattr(record, kind + "_observation")
    owner = fs if kind == "physical" else protocol
    name = (
        "observe_package_input"
        if kind == "physical"
        else "observe_specification_draft_input"
    )
    original = getattr(owner, name)
    monkeypatch.setattr(owner, name, lambda *args: reserved)
    replayed = handle.observe_input_custody()
    assert replayed.physical_evidence == before.physical_evidence
    assert replayed.physical == before.physical
    assert replayed.protocol == before.protocol
    assert f"{kind}_observation_history_regressed" in replayed.diagnostics
    assert getattr(record, kind + "_observation") == latest
    monkeypatch.setattr(owner, name, original)
    handle.release()
    forward = handle.observe_input_custody()
    assert forward.physical.owner_cleanup_outcome == "completed"
    assert forward.protocol.release_invocation == "returned"
    assert forward.physical_evidence.package_outcome == "published"
    assert (
        forward.physical_evidence.effects[: len(before.physical_evidence.effects)]
        == before.physical_evidence.effects
    )


@pytest.mark.parametrize("entrance", ["reserve", "require", "claim"])
@pytest.mark.parametrize("failure", ["missing", "ambiguous", "supplier"])
def test_pre_reservation_and_verification_failures_use_custody_boundary(
    inputs, monkeypatch, entrance, failure
):
    guard = reserve(inputs) if entrance != "reserve" else None
    target, plan, request, provider = inputs[2:]
    before = plan.observe_cleanup()
    descriptors = tuple(fs._HANDLES[plan].fds.values())
    if failure == "supplier":

        def unavailable():
            raise IssueDraftPackageRefusal("draft_integration_unavailable")

        monkeypatch.setattr(issue, "_owners", unavailable)
        code = "draft_integration_unavailable"
    else:
        monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
        if failure == "missing":
            monkeypatch.delenv("CODEX_THREAD_ID", raising=False)
        else:
            monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "other-harness")
        code = "provider_execution_identity_unavailable"
    with pytest.raises(IssueDraftInputCustodyRefusal) as caught:
        if entrance == "reserve":
            reserve(inputs)
        else:
            kwargs = {
                "protocol_target": target,
                "physical_plan": plan,
                "client_intent_id": request.client_intent_id,
            }
            if entrance == "claim":
                provider.claim_draft_input_custody(
                    guard, context_ref="context", **kwargs
                )
            else:
                provider.require_draft_input_custody(guard, **kwargs)
    assert caught.value.code == code
    assert caught.value.__cause__.code == code
    assert caught.value.input_custody is None
    assert caught.value.cause_diagnostics == (type(caught.value.__cause__).__name__,)
    assert plan.observe_cleanup() == before
    assert tuple(fs._HANDLES[plan].fds.values()) == descriptors
    for descriptor in descriptors:
        os.fstat(descriptor)
    if guard is not None:
        assert issue._CUSTODIES[guard].context is None
        assert not issue._CUSTODIES[guard].release_attempted


@pytest.mark.parametrize(
    "field",
    ["publication", "effects", "transfer", "cleanup", "release", "binding"],
)
def test_individual_owner_history_regressions_cannot_replace_retained_evidence(
    inputs, monkeypatch, field
):
    guard = reserve(inputs)
    handle = admit(inputs, associate(inputs, guard))
    stage(handle)
    handle.publish_package()
    handle.release()
    before = handle.observe_input_custody()
    record = issue._CUSTODIES[guard]
    original = record.physical_observation
    if field == "publication":
        incoming = replace(
            original,
            cleanup=replace(
                original.cleanup,
                evidence=replace(original.cleanup.evidence, package_outcome="none"),
            ),
        )
    elif field == "effects":
        incoming = replace(
            original,
            cleanup=replace(
                original.cleanup,
                evidence=replace(
                    original.cleanup.evidence,
                    effects=original.cleanup.evidence.effects[:-1],
                ),
            ),
        )
    elif field == "transfer":
        incoming = replace(original, transfer_state="not_attempted")
    elif field == "cleanup":
        incoming = replace(
            original,
            owner_cleanup_attempted=False,
            owner_cleanup_outcome="not_attempted",
        )
    elif field == "release":
        incoming = replace(original, release_invocation="not_invoked")
    else:
        incoming = replace(original, binding=None)
    monkeypatch.setattr(fs, "observe_package_input", lambda *args: incoming)
    after = handle.observe_input_custody()
    assert after.physical_evidence == before.physical_evidence
    assert after.physical == before.physical
    assert "physical_observation_history_regressed" in after.diagnostics
    assert record.physical_observation == original


def test_known_publication_survives_interrupted_original_postimage_return(
    inputs, monkeypatch
):
    guard = reserve(inputs)
    handle = admit(inputs, associate(inputs, guard))
    stage(handle)
    original = fs.RetainedPackagePublication.publish_package

    def interrupt(plan, **kwargs):
        original(plan, **kwargs)
        raise KeyboardInterrupt("applied rename; interrupted return")

    monkeypatch.setattr(fs.RetainedPackagePublication, "publish_package", interrupt)
    with pytest.raises(IssueDraftPackageRefusal) as caught:
        handle.publish_package()
    assert caught.value.evidence.package_outcome == "published"
    assert caught.value.input_custody.physical_evidence.package_outcome == "published"
    assert caught.value.input_custody.physical.owner_cleanup_outcome == "completed"
    assert (inputs[0] / "customer/specs/widget/README.md").read_bytes() == b"draft"


def test_foreign_read_refuses_without_releasing_admission_or_selection(inputs):
    handle = admit(inputs)
    stage(handle)
    image = handle.publish_package()
    read = handle.admit_published_read(physical_postimage=image)
    before = handle.observe_input_custody()
    for entrance in (handle.validate_published_read, handle.release_published_read):
        with pytest.raises(IssueDraftPackageRefusal, match="foreign"):
            entrance(object())
    assert handle.observe_input_custody() == before
    handle.validate_published_read(read)
    handle.finish(physical_postimage=image, read_selection=read)
    handle.release()
    handle.validate_published_read(read)
    handle.release_published_read(read)


@pytest.mark.parametrize("point", ["before", "after"])
def test_new_plan_reserved_before_fallback_disposal_is_not_cleaned(inputs, point):
    guard = reserve(inputs)
    new_plan = fs.retain_package_publication(
        root=inputs[0],
        target_path="customer/specs/other",
        scratch_path="customer/specs/.aware-spec-draft-" + "b" * 32,
        ordered_members=(("README.md", b"other"),),
    )
    second = fs.reserve_package_input(
        new_plan, attempt_ref="other-owner", client_intent_id="other-intent"
    )
    claim = (
        fs.transfer_package_input(second, receiver=object())
        if point == "after"
        else None
    )
    snapshot = fs.observe_package_input(second)
    with pytest.raises(IssueDraftInputCustodyRefusal):
        inputs[5].retain_draft_inputs(
            protocol_target=inputs[2],
            physical_plan=new_plan,
            attempt_ref="conflict",
            client_intent_id="conflict-intent",
        )
    with pytest.raises(fs.PackageInputCustodyRefusal):
        new_plan.release(input_claim=None)
    assert fs.observe_package_input(second) == snapshot
    assert not new_plan.observe_cleanup().attempted
    fs.release_package_input(claim if claim is not None else second)
    guard.release()


@pytest.mark.parametrize("role", ["bare", "context", "admission"])
def test_original_observation_failure_is_typed_not_a_cleanup_grant(
    inputs, monkeypatch, role
):
    guard = reserve(inputs)
    value = guard if role == "bare" else associate(inputs, guard)
    if role == "admission":
        value = admit(inputs, value)
    original = issue._custody_observation

    def unavailable(*args):
        raise KeyboardInterrupt("complete custody evidence unavailable")

    monkeypatch.setattr(issue, "_custody_observation", unavailable)
    with pytest.raises(IssueDraftInputCustodyRefusal) as caught:
        value.observe_input_custody() if role == "admission" else value.observe_cleanup()
    assert caught.value.input_custody is None
    assert not inputs[3].observe_cleanup().attempted
    monkeypatch.setattr(issue, "_custody_observation", original)
    value.release()


@pytest.mark.parametrize("replay", range(10))
def test_real_admission_transfer_vs_context_disposal_has_one_terminal_branch(
    inputs, replay
):
    guard = reserve(inputs)
    context = associate(inputs, guard)
    barrier = threading.Barrier(2)

    def run(index):
        barrier.wait(timeout=5)
        try:
            return admit(inputs, context) if index == 0 else context.release()
        except (IssueDraftPackageRefusal, IssueDraftInputCustodyRefusal):
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, (0, 1)))
    assert sum(result is not None for result in results) == 1
    if results[0] is not None:
        handle = results[0]
        assert handle.phase == "issued"
        assert not inputs[3].observe_cleanup().attempted
        assert handle.observe_input_custody().physical.transfer == "completed"
        handle.release()
    assert inputs[3].observe_cleanup().outcome == "completed"
    assert inputs[2].phase == "released"
