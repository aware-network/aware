"""Read-only SDK composition; output is review guidance, never admission."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shlex
from pathlib import Path

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry


def _configure(parser: argparse.ArgumentParser) -> None:
    for name, help_text in (
        ("repository-root", "Explicit absolute customer repository root."),
        (
            "protocol-manifest",
            "Explicit Protocol manifest, absolute or repository-relative.",
        ),
        (
            "spec-manifest",
            "Explicit repository-relative SPEC manifest; must fit the configured root/<spec-key>/aware.spec.toml layout.",
        ),
        (
            "snapshot-json",
            "Authored snapshot input, absolute or relative to this invocation directory.",
        ),
        (
            "issue-ref",
            "Exact existing Issue reference; preparation does not create or claim it.",
        ),
        ("author-ref", "Declared draft author, not authenticated execution authority."),
        (
            "authoring-intent-ref",
            "Explicit draft intent, not publication authorization.",
        ),
        (
            "client-intent-id",
            "Explicit attempt correlation for the separately invoked draft operation.",
        ),
    ):
        parser.add_argument("--" + name, required=True, help=help_text)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")


def register_draft_preparation_command(registry: AwareCommandRegistry) -> None:
    registry.register_command(
        name="prepare-draft",
        help="Observe SDK guards and configured target fit; render draft review without write admission or apply.",
        configure_parser=_configure,
        handle=_handle,
        source="aware_agent_cli",
        operation_ref="agent_cli.prepare_specification_draft",
    )


def _suppliers():
    # Load the whole required public closure before invoking any observation.
    issue = importlib.import_module("aware_issue_sdk")
    issue_fs = importlib.import_module("aware_issue_fs_adapter")
    protocol = importlib.import_module("aware_protocol_sdk")
    protocol_fs = importlib.import_module("aware_protocol_fs_adapter")
    protocol_values = importlib.import_module("aware_protocol_runtime")
    spec = importlib.import_module("aware_specification_sdk")
    spec_fs = importlib.import_module("aware_specification_fs_sdk_adapter")
    spec_values = importlib.import_module("aware_specification_runtime")
    for module, names in (
        (
            issue,
            (
                "IssueSdkOperationClient",
                "IssueReadProjectionResolveRequest",
                "IssueReadProjectionResolveOutcome",
                "IssueProviderResultError",
            ),
        ),
        (issue_fs, ("FilesystemIssueOperationProvider",)),
        (
            protocol,
            (
                "ProtocolSdkClient",
                "ProtocolTargetAdmissionRequest",
                "ProtocolTargetAdmissionError",
                "ProtocolSpecificationTargetFitClient",
                "ProtocolSpecificationTargetFitRequest",
                "ProtocolSpecificationTargetFitOutcome",
                "ProtocolSpecificationTargetFitError",
                "protocol_specification_target_fit_value_to_payload",
            ),
        ),
        (
            protocol_fs,
            (
                "FilesystemProtocolSdkProvider",
                "FilesystemProtocolSpecificationTargetFitProvider",
            ),
        ),
        (protocol_values, ("ProtocolAuthorityMode", "ProtocolAdmissionOutcomeKind")),
        (
            spec,
            (
                "SpecificationInputObservationClient",
                "SpecificationInputObservationRequest",
                "SpecificationInputObservationError",
                "SpecificationDraftRequest",
                "encode_specification_value",
                "encode_specification_input_value",
            ),
        ),
        (
            spec_fs,
            ("SpecificationFsInputObservationProvider", "render_specification_draft"),
        ),
        (spec_values, ("decode_specification_snapshot",)),
    ):
        for name in names:
            if not callable(getattr(module, name)):
                raise ImportError(  # noqa: TRY004 - missing qualified export, not caller type
                    "Required public supplier unavailable: " + name
                )
    for owner, method in (
        (issue.IssueSdkOperationClient, "resolve_read_projection"),
        (issue_fs.FilesystemIssueOperationProvider, "resolve_read_projection"),
        (protocol.ProtocolSdkClient, "admit_target"),
        (protocol_fs.FilesystemProtocolSdkProvider, "admit_target"),
        (protocol.ProtocolSpecificationTargetFitClient, "observe"),
        (
            protocol_fs.FilesystemProtocolSpecificationTargetFitProvider,
            "observe_specification_target_fit",
        ),
        (spec.SpecificationInputObservationClient, "observe_draft_input"),
        (spec_fs.SpecificationFsInputObservationProvider, "observe_draft_input"),
    ):
        if not callable(getattr(owner, method)):
            raise ImportError(  # noqa: TRY004 - missing qualified export, not caller type
                "Required public observation method unavailable: " + method
            )
    return (
        issue,
        issue_fs,
        protocol,
        protocol_fs,
        protocol_values,
        spec,
        spec_fs,
        spec_values,
    )


def _print_target_fit(observation: dict) -> None:
    request = observation.get("request") or {}
    print("Supplied SPEC target:", request.get("supplied_spec_manifest_locator"))
    print("Configured SPEC root:", observation.get("configured_root"))
    print("Configured template:", observation.get("path_template"))
    print("Expected target shape:", observation.get("expected_shape"))
    print("Target fit:", observation.get("fit", observation.get("observed_fit")))
    print("Target-fit reason:", observation.get("reason", observation.get("code")))
    print("Target-fit cleanup:", observation.get("cleanup"))
    print(
        "Layout observation only; not Issue eligibility, destination availability, semantic approval or future apply success."
    )


def _emit_refusal(output: dict, format: str) -> int:
    if format == "summary":
        print("Draft preparation refused — no executable preview/apply guidance.")
        observation = output["owner_observations"].get("target_fit")
        if observation is None and output.get("stage") == "target_fit_observation":
            observation = output.get("owner_error")
        if observation is not None:
            _print_target_fit(observation)
        print("Reason:", output.get("error"))
        if "next_action" in output:
            print(output["next_action"])
        print("Original observation and failure evidence:")
    print(json.dumps(output, sort_keys=True))
    return 2


def _handle(invocation: AwareCommandInvocation) -> int:
    args = invocation.args
    output = {
        "operation": "agent_cli.prepare_specification_draft",
        "status": "refused",
        "effect": "none",
        "write_admission_issued": False,
        "apply_invoked": False,
        "observations_atomic": False,
        "authorizes_retry": False,
        "owner_observations": {},
    }
    try:
        suppliers = _suppliers()
    except (ImportError, AttributeError) as error:
        output.update(
            error="draft_preparation_supplier_unavailable",
            detail=str(error),
            next_action="Use the qualified complete installation; do not substitute a private matcher, provider or environment.",
        )
        return _emit_refusal(output, args.format)
    issue, issue_fs, protocol, protocol_fs, pv, spec, spec_fs, sv = suppliers
    stage = "selection"
    try:
        root = Path(args.repository_root)
        if not root.is_absolute():
            raise ValueError("repository_root_absolute_required")
        # An explicit selection is not a repository snapshot or write permit.
        protocol_request = protocol.ProtocolTargetAdmissionRequest(
            pv.ProtocolAuthorityMode.FILESYSTEM,
            args.repository_root,
            args.protocol_manifest,
        )
        stage = "protocol_observation"
        protocol_result = protocol.ProtocolSdkClient(
            protocol_fs.FilesystemProtocolSdkProvider()
        ).admit_target(protocol_request)
        output["owner_observations"]["protocol"] = protocol_result.to_wire()
        if (
            protocol_result.admission.outcome
            is not pv.ProtocolAdmissionOutcomeKind.CANONICAL_V1
        ):
            output["error"] = "protocol_observation_not_canonical"
            return _emit_refusal(output, args.format)
        stage = "target_fit_request"
        target_fit_request = protocol.ProtocolSpecificationTargetFitRequest(
            args.repository_root,
            args.protocol_manifest,
            args.spec_manifest,
            protocol_result.admission.source_sha256,
        )
        stage = "target_fit_observation"
        target_fit = protocol.ProtocolSpecificationTargetFitClient(
            protocol_fs.FilesystemProtocolSpecificationTargetFitProvider()
        ).observe(target_fit_request)
        output["owner_observations"]["target_fit"] = (
            protocol.protocol_specification_target_fit_value_to_payload(target_fit)
        )
        if target_fit.fit is not protocol.ProtocolSpecificationTargetFitOutcome.MATCH:
            output.update(
                error=target_fit.reason,
                next_action="Choose a target explicitly using the configured root and expected shape, then prepare and review again. No target has been corrected or inferred; no executable guidance is available.",
            )
            return _emit_refusal(output, args.format)
        stage = "issue_observation"
        issue_result = issue.IssueSdkOperationClient(
            issue_fs.FilesystemIssueOperationProvider(
                repository_root=args.repository_root,
                protocol_source_ref=args.protocol_manifest,
            )
        ).resolve_read_projection(
            issue.IssueReadProjectionResolveRequest(args.issue_ref)
        )
        output["owner_observations"]["issue"] = issue_result.to_wire()
        if issue_result.outcome is not issue.IssueReadProjectionResolveOutcome.FOUND:
            output["error"] = "issue_observation_not_found"
            return _emit_refusal(output, args.format)
        stage = "input_observation"
        observed = spec.SpecificationInputObservationClient(
            spec_fs.SpecificationFsInputObservationProvider()
        ).observe_draft_input(
            spec.SpecificationInputObservationRequest(args.snapshot_json, os.getcwd())
        )
        output["owner_observations"]["input"] = json.loads(
            spec.encode_specification_input_value(observed)
        )
        stage = "draft_rendering"
        snapshot = sv.decode_specification_snapshot(observed.body)
        if len(snapshot.definitions) != 1:
            raise ValueError("draft_requires_one_definition_without_iterations")
        request = spec.SpecificationDraftRequest(
            snapshot.definitions[0], args.author_ref, args.authoring_intent_ref
        )
        members = spec_fs.render_specification_draft(request)
        output["draft_request"] = json.loads(spec.encode_specification_value(request))
        # Member presentation follows the original pure renderer; not publication.
        import hashlib

        output["members"] = [
            {
                "path": path,
                "bytes": len(body),
                "source_sha256": "sha256:" + hashlib.sha256(body).hexdigest(),
            }
            for path, body in members
        ]
        guards = {
            "issue_source_bytes": issue_result.projection.source_digest,
            "protocol_manifest_bytes": protocol_result.admission.source_sha256,
            "snapshot_input_bytes": observed.source_sha256,
        }
        argv = ["aware", "spec", "create-draft"]
        for name, value in (
            ("repository-root", args.repository_root),
            ("protocol-manifest", args.protocol_manifest),
            ("spec-manifest", args.spec_manifest),
            ("snapshot-json", observed.source_ref),
            ("issue-ref", args.issue_ref),
            ("author-ref", args.author_ref),
            ("authoring-intent-ref", args.authoring_intent_ref),
            ("client-intent-id", args.client_intent_id),
            ("expected-issue-sha256", guards["issue_source_bytes"]),
            ("expected-manifest-sha256", guards["protocol_manifest_bytes"]),
            ("expected-input-sha256", guards["snapshot_input_bytes"]),
        ):
            argv.extend(("--" + name, value))
        output.update(
            status="prepared",
            guards=guards,
            preview_argv=argv,
            apply_argv=[*argv, "--apply"],
            next_action="Layout matched only; review input, intended members, Issue eligibility and selections, then explicitly invoke the original preview or apply command with these guards unchanged. Destination availability, semantic validation and write admission are checked by that original command. Staleness requires new preparation and review, never guard refresh or automatic retry.",
        )
    except Exception as error:  # noqa: BLE001 - preserve original owner error data, without retry
        output.update(
            stage=stage,
            error=getattr(error, "code", str(error)),
            effect=getattr(
                error,
                "effect",
                "none" if stage in ("selection", "target_fit_request") else "unknown",
            ),
        )
        if isinstance(error, spec.SpecificationInputObservationError):
            output["owner_error"] = json.loads(
                spec.encode_specification_input_value(error)
            )
        elif isinstance(error, protocol.ProtocolSpecificationTargetFitError):
            output["owner_error"] = (
                protocol.protocol_specification_target_fit_value_to_payload(
                    getattr(error, "evidence")  # noqa: B009 - lazy owner class prevents static narrowing
                )
            )
            output["next_action"] = (
                "Inspect original target-fit refusal and cleanup evidence. No command is provided; do not correct a target, refresh a guard or retry automatically. Any new preparation requires explicit selection and review."
            )
        elif isinstance(
            error,
            (issue.IssueProviderResultError, protocol.ProtocolTargetAdmissionError),
        ):
            output["owner_error"] = getattr(error, "to_wire")()  # noqa: B009 - lazy owner class prevents static narrowing
        return _emit_refusal(output, args.format)
    if args.format == "json":
        print(json.dumps(output, sort_keys=True))
    else:
        print("Draft preparation only — no write admission or effects.")
        _print_target_fit(output["owner_observations"]["target_fit"])
        print("Issue:", args.issue_ref, "at", issue_result.projection.source_path)
        print("Observed Issue status:", issue_result.projection.status)
        print("Observed Issue execution:", issue_result.projection.owner_ref)
        print(
            "Observed Issue scope:", ", ".join(issue_result.projection.ownership_scope)
        )
        print("Protocol:", args.protocol_manifest, "in", args.repository_root)
        print("Input:", observed.source_ref, "cleanup:", observed.cleanup.value)
        print("Draft:", request.definition.title, "author:", request.author_ref)
        for meaning, guard in guards.items():
            print(meaning + ":", guard)
        for member in output["members"]:
            print("Member:", member["path"], "bytes:", member["bytes"])
        print("Independent observations; no atomic snapshot or exact publication plan.")
        print("Review then preview:", shlex.join(output["preview_argv"]))
        print("Explicit apply only after review:", shlex.join(output["apply_argv"]))
        print(output["next_action"])
    return 0
