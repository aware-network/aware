"""Typed bootstrap client; explicit provider selection, no physical writes."""

from __future__ import annotations

import importlib
import re
from weakref import WeakKeyDictionary

from aware_protocol_runtime.bootstrap import (
    _SELECTED,
    ProtocolBootstrapAdmission,
    ProtocolBootstrapEffect,
    ProtocolBootstrapError,
    ProtocolBootstrapErrorEvidence,
    ProtocolBootstrapFile,
    ProtocolBootstrapInput,
    ProtocolBootstrapPlan,
    ProtocolBootstrapPlanObservation,
    ProtocolBootstrapRequest,
    ProtocolBootstrapResult,
    ProtocolBootstrapValueError,
    _BootstrapRuntime,
    detached,
    protocol_bootstrap_value_from_json,
    protocol_bootstrap_value_from_payload,
    protocol_bootstrap_value_to_json,
    protocol_bootstrap_value_to_payload,
    unvalidated_report,
)

_CLIENTS = WeakKeyDictionary()


class ProtocolBootstrapClient:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- initialized by Python

    def __new__(cls):
        raise TypeError("explicit_bootstrap_provider_selection_required")

    @classmethod
    def filesystem(cls, *, repository_root: str, execution_id: str):
        module = importlib.import_module("aware_protocol_fs_adapter.bootstrap")
        physical = module.FilesystemProtocolBootstrapPort(
            repository_root=repository_root
        )
        runtime = _BootstrapRuntime(
            physical=physical,
            repository_root=repository_root,
            execution_id=execution_id,
        )
        client = object.__new__(cls)
        _CLIENTS[client] = runtime
        _SELECTED.add(runtime)
        return client

    def _provider(self):
        if type(self) is not ProtocolBootstrapClient or self not in _CLIENTS:
            raise ValueError("original_bootstrap_client_required")
        return _CLIENTS[self]

    def prepare_bootstrap_request(
        self, *, issue_root="docs/issues", install_agent_contract=True, dry_run=True
    ):
        provider = self._provider()
        provider._current()
        return detached(
            provider.physical.prepare_request(
                issue_root=issue_root,
                install_agent_contract=install_agent_contract,
                dry_run=dry_run,
            )
        )

    def render_bootstrap_input(
        self, request: ProtocolBootstrapRequest
    ) -> ProtocolBootstrapInput:
        return self._provider().render(request)

    def plan_initialization(
        self, request: ProtocolBootstrapRequest
    ) -> ProtocolBootstrapPlan:
        return self._provider().plan_initialization(request)

    def admit_initialization(
        self, plan: ProtocolBootstrapPlan
    ) -> ProtocolBootstrapAdmission:
        return self._provider().admit_initialization(plan)

    def initialize_profile(
        self,
        request: ProtocolBootstrapRequest,
        *,
        admission: ProtocolBootstrapAdmission | None = None,
    ) -> ProtocolBootstrapResult:
        provider = self._provider()
        with provider.lock:
            try:
                invocation = detached(request)
                dispatch = detached(invocation)
            except BaseException as error:  # retire even on interrupted snapshots
                raise provider.snapshot_failure(request, admission=admission) from error
            reported = provider.initialize_profile(dispatch, admission=admission)
            try:
                value = detached(reported)
                if (
                    type(value) is not ProtocolBootstrapResult
                    or invocation is None
                    or value.request != invocation
                    or detached(request) != invocation
                    or value.execution_id != provider.execution_id
                    or value != provider.last_original_result
                ):
                    raise ProtocolBootstrapValueError(
                        "bootstrap_result_correlation_failed"
                    )
                if value.cleanup_state != "completed" or not value.ledger_complete:
                    raise ProtocolBootstrapValueError("bootstrap_completion_unverified")
                if invocation.dry_run:
                    if (
                        value.outcome != "planned"
                        or value.effects
                        or value.provider_invoked
                        or value.attempt_ref is not None
                        or value.manifest_source_sha256 is not None
                        or value.manifest_semantic_digest is not None
                    ):
                        raise ProtocolBootstrapValueError(
                            "bootstrap_preview_effects_refused"
                        )
                elif (
                    value.outcome != "initialized"
                    or not value.provider_invoked
                    or value.attempt_ref is None
                    or re.fullmatch(r"protocol-attempt:[0-9a-f]{32}", value.attempt_ref)
                    is None
                    or value.manifest_source_sha256 is None
                    or value.manifest_semantic_digest is None
                    or not value.effects
                    or any(item.state != "applied" for item in value.effects)
                ):
                    raise ProtocolBootstrapValueError(
                        "bootstrap_publication_unverified"
                    )
                provider._current()
                return value
            except BaseException as error:
                raise provider.result_failure(
                    invocation if invocation is not None else request,
                    unvalidated_report(reported),
                ) from error


__all__ = [
    "ProtocolBootstrapAdmission",
    "ProtocolBootstrapClient",
    "ProtocolBootstrapEffect",
    "ProtocolBootstrapError",
    "ProtocolBootstrapErrorEvidence",
    "ProtocolBootstrapFile",
    "ProtocolBootstrapInput",
    "ProtocolBootstrapPlan",
    "ProtocolBootstrapPlanObservation",
    "ProtocolBootstrapRequest",
    "ProtocolBootstrapResult",
    "ProtocolBootstrapValueError",
    "protocol_bootstrap_value_from_json",
    "protocol_bootstrap_value_from_payload",
    "protocol_bootstrap_value_to_json",
    "protocol_bootstrap_value_to_payload",
]
