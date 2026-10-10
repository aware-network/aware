"""Strict portable V2 command/host values for Workspace materialization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import cast
from uuid import UUID

WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2 = "aware.workspace.materialize-command-proposal.v2"
WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3 = "aware.workspace.materialize-command-proposal.v3"
WORKSPACE_MATERIALIZE_HOST_RESULT_V2 = "aware.workspace.materialize-host-result.v2"
WORKSPACE_MATERIALIZE_HOST_RESULT_V3 = "aware.workspace.materialize-host-result.v3"
WORKSPACE_MATERIALIZE_HOST_RESULT_V4 = "aware.workspace.materialize-host-result.v4"
WORKSPACE_MATERIALIZE_SELECTED_ROOT_V1 = "aware.workspace.materialize-selected-root.v1"
WORKSPACE_MATERIALIZE_HOST_OPERATION_RECEIPT_V1 = (
    "aware.workspace.materialize-host-operation-receipt.v1"
)
WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS = (
    "canonical_replica", "checkout_apply", "oig_commit", "workspace_revision",
)
WORKSPACE_MATERIALIZE_SELECTOR_KINDS_V2 = (
    "module", "package", "repository", "workspace",
)
WORKSPACE_MATERIALIZE_HOST_STAGE_ORDER_V2 = (
    "request_decode", "host_admission", "catalog_observation", "selection",
    "graph_plan", "graph_admission", "graph_execution",
)
WORKSPACE_MATERIALIZE_HOST_COUNTER_ORDER_V2 = (
    "authority_preflight_count", "catalog_observation_count", "selector_count",
    "selected_package_count", "graph_node_count", "graph_edge_count",
    "graph_admission_count", "graph_execution_count",
)
WORKSPACE_MATERIALIZE_FAILURE_CODES_V2 = {
    "authority": frozenset({
        "caller_not_admitted", "generation_not_live", "graph_host_not_ready",
        "participant_checkout_overlap", "workspace_manifest_not_admitted",
    }),
    "catalog": frozenset({
        "catalog_contribution_mismatch", "catalog_moved", "catalog_not_live",
    }),
    "selection": frozenset({
        "participation_denied", "selection_ambiguous", "selector_not_admitted",
    }),
    "planning": frozenset({
        "planning_context_moved", "planning_cycle", "planning_unsatisfied",
    }),
    "graph_execution": frozenset(),
    "internal": frozenset({"host_invariant_failed"}),
}
_DIGEST_PREFIX = "sha256:"
_MAX_WIRE_BYTES = 16_000_000


class WorkspaceMaterializeTransportContractError(ValueError):
    """A portable materialization transport value is malformed."""


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeCommandSelectorV2:
    selector_kind: str
    selector_ref: str

    @classmethod
    def create(cls, *, selector_kind: str, selector_ref: str) -> WorkspaceMaterializeCommandSelectorV2:
        return cls(selector_kind=selector_kind, selector_ref=selector_ref)

    def __post_init__(self) -> None:
        if self.selector_kind not in WORKSPACE_MATERIALIZE_SELECTOR_KINDS_V2:
            raise WorkspaceMaterializeTransportContractError("selector kind unsupported")
        _text(self.selector_ref, "selector_ref")

    def to_wire(self) -> dict[str, str]:
        self.__post_init__()
        return {"selector_kind": self.selector_kind, "selector_ref": self.selector_ref}

    @classmethod
    def from_value(cls, value: object) -> WorkspaceMaterializeCommandSelectorV2:
        if type(value) is not dict or set(value) != {"selector_kind", "selector_ref"}:
            raise WorkspaceMaterializeTransportContractError("selector fields differ")
        root = cast(dict[str, object], value)
        return cls(
            selector_kind=_text(root["selector_kind"], "selector_kind"),
            selector_ref=_text(root["selector_ref"], "selector_ref"),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeCommandProposalV2:
    attempt_ref: str
    participant_checkout_root: str | None
    workspace_manifest_name: str
    selectors: tuple[WorkspaceMaterializeCommandSelectorV2, ...]
    plan_only: bool
    proposal_digest: str
    contract: str = WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS

    @classmethod
    def create(
        cls, *, attempt_ref: str, participant_checkout_root: str | None,
        workspace_manifest_name: str,
        selectors: tuple[WorkspaceMaterializeCommandSelectorV2, ...], plan_only: bool,
    ) -> WorkspaceMaterializeCommandProposalV2:
        _preflight_selectors(selectors)
        payload = _proposal_payload(
            attempt_ref, participant_checkout_root, workspace_manifest_name,
            selectors, plan_only,
        )
        return cls(
            attempt_ref=attempt_ref,
            participant_checkout_root=participant_checkout_root,
            workspace_manifest_name=workspace_manifest_name,
            selectors=selectors,
            plan_only=plan_only,
            proposal_digest=_semantic_digest(WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2, payload),
        )

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2:
            raise WorkspaceMaterializeTransportContractError("proposal contract differs")
        if type(self.non_claims) is not tuple or self.non_claims != WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS:
            raise WorkspaceMaterializeTransportContractError("proposal non-claims differ")
        payload = _proposal_payload(
            self.attempt_ref, self.participant_checkout_root,
            self.workspace_manifest_name, self.selectors, self.plan_only,
        )
        if self.proposal_digest != _semantic_digest(self.contract, payload):
            raise WorkspaceMaterializeTransportContractError("proposal digest mismatched")

    def _payload(self) -> dict[str, object]:
        return _proposal_payload(
            self.attempt_ref, self.participant_checkout_root,
            self.workspace_manifest_name, self.selectors, self.plan_only,
        )

    def to_wire(self) -> bytes:
        self.__post_init__()
        return _canonical_json_bytes({
            "contract": self.contract, **self._payload(),
            "proposal_digest": self.proposal_digest, "non_claims": list(self.non_claims),
        })

    @classmethod
    def from_wire(cls, wire: bytes) -> WorkspaceMaterializeCommandProposalV2:
        root = _decode_exact_object(wire, {
            "attempt_ref", "contract", "non_claims", "participant_checkout_root",
            "plan_only", "proposal_digest", "selectors", "workspace_manifest_name",
        })
        result = cls(
            attempt_ref=_text(root["attempt_ref"], "attempt_ref"),
            participant_checkout_root=_optional_text(root["participant_checkout_root"], "participant_checkout_root"),
            workspace_manifest_name=_text(root["workspace_manifest_name"], "workspace_manifest_name"),
            selectors=tuple(WorkspaceMaterializeCommandSelectorV2.from_value(item) for item in _list(root["selectors"])),
            plan_only=_boolean(root["plan_only"], "plan_only"),
            proposal_digest=_digest(root["proposal_digest"], "proposal_digest"),
            contract=_text(root["contract"], "contract"),
            non_claims=tuple(_text(item, "non_claim") for item in _list(root["non_claims"])),
        )
        if result.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("proposal wire is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeCommandProposalV3:
    """One exact occurrence address; unrelated modules are not selectors."""

    attempt_ref: str
    participant_checkout_root: str | None
    workspace_manifest_name: str
    package_address: tuple[str, str, str]
    plan_only: bool
    proposal_digest: str
    contract: str = WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS

    @classmethod
    def create(
        cls, *, attempt_ref: str, participant_checkout_root: str | None,
        workspace_manifest_name: str, package_address: tuple[str, str, str],
        plan_only: bool,
    ) -> WorkspaceMaterializeCommandProposalV3:
        payload = _proposal_v3_payload(
            attempt_ref, participant_checkout_root, workspace_manifest_name,
            package_address, plan_only,
        )
        result = cls(
            attempt_ref, participant_checkout_root, workspace_manifest_name,
            package_address, plan_only,
            _semantic_digest(WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3, payload),
        )
        result.__post_init__()
        return result

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V3:
            raise WorkspaceMaterializeTransportContractError("exact-address proposal contract differs")
        if type(self.non_claims) is not tuple or self.non_claims != WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS:
            raise WorkspaceMaterializeTransportContractError("exact-address proposal non-claims differ")
        payload = _proposal_v3_payload(
            self.attempt_ref, self.participant_checkout_root,
            self.workspace_manifest_name, self.package_address, self.plan_only,
        )
        if self.proposal_digest != _semantic_digest(self.contract, payload):
            raise WorkspaceMaterializeTransportContractError("exact-address proposal digest differs")

    def to_wire(self) -> bytes:
        self.__post_init__()
        return _canonical_json_bytes({
            "contract": self.contract,
            **_proposal_v3_payload(
                self.attempt_ref, self.participant_checkout_root,
                self.workspace_manifest_name, self.package_address, self.plan_only,
            ),
            "proposal_digest": self.proposal_digest,
            "non_claims": list(self.non_claims),
        })

    @classmethod
    def from_wire(cls, wire: bytes) -> WorkspaceMaterializeCommandProposalV3:
        root = _decode_exact_object(wire, {
            "attempt_ref", "contract", "non_claims", "participant_checkout_root",
            "plan_only", "proposal_digest", "package_address", "workspace_manifest_name",
        })
        address = _list(root["package_address"])
        if len(address) != 3:
            raise WorkspaceMaterializeTransportContractError("exact package address requires three fields")
        result = cls(
            attempt_ref=_text(root["attempt_ref"], "attempt_ref"),
            participant_checkout_root=_optional_text(root["participant_checkout_root"], "participant_checkout_root"),
            workspace_manifest_name=_text(root["workspace_manifest_name"], "workspace_manifest_name"),
            package_address=tuple(_address_component(item) for item in address),
            plan_only=_boolean(root["plan_only"], "plan_only"),
            proposal_digest=_digest(root["proposal_digest"], "proposal_digest"),
            contract=_text(root["contract"], "contract"),
            non_claims=tuple(_text(item, "non_claim") for item in _list(root["non_claims"])),
        )
        if result.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("exact-address proposal wire is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeHostResultV2:
    attempt_ref: str
    proposal_digest: str
    outcome: str
    terminal_stage: str
    host_timing_ns: tuple[tuple[str, int], ...]
    host_total_ns: int
    host_counters: tuple[tuple[str, int], ...]
    plan_result_wire_text: str | None
    plan_result_wire_digest: str | None
    graph_result_wire_text: str | None
    graph_result_wire_digest: str | None
    failure_kind: str | None
    failure_code: str | None
    response_digest: str
    contract: str = WORKSPACE_MATERIALIZE_HOST_RESULT_V2
    non_claims: tuple[str, ...] = WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS

    @classmethod
    def create(
        cls, *, proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3, outcome: str,
        terminal_stage: str, host_timing_ns: tuple[tuple[str, int], ...],
        host_total_ns: int, host_counters: tuple[tuple[str, int], ...],
        plan_result_wire: bytes | None, graph_result_wire: bytes | None,
        failure_kind: str | None, failure_code: str | None,
    ) -> WorkspaceMaterializeHostResultV2:
        if type(proposal) not in (WorkspaceMaterializeCommandProposalV2, WorkspaceMaterializeCommandProposalV3):
            raise TypeError("original V2 or V3 proposal required")
        proposal.__post_init__()
        plan_text, plan_digest = _retain_nested_wire(plan_result_wire, "plan_result")
        graph_text, graph_digest = _retain_nested_wire(graph_result_wire, "graph_result")
        payload = _host_result_payload(
            proposal.attempt_ref, proposal.proposal_digest, outcome, terminal_stage,
            host_timing_ns, host_total_ns, host_counters, plan_text, plan_digest,
            graph_text, graph_digest, failure_kind, failure_code,
        )
        return cls(
            attempt_ref=proposal.attempt_ref, proposal_digest=proposal.proposal_digest,
            outcome=outcome, terminal_stage=terminal_stage,
            host_timing_ns=host_timing_ns, host_total_ns=host_total_ns,
            host_counters=host_counters, plan_result_wire_text=plan_text,
            plan_result_wire_digest=plan_digest, graph_result_wire_text=graph_text,
            graph_result_wire_digest=graph_digest, failure_kind=failure_kind,
            failure_code=failure_code,
            response_digest=_semantic_digest(WORKSPACE_MATERIALIZE_HOST_RESULT_V2, payload),
        )

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_HOST_RESULT_V2:
            raise WorkspaceMaterializeTransportContractError("host result contract differs")
        if type(self.non_claims) is not tuple or self.non_claims != WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS:
            raise WorkspaceMaterializeTransportContractError("host result non-claims differ")
        _text(self.attempt_ref, "attempt_ref")
        _digest(self.proposal_digest, "proposal_digest")
        if self.outcome not in {"succeeded", "blocked", "failed"}:
            raise WorkspaceMaterializeTransportContractError("host result outcome unsupported")
        if self.terminal_stage not in WORKSPACE_MATERIALIZE_HOST_STAGE_ORDER_V2:
            raise WorkspaceMaterializeTransportContractError("host result terminal stage unsupported")
        timing_names = _metric_tuple(self.host_timing_ns, "host_timing_ns")
        terminal_index = WORKSPACE_MATERIALIZE_HOST_STAGE_ORDER_V2.index(self.terminal_stage)
        if timing_names != WORKSPACE_MATERIALIZE_HOST_STAGE_ORDER_V2[: terminal_index + 1]:
            raise WorkspaceMaterializeTransportContractError("host timings are not the exact terminal-stage prefix")
        _nonnegative_integer(self.host_total_ns, "host_total_ns")
        if self.host_total_ns < sum(value for _, value in self.host_timing_ns):
            raise WorkspaceMaterializeTransportContractError("host total is shorter than stage timings")
        if _metric_tuple(self.host_counters, "host_counters") != WORKSPACE_MATERIALIZE_HOST_COUNTER_ORDER_V2:
            raise WorkspaceMaterializeTransportContractError("host counters are not the complete canonical closure")
        counters = dict(self.host_counters)
        if counters["selector_count"] <= 0:
            raise WorkspaceMaterializeTransportContractError("host selector count must be positive")
        if counters["graph_admission_count"] not in {0, 1} or counters["graph_execution_count"] not in {0, 1}:
            raise WorkspaceMaterializeTransportContractError("host graph counters must be zero or one")
        plan_wire = _validate_retained_nested_wire(self.plan_result_wire_text, self.plan_result_wire_digest, "plan_result")
        graph_wire = _validate_retained_nested_wire(self.graph_result_wire_text, self.graph_result_wire_digest, "graph_result")
        if self.outcome == "succeeded":
            if self.failure_kind is not None or self.failure_code is not None:
                raise WorkspaceMaterializeTransportContractError("successful host result cannot carry failure")
            if self.terminal_stage == "graph_plan":
                if plan_wire is None or graph_wire is not None:
                    raise WorkspaceMaterializeTransportContractError("plan-only host result evidence differs")
            elif self.terminal_stage == "graph_execution":
                if plan_wire is None or graph_wire is None:
                    raise WorkspaceMaterializeTransportContractError("executed host result evidence differs")
            else:
                raise WorkspaceMaterializeTransportContractError("successful host result terminal stage differs")
        else:
            _validate_failure_pair(self.failure_kind, self.failure_code)
            if self.terminal_stage == "graph_execution":
                if plan_wire is None or graph_wire is None or self.failure_kind != "graph_execution":
                    raise WorkspaceMaterializeTransportContractError("terminal graph failure evidence differs")
            elif graph_wire is not None:
                raise WorkspaceMaterializeTransportContractError("pre-execution result cannot carry graph evidence")
            if plan_wire is not None and terminal_index < WORKSPACE_MATERIALIZE_HOST_STAGE_ORDER_V2.index("graph_plan"):
                raise WorkspaceMaterializeTransportContractError("pre-plan result cannot carry plan evidence")
        if self.response_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeTransportContractError("host result digest mismatched")

    def _payload(self) -> dict[str, object]:
        return _host_result_payload(
            self.attempt_ref, self.proposal_digest, self.outcome, self.terminal_stage,
            self.host_timing_ns, self.host_total_ns, self.host_counters,
            self.plan_result_wire_text, self.plan_result_wire_digest,
            self.graph_result_wire_text, self.graph_result_wire_digest,
            self.failure_kind, self.failure_code,
        )

    def plan_result_wire(self) -> bytes | None:
        self.__post_init__()
        return None if self.plan_result_wire_text is None else self.plan_result_wire_text.encode()

    def graph_result_wire(self) -> bytes | None:
        self.__post_init__()
        return None if self.graph_result_wire_text is None else self.graph_result_wire_text.encode()

    def to_wire(self) -> bytes:
        self.__post_init__()
        return _canonical_json_bytes({
            "contract": self.contract, **self._payload(),
            "response_digest": self.response_digest, "non_claims": list(self.non_claims),
        })

    @classmethod
    def from_wire(
        cls, wire: bytes, *, proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3,
    ) -> WorkspaceMaterializeHostResultV2:
        if type(proposal) not in (WorkspaceMaterializeCommandProposalV2, WorkspaceMaterializeCommandProposalV3):
            raise TypeError("original V2 or V3 proposal required")
        proposal.__post_init__()
        root = _decode_exact_object(wire, {
            "attempt_ref", "contract", "failure_code", "failure_kind",
            "graph_result_wire_digest", "graph_result_wire_text", "host_counters",
            "host_timing_ns", "host_total_ns", "non_claims", "outcome",
            "plan_result_wire_digest", "plan_result_wire_text", "proposal_digest",
            "response_digest", "terminal_stage",
        })
        result = cls(
            attempt_ref=_text(root["attempt_ref"], "attempt_ref"),
            proposal_digest=_digest(root["proposal_digest"], "proposal_digest"),
            outcome=_text(root["outcome"], "outcome"),
            terminal_stage=_text(root["terminal_stage"], "terminal_stage"),
            host_timing_ns=_decode_metrics(root["host_timing_ns"], "host_timing_ns"),
            host_total_ns=_nonnegative_integer(root["host_total_ns"], "host_total_ns"),
            host_counters=_decode_metrics(root["host_counters"], "host_counters"),
            plan_result_wire_text=_optional_text(root["plan_result_wire_text"], "plan_result_wire_text"),
            plan_result_wire_digest=_optional_digest(root["plan_result_wire_digest"], "plan_result_wire_digest"),
            graph_result_wire_text=_optional_text(root["graph_result_wire_text"], "graph_result_wire_text"),
            graph_result_wire_digest=_optional_digest(root["graph_result_wire_digest"], "graph_result_wire_digest"),
            failure_kind=_optional_text(root["failure_kind"], "failure_kind"),
            failure_code=_optional_text(root["failure_code"], "failure_code"),
            response_digest=_digest(root["response_digest"], "response_digest"),
            contract=_text(root["contract"], "contract"),
            non_claims=tuple(_text(item, "non_claim") for item in _list(root["non_claims"])),
        )
        if result.attempt_ref != proposal.attempt_ref or result.proposal_digest != proposal.proposal_digest:
            raise WorkspaceMaterializeTransportContractError("host result correlation differs from proposal")
        if result.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("host result wire is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeHostOperationReceiptV1:
    """Detached proof of one original host/source operation, never a capability."""

    operation_ref: str
    parent_ref: str
    epoch_ref: str
    attempt_ref: str
    proposal_digest: str
    declaration_scope_digest: str
    receipt_digest: str
    contract: str = WORKSPACE_MATERIALIZE_HOST_OPERATION_RECEIPT_V1

    @classmethod
    def create(
        cls, *, operation_ref: str, parent_ref: str, epoch_ref: str,
        attempt_ref: str, proposal_digest: str, declaration_scope_digest: str,
    ) -> WorkspaceMaterializeHostOperationReceiptV1:
        payload = {
            "operation_ref": operation_ref,
            "parent_ref": parent_ref,
            "epoch_ref": epoch_ref,
            "attempt_ref": attempt_ref,
            "proposal_digest": proposal_digest,
            "declaration_scope_digest": declaration_scope_digest,
        }
        result = cls(
            operation_ref=operation_ref,
            parent_ref=parent_ref,
            epoch_ref=epoch_ref,
            attempt_ref=attempt_ref,
            proposal_digest=proposal_digest,
            declaration_scope_digest=declaration_scope_digest,
            receipt_digest=_semantic_digest(
                WORKSPACE_MATERIALIZE_HOST_OPERATION_RECEIPT_V1, payload
            ),
        )
        result.__post_init__()
        return result

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_HOST_OPERATION_RECEIPT_V1:
            raise WorkspaceMaterializeTransportContractError("operation receipt contract differs")
        _uuid_ref(self.operation_ref, "workspace-materialize-operation:", "operation_ref")
        _uuid_ref(self.parent_ref, "workspace-command-parent:", "parent_ref")
        _uuid_ref(self.epoch_ref, "workspace-command-epoch:", "epoch_ref")
        _text(self.attempt_ref, "attempt_ref")
        _digest(self.proposal_digest, "proposal_digest")
        _digest(self.declaration_scope_digest, "declaration_scope_digest")
        if self.receipt_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeTransportContractError("operation receipt digest mismatched")

    def _payload(self) -> dict[str, str]:
        return {
            "operation_ref": self.operation_ref,
            "parent_ref": self.parent_ref,
            "epoch_ref": self.epoch_ref,
            "attempt_ref": self.attempt_ref,
            "proposal_digest": self.proposal_digest,
            "declaration_scope_digest": self.declaration_scope_digest,
        }

    def to_value(self) -> dict[str, str]:
        self.__post_init__()
        return {
            "contract": self.contract,
            **self._payload(),
            "receipt_digest": self.receipt_digest,
        }

    def to_wire(self) -> bytes:
        return _canonical_json_bytes(self.to_value())

    @classmethod
    def from_value(cls, value: object) -> WorkspaceMaterializeHostOperationReceiptV1:
        if type(value) is not dict or set(value) != {
            "contract", "operation_ref", "parent_ref", "epoch_ref", "attempt_ref",
            "proposal_digest", "declaration_scope_digest", "receipt_digest",
        }:
            raise WorkspaceMaterializeTransportContractError("operation receipt fields differ")
        root = cast(dict[str, object], value)
        result = cls(
            operation_ref=_text(root["operation_ref"], "operation_ref"),
            parent_ref=_text(root["parent_ref"], "parent_ref"),
            epoch_ref=_text(root["epoch_ref"], "epoch_ref"),
            attempt_ref=_text(root["attempt_ref"], "attempt_ref"),
            proposal_digest=_digest(root["proposal_digest"], "proposal_digest"),
            declaration_scope_digest=_digest(
                root["declaration_scope_digest"], "declaration_scope_digest"
            ),
            receipt_digest=_digest(root["receipt_digest"], "receipt_digest"),
            contract=_text(root["contract"], "contract"),
        )
        result.__post_init__()
        return result

    @classmethod
    def from_wire(cls, wire: bytes) -> WorkspaceMaterializeHostOperationReceiptV1:
        root = _decode_json(wire)
        result = cls.from_value(root)
        if result.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("operation receipt wire is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeHostResultV3:
    """Versioned host-source result; retained V2 fields remain unchanged."""

    predecessor: WorkspaceMaterializeHostResultV2
    operation_receipt: WorkspaceMaterializeHostOperationReceiptV1
    response_digest: str
    contract: str = WORKSPACE_MATERIALIZE_HOST_RESULT_V3

    @classmethod
    def create(
        cls, *, predecessor: WorkspaceMaterializeHostResultV2,
        operation_receipt: WorkspaceMaterializeHostOperationReceiptV1,
    ) -> WorkspaceMaterializeHostResultV3:
        result = cls(
            predecessor=predecessor,
            operation_receipt=operation_receipt,
            response_digest=_semantic_digest(
                WORKSPACE_MATERIALIZE_HOST_RESULT_V3,
                {
                    "predecessor_wire_text": predecessor.to_wire().decode(),
                    "operation_receipt_wire_text": operation_receipt.to_wire().decode(),
                },
            ),
        )
        result.__post_init__()
        return result

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_HOST_RESULT_V3:
            raise WorkspaceMaterializeTransportContractError("host result V3 contract differs")
        if type(self.predecessor) is not WorkspaceMaterializeHostResultV2:
            raise TypeError("exact V2 predecessor required")
        if type(self.operation_receipt) is not WorkspaceMaterializeHostOperationReceiptV1:
            raise TypeError("exact host operation receipt required")
        self.predecessor.__post_init__()
        self.operation_receipt.__post_init__()
        if (
            self.predecessor.outcome != "blocked"
            or self.predecessor.terminal_stage != "host_admission"
            or self.predecessor.failure_kind != "authority"
            or self.predecessor.failure_code != "graph_host_not_ready"
            or self.predecessor.plan_result_wire_text is not None
            or self.predecessor.graph_result_wire_text is not None
            or self.operation_receipt.attempt_ref != self.predecessor.attempt_ref
            or self.operation_receipt.proposal_digest != self.predecessor.proposal_digest
        ):
            raise WorkspaceMaterializeTransportContractError(
                "host operation receipt does not match source-admitted refusal"
            )
        counters = dict(self.predecessor.host_counters)
        if (
            counters["authority_preflight_count"] != 1
            or counters["catalog_observation_count"] != 0
            or counters["selected_package_count"] != 0
            or counters["graph_admission_count"] != 0
            or counters["graph_execution_count"] != 0
        ):
            raise WorkspaceMaterializeTransportContractError(
                "host operation receipt cannot claim later admission"
            )
        if self.response_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeTransportContractError("host result V3 digest mismatched")

    def _payload(self) -> dict[str, str]:
        return {
            "predecessor_wire_text": self.predecessor.to_wire().decode(),
            "operation_receipt_wire_text": self.operation_receipt.to_wire().decode(),
        }

    def to_wire(self) -> bytes:
        self.__post_init__()
        return _canonical_json_bytes({
            "contract": self.contract,
            **self._payload(),
            "response_digest": self.response_digest,
        })

    @classmethod
    def from_wire(
        cls, wire: bytes, *, proposal: WorkspaceMaterializeCommandProposalV2,
    ) -> WorkspaceMaterializeHostResultV3:
        root = _decode_exact_object(wire, {
            "contract", "predecessor_wire_text", "operation_receipt_wire_text",
            "response_digest",
        })
        predecessor = WorkspaceMaterializeHostResultV2.from_wire(
            _text(root["predecessor_wire_text"], "predecessor_wire_text").encode(),
            proposal=proposal,
        )
        receipt = WorkspaceMaterializeHostOperationReceiptV1.from_wire(
            _text(root["operation_receipt_wire_text"], "operation_receipt_wire_text").encode()
        )
        result = cls(
            predecessor=predecessor,
            operation_receipt=receipt,
            response_digest=_digest(root["response_digest"], "response_digest"),
            contract=_text(root["contract"], "contract"),
        )
        if result.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("host result V3 wire is not canonical")
        return result


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeSelectedRootV1:
    """Detached observation of one selected source; never a retained handle."""

    workspace_handle: str
    workspace_manifest_path: str
    module_id: str
    package_id: str
    semantic_package_name: str
    semantic_version: str
    source_identity_digest: str
    selection_digest: str
    contract: str = WORKSPACE_MATERIALIZE_SELECTED_ROOT_V1

    @classmethod
    def create(
        cls, *, workspace_handle: str, workspace_manifest_path: str, module_id: str,
        package_id: str, semantic_package_name: str, semantic_version: str,
        source_identity_digest: str,
    ) -> WorkspaceMaterializeSelectedRootV1:
        payload = {
            "workspace_handle": workspace_handle,
            "workspace_manifest_path": workspace_manifest_path,
            "module_id": module_id,
            "package_id": package_id,
            "semantic_package_name": semantic_package_name,
            "semantic_version": semantic_version,
            "source_identity_digest": source_identity_digest,
        }
        result = cls(
            workspace_handle, workspace_manifest_path, module_id, package_id,
            semantic_package_name, semantic_version, source_identity_digest,
            _semantic_digest(WORKSPACE_MATERIALIZE_SELECTED_ROOT_V1, payload),
        )
        result.__post_init__()
        return result

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_SELECTED_ROOT_V1:
            raise WorkspaceMaterializeTransportContractError("selected-root contract differs")
        _text(self.workspace_manifest_path, "workspace_manifest_path")
        for value in (self.workspace_handle, self.module_id, self.package_id, self.semantic_package_name, self.semantic_version):
            _text(value, "selected_root_field")
        _digest(self.source_identity_digest, "source_identity_digest")
        if self.selection_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeTransportContractError("selected-root digest differs")

    def _payload(self) -> dict[str, str]:
        return {
            "workspace_handle": self.workspace_handle,
            "workspace_manifest_path": self.workspace_manifest_path,
            "module_id": self.module_id,
            "package_id": self.package_id,
            "semantic_package_name": self.semantic_package_name,
            "semantic_version": self.semantic_version,
            "source_identity_digest": self.source_identity_digest,
        }

    def to_value(self) -> dict[str, str]:
        self.__post_init__()
        return {"contract": self.contract, **self._payload(), "selection_digest": self.selection_digest}

    def to_wire(self) -> bytes:
        return _canonical_json_bytes(self.to_value())

    @classmethod
    def from_value(cls, value: object) -> WorkspaceMaterializeSelectedRootV1:
        if type(value) is not dict or set(value) != {
            "contract", "workspace_handle", "workspace_manifest_path", "module_id", "package_id",
            "semantic_package_name", "semantic_version", "source_identity_digest",
            "selection_digest",
        }:
            raise WorkspaceMaterializeTransportContractError("selected-root fields differ")
        root = cast(dict[str, object], value)
        result = cls(
            workspace_handle=_text(root["workspace_handle"], "workspace_handle"),
            workspace_manifest_path=_text(root["workspace_manifest_path"], "workspace_manifest_path"),
            module_id=_text(root["module_id"], "module_id"),
            package_id=_text(root["package_id"], "package_id"),
            semantic_package_name=_text(root["semantic_package_name"], "semantic_package_name"),
            semantic_version=_text(root["semantic_version"], "semantic_version"),
            source_identity_digest=_digest(root["source_identity_digest"], "source_identity_digest"),
            selection_digest=_digest(root["selection_digest"], "selection_digest"),
            contract=_text(root["contract"], "contract"),
        )
        result.__post_init__()
        return result

    @classmethod
    def from_wire(cls, wire: bytes) -> WorkspaceMaterializeSelectedRootV1:
        value = cls.from_value(_decode_json(wire))
        if value.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("selected-root wire is not canonical")
        return value


@dataclass(frozen=True, slots=True)
class WorkspaceMaterializeHostResultV4:
    """Blocked exact-address selection with original host and source evidence."""

    predecessor: WorkspaceMaterializeHostResultV2
    operation_receipt: WorkspaceMaterializeHostOperationReceiptV1
    selected_root: WorkspaceMaterializeSelectedRootV1
    response_digest: str
    contract: str = WORKSPACE_MATERIALIZE_HOST_RESULT_V4

    @classmethod
    def create(
        cls, *, predecessor: WorkspaceMaterializeHostResultV2,
        operation_receipt: WorkspaceMaterializeHostOperationReceiptV1,
        selected_root: WorkspaceMaterializeSelectedRootV1,
    ) -> WorkspaceMaterializeHostResultV4:
        payload = {
            "predecessor_wire_text": predecessor.to_wire().decode(),
            "operation_receipt_wire_text": operation_receipt.to_wire().decode(),
            "selected_root_wire_text": selected_root.to_wire().decode(),
        }
        result = cls(predecessor, operation_receipt, selected_root,
            _semantic_digest(WORKSPACE_MATERIALIZE_HOST_RESULT_V4, payload))
        result.__post_init__()
        return result

    def __post_init__(self) -> None:
        if self.contract != WORKSPACE_MATERIALIZE_HOST_RESULT_V4:
            raise WorkspaceMaterializeTransportContractError("exact-address host result contract differs")
        if type(self.predecessor) is not WorkspaceMaterializeHostResultV2 or type(self.operation_receipt) is not WorkspaceMaterializeHostOperationReceiptV1 or type(self.selected_root) is not WorkspaceMaterializeSelectedRootV1:
            raise TypeError("original selection result parts required")
        self.predecessor.__post_init__()
        self.operation_receipt.__post_init__()
        self.selected_root.__post_init__()
        counters = dict(self.predecessor.host_counters)
        if (
            self.predecessor.outcome != "blocked"
            or self.predecessor.terminal_stage != "selection"
            or self.predecessor.failure_kind != "authority"
            or self.predecessor.failure_code != "graph_host_not_ready"
            or self.predecessor.plan_result_wire_text is not None
            or self.predecessor.graph_result_wire_text is not None
            or counters["authority_preflight_count"] != 1
            or counters["selected_package_count"] != 1
            or counters["graph_admission_count"] != 0
            or counters["graph_execution_count"] != 0
            or self.operation_receipt.attempt_ref != self.predecessor.attempt_ref
            or self.operation_receipt.proposal_digest != self.predecessor.proposal_digest
        ):
            raise WorkspaceMaterializeTransportContractError("exact-address selection evidence differs")
        if self.response_digest != _semantic_digest(self.contract, self._payload()):
            raise WorkspaceMaterializeTransportContractError("exact-address host result digest differs")

    def _payload(self) -> dict[str, str]:
        return {
            "predecessor_wire_text": self.predecessor.to_wire().decode(),
            "operation_receipt_wire_text": self.operation_receipt.to_wire().decode(),
            "selected_root_wire_text": self.selected_root.to_wire().decode(),
        }

    def to_wire(self) -> bytes:
        self.__post_init__()
        return _canonical_json_bytes({"contract": self.contract, **self._payload(), "response_digest": self.response_digest})

    @classmethod
    def from_wire(
        cls, wire: bytes, *, proposal: WorkspaceMaterializeCommandProposalV3,
    ) -> WorkspaceMaterializeHostResultV4:
        if type(proposal) is not WorkspaceMaterializeCommandProposalV3:
            raise TypeError("exact-address proposal required")
        root = _decode_exact_object(wire, {
            "contract", "predecessor_wire_text", "operation_receipt_wire_text",
            "selected_root_wire_text", "response_digest",
        })
        result = cls(
            predecessor=WorkspaceMaterializeHostResultV2.from_wire(
                _text(root["predecessor_wire_text"], "predecessor_wire_text").encode(),
                proposal=proposal,
            ),
            operation_receipt=WorkspaceMaterializeHostOperationReceiptV1.from_wire(
                _text(root["operation_receipt_wire_text"], "operation_receipt_wire_text").encode()
            ),
            selected_root=WorkspaceMaterializeSelectedRootV1.from_wire(
                _text(root["selected_root_wire_text"], "selected_root_wire_text").encode()
            ),
            response_digest=_digest(root["response_digest"], "response_digest"),
            contract=_text(root["contract"], "contract"),
        )
        if (
            result.selected_root.workspace_handle != proposal.package_address[0]
            or result.selected_root.module_id != proposal.package_address[1]
            or result.selected_root.package_id != proposal.package_address[2]
            or result.selected_root.workspace_manifest_path != proposal.workspace_manifest_name
        ):
            raise WorkspaceMaterializeTransportContractError("selected package address differs")
        if result.to_wire() != wire:
            raise WorkspaceMaterializeTransportContractError("exact-address host wire is not canonical")
        return result


def empty_workspace_materialize_host_counters_v2(
    proposal: WorkspaceMaterializeCommandProposalV2 | WorkspaceMaterializeCommandProposalV3,
) -> tuple[tuple[str, int], ...]:
    if type(proposal) not in (WorkspaceMaterializeCommandProposalV2, WorkspaceMaterializeCommandProposalV3):
        raise TypeError("original V2 or V3 proposal required")
    proposal.__post_init__()
    values = {key: 0 for key in WORKSPACE_MATERIALIZE_HOST_COUNTER_ORDER_V2}
    values["selector_count"] = len(proposal.selectors) if type(proposal) is WorkspaceMaterializeCommandProposalV2 else 1
    return tuple((key, values[key]) for key in WORKSPACE_MATERIALIZE_HOST_COUNTER_ORDER_V2)


def _preflight_selectors(value: object) -> tuple[WorkspaceMaterializeCommandSelectorV2, ...]:
    if type(value) is not tuple or not value:
        raise TypeError("selectors must be a nonempty exact tuple")
    wires: list[bytes] = []
    for item in value:
        if type(item) is not WorkspaceMaterializeCommandSelectorV2:
            raise TypeError("selectors must contain exact V2 selector values")
        item.__post_init__()
        wires.append(_canonical_json_bytes(item.to_wire()))
    if tuple(wires) != tuple(sorted(set(wires))):
        raise WorkspaceMaterializeTransportContractError("selectors must be unique canonical-byte order")
    return cast(tuple[WorkspaceMaterializeCommandSelectorV2, ...], value)


def _proposal_payload(
    attempt_ref: object, participant_checkout_root: object,
    workspace_manifest_name: object, selectors: object, plan_only: object,
) -> dict[str, object]:
    admitted = _preflight_selectors(selectors)
    return {
        "attempt_ref": _text(attempt_ref, "attempt_ref"),
        "participant_checkout_root": None if participant_checkout_root is None else _text(participant_checkout_root, "participant_checkout_root"),
        "workspace_manifest_name": _text(workspace_manifest_name, "workspace_manifest_name"),
        "selectors": [item.to_wire() for item in admitted],
        "plan_only": _boolean(plan_only, "plan_only"),
    }


def _address_component(value: object) -> str:
    component = _text(value, "package_address_component")
    if ":" in component or "/" in component or any(char.isspace() for char in component):
        raise WorkspaceMaterializeTransportContractError("package address component is not canonical")
    return component


def _proposal_v3_payload(
    attempt_ref: object, participant_checkout_root: object,
    workspace_manifest_name: object, package_address: object, plan_only: object,
) -> dict[str, object]:
    if type(package_address) is not tuple or len(package_address) != 3:
        raise WorkspaceMaterializeTransportContractError("exact package address requires three fields")
    address = tuple(_address_component(item) for item in package_address)
    return {
        "attempt_ref": _text(attempt_ref, "attempt_ref"),
        "participant_checkout_root": None if participant_checkout_root is None else _text(participant_checkout_root, "participant_checkout_root"),
        "workspace_manifest_name": _text(workspace_manifest_name, "workspace_manifest_name"),
        "package_address": list(address),
        "plan_only": _boolean(plan_only, "plan_only"),
    }


def _host_result_payload(
    attempt_ref: object, proposal_digest: object, outcome: object,
    terminal_stage: object, host_timing_ns: object, host_total_ns: object,
    host_counters: object, plan_text: object, plan_digest: object,
    graph_text: object, graph_digest: object, failure_kind: object,
    failure_code: object,
) -> dict[str, object]:
    timings = cast(tuple[tuple[str, int], ...], host_timing_ns)
    counters = cast(tuple[tuple[str, int], ...], host_counters)
    return {
        "attempt_ref": attempt_ref, "proposal_digest": proposal_digest,
        "outcome": outcome, "terminal_stage": terminal_stage,
        "host_timing_ns": [{"stage": key, "elapsed_ns": value} for key, value in timings],
        "host_total_ns": host_total_ns,
        "host_counters": [{"counter": key, "value": value} for key, value in counters],
        "plan_result_wire_text": plan_text, "plan_result_wire_digest": plan_digest,
        "graph_result_wire_text": graph_text, "graph_result_wire_digest": graph_digest,
        "failure_kind": failure_kind, "failure_code": failure_code,
    }


def _retain_nested_wire(wire: object, field: str) -> tuple[str | None, str | None]:
    if wire is None:
        return None, None
    if type(wire) is not bytes:
        raise TypeError(f"{field} wire must be exact bytes or null")
    root = _decode_json(wire)
    if type(root) is not dict or _canonical_json_bytes(root) != wire:
        raise WorkspaceMaterializeTransportContractError(f"{field} wire must be a canonical JSON object")
    return wire.decode(), _wire_digest(field, wire)


def _validate_retained_nested_wire(text: object, digest: object, field: str) -> bytes | None:
    if text is None or digest is None:
        if text is not None or digest is not None:
            raise WorkspaceMaterializeTransportContractError(f"{field} wire and digest absence differ")
        return None
    wire = _text(text, f"{field}_wire_text").encode()
    root = _decode_json(wire)
    if type(root) is not dict or _canonical_json_bytes(root) != wire:
        raise WorkspaceMaterializeTransportContractError(f"{field} wire must be a canonical JSON object")
    if _digest(digest, f"{field}_wire_digest") != _wire_digest(field, wire):
        raise WorkspaceMaterializeTransportContractError(f"{field} wire digest differs")
    return wire


def _wire_digest(field: str, wire: bytes) -> str:
    return _DIGEST_PREFIX + hashlib.sha256(
        f"aware.workspace.materialize-{field}-wire.v2".encode() + b"\x00" + wire
    ).hexdigest()


def _validate_failure_pair(kind: object, code: object) -> None:
    admitted_kind = _text(kind, "failure_kind")
    admitted_code = _text(code, "failure_code")
    allowed = WORKSPACE_MATERIALIZE_FAILURE_CODES_V2.get(admitted_kind)
    if allowed is None or (admitted_kind != "graph_execution" and admitted_code not in allowed):
        raise WorkspaceMaterializeTransportContractError("host result failure kind/code unsupported")


def _semantic_digest(contract: str, payload: object) -> str:
    return _DIGEST_PREFIX + hashlib.sha256(contract.encode() + b"\n" + _canonical_json_bytes(payload)).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()


def _decode_json(wire: bytes) -> object:
    if type(wire) is not bytes or not wire or len(wire) > _MAX_WIRE_BYTES:
        raise WorkspaceMaterializeTransportContractError("wire must be bounded nonempty exact bytes")
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise WorkspaceMaterializeTransportContractError("wire contains a duplicate object key")
            result[key] = value
        return result
    try:
        return json.loads(
            wire.decode(), object_pairs_hook=pairs,
            parse_float=lambda _value: _raise_float(),
            parse_constant=lambda _value: _raise_float(),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise WorkspaceMaterializeTransportContractError("wire is not strict JSON") from error


def _decode_exact_object(wire: bytes, fields: set[str]) -> dict[str, object]:
    root = _decode_json(wire)
    if type(root) is not dict or set(root) != fields:
        raise WorkspaceMaterializeTransportContractError("wire object fields differ")
    return cast(dict[str, object], root)


def _raise_float() -> object:
    raise WorkspaceMaterializeTransportContractError("floating-point JSON values are unsupported")


def _decode_metrics(value: object, field: str) -> tuple[tuple[str, int], ...]:
    name_field = "counter" if field == "host_counters" else "stage"
    value_field = "value" if field == "host_counters" else "elapsed_ns"
    result: list[tuple[str, int]] = []
    for item in _list(value):
        if type(item) is not dict or set(item) != {name_field, value_field}:
            raise WorkspaceMaterializeTransportContractError(f"{field} entry fields differ")
        entry = cast(dict[str, object], item)
        result.append((_text(entry[name_field], name_field), _nonnegative_integer(entry[value_field], value_field)))
    return tuple(result)


def _metric_tuple(value: object, field: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be an exact tuple")
    names: list[str] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise TypeError(f"{field} entries must be exact pairs")
        names.append(_text(item[0], f"{field}_name"))
        _nonnegative_integer(item[1], f"{field}_value")
    if len(names) != len(set(names)):
        raise WorkspaceMaterializeTransportContractError(f"{field} names must be unique")
    return tuple(names)


def _text(value: object, field: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise WorkspaceMaterializeTransportContractError(f"{field} must be nonempty exact text")
    return value


def _uuid_ref(value: object, prefix: str, field: str) -> str:
    result = _text(value, field)
    if not result.startswith(prefix):
        raise WorkspaceMaterializeTransportContractError(f"{field} prefix differs")
    suffix = result[len(prefix):]
    try:
        parsed = UUID(suffix)
    except ValueError as error:
        raise WorkspaceMaterializeTransportContractError(f"{field} must contain UUID") from error
    if str(parsed) != suffix:
        raise WorkspaceMaterializeTransportContractError(f"{field} UUID is not canonical")
    return result


def _optional_text(value: object, field: str) -> str | None:
    return None if value is None else _text(value, field)


def _digest(value: object, field: str) -> str:
    result = _text(value, field)
    if len(result) != 71 or not result.startswith(_DIGEST_PREFIX):
        raise WorkspaceMaterializeTransportContractError(f"{field} must be a sha256 digest")
    try:
        int(result[7:], 16)
    except ValueError as error:
        raise WorkspaceMaterializeTransportContractError(f"{field} must be a sha256 digest") from error
    if result != result.lower():
        raise WorkspaceMaterializeTransportContractError(f"{field} must use lowercase hexadecimal")
    return result


def _optional_digest(value: object, field: str) -> str | None:
    return None if value is None else _digest(value, field)


def _boolean(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise WorkspaceMaterializeTransportContractError(f"{field} must be an exact boolean")
    return value


def _nonnegative_integer(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise WorkspaceMaterializeTransportContractError(f"{field} must be a nonnegative exact integer")
    return value


def _list(value: object) -> list[object]:
    if type(value) is not list:
        raise WorkspaceMaterializeTransportContractError("wire field must be an exact list")
    return cast(list[object], value)


__all__ = [
    "WORKSPACE_MATERIALIZE_COMMAND_PROPOSAL_V2",
    "WORKSPACE_MATERIALIZE_FAILURE_CODES_V2",
    "WORKSPACE_MATERIALIZE_HOST_COUNTER_ORDER_V2",
    "WORKSPACE_MATERIALIZE_HOST_RESULT_V2",
    "WORKSPACE_MATERIALIZE_HOST_STAGE_ORDER_V2",
    "WORKSPACE_MATERIALIZE_SELECTOR_KINDS_V2",
    "WORKSPACE_MATERIALIZE_TRANSPORT_NON_CLAIMS",
    "WorkspaceMaterializeCommandProposalV2",
    "WorkspaceMaterializeCommandSelectorV2",
    "WorkspaceMaterializeHostResultV2",
    "WorkspaceMaterializeTransportContractError",
    "empty_workspace_materialize_host_counters_v2",
]
