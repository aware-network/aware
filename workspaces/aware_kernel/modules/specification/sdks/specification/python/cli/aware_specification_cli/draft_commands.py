"""Lazy original-owner draft projection; no policy, renderer or physical writer."""

from __future__ import annotations

import argparse
import errno
import hashlib
import importlib
import json
import os
import stat
import sys
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from pathlib import Path
from secrets import token_hex
from typing import Any

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry

from .read_commands import SOURCE_ARGUMENT_HELP

INPUT_LIMIT = 2 * 1024 * 1024


class DraftInputError(ValueError):
    def __init__(self, code: str, *, diagnostics: tuple[str, ...] = ()) -> None:
        super().__init__(code)
        self.code = code
        self.diagnostics = diagnostics


def _configure(parser: argparse.ArgumentParser) -> None:
    help_text = {
        **SOURCE_ARGUMENT_HELP,
        "snapshot-json": "Canonical snapshot input file; relative to the invocation directory or absolute, not --repository-root. Maximum 2 MiB; no final symlink.",
        "author-ref": "Declared draft author reference; not approval or execution authority.",
        "authoring-intent-ref": "Explicit customer draft intent; does not authorize publication by itself.",
        "client-intent-id": "Explicit attempt correlation; not a reusable admission or automatic retry key.",
        "issue-ref": "Exact active Issue reference, independently admitted by the Issue owner.",
        "expected-issue-sha256": "sha256:<hex> of exact Issue document bytes observed through the Issue owner; not Protocol or SPEC bytes.",
    }
    for flag in (
        "repository-root",
        "spec-manifest",
        "snapshot-json",
        "author-ref",
        "authoring-intent-ref",
        "client-intent-id",
        "issue-ref",
        "expected-issue-sha256",
        "expected-manifest-sha256",
    ):
        parser.add_argument("--" + flag, required=True, help=help_text[flag])
    parser.add_argument(
        "--protocol-manifest",
        default="aware.protocol.toml",
        help=help_text["protocol-manifest"],
    )
    parser.add_argument(
        "--expected-input-sha256",
        help="sha256:<hex> of exact snapshot input bytes from the reviewed preview's input_sha256; required for --apply. Not snapshot_digest or rendered member digests.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Explicit publication request; default is preview. Fresh admissions required; no stale-guard refresh or automatic retry after refusal/publication.",
    )


def register_draft_commands(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="create-draft",
        help="Preview a governed draft; --apply explicitly requests publication.",
        configure_parser=_configure,
        handle=_handle,
        source="aware_specification_cli",
        operation_ref="specification_sdk.create_draft",
    )


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def read_draft_input(path: Path) -> bytes:
    """One bounded regular-file observation, not Specification admission."""
    try:
        descriptor = os.open(
            path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
        )
    except OSError as error:
        reason = {
            errno.ENOENT: "not_found",
            errno.ENOTDIR: "parent_not_directory",
            errno.EACCES: "permission_denied",
            errno.EPERM: "permission_denied",
            errno.ELOOP: "symlink_or_loop",
        }.get(error.errno if error.errno is not None else 0, "unavailable")
        raise DraftInputError(
            "draft_input_open_failed",
            diagnostics=(
                "draft_input_reason:" + reason,
                "draft_input_detail:" + type(error).__name__,
            ),
        ) from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise DraftInputError("draft_input_regular_file_required")
        if before.st_size > INPUT_LIMIT:
            raise DraftInputError("draft_input_too_large")
        parts = []
        count = 0
        while True:
            body = os.read(descriptor, min(65536, INPUT_LIMIT + 1 - count))
            if not body:
                break
            parts.append(body)
            count += len(body)
            if count > INPUT_LIMIT:
                raise DraftInputError("draft_input_too_large")
        after = os.fstat(descriptor)
        named = path.lstat()
        if _identity(before) != _identity(after) or _identity(after) != _identity(
            named
        ):
            raise DraftInputError("draft_input_changed")
        if count != before.st_size:
            raise DraftInputError("draft_input_changed")
        return b"".join(parts)
    finally:
        os.close(descriptor)


def _wire(value: object) -> object:
    if isinstance(value, bytes):
        return {"encoding": "hex", "body": value.hex()}
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    raise TypeError("unsupported_draft_evidence_value")


def _suppliers() -> tuple[Any, Any, Any, Any, Any, Any]:
    # These integration imports are never reached by registration or readers.
    runtime = importlib.import_module("aware_specification_runtime")
    sdk = importlib.import_module("aware_specification_sdk")
    cleanup = importlib.import_module("aware_specification_sdk.draft_cleanup")
    spec = importlib.import_module("aware_specification_fs_sdk_adapter")
    protocol = importlib.import_module("aware_protocol_fs_adapter")
    physical = importlib.import_module("aware_file_system.retained_package")
    issue = importlib.import_module("aware_issue_fs_adapter")
    custody_values = importlib.import_module("aware_issue_sdk.draft_input_custody")
    for module, names in (
        (spec, ("render_specification_draft", "open_governed_specification_draft")),
        (
            protocol,
            ("admit_specification_draft_target", "release_specification_draft_target"),
        ),
        (physical, ("retain_package_publication", "observe_package_cleanup")),
        (
            issue.FilesystemIssueOperationProvider,
            ("observe_draft_package_cleanup", "retain_draft_inputs"),
        ),
        (sdk, ("SpecificationDraftCleanupEvidence",)),
    ):
        for name in names:
            getattr(module, name)
    return runtime, sdk, cleanup, spec, protocol, (physical, issue, custody_values)


def _handle(invocation: AwareCommandInvocation) -> int:
    args = invocation.args  # Invocation context supplies no authority.
    output: dict[str, Any] = {
        "effect": "none",
        "consumer_completion_verified": False,
        "retained_capability_exported": False,
    }
    try:
        runtime, sdk, cleanup, spec, protocol, owners = _suppliers()
    except (ImportError, AttributeError) as error:
        output.update(
            error="governed_draft_integration_unavailable", detail=type(error).__name__
        )
        print(json.dumps(output, sort_keys=True))
        return 2
    physical, issue, custody_values = owners
    manager = target = plan = custody = None
    carrier = None
    input_custody: Any = None
    primary: BaseException | None = None
    diagnostics: list[str] = []
    caller_cleanup: dict[str, Any] = {}

    def remember_input_custody(value: object) -> None:
        nonlocal input_custody
        if type(value) is not custody_values.IssueDraftInputCustodyObservation:
            raise ValueError("original_issue_custody_observation_required")
        candidate: Any = deepcopy(value)
        candidate.__post_init__()
        if input_custody is not None and (
            candidate.attempt_ref,
            candidate.client_intent_id,
            candidate.execution_ref,
        ) != (
            input_custody.attempt_ref,
            input_custody.client_intent_id,
            input_custody.execution_ref,
        ):
            raise ValueError("cli_custody_observation_correlation_failed")
        input_custody = candidate

    def observe_cleanup() -> None:
        nonlocal carrier, input_custody
        # This portable evidence never grants disposal authority. Only original
        # custody handles/guarded resource ports arbitrate ownership.
        try:
            supplied = (
                None if primary is None else getattr(primary, "input_custody", None)
            )
            if supplied is not None:
                remember_input_custody(supplied)
            if custody is not None:
                remember_input_custody(custody.observe_cleanup())
        except BaseException as error:  # noqa: BLE001 - preserve primary and previously observed history
            diagnostics.append("cli_custody_observation_failed:" + type(error).__name__)
        try:
            supplied = (
                None if primary is None else getattr(primary, "cleanup_evidence", None)
            )
            if supplied is not None:
                candidate = cleanup.snapshot_draft_cleanup(supplied)
                if carrier is not None:
                    cleanup.require_cleanup_extension(carrier, candidate)
                carrier = candidate
            if manager is not None:
                candidate = cleanup.snapshot_draft_cleanup(
                    manager.observe_draft_cleanup()
                )
                if carrier is not None:
                    cleanup.require_cleanup_extension(carrier, candidate)
                carrier = candidate
        except BaseException as error:  # noqa: BLE001 - secondary observation never masks primary/effects
            diagnostics.append("cli_cleanup_observation_failed:" + type(error).__name__)

    try:
        if args.apply and args.expected_input_sha256 is None:
            raise DraftInputError("draft_apply_input_digest_required")
        body = read_draft_input(Path(args.snapshot_json))
        digest = "sha256:" + hashlib.sha256(body).hexdigest()
        output["input_sha256"] = digest
        if (
            args.expected_input_sha256 is not None
            and args.expected_input_sha256 != digest
        ):
            raise DraftInputError("draft_input_sha256_mismatch")
        snapshot = runtime.decode_specification_snapshot(body)
        if len(snapshot.definitions) != 1:
            raise DraftInputError("draft_requires_one_definition_without_iterations")
        request = sdk.SpecificationDraftRequest(
            snapshot.definitions[0], args.author_ref, args.authoring_intent_ref
        )
        members = spec.render_specification_draft(request)
        output.update(
            snapshot_digest=snapshot.snapshot_digest,
            members=[
                {
                    "path": path,
                    "bytes": len(value),
                    "sha256": "sha256:" + hashlib.sha256(value).hexdigest(),
                }
                for path, value in members
            ],
        )
        root = Path(args.repository_root).absolute()
        manifest = Path(args.protocol_manifest)
        if not manifest.is_absolute():
            manifest = root / manifest
        target = protocol.admit_specification_draft_target(
            repository_root=root,
            manifest_path=manifest,
            selected_manifest_path=args.spec_manifest,
            expected_manifest_sha256=args.expected_manifest_sha256,
        )
        # Only the original target supplies the admitted locator; no key inference.
        locator = target.manifest_locator
        plan = physical.retain_package_publication(
            root=root, target_path=target.target_locator, ordered_members=members
        )
        provider = issue.FilesystemIssueOperationProvider(
            repository_root=root, protocol_source_ref=locator
        )
        custody = provider.retain_draft_inputs(
            attempt_ref="cli-specification-draft:" + token_hex(16),
            client_intent_id=args.client_intent_id,
            protocol_target=target,
            physical_plan=plan,
        )
        manager = spec.open_governed_specification_draft(
            request=request,
            issue_provider=provider,
            issue_ref=args.issue_ref,
            expected_issue_sha256=args.expected_issue_sha256,
            protocol_draft_target=target,
            physical_package_plan=plan,
            client_intent_id=args.client_intent_id,
            input_custody=custody,
        )
        with manager as client:
            if args.apply:
                result = client.create_draft(request)
                output.update(
                    operation_outcome="published",
                    effect="published",
                    created_paths=result.created_paths,
                    authoring_intent_ref=result.authoring_intent_ref,
                    evidence=result.evidence,
                )
                # This actual read remains separately non-authorizing.
                from .read_commands import _observation

                output["observation"] = _observation(result.observation)
            else:
                output["operation_outcome"] = "previewed"
        observe_cleanup()  # Never emit success from inside the context.
    except BaseException as error:  # noqa: BLE001 - preserve interruption while releasing owned inputs
        primary = error
        output.update(
            error=getattr(error, "code", "draft_request_or_source_invalid"),
            effect=getattr(
                error,
                "effect",
                "unknown" if output["effect"] == "published" else "none",
            ),
        )
        evidence = getattr(error, "evidence", None)
        if evidence is not None:
            output["evidence"] = evidence
        output["evidence_diagnostics"] = tuple(
            getattr(error, "evidence_diagnostics", ())
        )
        output["primary_diagnostics"] = (
            tuple(getattr(error, "diagnostics", ()))
            + tuple(getattr(error, "cause_diagnostics", ()))
            + tuple(getattr(error, "__notes__", ()))
        )
        if isinstance(error, DraftInputError):
            next_action = {
                "draft_apply_input_digest_required": (
                    "Run preview, review its exact input_sha256, then supply "
                    "--expected-input-sha256 for an explicitly requested apply."
                ),
                "draft_input_sha256_mismatch": (
                    "The saved input differs from the reviewed guard. "
                    "Reobserve and review the changed input in a new preview; "
                    "do not silently replace the guard or retry apply."
                ),
                "draft_input_too_large": "Prepare canonical snapshot input within the 2 MiB limit before a new preview.",
                "draft_input_regular_file_required": "Select a regular snapshot file, not a directory or special file, before a new preview.",
                "draft_input_changed": "Input changed during observation. Stabilize and review its exact bytes in a new preview before any apply.",
                "draft_requires_one_definition_without_iterations": "Prepare exactly one complete draft definition without iterations, then review a new preview.",
            }.get(
                error.code,
                "Select a readable regular snapshot file using an absolute path "
                "or a path relative to the invocation directory, not --repository-root. "
                "Review exact input bytes and guards before a new preview; "
                "do not automatically retry apply.",
            )
            output["input_guidance"] = {
                "argument": "--snapshot-json",
                "path_base": "invocation_directory_or_absolute",
                "reason": error.code,
                "next_action": next_action,
            }
        observe_cleanup()
    finally:
        cleanup_already_attempted = input_custody is not None and all(
            resource.release_invocation != "not_invoked"
            for resource in (input_custody.physical, input_custody.protocol)
        )
        if custody is not None and manager is None and not cleanup_already_attempted:
            # Factory construction may fail before association. Ask the original
            # bare custody exactly once; it refuses an associated context before
            # effects. No public phase/DTO is treated as a cleanup permission.
            caller_cleanup["custody"] = {"invocation_state": "invoked"}
            try:
                remember_input_custody(custody.release())
                caller_cleanup["custody"]["invocation_state"] = "returned"
            except BaseException as error:  # noqa: BLE001 - original arbitration preserves other owners
                caller_cleanup["custody"]["invocation_state"] = "raised"
                supplied = getattr(error, "input_custody", None)
                if supplied is not None:
                    try:
                        remember_input_custody(supplied)
                    except BaseException as observation_error:  # noqa: BLE001 - never mask original disposal refusal
                        diagnostics.append(
                            "cli_custody_observation_failed:"
                            + type(observation_error).__name__
                        )
                diagnostics.append("cli_custody_release_failed:" + type(error).__name__)
        # No returned custody: dispose only CLI-created originals through the
        # successors' atomic unreserved guards. A racing/partial reservation
        # refuses before effects; an observation is never a substitute claim.
        for label, holder, release in (
            (
                "physical",
                plan,
                None if plan is None else lambda: plan.release(input_claim=None),
            ),
            (
                "protocol",
                target,
                None
                if target is None
                else lambda: protocol.release_specification_draft_target(
                    target, input_claim=None
                ),
            ),
        ):
            if custody is not None or holder is None or release is None:
                continue
            if label == "physical":
                try:
                    observed = physical.observe_package_cleanup(plan)
                    caller_cleanup["physical_observation"] = observed
                    if observed.attempted:
                        continue
                except BaseException as error:  # noqa: BLE001 - the atomic owner guard, not unknown evidence, decides
                    diagnostics.append(
                        "cli_physical_observation_failed:" + type(error).__name__
                    )
            caller_cleanup[label] = {
                "invocation_state": "invoked",
                "owner_completion": "unknown",
            }
            try:
                release()
                caller_cleanup[label]["invocation_state"] = "returned"
            except BaseException as error:  # noqa: BLE001 - attempt other owned cleanup once; preserve primary
                caller_cleanup[label]["invocation_state"] = "raised"
                diagnostics.append(
                    "cli_" + label + "_release_failed:" + type(error).__name__
                )
            if label == "physical":
                try:
                    caller_cleanup["physical_observation"] = (
                        physical.observe_package_cleanup(plan)
                    )
                except BaseException as error:  # noqa: BLE001 - never invent owner completion
                    diagnostics.append(
                        "cli_physical_observation_failed:" + type(error).__name__
                    )
        observe_cleanup()
    output.update(
        cleanup_evidence=carrier,
        input_custody=input_custody,
        caller_cleanup=caller_cleanup,
        cleanup_diagnostics=diagnostics,
        protocol_owner_completion="unknown"
        if carrier is None
        else carrier.protocol_owner_outcome,
    )
    # Conservatively retain known publication from either independent owner ledger.
    if carrier is not None:
        for value in (carrier.issue_disposition, carrier.physical_observation):
            if (
                value is not None
                and value.evidence is not None
                and value.evidence.package_outcome == "published"
            ):
                output["effect"] = "published"
        if (
            carrier.input_custody is not None
            and carrier.input_custody.physical_evidence is not None
            and carrier.input_custody.physical_evidence.package_outcome == "published"
        ):
            output["effect"] = "published"
    if (
        input_custody is not None
        and input_custody.physical_evidence is not None
        and input_custody.physical_evidence.package_outcome == "published"
    ):
        output["effect"] = "published"
    # Presentation of this genuine, fully exited composition only. Detached
    # evidence never admits a write, restores a claim or authorizes cleanup.
    verified = (
        primary is None
        and manager is not None
        and custody is not None
        and not diagnostics
        and not caller_cleanup
        and output.get("operation_outcome")
        == ("published" if args.apply else "previewed")
        and carrier is not None
        and carrier.context_state == "closed"
        and not carrier.cleanup_diagnostics
        and carrier.protocol_owner_attempted is True
        and carrier.protocol_owner_outcome == "completed"
        and carrier.input_custody is not None
        and input_custody is not None
        and (
            carrier.attempt_ref,
            carrier.input_custody.client_intent_id,
            carrier.input_custody.execution_ref,
            carrier.input_custody.context_ref,
        )
        == (
            input_custody.attempt_ref,
            input_custody.client_intent_id,
            input_custody.execution_ref,
            input_custody.context_ref,
        )
        and carrier.input_custody.context_ref is not None
        and not carrier.input_custody.diagnostics
        and not input_custody.diagnostics
        and all(
            resource.owner_cleanup_attempted is True
            and resource.owner_cleanup_outcome == "completed"
            and resource.release_invocation == "returned"
            and not resource.diagnostics
            for value in (carrier.input_custody, input_custody)
            for resource in (value.physical, value.protocol)
        )
        and all(
            value.responsibility == "context"
            and value.invocation_state == "returned"
            and not value.diagnostics
            for value in (carrier.physical_invocation, carrier.protocol_invocation)
        )
        and carrier.issue_disposition is not None
        and carrier.issue_disposition.physical_claim == "claimed"
        and carrier.issue_disposition.physical_cleanup_attempted is True
        and carrier.issue_disposition.physical_cleanup_outcome == "completed"
        and carrier.physical_observation is not None
        and carrier.physical_observation.attempted is True
        and carrier.physical_observation.outcome == "completed"
        and all(
            ledger is not None
            and not ledger.cleanup_diagnostics
            and not ledger.residual_scratch_paths
            for ledger in (
                carrier.issue_disposition.evidence,
                carrier.physical_observation.evidence,
                carrier.input_custody.physical_evidence,
                input_custody.physical_evidence,
            )
        )
    )
    output["consumer_completion_verified"] = verified
    if primary is None and not verified:
        output["error"] = "draft_cleanup_completion_unverified"
    if isinstance(primary, (KeyboardInterrupt, SystemExit)):
        print(json.dumps(output, sort_keys=True, default=_wire), file=sys.stderr)
        raise primary
    print(json.dumps(output, sort_keys=True, default=_wire))
    return 0 if verified else 2
