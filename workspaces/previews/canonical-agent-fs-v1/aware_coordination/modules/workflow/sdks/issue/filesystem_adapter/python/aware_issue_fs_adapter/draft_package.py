"""Original Issue draft authority over fixed Protocol/FileSystem owner ports.

No setup-permit reuse, injected validator, semantic parser or raw-writer fallback.
Protocol is lazily required only for this explicitly selected authoring entrance.
"""

from __future__ import annotations

import hashlib
import os
import threading
from dataclasses import dataclass, field, replace
from importlib import import_module
from pathlib import Path
from weakref import WeakKeyDictionary, finalize, ref

from aware_issue_operational_runtime import evaluate_issue_source_scope
from aware_issue_sdk.draft_input_custody import (
    IssueDraftInputBinding,
    IssueDraftInputCustodyObservation,
    IssueDraftInputCustodyRefusal,
    IssueDraftInputResourceObservation,
)
from aware_issue_sdk.draft_input_custody import (
    _text as _custody_text,
)
from aware_issue_sdk.draft_package import (
    ISSUE_DRAFT_PACKAGE_OPERATION_REF,
    IssueDraftPackageBinding,
    IssueDraftPackageCleanupDisposition,
    IssueDraftPackageEffect,
    IssueDraftPackageEvidence,
    IssueDraftPackageReceipt,
    IssueDraftPackageRefusal,
    IssueDraftPackageRequest,
)

from .source_change import _execution, _read_issue, _relative_manifest

_ADMISSIONS: WeakKeyDictionary = WeakKeyDictionary()
_PLANS: WeakKeyDictionary = WeakKeyDictionary()
_ISSUANCE_LOCK = threading.RLock()
_CUSTODIES: WeakKeyDictionary = WeakKeyDictionary()
_CONTEXTS: WeakKeyDictionary = WeakKeyDictionary()


def _owners():
    try:
        physical = import_module("aware_file_system.retained_package")
        protocol = import_module("aware_protocol_fs_adapter.specification_draft_target")
        for name in (
            "require_retained_package_plan",
            "observe_package_plan",
            "require_retained_package_postimage",
            "observe_package_cleanup",
            "transfer_package_input",
            "release_package_input",
            "observe_package_input",
        ):
            getattr(physical, name)
        for name in (
            "require_specification_draft_target",
            "bind_specification_draft_physical_plan",
            "spend_specification_draft_publication",
            "finish_specification_draft_target",
            "reserve_specification_draft_input",
            "transfer_specification_draft_input",
            "release_specification_draft_input",
            "observe_specification_draft_input",
        ):
            getattr(protocol, name)
        return physical, protocol
    except (ImportError, AttributeError) as error:
        raise IssueDraftPackageRefusal("draft_integration_unavailable") from error


@dataclass
class _Claim:
    provider: object
    target: object
    snapshot: IssueDraftPackageCleanupDisposition
    state: object | None = None
    pid: int = field(default_factory=os.getpid)


@dataclass
class _Custody:
    provider: object
    target: object
    physical: object
    fs: object
    protocol: object
    attempt: str
    intent: str
    execution: str
    provider_root: Path
    provider_manifest: str
    pid: int = field(default_factory=os.getpid)
    phase: str = "reserving"
    context: str | None = None
    joint: object | None = None
    physical_reservation: object | None = None
    physical_claim: object | None = None
    protocol_claim: object | None = None
    physical_observation: object | None = None
    protocol_observation: object | None = None
    binding: IssueDraftInputBinding | None = None
    admission: object | None = None
    release_attempted: bool = False
    release_failed: bool = False
    diagnostics: list[str] = field(default_factory=list)


def _correlated(custody, observation):
    return observation is not None and (
        observation.attempt_ref,
        observation.client_intent_id,
    ) == (custody.attempt, custody.intent)


def _extends_history(previous, incoming, *, physical):
    """Check detached history, never freshness or permission to dispose."""
    if previous is None:
        return True
    if type(incoming) is not type(previous):
        return False
    for name, transitions in (
        (
            "resource_state",
            {
                "reserved": {"reserved", "transferred", "released"},
                "transferred": {"transferred", "released"},
                "released": {"released"},
            },
        ),
        (
            "transfer_state",
            {
                "not_attempted": {"not_attempted", "attempted", "completed"},
                "attempted": {"attempted", "completed"},
                "completed": {"completed"},
            },
        ),
        (
            "release_invocation",
            {
                "not_invoked": {"not_invoked", "invoked", "returned", "raised"},
                "invoked": {"invoked", "returned", "raised"},
                "returned": {"returned"},
                "raised": {"raised"},
            },
        ),
    ):
        old, new = getattr(previous, name), getattr(incoming, name)
        if new not in transitions.get(old, {old}):
            return False
    if (
        previous.owner_cleanup_attempted is not None
        and incoming.owner_cleanup_attempted
        not in ({True} if previous.owner_cleanup_attempted else {False, True})
    ):
        return False
    if previous.owner_cleanup_outcome in {"completed", "incomplete"} and (
        incoming.owner_cleanup_outcome != previous.owner_cleanup_outcome
    ):
        return False
    if incoming.diagnostics[: len(previous.diagnostics)] != previous.diagnostics:
        return False
    if not physical:
        if any(
            getattr(previous, name) is not None
            and getattr(incoming, name) != getattr(previous, name)
            for name in (
                "root_locator",
                "manifest_locator",
                "manifest_sha256",
                "target_locator",
            )
        ):
            return False
        return previous.physical is None or (
            incoming.physical is not None
            and _extends_history(previous.physical, incoming.physical, physical=True)
        )
    if previous.binding is not None and incoming.binding != previous.binding:
        return False
    old, new = previous.cleanup, incoming.cleanup
    if old is None:
        return True
    if new is None or (
        (old.root_locator, old.target_path, old.scratch_path)
        != (new.root_locator, new.target_path, new.scratch_path)
        or (old.attempted and not new.attempted)
        or (old.outcome in {"completed", "incomplete"} and new.outcome != old.outcome)
    ):
        return False
    before, after = old.evidence, new.evidence
    return (
        (before.package_outcome != "published" or after.package_outcome == "published")
        and after.effects[: len(before.effects)] == before.effects
        and after.cleanup_diagnostics[: len(before.cleanup_diagnostics)]
        == before.cleanup_diagnostics
        and (not before.durability_confirmed or after.durability_confirmed)
        # Residue can lawfully disappear during cleanup, unlike effect history.
    )


def _retain_observation(custody, kind, incoming):
    if not _correlated(custody, incoming):
        raise ValueError("Original custody correlation changed")
    previous = getattr(custody, kind + "_observation")
    if not _extends_history(previous, incoming, physical=kind == "physical"):
        custody.diagnostics.append(f"{kind}_observation_history_regressed")
        return
    setattr(custody, kind + "_observation", incoming)


def _refresh_custody(custody):
    for kind, value, observe in (
        (
            "physical",
            custody.physical_claim or custody.physical_reservation,
            custody.fs.observe_package_input,
        ),
        (
            "protocol",
            custody.protocol_claim or custody.joint,
            custody.protocol.observe_specification_draft_input,
        ),
    ):
        if value is None:
            continue
        try:
            result = observe(value)
            _retain_observation(custody, kind, result)
        except BaseException as error:  # noqa: BLE001 - preserve prior known custody history
            custody.diagnostics.append(
                f"{kind}_observation_unavailable:{type(error).__name__}"
            )


def _resource(custody, observation):
    if observation is None:
        return IssueDraftInputResourceObservation(
            "unknown",
            "unknown",
            "unknown",
            "not_invoked",
            None,
            "unknown",
            (),
        )
    acquired = observation.resource_state in {"reserved", "transferred", "released"}
    return IssueDraftInputResourceObservation(
        "acquired" if acquired else "unknown",
        "admission"
        if custody.admission is not None
        else "custody"
        if acquired
        else "unknown",
        observation.transfer_state,
        observation.release_invocation,
        observation.owner_cleanup_attempted,
        observation.owner_cleanup_outcome,
        tuple(observation.diagnostics),
    )


def _custody_observation(custody):
    _refresh_custody(custody)
    binding = custody.binding
    physical = custody.physical_observation
    cleanup = None if physical is None else physical.cleanup
    return IssueDraftInputCustodyObservation(
        custody.attempt,
        custody.intent,
        custody.execution,
        custody.phase,
        None if binding is None else binding.root_locator,
        None if binding is None else binding.manifest_locator,
        None if binding is None else binding.manifest_sha256,
        None if binding is None else binding.target_locator,
        None if binding is None else binding.scratch_locator,
        _resource(custody, physical),
        _resource(custody, custody.protocol_observation),
        None if cleanup is None else _portable_evidence(cleanup.evidence),
        tuple(custody.diagnostics),
        custody.context,
    )


def _custody_refusal(code, custody=None, cause=None):
    observation = None
    if custody is not None:
        try:
            observation = _custody_observation(custody)
        except BaseException:  # noqa: BLE001 - unknown is never caller-owned
            observation = None
    return IssueDraftInputCustodyRefusal(
        code,
        input_custody=observation,
        cause_diagnostics=() if cause is None else (type(cause).__name__,),
    )


def _safe_custody_observation(custody):
    try:
        return _custody_observation(custody)
    except BaseException as error:  # noqa: BLE001 - refuse with unknown, never a cleanup grant
        custody.diagnostics.append(
            f"custody_evidence_unavailable:{type(error).__name__}"
        )
        return None


def _require_custody_observation(custody):
    value = _safe_custody_observation(custody)
    if value is None:
        raise _custody_refusal("issue_input_observation_unavailable")
    return value


def _custody_local(value, *, context=False):
    expected = IssueDraftInputContextClaim if context else IssueDraftInputCustody
    registry = _CONTEXTS if context else _CUSTODIES
    custody = registry.get(value) if type(value) is expected else None
    if custody is None or custody.pid != os.getpid():
        raise _custody_refusal("original_local_issue_input_custody_required")
    return custody


def _custody_identity(custody, provider, target, physical, intent):
    try:
        execution = _execution()
        owners = _owners()
    except BaseException as error:  # Verification does not acquire or dispose.
        raise _custody_refusal(
            getattr(error, "code", "issue_input_verification_failed"), cause=error
        ) from error
    if (
        custody.provider is not provider
        or custody.target is not target
        or custody.physical is not physical
        or custody.intent != intent
        or execution != custody.execution
        or provider._repository_root != custody.provider_root
        or provider._protocol_source_ref != custody.provider_manifest
        or owners != (custody.fs, custody.protocol)
    ):
        raise _custody_refusal("issue_input_custody_mismatch")


def _release_custody(custody):
    if custody.release_attempted:
        return
    custody.release_attempted = True
    custody.phase = "releasing"
    # Before physical transfer the joint reservation owns its child. Afterwards
    # Issue owns that claim independently; Protocol disposal cannot replace it.
    resources = []
    if custody.physical_claim is not None:
        resources.append(
            ("physical", custody.physical_claim, custody.fs.release_package_input)
        )
    if custody.protocol_claim is not None or custody.joint is not None:
        resources.append(
            (
                "protocol",
                custody.protocol_claim or custody.joint,
                custody.protocol.release_specification_draft_input,
            )
        )
    for kind, value, release in resources:
        try:
            result = release(value)
            if _correlated(custody, result):
                _retain_observation(custody, kind, result)
        except BaseException as error:  # noqa: BLE001 - dispose other owned resources independently
            custody.release_failed = True
            custody.diagnostics.append(f"{kind}_release_failed:{type(error).__name__}")
            observed = getattr(error, "input_observation", None)
            if _correlated(custody, observed):
                _retain_observation(custody, kind, observed)
    custody.phase = "released"
    _refresh_custody(custody)


def _abandon_custody(custody, role):
    if custody.pid != os.getpid():
        return
    with _ISSUANCE_LOCK:
        if custody.admission is not None or (
            role == "bare" and custody.context is not None
        ):
            return
        _release_custody(custody)


class IssueDraftInputCustody:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use provider.retain_draft_inputs")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original custody cannot be subclassed")

    def __copy__(self):
        raise TypeError("Custody cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Custody cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Custody cannot be serialized")

    def observe_cleanup(self):
        with _ISSUANCE_LOCK:
            return _require_custody_observation(_custody_local(self))

    def release(self):
        with _ISSUANCE_LOCK:
            custody = _custody_local(self)
            if custody.context is not None or custody.admission is not None:
                raise _custody_refusal("issue_input_cleanup_associated", custody)
            _release_custody(custody)
            if custody.release_failed:
                raise _custody_refusal("issue_input_release_incomplete", custody)
            return _require_custody_observation(custody)


class IssueDraftInputContextClaim:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use claim_draft_input_custody")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original context claim cannot be subclassed")

    def __copy__(self):
        raise TypeError("Context claim cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Context claim cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Context claim cannot be serialized")

    def observe_cleanup(self):
        with _ISSUANCE_LOCK:
            return _require_custody_observation(_custody_local(self, context=True))

    def observe_inputs(self):
        with _ISSUANCE_LOCK:
            custody = _custody_local(self, context=True)
            if custody.binding is None:
                raise _custody_refusal("issue_input_binding_unavailable", custody)
            return replace(custody.binding, context_ref=custody.context)

    def release(self):
        with _ISSUANCE_LOCK:
            custody = _custody_local(self, context=True)
            if custody.admission is not None:
                raise _custody_refusal("issue_input_cleanup_transferred", custody)
            _release_custody(custody)
            if custody.release_failed:
                raise _custody_refusal("issue_input_release_incomplete", custody)
            return _require_custody_observation(custody)


def _retain_inputs(provider, target, physical, attempt_ref, client_intent_id):
    from .provider import FilesystemIssueOperationProvider

    if type(provider) is not FilesystemIssueOperationProvider:
        raise _custody_refusal("original_issue_provider_required")
    attempt, intent = _custody_text(attempt_ref), _custody_text(client_intent_id)
    try:
        execution = _execution()
        fs, protocol = _owners()
    except BaseException as error:  # No original resources acquired.
        raise _custody_refusal(
            getattr(error, "code", "issue_input_reservation_failed"), cause=error
        ) from error
    custody = _Custody(
        provider,
        target,
        physical,
        fs,
        protocol,
        attempt,
        intent,
        execution,
        provider._repository_root,
        provider._protocol_source_ref,
    )
    with _ISSUANCE_LOCK:
        try:
            custody.joint = protocol.reserve_specification_draft_input(
                target,
                physical_plan=physical,
                attempt_ref=attempt,
                client_intent_id=intent,
            )
            custody.physical_reservation = custody.joint.physical_reservation
            _refresh_custody(custody)
            observed = custody.protocol_observation
            physical_observation = custody.physical_observation
            if (
                observed is None
                or physical_observation is None
                or physical_observation.binding is None
            ):
                raise ValueError("Original historical binding unavailable")
            binding = physical_observation.binding
            custody.binding = IssueDraftInputBinding(
                attempt,
                intent,
                custody.execution,
                None,
                observed.root_locator,
                observed.manifest_locator,
                observed.manifest_sha256,
                observed.target_locator,
                binding.scratch_path,
                binding.ordered_members,
            )
            if binding.root_locator != str(
                provider._repository_root.expanduser().resolve()
            ):
                raise ValueError("Original provider root mismatch")
            custody.phase = "reserved"
            handle = object.__new__(IssueDraftInputCustody)
            _CUSTODIES[handle] = custody
            finalize(handle, _abandon_custody, custody, "bare")
            return handle
        except BaseException as error:
            observed = getattr(error, "input_observation", None)
            if _correlated(custody, observed):
                _retain_observation(custody, "protocol", observed)
                if _correlated(custody, observed.physical):
                    _retain_observation(custody, "physical", observed.physical)
            # No returned joint capability means the lower issuer owns its own
            # partial-failure disposal, not permission to release raw originals.
            if custody.joint is not None:
                _release_custody(custody)
            else:
                custody.phase = "failed"
            raise _custody_refusal(
                "issue_input_reservation_failed", custody, error
            ) from error


def require_draft_input_custody(
    value, *, provider, protocol_target, physical_plan, client_intent_id
):
    with _ISSUANCE_LOCK:
        custody = _custody_local(value)
        _custody_identity(
            custody, provider, protocol_target, physical_plan, client_intent_id
        )
        if custody.phase != "reserved" or custody.context is not None:
            raise _custody_refusal("issue_input_custody_spent", custody)
        return value


def claim_draft_input_custody(
    value, *, provider, protocol_target, physical_plan, client_intent_id, context_ref
):
    context_ref = _custody_text(context_ref)
    with _ISSUANCE_LOCK:
        require_draft_input_custody(
            value,
            provider=provider,
            protocol_target=protocol_target,
            physical_plan=physical_plan,
            client_intent_id=client_intent_id,
        )
        custody = _custody_local(value)
        try:
            claim = object.__new__(IssueDraftInputContextClaim)
            _CONTEXTS[claim] = custody
            custody.context = context_ref
            finalize(claim, _abandon_custody, custody, "context")
            return claim
        except BaseException as error:
            _release_custody(custody)
            raise _custody_refusal(
                "issue_input_context_claim_failed", custody, error
            ) from error


@dataclass
class _State:
    provider: object
    provider_root: Path
    provider_manifest: str
    root: Path
    issue_path: str
    identity: tuple
    parents: tuple
    manifest_identity: tuple
    manifest_parents: tuple
    execution: str
    request: IssueDraftPackageRequest
    physical: object
    target: object
    fs: object
    protocol: object
    pid: int = field(default_factory=os.getpid)
    phase: str = "issued"
    postimage: object | None = None
    publication_attempted: bool = False
    last_evidence: IssueDraftPackageEvidence | None = None
    physical_diagnostics: tuple[str, ...] = ()
    cleanup_attempted: bool = False
    cleanup_outcome: str = "not_attempted"
    claim: _Claim | None = None
    diagnostics: list[str] = field(default_factory=list)
    lock: threading.RLock = field(default_factory=threading.RLock)
    custody: _Custody | None = None
    physical_claim: object | None = None
    protocol_claim: object | None = None
    read_selection: object | None = None


def _effect(effect):
    return IssueDraftPackageEffect(
        effect.path,
        effect.kind,
        effect.state.value,
        effect.durability_confirmed,
        effect.mode,
        effect.before_digest,
        effect.after_digest,
        effect.after_identity,
    )


def _evidence(state):
    try:
        value = state.physical.evidence
    except BaseException as error:  # noqa: BLE001 - original foreign-process refusals retain historical evidence
        value = getattr(error, "evidence", None)
        if value is None:
            previous = state.last_evidence or IssueDraftPackageEvidence(
                "unknown", (), (), ()
            )
            return replace(
                previous,
                package_outcome=(
                    "published"
                    if state.postimage is not None
                    or previous.package_outcome == "published"
                    else "unknown"
                    if state.publication_attempted
                    else previous.package_outcome
                ),
                ledger_complete=False,
                cleanup_diagnostics=(
                    *previous.cleanup_diagnostics,
                    *state.diagnostics,
                    f"physical_evidence_unavailable:{type(error).__name__}",
                ),
            )
    return _remember_evidence(state, value)


def _portable_evidence(value, diagnostics=()):
    return IssueDraftPackageEvidence(
        value.package_outcome,
        tuple(_effect(e) for e in value.effects),
        value.residual_scratch_paths,
        (*value.cleanup_diagnostics, *diagnostics),
        value.durability_confirmed,
    )


def _remember_evidence(state, value):
    """Consume owner snapshots, including release's returned cleanup ledger."""
    result = _portable_evidence(value, state.diagnostics)
    state.last_evidence = result
    state.physical_diagnostics = value.cleanup_diagnostics
    return result


def _issue_path(provider, request):
    from aware_issue_sdk import IssueMutationResult

    target = provider._mutation_target(
        operation_ref=ISSUE_DRAFT_PACKAGE_OPERATION_REF, issue_ref=request.issue_ref
    )
    if isinstance(target, IssueMutationResult):
        raise IssueDraftPackageRefusal("issue_authority_unavailable")
    return target[1]


def _policy(provider, request, execution, path, body):
    from aware_issue_runtime import IssueReadProjection

    if "sha256:" + hashlib.sha256(body).hexdigest() != request.expected_issue_sha256:
        raise IssueDraftPackageRefusal("issue_source_sha256_mismatch")
    projection = provider._parse_projection(
        operation_ref=ISSUE_DRAFT_PACKAGE_OPERATION_REF,
        issue_ref=request.issue_ref,
        relative_path=path,
        source=body,
    )
    if not isinstance(projection, IssueReadProjection):
        raise IssueDraftPackageRefusal("issue_projection_unavailable")
    decision = evaluate_issue_source_scope(
        issue_owner=projection.owner_ref or "",
        issue_status=projection.status,
        scope_paths=projection.ownership_scope,
        actor_ref=execution,
        effect_paths=request.ordered_effect_paths,
    )
    if not decision.allowed:
        raise IssueDraftPackageRefusal(
            decision.refusal.value, required_effect_paths=request.ordered_effect_paths
        )


def _check_issue(state):
    if _execution() != state.execution:
        raise IssueDraftPackageRefusal("provider_execution_changed")
    if (
        state.provider._repository_root != state.provider_root
        or state.provider._protocol_source_ref != state.provider_manifest
        or state.provider._repository_root.expanduser().resolve() != state.root
        or _issue_path(state.provider, state.request) != state.issue_path
    ):
        raise IssueDraftPackageRefusal("original_issue_provider_changed")
    body, identity, parents = _read_issue(state.root, state.issue_path)
    if identity != state.identity or parents != state.parents:
        raise IssueDraftPackageRefusal("issue_authority_identity_changed")
    _policy(state.provider, state.request, state.execution, state.issue_path, body)
    body, identity, parents = _read_issue(state.root, state.request.manifest_locator)
    if (
        identity != state.manifest_identity
        or parents != state.manifest_parents
        or "sha256:" + hashlib.sha256(body).hexdigest()
        != state.request.expected_manifest_sha256
    ):
        raise IssueDraftPackageRefusal("manifest_authority_changed")


def _check_protocol_target(state):
    target = state.protocol.require_specification_draft_target(
        state.target, input_claim=state.protocol_claim
    )
    if target is not state.target:
        raise IssueDraftPackageRefusal("original_protocol_target_required")
    observed = state.protocol.observe_specification_draft_input(state.protocol_claim)
    if observed.manifest_locator != state.request.manifest_locator:
        raise IssueDraftPackageRefusal("protocol_manifest_locator_mismatch")
    if (
        observed.manifest_sha256 != state.request.expected_manifest_sha256
        or observed.target_locator != state.request.target_locator
    ):
        raise IssueDraftPackageRefusal("protocol_draft_binding_changed")


def _check_owners(state):
    fs, protocol = _owners()
    if fs is not state.fs or protocol is not state.protocol:
        raise IssueDraftPackageRefusal("original_draft_supplier_changed")
    fs.require_retained_package_plan(state.physical, input_claim=state.physical_claim)
    _check_protocol_target(state)
    # A consumed plan remains correlated, but ordinary observe_package_plan is
    # intentionally a live writer check. Use its retained historical custody.
    binding = fs.observe_package_input(state.physical_claim).binding
    if (
        binding.root_locator != str(state.root)
        or binding.target_path != state.request.target_locator
        or binding.scratch_path != state.request.scratch_locator
        or binding.ordered_members != state.request.ordered_members
    ):
        raise IssueDraftPackageRefusal("physical_draft_binding_mismatch")


def _disposition(state):
    owner = "issue"
    attempted = state.cleanup_attempted
    outcome = state.cleanup_outcome
    try:
        observed = state.fs.observe_package_cleanup(state.physical)
        if not attempted and observed.attempted:
            owner, attempted, outcome = "filesystem", True, observed.outcome
    except BaseException:  # noqa: BLE001 - unavailable observation never implies untouched inputs
        if not attempted:
            owner, attempted, outcome = "unknown", None, "unknown"
    value = IssueDraftPackageCleanupDisposition(
        replace(state.request),
        state.execution,
        "claimed" if state.physical_claim is not None else "unclaimed",
        owner,
        attempted,
        outcome,
        "issue" if state.custody is not None else "unknown",
        _evidence(state),
    )
    if state.claim is not None:
        state.claim.snapshot = value
    return value


def _release(state):
    if state.cleanup_attempted:
        return False
    _evidence(state)
    state.cleanup_attempted = True
    state.cleanup_outcome = "unknown"
    state.phase = "released"
    _disposition(state)  # Record ownership/attempt before invoking the physical owner.
    _release_custody(state.custody)
    for diagnostic in state.custody.diagnostics:
        if diagnostic not in state.diagnostics:
            state.diagnostics.append(diagnostic)
    try:
        observed = state.fs.observe_package_cleanup(state.physical)
        state.cleanup_outcome = observed.outcome if observed.attempted else "unknown"
    except BaseException as error:  # noqa: BLE001 - missing cleanup observation is not a new cleanup grant
        state.diagnostics.append(
            f"physical_cleanup_observation_unavailable:{type(error).__name__}"
        )
    _disposition(state)
    return state.custody.release_failed or state.cleanup_outcome != "completed"


def _retire(state, error):
    _release(state)
    state.phase = "retired"
    raise IssueDraftPackageRefusal(
        getattr(error, "code", "draft_admission_failed"),
        _evidence(state),
        getattr(error, "required_effect_paths", ()),
        input_cleanup=_disposition(state),
        input_custody=_safe_custody_observation(state.custody),
    ) from error


def _check(state):
    if state.phase in {"preparing", "retired", "consumed", "released"}:
        raise IssueDraftPackageRefusal("draft_admission_terminal", _evidence(state))
    try:
        _check_owners(state)
        _check_issue(state)
        _check_owners(state)
    except BaseException as error:  # noqa: BLE001 - interruption terminally spends authority
        _retire(state, error)


def _issued(value):
    state = (
        _ADMISSIONS.get(value)
        if type(value) is FilesystemIssueDraftPackageAdmission
        else None
    )
    if state is None:
        raise IssueDraftPackageRefusal("original_draft_admission_required")
    if state.pid != os.getpid():
        raise IssueDraftPackageRefusal(
            "draft_admission_foreign_process", state.last_evidence
        )
    return state


def _abandon(state):
    if state.pid != os.getpid():
        return
    with state.lock:
        _release(state)


class FilesystemIssueDraftPackageAdmission:
    __slots__ = ("__weakref__",)

    def __new__(cls):
        raise TypeError("Use the original provider's admit_draft_package")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Original draft admission cannot be subclassed")

    def __copy__(self):
        raise TypeError("Draft admission cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Draft admission cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Draft admission cannot be serialized")

    @property
    def phase(self):
        state = _issued(self)
        with state.lock:
            return state.phase

    @property
    def evidence(self):
        state = _issued(self)
        with state.lock:
            return _evidence(state)

    def observe_binding(self) -> IssueDraftPackageBinding:
        state = _issued(self)
        with state.lock:
            return _binding(state)

    def observe_cleanup(self) -> IssueDraftPackageCleanupDisposition:
        state = _ADMISSIONS.get(self)
        if state is None or state.pid != os.getpid():
            raise IssueDraftPackageRefusal("original_local_draft_observation_required")
        with state.lock:
            return _disposition(state)

    def validate_current(self):
        state = _issued(self)
        with state.lock:
            _check(state)

    def stage_next_effect(self):
        state = _issued(self)
        with state.lock:
            _check(state)
            try:
                if state.phase not in {"issued", "staging"}:
                    raise IssueDraftPackageRefusal("draft_staging_terminal")
                state.phase = "staging"
                effect = state.physical.stage_next_effect(
                    input_claim=state.physical_claim
                )
                if state.physical.phase == "staged":
                    state.phase = "staged"
                _check(state)
                return _effect(effect) if effect is not None else None
            except BaseException as error:  # noqa: BLE001 - staging effects must survive refusal
                _retire(state, error)

    def lend_staged_source(self):
        state = _issued(self)
        with state.lock:
            _check(state)
            try:
                if state.phase != "staged":
                    raise IssueDraftPackageRefusal("draft_stage_required")
                lens = state.physical.lend_staged_source(
                    input_claim=state.physical_claim
                )
                _check(state)
                return lens
            except BaseException as error:  # noqa: BLE001 - lens validation interruption retires authority
                _retire(state, error)

    def publish_package(self):
        state = _issued(self)
        with state.lock:
            _check(state)
            try:
                if state.phase != "staged":
                    raise IssueDraftPackageRefusal("draft_stage_required")
                state.phase = "publication_spent"
                state.publication_attempted = True
                state.protocol.spend_specification_draft_publication(
                    state.target, input_claim=state.protocol_claim
                )
                _check(state)
                image = state.physical.publish_package(input_claim=state.physical_claim)
                state.fs.require_retained_package_postimage(
                    image, plan=state.physical, input_claim=state.physical_claim
                )
                state.phase = "published"
                state.postimage = image
                _check(state)
                return image
            except BaseException as error:  # noqa: BLE001 - uncertain publication never retries
                _retire(state, error)

    def observe_input_custody(self):
        state = _issued(self)
        with state.lock:
            value = _safe_custody_observation(state.custody)
            if value is None:
                raise _custody_refusal("issue_input_observation_unavailable")
            return value

    def admit_published_read(self, *, physical_postimage):
        state = _issued(self)
        with state.lock:
            _check(state)
            if state.phase != "published" or physical_postimage is not state.postimage:
                raise IssueDraftPackageRefusal("original_admission_postimage_required")
            if state.read_selection is not None:
                raise IssueDraftPackageRefusal("draft_read_replay")
            try:
                state.read_selection = (
                    state.protocol.admit_specification_draft_published_read(
                        state.target,
                        physical_postimage=physical_postimage,
                        input_claim=state.protocol_claim,
                    )
                )
                _check(state)
                return state.read_selection
            except BaseException as error:  # noqa: BLE001 - preserve known publication on read refusal
                _retire(state, error)

    def validate_published_read(self, read_selection):
        state = _issued(self)
        with state.lock:
            if read_selection is not state.read_selection or read_selection is None:
                raise IssueDraftPackageRefusal("foreign_draft_read_selection")
            # Independent reads survive writer cleanup without renewing it.
            selection = import_module(
                "aware_protocol_fs_adapter.specification_selection"
            )
            selection.require_specification_selection(read_selection)

    def release_published_read(self, read_selection):
        state = _issued(self)
        with state.lock:
            if read_selection is not state.read_selection or read_selection is None:
                raise IssueDraftPackageRefusal("foreign_draft_read_selection")
            try:
                selection = import_module(
                    "aware_protocol_fs_adapter.specification_selection"
                )
                selection.release_specification_selection(read_selection)
            except BaseException as error:
                state.diagnostics.append(f"read_release_failed:{type(error).__name__}")
                raise IssueDraftPackageRefusal(
                    "draft_read_release_incomplete",
                    _evidence(state),
                    input_custody=_safe_custody_observation(state.custody),
                ) from error

    def finish(self, *, physical_postimage, read_selection):
        state = _issued(self)
        with state.lock:
            _check(state)
            try:
                if state.phase != "published":
                    raise IssueDraftPackageRefusal("draft_publication_required")
                if (
                    physical_postimage is not state.postimage
                    or read_selection is not state.read_selection
                ):
                    raise IssueDraftPackageRefusal("original_admission_read_required")
                state.fs.require_retained_package_postimage(
                    physical_postimage,
                    plan=state.physical,
                    input_claim=state.physical_claim,
                )
                state.protocol.finish_specification_draft_target(
                    state.target,
                    read_selection=read_selection,
                    input_claim=state.protocol_claim,
                )
                state.physical.finish(
                    physical_postimage, input_claim=state.physical_claim
                )
                _check_issue(state)
                _check_protocol_target(state)
                state.fs.require_retained_package_postimage(
                    physical_postimage,
                    plan=state.physical,
                    input_claim=state.physical_claim,
                )
                state.phase = "consumed"
                return IssueDraftPackageReceipt(
                    state.request.issue_ref,
                    state.execution,
                    state.request.client_intent_id,
                    state.request.authoring_intent_ref,
                    state.request.expected_issue_sha256,
                    state.request.expected_manifest_sha256,
                    state.request.candidate_sha256,
                    state.request.ordered_effect_paths,
                    _evidence(state),
                )
            except BaseException as error:  # noqa: BLE001 - late refusal preserves published package
                _retire(state, error)

    def release(self):
        state = _issued(self)
        with state.lock:
            completed = state.phase == "consumed"
            cleanup_failed = _release(state)
            if cleanup_failed:
                raise IssueDraftPackageRefusal(
                    "draft_release_incomplete",
                    _evidence(state),
                    input_cleanup=_disposition(state),
                    input_custody=_safe_custody_observation(state.custody),
                )
            if completed:
                try:
                    _check_issue(state)
                except BaseException as error:  # noqa: BLE001 - cleanup does not erase the final Issue guard
                    _retire(state, error)
            return _evidence(state)

    def validate_completed_current(self):
        """Consumed read-only return check, never another physical effect."""
        state = _issued(self)
        with state.lock:
            if state.phase != "consumed":
                raise IssueDraftPackageRefusal(
                    "draft_completed_admission_required", _evidence(state)
                )
            try:
                _check_issue(state)
                _check_protocol_target(state)
                state.fs.require_retained_package_postimage(
                    state.postimage,
                    plan=state.physical,
                    input_claim=state.physical_claim,
                )
            except BaseException as error:  # noqa: BLE001 - return-time interruption retires authority
                _retire(state, error)


def _binding(state):
    # Detach the portable snapshot from internal request identity; neither it
    # nor a reconstructed equal value can pass original admission verification.
    return IssueDraftPackageBinding(state.execution, replace(state.request))


def _observe_binding(provider, admission):
    from .provider import FilesystemIssueOperationProvider

    if type(provider) is not FilesystemIssueOperationProvider:
        raise IssueDraftPackageRefusal("original_issue_provider_required")
    state = _issued(admission)
    with state.lock:
        if state.provider is not provider:
            # Read rejection must not retire another provider's valid authority.
            raise IssueDraftPackageRefusal("foreign_issue_provider")
        return _binding(state)


def _validate_bound(provider, admission):
    state = _issued(admission)
    with state.lock:
        if state.provider is not provider:
            raise IssueDraftPackageRefusal("foreign_issue_provider")
        _check(state)


def _observe_cleanup(provider, protocol_target, physical_plan):
    from .provider import FilesystemIssueOperationProvider

    if type(provider) is not FilesystemIssueOperationProvider:
        raise IssueDraftPackageRefusal("original_issue_provider_required")
    with _ISSUANCE_LOCK:
        try:
            claim = _PLANS.get(physical_plan)
        except TypeError as error:
            raise IssueDraftPackageRefusal(
                "draft_cleanup_observation_unavailable"
            ) from error
        if (
            claim is None
            or claim.pid != os.getpid()
            or claim.provider() is not provider
        ):
            raise IssueDraftPackageRefusal("draft_cleanup_observation_unavailable")
        original_target = claim.target()
        if original_target is None or original_target is not protocol_target:
            raise IssueDraftPackageRefusal("draft_cleanup_observation_unavailable")
        state = claim.state() if claim.state is not None else None
        if state is not None:
            with state.lock:
                return _disposition(state)
        return replace(claim.snapshot, request=replace(claim.snapshot.request))


def _admit(provider, request, protocol_target, physical_plan, input_custody=None):
    from .provider import FilesystemIssueOperationProvider

    if type(provider) is not FilesystemIssueOperationProvider:
        raise IssueDraftPackageRefusal("original_issue_provider_required")
    if type(request) is not IssueDraftPackageRequest:
        raise TypeError("Draft requires exact neutral request, never setup intent")
    request = replace(request)
    custody = None
    state = None
    with _ISSUANCE_LOCK:
        try:
            if input_custody is None:
                # Every successor admission enrolls; this is not the old
                # invisible _PLANS rail. A fresh attempt remains distinct.
                import secrets

                guard = _retain_inputs(
                    provider,
                    protocol_target,
                    physical_plan,
                    "issue-legacy:" + secrets.token_hex(16),
                    request.client_intent_id,
                )
                context = claim_draft_input_custody(
                    guard,
                    provider=provider,
                    protocol_target=protocol_target,
                    physical_plan=physical_plan,
                    client_intent_id=request.client_intent_id,
                    context_ref="issue-legacy-context:" + secrets.token_hex(16),
                )
                custody = _custody_local(context, context=True)
            else:
                candidate = _custody_local(input_custody, context=True)
                _custody_identity(
                    candidate,
                    provider,
                    protocol_target,
                    physical_plan,
                    request.client_intent_id,
                )
                if candidate.phase != "reserved" or candidate.admission is not None:
                    raise _custody_refusal("issue_input_custody_spent")
                custody = candidate  # Only positively verified inputs may be disposed.
            fs, protocol = custody.fs, custody.protocol
            root = provider._repository_root.expanduser().resolve()
            binding = custody.binding
            if binding is None or (
                binding.root_locator != str(root)
                or binding.manifest_locator != request.manifest_locator
                or binding.manifest_sha256 != request.expected_manifest_sha256
                or binding.target_locator != request.target_locator
                or binding.scratch_locator != request.scratch_locator
                or binding.ordered_members != request.ordered_members
                or _relative_manifest(root, provider._protocol_source_ref)
                != request.manifest_locator
            ):
                raise IssueDraftPackageRefusal("draft_input_binding_mismatch")
            execution = _execution()
            path = _issue_path(provider, request)
            body, identity, parents = _read_issue(root, path)
            _policy(provider, request, execution, path, body)
            state = _State(
                provider,
                provider._repository_root,
                provider._protocol_source_ref,
                root,
                path,
                identity,
                parents,
                (),  # Filled only after authenticated lower-owner transfer.
                (),
                execution,
                request,
                physical_plan,
                protocol_target,
                fs,
                protocol,
                phase="preparing",
                lock=_ISSUANCE_LOCK,
                custody=custody,
            )
            handle = object.__new__(FilesystemIssueDraftPackageAdmission)
            _ADMISSIONS[handle] = state
            # Receiver is minted privately only for the genuine disabled
            # admission in this registry; no caller-supplied receiver/callback.
            receiver = object()
            custody.admission = ref(state)
            state.claim = _Claim(
                ref(provider),
                ref(protocol_target),
                IssueDraftPackageCleanupDisposition(
                    replace(request),
                    execution,
                    "unclaimed",
                    "issue",
                    False,
                    "not_attempted",
                    "issue",
                    _evidence(state),
                ),
                state=ref(state),
            )
            _PLANS[physical_plan] = state.claim  # History, never admission authority.
            custody.phase = "transferring"
            state.physical_claim = fs.transfer_package_input(
                custody.physical_reservation, receiver=receiver
            )
            custody.physical_claim = state.physical_claim
            state.protocol_claim = protocol.transfer_specification_draft_input(
                custody.joint, physical_claim=state.physical_claim, receiver=receiver
            )
            custody.protocol_claim = state.protocol_claim
            custody.phase = "transferred"
            manifest, manifest_identity, manifest_parents = _read_issue(
                root, request.manifest_locator
            )
            if (
                "sha256:" + hashlib.sha256(manifest).hexdigest()
                != request.expected_manifest_sha256
            ):
                raise IssueDraftPackageRefusal("manifest_source_sha256_mismatch")
            state.manifest_identity, state.manifest_parents = (
                manifest_identity,
                manifest_parents,
            )
            protocol.bind_specification_draft_physical_plan(
                protocol_target,
                physical_plan=physical_plan,
                input_claim=state.protocol_claim,
                physical_input_claim=state.physical_claim,
            )
            _check_owners(state)
            _check_issue(state)
            _check_owners(state)
            _disposition(state)
            finalize(handle, _abandon, state)
            state.phase = "issued"
            return handle
        except BaseException as error:
            if state is not None:
                _retire(state, error)
            if custody is not None and custody.admission is None:
                _release_custody(custody)
            observation = getattr(error, "input_custody", None)
            if custody is not None:
                try:
                    observation = _custody_observation(custody)
                except BaseException:  # noqa: BLE001 - unavailable is not permission
                    observation = None
            evidence = None if observation is None else observation.physical_evidence
            disposition = None
            if custody is not None and observation is not None:
                disposition = IssueDraftPackageCleanupDisposition(
                    replace(request),
                    custody.execution,
                    "claimed"
                    if observation.physical.transfer == "completed"
                    else "unclaimed",
                    "issue",
                    observation.physical.owner_cleanup_attempted,
                    observation.physical.owner_cleanup_outcome,
                    "issue",
                    evidence,
                )
                if custody.admission is None:
                    _PLANS[physical_plan] = _Claim(
                        ref(provider), ref(protocol_target), disposition
                    )
            raise IssueDraftPackageRefusal(
                getattr(error, "code", "draft_admission_failed"),
                evidence,
                getattr(error, "required_effect_paths", ()),
                input_custody=observation,
                input_cleanup=disposition,
            ) from error
