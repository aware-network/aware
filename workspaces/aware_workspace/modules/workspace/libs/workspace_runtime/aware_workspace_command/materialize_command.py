"""Observable neutral `workspace materialize` command boundary."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Protocol

from aware_workspace_materialize_transport import (
    WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2,
    WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3,
    WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS,
    WorkspaceMaterializeCommandProposalV2,
    WorkspaceMaterializeCommandProposalV3,
    WorkspaceMaterializeCommandSelectorV2,
    WorkspaceMaterializeHostResultV2,
    WorkspaceMaterializeHostResultV4,
    WorkspaceMaterializeSelectedRootV1,
    empty_workspace_materialize_host_counters_v2,
)
from aware_workspace_materialize_transport.contracts import (
    WORKSPACE_MATERIALIZE_HOST_RESULT_V2,
    WORKSPACE_MATERIALIZE_HOST_RESULT_V3,
    WORKSPACE_MATERIALIZE_HOST_RESULT_V4,
    WorkspaceMaterializeHostOperationReceiptV1,
    WorkspaceMaterializeHostResultV3,
)

WORKSPACE_MATERIALIZE_COMMAND_RESULT = "aware.workspace.materialize-command-result.v2"
WORKSPACE_MATERIALIZE_COMMAND_RESULT_V3 = "aware.workspace.materialize-command-result.v3"
WORKSPACE_MATERIALIZE_COMMAND_RESULT_V4 = "aware.workspace.materialize-command-result.v4"
WORKSPACE_MATERIALIZE_COMMAND_NON_CLAIMS = WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS
_TIMING_PREFIX_ORDER = (
    "cli_startup",
    "command_discovery",
    "command_import_parser",
    "proposal_encode",
    "transport",
)
_MODULE_FAMILIES = (
    "aware_code_semantic_contract_runtime",
    "aware_meta",
    "aware_ontology",
    "aware_orm",
    "aware_workspace",
    "aware_workspace_command",
    "aware_workspace_materialize_transport",
    "aware_workspace_runtime",
    "pydantic",
    "sqlalchemy",
)


class WorkspaceMaterializeCommandError(RuntimeError):
    """The portable command proposal or result was invalid."""


def _decode_installed_workspace_json(wire: bytes, *, maximum_bytes: int) -> dict[str, Any]:
    """Bound the installed route before decoding; issue no command authority.

    The existing transport codecs still own canonical bytes, exact schemas and
    digests. This lexical pass only applies the narrower installed-profile
    byte/depth limits, including braces inside quoted and escaped strings.
    """
    if type(wire) is not bytes or not wire or len(wire) > maximum_bytes:
        raise WorkspaceMaterializeCommandError("installed wire size or type differs")
    stack: list[int] = []
    quoted = False
    escaped = False
    for byte in wire:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (123, 91):
            if len(stack) == 12:
                raise WorkspaceMaterializeCommandError("installed JSON depth exceeds twelve")
            stack.append(byte)
        elif byte in (125, 93) and (
            not stack or (stack.pop(), byte) not in ((123, 125), (91, 93))
        ):
            raise WorkspaceMaterializeCommandError("installed JSON delimiters differ")
    if quoted or stack:
        raise WorkspaceMaterializeCommandError("installed JSON is incomplete")
    try:
        value = json.loads(wire)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise WorkspaceMaterializeCommandError("installed wire is not JSON") from error
    if type(value) is not dict:
        raise WorkspaceMaterializeCommandError("installed wire must be a JSON object")
    return value


def _decode_installed_workspace_proposal_wire(
    proposal_wire: bytes,
) -> WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3:
    """Decode portable meaning only; never adopt a source inspection or launch."""
    value = _decode_installed_workspace_json(proposal_wire, maximum_bytes=65_536)
    if value.get("contract") == WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2:
        return WorkspaceMaterializeCommandProposalV2.from_wire(proposal_wire)
    if value.get("contract") == WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3:
        return WorkspaceMaterializeCommandProposalV3.from_wire(proposal_wire)
    raise WorkspaceMaterializeCommandError("installed proposal contract unsupported")


def _decode_installed_workspace_host_result(
    *, proposal_wire: bytes, result_wire: bytes,
) -> WorkspaceMaterializeHostResultV2 | WorkspaceMaterializeHostResultV3 | WorkspaceMaterializeHostResultV4:
    """Check portable correspondence, without certifying delivery or cleanup.

    Callers must separately prove the original parent, both EOFs and settlement.
    The public transport does not call this dormant helper yet. A returned DTO
    cannot enroll a command or open an installed execution inlet.
    """
    proposal = _decode_installed_workspace_proposal_wire(proposal_wire)
    value = _decode_installed_workspace_json(result_wire, maximum_bytes=131_072)
    predecessor = value
    for field in (
        "predecessor_wire_text", "operation_receipt_wire_text", "selected_root_wire_text",
    ):
        if field not in value:
            continue
        text = value[field]
        if type(text) is not str:
            raise WorkspaceMaterializeCommandError("installed nested wire must be text")
        try:
            nested = _decode_installed_workspace_json(text.encode(), maximum_bytes=131_072)
        except UnicodeEncodeError as error:
            raise WorkspaceMaterializeCommandError("installed nested wire is not UTF-8") from error
        if field == "predecessor_wire_text":
            predecessor = nested
    for field in ("plan_result_wire_text", "graph_result_wire_text"):
        text = predecessor.get(field)
        if text is not None:
            if type(text) is not str:
                raise WorkspaceMaterializeCommandError("installed graph wire must be text")
            try:
                _decode_installed_workspace_json(text.encode(), maximum_bytes=131_072)
            except UnicodeEncodeError as error:
                raise WorkspaceMaterializeCommandError("installed graph wire is not UTF-8") from error
    contract = value.get("contract")
    if contract == WORKSPACE_MATERIALIZE_HOST_RESULT_V2:
        return WorkspaceMaterializeHostResultV2.from_wire(result_wire, proposal=proposal)
    if contract == WORKSPACE_MATERIALIZE_HOST_RESULT_V3:
        return WorkspaceMaterializeHostResultV3.from_wire(result_wire, proposal=proposal)
    if contract == WORKSPACE_MATERIALIZE_HOST_RESULT_V4:
        if type(proposal) is not WorkspaceMaterializeCommandProposalV3:
            raise WorkspaceMaterializeCommandError("installed exact-address result requires V3 proposal")
        return WorkspaceMaterializeHostResultV4.from_wire(result_wire, proposal=proposal)
    raise WorkspaceMaterializeCommandError("installed host result contract unsupported")


class WorkspaceMaterializeCommandTransport(Protocol):
    def invoke(
        self, proposal_wire: bytes
    ) -> WorkspaceMaterializeHostResultV2 | WorkspaceMaterializeHostResultV3 | WorkspaceMaterializeHostResultV4: ...


class _DirectWorkspaceCommandTransport:
    """Process-local adapter to Workspace's original command source admission."""

    admission_diagnostic: str | None = None

    def invoke(
        self, proposal_wire: bytes
    ) -> WorkspaceMaterializeHostResultV2 | WorkspaceMaterializeHostResultV3 | WorkspaceMaterializeHostResultV4:
        import asyncio

        from aware_workspace_runtime.direct_command_composition import (
            WorkspaceDirectCommandRootUnavailable,
            admit_direct_workspace_cli_source,
        )
        from aware_workspace_runtime.lease import (
            WorkspaceObservationLeaseUnavailable,
        )
        from aware_workspace_runtime.source_observation_io import (
            SourceObservationUnavailable,
        )

        self.admission_diagnostic = None
        decode_started = time.perf_counter_ns()
        proposed = json.loads(proposal_wire)
        proposal = (
            WorkspaceMaterializeCommandProposalV3.from_wire(proposal_wire)
            if type(proposed) is dict and proposed.get("contract") == WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3
            else WorkspaceMaterializeCommandProposalV2.from_wire(proposal_wire)
        )
        request_decode_ns = time.perf_counter_ns() - decode_started
        admission_started = time.perf_counter_ns()
        failure_code = "caller_not_admitted"
        inspection = None
        root_text = proposal.participant_checkout_root
        if root_text is not None:
            try:
                inspection = asyncio.run(admit_direct_workspace_cli_source(proposal=proposal))
            except SourceObservationUnavailable:
                failure_code = "workspace_manifest_not_admitted"
            except WorkspaceObservationLeaseUnavailable as error:
                # The original observer remains owner of this checkout. Report
                # the existing overlap refusal without issuing a receipt or
                # authorizing another writer.
                failure_code = "participant_checkout_overlap"
                self.admission_diagnostic = str(error)
            except WorkspaceDirectCommandRootUnavailable as error:
                failure_code = "caller_not_admitted"
                self.admission_diagnostic = str(error)
            else:
                if (
                    inspection.attempt_ref != proposal.attempt_ref
                    or inspection.proposal_digest != proposal.proposal_digest
                ):
                    raise WorkspaceMaterializeCommandError(
                        "direct host admission correspondence differs"
                    )
                # The original Workspace command is live and its retained
                # declarations were revalidated. No provider/catalog/graph
                # admission is inferred from this source-only checkpoint.
                failure_code = "graph_host_not_ready"
        counters = dict(empty_workspace_materialize_host_counters_v2(proposal))
        counters["authority_preflight_count"] = 1
        admission_ns = time.perf_counter_ns() - admission_started
        selection = None if inspection is None else inspection.selected_root
        if selection is not None and type(proposal) is not WorkspaceMaterializeCommandProposalV3:
            raise WorkspaceMaterializeCommandError("unexpected exact-address selection")
        if selection is None and inspection is not None and type(proposal) is WorkspaceMaterializeCommandProposalV3:
            raise WorkspaceMaterializeCommandError("exact-address selection missing")
        if selection is not None:
            counters["selected_package_count"] = 1
        predecessor = WorkspaceMaterializeHostResultV2.create(
            proposal=proposal,
            outcome="blocked",
            terminal_stage="selection" if selection is not None else "host_admission",
            host_timing_ns=(
                ("request_decode", request_decode_ns),
                ("host_admission", max(0, admission_ns - inspection.selected_timing_ns)),
                ("catalog_observation", 0),
                ("selection", inspection.selected_timing_ns),
            ) if selection is not None else (
                ("request_decode", request_decode_ns),
                ("host_admission", admission_ns),
            ),
            host_total_ns=request_decode_ns + admission_ns,
            host_counters=tuple(counters.items()),
            plan_result_wire=None,
            graph_result_wire=None,
            failure_kind="authority",
            failure_code=failure_code,
        )
        if inspection is None:
            return predecessor
        if type(inspection.operation_receipt) is not WorkspaceMaterializeHostOperationReceiptV1:
            raise WorkspaceMaterializeCommandError("original host operation receipt required")
        if selection is not None:
            return WorkspaceMaterializeHostResultV4.create(
                predecessor=predecessor,
                operation_receipt=inspection.operation_receipt,
                selected_root=selection,
            )
        return WorkspaceMaterializeHostResultV3.create(
            predecessor=predecessor,
            operation_receipt=inspection.operation_receipt,
        )


@dataclass(frozen=True, slots=True)
class _CommandOutcome:
    outcome: str
    terminal_stage: str
    operation_payload: dict[str, object] | None = None
    failure_code: str | None = None
    host_timing_ns: tuple[tuple[str, int], ...] = ()
    host_total_ns: int | None = None
    host_counters: tuple[tuple[str, int], ...] = ()

    def __post_init__(self) -> None:
        if self.outcome not in {"succeeded", "blocked", "failed"}:
            raise WorkspaceMaterializeCommandError("transport outcome unsupported")
        _text(self.terminal_stage, "terminal_stage")
        if self.outcome == "succeeded":
            if (
                type(self.operation_payload) is not dict
                or self.failure_code is not None
            ):
                raise WorkspaceMaterializeCommandError(
                    "successful transport response shape differs"
                )
        else:
            if self.failure_code is None:
                raise WorkspaceMaterializeCommandError(
                    "unsuccessful transport response shape differs"
                )
            if self.operation_payload is not None:
                if type(self.operation_payload) is not dict:
                    raise WorkspaceMaterializeCommandError("blocked operation evidence must be an object")
                valid_source = (
                    self.terminal_stage == "host_admission"
                    and set(self.operation_payload) == {"host_receipt"}
                )
                valid_selection = (
                    self.terminal_stage == "selection"
                    and set(self.operation_payload) == {"host_receipt", "selected_root"}
                )
                if (
                    self.outcome != "blocked"
                    or self.failure_code != "graph_host_not_ready"
                    or not (valid_source or valid_selection)
                ):
                    raise WorkspaceMaterializeCommandError(
                        "blocked operation receipt shape differs"
                    )
                WorkspaceMaterializeHostOperationReceiptV1.from_value(
                    self.operation_payload["host_receipt"]
                )
                if valid_selection:
                    WorkspaceMaterializeSelectedRootV1.from_value(
                        self.operation_payload["selected_root"]
                    )
        if self.failure_code is not None:
            _text(self.failure_code, "failure_code")
        if self.host_total_ns is None:
            if self.host_timing_ns or self.host_counters:
                raise WorkspaceMaterializeCommandError(
                    "host metrics require a host total"
                )
        else:
            if type(self.host_total_ns) is not int or self.host_total_ns < 0:
                raise TypeError("host_total_ns must be nonnegative exact integer")
            for metrics in (self.host_timing_ns, self.host_counters):
                if type(metrics) is not tuple or any(
                    type(item) is not tuple
                    or len(item) != 2
                    or type(item[0]) is not str
                    or type(item[1]) is not int
                    or item[1] < 0
                    for item in metrics
                ):
                    raise TypeError("host metrics must be exact nonnegative pairs")


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeCommandResult:
    attempt_ref: str
    outcome: str
    terminal_stage: str
    timing_ns: tuple[tuple[str, int], ...]
    imported_module_family_counts: tuple[tuple[str, int], ...]
    operation_payload: dict[str, object] | None
    failure_code: str | None
    host_timing_ns: tuple[tuple[str, int], ...] = ()
    host_total_ns: int | None = None
    host_counters: tuple[tuple[str, int], ...] = ()
    contract: str = WORKSPACE_MATERIALIZE_COMMAND_RESULT
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZE_COMMAND_NON_CLAIMS

    def __post_init__(self) -> None:
        expected_contract = (
            WORKSPACE_MATERIALIZE_COMMAND_RESULT_V4
            if self.outcome == "blocked" and self.operation_payload is not None
            and "selected_root" in self.operation_payload
            else WORKSPACE_MATERIALIZE_COMMAND_RESULT_V3
            if self.outcome == "blocked" and self.operation_payload is not None
            else WORKSPACE_MATERIALIZE_COMMAND_RESULT
        )
        if self.contract != expected_contract:
            raise WorkspaceMaterializeCommandError("result contract differs")
        if tuple(self.non_claims) != WORKSPACE_MATERIALIZE_COMMAND_NON_CLAIMS:
            raise WorkspaceMaterializeCommandError("result non-claims differ")
        _text(self.attempt_ref, "attempt_ref")
        if self.outcome not in {"succeeded", "blocked", "failed"}:
            raise WorkspaceMaterializeCommandError("command outcome unsupported")
        _text(self.terminal_stage, "terminal_stage")
        if type(self.timing_ns) is not tuple or not self.timing_ns:
            raise TypeError("timing_ns must be a nonempty exact tuple")
        names: list[str] = []
        for item in self.timing_ns:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not int
                or item[1] < 0
            ):
                raise TypeError("timing entry must be exact and nonnegative")
            names.append(item[0])
        suffix_length = 2 if names[-2:] == ["output_encode", "total"] else 0
        prefix_names = tuple(names[:-suffix_length] if suffix_length else names)
        if prefix_names != _TIMING_PREFIX_ORDER[: len(prefix_names)] or len(
            prefix_names
        ) > len(_TIMING_PREFIX_ORDER):
            raise WorkspaceMaterializeCommandError(
                "command timings are not an exact stage prefix"
            )
        if (
            type(self.imported_module_family_counts) is not tuple
            or tuple(name for name, _ in self.imported_module_family_counts)
            != _MODULE_FAMILIES
            or any(
                type(value) is not int or value < 0
                for _, value in self.imported_module_family_counts
            )
        ):
            raise WorkspaceMaterializeCommandError(
                "imported module family counts differ"
            )
        _CommandOutcome(
            outcome=self.outcome,
            terminal_stage=self.terminal_stage,
            operation_payload=self.operation_payload,
            failure_code=self.failure_code,
            host_timing_ns=self.host_timing_ns,
            host_total_ns=self.host_total_ns,
            host_counters=self.host_counters,
        )

    def payload(self) -> dict[str, object]:
        self.__post_init__()
        return {
            "attempt_ref": self.attempt_ref,
            "contract": self.contract,
            "failure_code": self.failure_code,
            "host_counters": [
                {"counter": name, "value": value} for name, value in self.host_counters
            ],
            "host_timing_ns": [
                {"elapsed_ns": value, "stage": name}
                for name, value in self.host_timing_ns
            ],
            "host_total_ns": self.host_total_ns,
            "imported_module_family_counts": {
                name: value for name, value in self.imported_module_family_counts
            },
            "non_claims": list(self.non_claims),
            "operation": self.operation_payload,
            "outcome": self.outcome,
            "terminal_stage": self.terminal_stage,
            "timing_ns": [
                {"elapsed_ns": value, "stage": name} for name, value in self.timing_ns
            ],
        }


def register_workspace_materialize_parser(
    workspace_subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    parser = workspace_subparsers.add_parser(
        "materialize",
        help="Run the neutral Workspace semantic materialization operation.",
        description=(
            "Submit one portable Workspace materialization proposal to the "
            "admitted Workspace authority. This command does not import a "
            "provider, ORM, generated API, Ontology, Meta or OIG runtime."
        ),
    )
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--workspace-toml", default="aware.workspace.toml")
    parser.add_argument("--package", action="append", default=[])
    parser.add_argument(
        "--package-address", default=None,
        metavar="WORKSPACE:MODULE:PACKAGE",
        help="Select one exact declared package occurrence within the named Workspace.",
    )
    parser.add_argument("--module", action="append", default=[])
    parser.add_argument("--workspace", action="append", default=[])
    parser.add_argument("--repository", action="append", default=[])
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def handle_workspace_materialize_command(
    *,
    args: argparse.Namespace,
    context: Any = None,
    transport: WorkspaceMaterializeCommandTransport | None = None,
) -> int:
    module_started_ns = int(
        getattr(args, "_aware_cli_module_started_ns", time.perf_counter_ns())
    )
    now = time.perf_counter_ns()
    timings: list[tuple[str, int]] = [
        ("cli_startup", max(0, now - module_started_ns)),
        ("command_discovery", _metric(args, "_aware_cli_command_discovery_ns")),
        (
            "command_import_parser",
            _metric(args, "_aware_cli_command_import_parser_ns"),
        ),
    ]
    from uuid import uuid4

    attempt_ref = f"workspace-materialize-attempt:{uuid4()}"
    proposal_started = time.perf_counter_ns()
    try:
        workspace_root = getattr(args, "repo_root", None) or getattr(
            args, "workspace_root", None
        )
        address_text = getattr(args, "package_address", None)
        selected = tuple(
            WorkspaceMaterializeCommandSelectorV2.create(
                selector_kind=kind,
                selector_ref=str(value),
            )
            for kind in ("package", "module", "workspace", "repository")
            for value in (getattr(args, kind, ()) or ())
        )
        if address_text is not None:
            if selected or type(address_text) is not str:
                raise WorkspaceMaterializeCommandError(
                    "exact package address cannot be combined with broad selectors"
                )
            address = tuple(address_text.split(":"))
            proposal = WorkspaceMaterializeCommandProposalV3.create(
                attempt_ref=attempt_ref,
                participant_checkout_root=(str(workspace_root) if workspace_root else None),
                workspace_manifest_name=str(getattr(args, "workspace_toml", "") or ""),
                package_address=address,
                plan_only=bool(getattr(args, "plan", False)),
            )
        else:
            selectors = tuple(sorted(
                selected,
                key=lambda item: json.dumps(
                    item.to_wire(), ensure_ascii=False,
                    separators=(",", ":"), sort_keys=True,
                ).encode(),
            ))
            proposal = WorkspaceMaterializeCommandProposalV2.create(
                attempt_ref=attempt_ref,
                participant_checkout_root=(str(workspace_root) if workspace_root else None),
                workspace_manifest_name=str(getattr(args, "workspace_toml", "") or ""),
                selectors=selectors,
                plan_only=bool(getattr(args, "plan", False)),
            )
        proposal_wire = proposal.to_wire()
    except Exception as error:  # noqa: BLE001 - total command proposal boundary
        timings.append(("proposal_encode", time.perf_counter_ns() - proposal_started))
        return _emit_result(
            args=args,
            attempt_ref=attempt_ref,
            response=_CommandOutcome(
                outcome="failed",
                terminal_stage="proposal_encode",
                failure_code="proposal_invalid",
            ),
            timings=timings,
            diagnostic=str(error),
            module_started_ns=module_started_ns,
        )
    timings.append(("proposal_encode", time.perf_counter_ns() - proposal_started))

    transport_started = time.perf_counter_ns()
    try:
        if transport is None:
            direct_transport = _DirectWorkspaceCommandTransport()
            selected_transport = direct_transport
        else:
            direct_transport = None
            selected_transport = transport
        host_result = selected_transport.invoke(proposal_wire)
        host_receipt = None
        selected_root = None
        if type(host_result) is WorkspaceMaterializeHostResultV4:
            if transport is not None or type(proposal) is not WorkspaceMaterializeCommandProposalV3:
                raise WorkspaceMaterializeCommandError(
                    "caller transport cannot issue exact-address evidence"
                )
            host_result.__post_init__()
            selected_root = host_result.selected_root
            if (
                selected_root.workspace_handle != proposal.package_address[0]
                or selected_root.module_id != proposal.package_address[1]
                or selected_root.package_id != proposal.package_address[2]
                or selected_root.workspace_manifest_path != proposal.workspace_manifest_name
            ):
                raise WorkspaceMaterializeCommandError("exact-address result differs")
            host_receipt = host_result.operation_receipt
            host_result = host_result.predecessor
        elif type(host_result) is WorkspaceMaterializeHostResultV3:
            if transport is not None:
                raise WorkspaceMaterializeCommandError(
                    "caller transport cannot issue direct-host operation evidence"
                )
            host_result.__post_init__()
            host_receipt = host_result.operation_receipt
            host_result = host_result.predecessor
        if type(host_result) is not WorkspaceMaterializeHostResultV2:
            raise TypeError("transport returned a foreign response")
        host_result.__post_init__()
        if (
            host_result.attempt_ref != proposal.attempt_ref
            or host_result.proposal_digest != proposal.proposal_digest
        ):
            raise WorkspaceMaterializeCommandError(
                "transport result correlation differs"
            )
        plan_wire = host_result.plan_result_wire()
        graph_wire = host_result.graph_result_wire()
        if host_receipt is not None:
            operation_payload: dict[str, object] | None = {
                "host_receipt": host_receipt.to_value()
            }
            if selected_root is not None:
                operation_payload["selected_root"] = selected_root.to_value()
        elif plan_wire is None and graph_wire is None:
            operation_payload = None
        else:
            operation_payload = {
                "plan_result": None if plan_wire is None else json.loads(plan_wire),
                "plan_result_wire_digest": host_result.plan_result_wire_digest,
                "graph_result": None if graph_wire is None else json.loads(graph_wire),
                "graph_result_wire_digest": host_result.graph_result_wire_digest,
            }
        response = _CommandOutcome(
            outcome=host_result.outcome,
            terminal_stage=host_result.terminal_stage,
            operation_payload=operation_payload,
            failure_code=host_result.failure_code,
            host_timing_ns=host_result.host_timing_ns,
            host_total_ns=host_result.host_total_ns,
            host_counters=host_result.host_counters,
        )
        diagnostic = (
            direct_transport.admission_diagnostic
            if direct_transport is not None else None
        )
    except Exception as error:  # noqa: BLE001 - total transport boundary
        response = _CommandOutcome(
            outcome="failed",
            terminal_stage="transport",
            failure_code="transport_failed",
        )
        diagnostic = str(error)
    timings.append(("transport", time.perf_counter_ns() - transport_started))
    return _emit_result(
        args=args,
        attempt_ref=attempt_ref,
        response=response,
        timings=timings,
        diagnostic=diagnostic,
        module_started_ns=module_started_ns,
    )


def _emit_result(
    *,
    args: argparse.Namespace,
    attempt_ref: str,
    response: _CommandOutcome,
    timings: list[tuple[str, int]],
    diagnostic: str | None,
    module_started_ns: int,
) -> int:
    output_started = time.perf_counter_ns()
    result_contract = (
        WORKSPACE_MATERIALIZE_COMMAND_RESULT_V4
        if response.outcome == "blocked" and response.operation_payload is not None
        and "selected_root" in response.operation_payload
        else WORKSPACE_MATERIALIZE_COMMAND_RESULT_V3
        if response.outcome == "blocked" and response.operation_payload is not None
        else WORKSPACE_MATERIALIZE_COMMAND_RESULT
    )
    provisional = WorkspaceMaterializeCommandResult(
        attempt_ref=attempt_ref,
        outcome=response.outcome,
        terminal_stage=response.terminal_stage,
        timing_ns=tuple(timings),
        imported_module_family_counts=_module_family_counts(),
        operation_payload=response.operation_payload,
        failure_code=response.failure_code,
        host_timing_ns=response.host_timing_ns,
        host_total_ns=response.host_total_ns,
        host_counters=response.host_counters,
        contract=result_contract,
    )
    _canonical_json_bytes(provisional.payload())
    timings.append(("output_encode", time.perf_counter_ns() - output_started))
    timings.append(("total", time.perf_counter_ns() - module_started_ns))
    result = WorkspaceMaterializeCommandResult(
        attempt_ref=attempt_ref,
        outcome=response.outcome,
        terminal_stage=response.terminal_stage,
        timing_ns=tuple(timings),
        imported_module_family_counts=_module_family_counts(),
        operation_payload=response.operation_payload,
        failure_code=response.failure_code,
        host_timing_ns=response.host_timing_ns,
        host_total_ns=response.host_total_ns,
        host_counters=response.host_counters,
        contract=result_contract,
    )
    if bool(getattr(args, "json", False)):
        print(json.dumps(result.payload(), sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"Workspace materialize {result.outcome} "
            f"(stage={result.terminal_stage}, attempt={result.attempt_ref})"
        )
        if diagnostic:
            print(diagnostic, file=sys.stderr)
    return 0 if result.outcome == "succeeded" else 2


def _metric(args: argparse.Namespace, name: str) -> int:
    value = getattr(args, name, 0)
    if type(value) is not int or value < 0:
        raise WorkspaceMaterializeCommandError(f"{name} metric is invalid")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _module_family_counts() -> tuple[tuple[str, int], ...]:
    loaded = tuple(sys.modules)
    return tuple(
        (
            root,
            sum(
                1
                for module_name in loaded
                if module_name == root or module_name.startswith(root + ".")
            ),
        )
        for root in _MODULE_FAMILIES
    )


def _text(value: object, field: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise WorkspaceMaterializeCommandError(f"{field} must be nonempty text")
    return value


__all__ = [
    "WORKSPACE_MATERIALIZE_COMMAND_NON_CLAIMS",
    "WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2",
    "WORKSPACE_MATERIALIZE_COMMAND_RESULT",
    "WorkspaceMaterializeCommandError",
    "WorkspaceMaterializeCommandProposalV2",
    "WorkspaceMaterializeCommandResult",
    "WorkspaceMaterializeCommandTransport",
    "handle_workspace_materialize_command",
    "register_workspace_materialize_parser",
]
