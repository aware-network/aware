"""SDK-owned read projections over the neutral Kernel command substrate."""

import argparse
import json
from pathlib import Path

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry
from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_runtime import (
    encode_specification_snapshot,
    resolve_iteration_identity,
)
from aware_specification_sdk import (
    SPECIFICATION_OBSERVE_OPERATION_REF,
    SpecificationObservation,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)

SOURCE_ARGUMENT_HELP = {
    "repository-root": "Customer repository root; relative to the invocation directory or absolute.",
    "protocol-manifest": "Protocol manifest; relative to --repository-root or absolute; default aware.protocol.toml.",
    "spec-manifest": "Selected aware.spec.toml; canonical repository-relative path, not absolute or relative to the Protocol manifest.",
    "expected-manifest-sha256": "sha256:<hex> of exact Protocol manifest bytes selected by --protocol-manifest, not aware.spec.toml or normalized semantics. No automatic refresh or retry.",
}


def _observation(value: SpecificationObservation) -> dict[str, object]:
    return {
        "snapshot": json.loads(encode_specification_snapshot(value.snapshot)),
        "source_digest": value.source_digest,
        "source_context_digest": value.source_context_digest,
        "provider_ref": value.provider_ref,
        "authority_mode": value.authority_mode,
        "observation_grade": value.observation_grade,
        "iterations": [
            {
                "iteration_ref": i.iteration_ref,
                "plan_revision": i.plan.plan_revision,
                "plan_digest": i.plan_digest,
            }
            for i in value.iterations
        ],
        "work_authority": False,
        "phase_acceptance": False,
    }


def _configure_observe(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repository-root", required=True, help=SOURCE_ARGUMENT_HELP["repository-root"]
    )
    parser.add_argument(
        "--protocol-manifest",
        default="aware.protocol.toml",
        help=SOURCE_ARGUMENT_HELP["protocol-manifest"],
    )
    parser.add_argument(
        "--spec-manifest",
        action="append",
        required=True,
        help=SOURCE_ARGUMENT_HELP["spec-manifest"]
        + " Repeat in exact UTF-8-byte order.",
    )
    parser.add_argument(
        "--expected-manifest-sha256",
        help=SOURCE_ARGUMENT_HELP["expected-manifest-sha256"],
    )
    parser.add_argument(
        "--expected-source-digest",
        help="SPEC source closure digest returned by observe; separate from Protocol manifest bytes, snapshot digest and source_context_digest.",
    )


def _configure_identity(parser: argparse.ArgumentParser) -> None:
    _configure_observe(parser)
    parser.add_argument(
        "--iteration-ref",
        required=True,
        help="Exact existing iteration_ref; resolves identity without approval or Issue binding.",
    )


def register_read_commands(registry: AwareCommandRegistry) -> None:
    """Register only reads, without source IO, admission or operation execution."""
    for name, help_text, configure in (
        (
            "observe",
            "Observe explicitly selected Specification sources.",
            _configure_observe,
        ),
        (
            "iteration-identity",
            "Resolve an existing iteration from a fresh observation.",
            _configure_identity,
        ),
    ):
        registry.register_command(
            name=name,
            help=help_text,
            configure_parser=configure,
            handle=_handle_read,
            source="aware_specification_cli",
            operation_ref=SPECIFICATION_OBSERVE_OPERATION_REF,
        )


def _handle_read(invocation: AwareCommandInvocation) -> int:
    args = invocation.args
    provider = None
    selection = None
    release = None
    output: dict[str, object] = {}
    exit_code = 2
    try:
        try:
            from aware_protocol_fs_adapter import (
                admit_specification_selection,
                release_specification_selection,
                require_specification_selection,
            )
        except ImportError as error:
            raise SpecificationOperationError(
                "protocol_integration_unavailable"
            ) from error
        release = release_specification_selection
        repository = Path(args.repository_root)
        manifest = Path(args.protocol_manifest)
        # Protocol resolves relative manifests beneath the repository once.
        admission = admit_specification_selection(
            repository_root=repository,
            manifest_path=manifest,
            selected_manifest_paths=tuple(args.spec_manifest),
            expected_manifest_sha256=args.expected_manifest_sha256,
        )
        selection = admission.selection
        if selection is None:
            output = {
                "error": "protocol_selection_admission_refused",
                "diagnostics": list(admission.admission.diagnostics),
                "effect": "none",
            }
        else:
            provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
            observation = SpecificationSdkClient(provider).observe(
                SpecificationObserveRequest(args.expected_source_digest)
            )
            output = _observation(observation)
            output["retained_capability_exported"] = False
            if args.command == "iteration-identity":
                identity = resolve_iteration_identity(
                    observation.snapshot, args.iteration_ref
                )
                output["selected_iteration_ref"] = identity.iteration_ref
            require_specification_selection(selection)
            exit_code = 0
    except (ValueError, OSError) as error:
        output = {
            "error": getattr(error, "code", "request_or_source_invalid"),
            "effect": getattr(error, "effect", "none"),
        }
        diagnostics = (
            tuple(getattr(error, "diagnostics", ()))
            + tuple(getattr(error, "cause_diagnostics", ()))
            + tuple(getattr(error, "__notes__", ()))
        )
        if diagnostics:
            output["diagnostics"] = list(diagnostics)
    finally:
        cleanup: list[str] = []
        try:
            if provider is not None:
                provider.close()
        except (ValueError, OSError) as error:
            cleanup.append(f"source_provider_cleanup_failed:{type(error).__name__}")
        finally:
            try:
                if selection is not None and release is not None:
                    release(selection)
            except (ValueError, OSError) as error:
                cleanup.append(
                    f"protocol_selection_cleanup_failed:{type(error).__name__}"
                )
        if cleanup:
            if exit_code == 0:
                output = {"error": "source_cleanup_failed", "effect": "none"}
                exit_code = 2
            output["cleanup_diagnostics"] = cleanup
    print(json.dumps(output, sort_keys=True))
    return exit_code
