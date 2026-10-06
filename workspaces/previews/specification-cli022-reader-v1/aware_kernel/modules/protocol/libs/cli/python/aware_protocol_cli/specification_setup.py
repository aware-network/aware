"""Optional client composition above Protocol and Issue owners.

No new writer or policy: the real Issue capability consumes its owning physical
operations. New command source does not establish an installed release.
"""

from __future__ import annotations

from argparse import Namespace
from dataclasses import asdict, replace
from importlib import import_module
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from aware_issue_fs_adapter import FilesystemIssueOperationProvider
    from aware_issue_sdk.source_change import (
        IssueSourceChangeAdmission,
        IssueSourceChangeClient,
        IssueSourceChangeEffect,
        IssueSourceChangeReceipt,
        IssueSourceChangeRequest,
    )

from aware_protocol_fs_adapter.specification_setup import prepare_specification_setup
from aware_protocol_sdk import (
    PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF,
    ProtocolSpecificationSetupEffect,
    ProtocolSpecificationSetupError,
    ProtocolSpecificationSetupRequest,
    ProtocolSpecificationSetupResult,
)


def setup_command_payload(args: Namespace) -> tuple[dict[str, object], int]:
    """Project explicit command inputs; policy and mutation stay with owners."""
    try:
        request = ProtocolSpecificationSetupRequest(
            repository_root=args.repository_root,
            manifest_path=args.manifest_path,
            expected_manifest_sha256=args.expected_manifest_sha256,
            issue_ref=args.issue_ref,
            expected_issue_sha256=args.expected_issue_sha256,
            specification_root=args.specification_root,
            directory_paths=tuple(args.directory_path),
            client_intent_id=args.client_intent_id,
            dry_run=not args.apply,
        )
    except (TypeError, ValueError) as error:
        return {
            "status": "refused",
            "operation_ref": PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF,
            "code": "setup_request_invalid",
            "error_type": type(error).__name__,
            "effect": "none",
            "effects": [],
            "residual_scratch_paths": [],
        }, 2

    # Values and digest text are inputs, not transferable authorizations.
    from aware_protocol_sdk import ProtocolSpecificationSetupClient

    try:
        result = ProtocolSpecificationSetupClient(
            IssueGovernedSpecificationSetupProvider()
        ).setup_specification(request)
        return result.to_wire(), 0
    except ProtocolSpecificationSetupError as error:
        return {
            "status": "refused",
            "operation_ref": PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF,
            "code": error.code,
            "error_type": type(error).__name__,
            "effect": error.effect,
            "effects": [asdict(effect) for effect in error.effects],
            "residual_scratch_paths": list(error.residual_scratch_paths),
        }, 2
    except Exception as error:  # noqa: BLE001 -- invocation cannot prove no effects
        return {
            "status": "error",
            "operation_ref": PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF,
            "code": "setup_invocation_failed",
            "error_type": type(error).__name__,
            "effect": "unknown",
            "effects": [],
            "residual_scratch_paths": [],
        }, 1


def _effects(
    values: tuple[IssueSourceChangeEffect, ...],
) -> tuple[ProtocolSpecificationSetupEffect, ...]:
    return tuple(
        ProtocolSpecificationSetupEffect(
            e.path,
            e.kind,
            e.state,
            e.durability_confirmed,
            e.mode,
            e.before_digest,
            e.after_digest,
            e.after_identity,
        )
        for e in values
    )


class IssueGovernedSpecificationSetupProvider:
    def setup_specification(
        self, request: ProtocolSpecificationSetupRequest
    ) -> ProtocolSpecificationSetupResult:
        if type(request) is not ProtocolSpecificationSetupRequest:
            raise TypeError("Setup requires the exact neutral request")
        request = replace(request)
        candidate = prepare_specification_setup(request)
        try:
            issue_sdk = import_module("aware_issue_sdk")
            issue_fs = import_module("aware_issue_fs_adapter")
            request_type = cast(
                "type[IssueSourceChangeRequest]", issue_sdk.IssueSourceChangeRequest
            )
            receipt_type = cast(
                "type[IssueSourceChangeReceipt]", issue_sdk.IssueSourceChangeReceipt
            )
            client_type = cast(
                "type[IssueSourceChangeClient]", issue_sdk.IssueSourceChangeClient
            )
            provider_type = cast(
                "type[FilesystemIssueOperationProvider]",
                issue_fs.FilesystemIssueOperationProvider,
            )
        except (ImportError, AttributeError) as error:
            raise ProtocolSpecificationSetupError(
                "setup_issue_integration_unavailable"
            ) from error
        client = client_type(
            provider_type(
                repository_root=candidate.repository_root,
                protocol_source_ref=str(candidate.manifest_path),
            )
        )
        admission: IssueSourceChangeAdmission | None = None
        bound = False
        result = None
        failure = None
        cause = None
        try:
            admission = client.admit(
                request_type(
                    issue_ref=request.issue_ref,
                    expected_issue_sha256=request.expected_issue_sha256,
                    manifest_locator=str(candidate.manifest_path),
                    expected_manifest_sha256=request.expected_manifest_sha256,
                    candidate=candidate.postimage,
                    directory_paths=request.directory_paths,
                    client_intent_id=request.client_intent_id,
                )
            )
            client.validate(admission)
            bound = True
            paths = (*request.directory_paths, candidate.relative_manifest_path)
            if request.dry_run:
                result = ProtocolSpecificationSetupResult(
                    "planned",
                    request.expected_manifest_sha256,
                    candidate.postimage_sha256,
                    request.specification_root,
                    paths,
                )
            else:
                assert admission is not None
                for _ in request.directory_paths:
                    admission.prepare_next_directory()
                admission.replace_manifest()
                receipt = admission.finish()
                if type(receipt) is not receipt_type or (
                    receipt.issue_ref != request.issue_ref
                    or receipt.client_intent_id != request.client_intent_id
                    or receipt.issue_sha256 != request.expected_issue_sha256
                    or receipt.manifest_preimage_sha256
                    != request.expected_manifest_sha256
                    or receipt.manifest_postimage_sha256 != candidate.postimage_sha256
                    or receipt.ordered_effect_paths != paths
                    or receipt.confinement_profile != "descriptor_walk_v1"
                ):
                    raise ProtocolSpecificationSetupError(
                        "setup_issue_completion_invalid"
                    )
                result = ProtocolSpecificationSetupResult(
                    "completed",
                    receipt.manifest_preimage_sha256,
                    receipt.manifest_postimage_sha256,
                    request.specification_root,
                    paths,
                    _effects(receipt.effects),
                    receipt.execution_ref,
                    receipt.authority_grade,
                )
        except BaseException as error:  # noqa: BLE001 -- interruption must retain effects and retire
            values = getattr(error, "effects", ())
            if bound:
                try:
                    assert admission is not None
                    values = admission.effects
                except BaseException as evidence_error:  # noqa: BLE001 -- preserve primary refusal
                    values = getattr(evidence_error, "effects", values)
            failure = ProtocolSpecificationSetupError(
                getattr(error, "code", "setup_consumption_failed"),
                _effects(values),
                getattr(error, "residual_scratch_paths", ()),
            )
            cause = error
        finally:
            if bound:
                try:
                    assert admission is not None
                    admission.release()
                except BaseException as cleanup_error:  # noqa: BLE001 -- interrupted cleanup is a refusal
                    if failure is not None:
                        failure.add_note(
                            "setup_cleanup_failed:" + type(cleanup_error).__name__
                        )
                    else:
                        values = getattr(cleanup_error, "effects", ())
                        try:
                            assert admission is not None
                            values = admission.effects
                        except BaseException:  # noqa: BLE001 -- retain already transported evidence
                            if result is not None:
                                # Already transported genuine completion evidence.
                                values = ()
                        failure = ProtocolSpecificationSetupError(
                            "setup_cleanup_failed",
                            _effects(values)
                            if values
                            else (result.effects if result is not None else ()),
                            getattr(cleanup_error, "residual_scratch_paths", ()),
                        )
                        cause = cleanup_error
        if failure is not None:
            raise failure from cause
        assert result is not None
        return result
