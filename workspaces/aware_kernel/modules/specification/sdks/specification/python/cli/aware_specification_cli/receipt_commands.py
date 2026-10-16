"""Present saved draft evidence through its SDK, never replay the operation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import TextIO, cast

from aware_command_runtime import AwareCommandInvocation, AwareCommandRegistry
from aware_specification_fs_sdk_adapter import SpecificationFsSavedReceiptProvider
from aware_specification_sdk.saved_receipt import (
    SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE,
    SPECIFICATION_SAVED_RECEIPT_OPERATION_REF,
    SpecificationSavedReceiptClient,
    SpecificationSavedReceiptError,
    SpecificationSavedReceiptErrorEvidence,
    SpecificationSavedReceiptRequest,
    SpecificationSavedReceiptValueError,
    encode_specification_saved_receipt_value,
)


def _configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--receipt-base",
        required=True,
        help="Explicit absolute normalized evidence directory; no cwd or repository default.",
    )
    parser.add_argument(
        "--receipt",
        required=True,
        help="Canonical relative saved-file path beneath --receipt-base; no absolute path or parent segments.",
    )
    parser.add_argument(
        "--expected-receipt-sha256",
        required=True,
        help="sha256:<hex> of exact saved receipt bytes, not Issue, Protocol or SPEC digests. No automatic refresh or retry.",
    )
    parser.add_argument(
        "--input-profile",
        required=True,
        choices=(SPECIFICATION_SAVED_RECEIPT_INPUT_PROFILE,),
        help="Explicit receiving transport profile; shape recognition does not authenticate the capture.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "full"),
        default="summary",
        help="Summary validates the whole capture before omission; full emits exact saved bytes without an added newline.",
    )


def register_receipt_commands(registry: AwareCommandRegistry) -> None:
    """Register a read-only command without source IO or supplier acquisition."""
    registry.register_command(
        name="present-receipt",
        help="Present a guarded saved draft capture; no operation replay or restored authority.",
        configure_parser=_configure,
        handle=_handle,
        source="aware_specification_cli",
        operation_ref=SPECIFICATION_SAVED_RECEIPT_OPERATION_REF,
    )


def _value(value: object) -> dict[str, object]:
    # The original SDK codec revalidates the complete value before projection.
    return json.loads(encode_specification_saved_receipt_value(value))["value"]


def _full_access(request: SpecificationSavedReceiptRequest) -> dict[str, object]:
    arguments = [
        "present-receipt",
        "--receipt-base",
        request.base_ref,
        "--receipt",
        request.source_ref,
        "--expected-receipt-sha256",
        request.expected_source_sha256,
        "--input-profile",
        request.input_profile,
        "--format",
        "full",
    ]
    return {
        "availability": "guarded_source_read",
        "standalone_argv": ["aware-spec", *arguments],
        "agent_argv": ["aware", "spec", *arguments],
    }


def _cause_kinds(error: BaseException) -> list[str]:
    kinds: list[str] = []
    seen: set[int] = set()
    cause = error.__cause__
    while cause is not None:
        if id(cause) in seen:
            kinds.append("cause_chain_cycle")
            break
        seen.add(id(cause))
        kinds.append(type(cause).__name__)
        cause = cause.__cause__
    return kinds


def _discard_failed_destination(stream: TextIO) -> tuple[str, tuple[str, ...]]:
    """Discard shutdown buffer residue, without flushing or closing the stream.

    Replacing only its destination prevents interpreter finalization from
    redelivering buffered bytes to the failed pipe and replacing exit 2 with 120.
    This is terminal CLI-output handling, not source-owner cleanup.
    """
    destination = None
    sink = None
    outcome = "unknown"
    diagnostics: list[str] = []
    try:
        destination = stream.fileno()
        sink = os.open(os.devnull, os.O_WRONLY | os.O_CLOEXEC)
        if sink != destination:
            _ = os.dup2(sink, destination)
        outcome = "discard_sink_installed"
    except BaseException as error:  # noqa: BLE001 - output retirement cannot erase original refusal evidence
        diagnostics.append(f"output_retirement_failed:{type(error).__name__}")
    finally:
        # If open reused an already closed destination, that fd now owns the
        # sink. Keep it alive for finalization; never close the stream itself.
        if sink is not None and sink != destination:
            try:
                os.close(sink)
            except BaseException as error:  # noqa: BLE001 - an uncertain close is not retried
                diagnostics.append(
                    f"discard_descriptor_close_unknown:{type(error).__name__}"
                )
    return outcome, tuple(diagnostics)


def _emit(
    output: dict[str, object], *, body: bytes | None = None, exit_code: int = 0
) -> int:
    """Write/flush success and refusal through the same terminal boundary."""
    stdout = sys.stdout
    try:
        if body is not None:
            stream = stdout.buffer
            if stream.write(body) != len(body):
                raise OSError("receipt_output_incomplete")
            stream.flush()
        else:
            text = json.dumps(output, sort_keys=True) + "\n"
            if stdout.write(text) != len(text):
                raise OSError("receipt_output_incomplete")
            stdout.flush()
    except BaseException as error:  # noqa: BLE001 - failed output never changes source outcomes or authorizes replay
        retirement, diagnostics = _discard_failed_destination(stdout)
        if exit_code == 2:
            # Preserve the complete original local/SDK refusal, its request,
            # unvalidated reports, observed source and cleanup. Do not replace
            # its primary error with the secondary output failure.
            failure = dict(output)
        else:
            failure = {
                "error": "receipt_output_failed",
                "request": output["request"],
                "validated_source": output["source"],
                "currentness": output["currentness"],
                "operation_invoked": False,
                "authority_restored": False,
                "authorizes_retry": False,
            }
        failure.update(
            output_error="receipt_output_failed",
            output_error_kind=type(error).__name__,
            output_completion="unknown",
            output_retirement=retirement,
            output_retirement_diagnostics=list(diagnostics),
        )
        stderr = sys.stderr
        try:
            print(json.dumps(failure, sort_keys=True), file=stderr, flush=True)
        except BaseException:  # noqa: BLE001 - no invented fallback when both output destinations fail
            _ = _discard_failed_destination(stderr)
        return 2
    return exit_code


def _handle(invocation: AwareCommandInvocation) -> int:
    args = invocation.args
    try:
        request = SpecificationSavedReceiptRequest(
            base_ref=args.receipt_base,
            source_ref=args.receipt,
            expected_source_sha256=args.expected_receipt_sha256,
            input_profile=args.input_profile,
            view=args.format,
        )
    except (SpecificationSavedReceiptValueError, UnicodeError) as error:
        refusal = SpecificationSavedReceiptError(
            SpecificationSavedReceiptErrorEvidence(
                "receipt_request_invalid",
                "Saved receipt request validation failed before invocation.",
                diagnostics=(str(error),),
            )
        )
        output = _value(refusal.evidence)
        output["error"] = refusal.code
        return _emit(output, exit_code=2)

    try:
        result = SpecificationSavedReceiptClient(
            SpecificationFsSavedReceiptProvider()
        ).present_draft_receipt(request)
    except SpecificationSavedReceiptError as error:
        output = _value(error.evidence)
        output["error"] = error.code
        # Preserve SDK notes and original cause classes, not host file contents.
        output["presentation_diagnostics"] = list(getattr(error, "__notes__", ()))
        output["cause_kind"] = (
            None if error.__cause__ is None else type(error.__cause__).__name__
        )
        output["cause_kinds"] = _cause_kinds(error)
        return _emit(output, exit_code=2)

    output = _value(result)
    body = bytes.fromhex(cast(str, output.pop("full_body_hex")))
    output["presentation_projection"] = "summary_without_full_body.v1"
    output["full_capture_omitted"] = True
    output["full_access"] = _full_access(result.request)
    return _emit(output, body=body if result.request.view == "full" else None)
