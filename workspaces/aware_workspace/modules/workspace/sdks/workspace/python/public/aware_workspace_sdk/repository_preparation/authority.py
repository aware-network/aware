"""Original SDK selection and single-use preparation handles."""

from __future__ import annotations

import importlib
import os
import re
import threading
from typing import Any
from weakref import WeakKeyDictionary

from .codec import (
    RepositoryPreparationValueError,
    detached,
    unvalidated_report,
)
from .values import RepositoryPrepareRequest, RepositoryPrepareResult

_OWNERS: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()
_CLIENTS: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()
_PHYSICAL_CLAIMS = WeakKeyDictionary()
_CLAIM_LOCK = threading.Lock()
_RUNTIME_TYPES = set()


class _Original:
    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- Python initializes the weakref slot

    def __new__(cls):
        raise TypeError("original_preparation_issuer_required")

    def __copy__(self):
        raise TypeError("preparation_handle_not_copyable")

    def __deepcopy__(self, memo):
        raise TypeError("preparation_handle_not_copyable")

    def __reduce_ex__(self, protocol):
        raise TypeError("preparation_handle_not_serializable")

    def release(self):
        raise NotImplementedError("original_owner_release_required")

    def __del__(self):
        try:
            self.release()
        except BaseException:  # noqa: BLE001 -- finalizer must not suppress active errors
            return  # Fallback disposal is not completion evidence.


def _owner(handle):
    if (
        type(handle) is not RepositoryPreparationPlan
        and type(handle) is not RepositoryPreparationAdmission
    ):
        raise ValueError("original_preparation_handle_required")
    owner = _OWNERS.get(handle)
    if owner is None:
        raise ValueError("original_preparation_handle_required")
    return owner


class RepositoryPreparationPlan(_Original):
    __slots__ = ()

    def observe(self):
        return _owner(self).observe_plan(self)

    def release(self):
        _owner(self).release_plan(self)

    def __enter__(self):
        self.observe()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.release()
        return False


class RepositoryPreparationAdmission(_Original):
    __slots__ = ()

    def release(self):
        _owner(self).release_admission(self)


class _PhysicalClaim(_Original):
    __slots__ = ()

    def release(self):
        with _CLAIM_LOCK:
            _PHYSICAL_CLAIMS.pop(self, None)


def _issue_physical_claim(owner, plan):
    if _OWNERS.get(plan) is not owner:
        raise ValueError("original_preparation_plan_required")
    state = owner.plans.get(plan)
    if state is None or state.phase != "spent" or state.request.dry_run:
        raise ValueError("spent_preparation_admission_required")
    claim = object.__new__(_PhysicalClaim)
    with _CLAIM_LOCK:
        _PHYSICAL_CLAIMS[claim] = (
            state.physical,
            owner.pid,
            owner.execution_id,
            state.attempt_ref,
        )
    return claim


def _consume_physical_claim(claim, physical):
    # Atomic registry consumption under the SDK's leaf lock.
    # No callback to the runtime, no freshness callback, no lock inversion.
    with _CLAIM_LOCK:
        state = _PHYSICAL_CLAIMS.get(claim) if type(claim) is _PhysicalClaim else None
        if state is None or state[0] is not physical:
            raise ValueError("original_preparation_physical_claim_required")
        del _PHYSICAL_CLAIMS[claim]
    identities = [
        prefix + os.environ[name].strip()
        for name, prefix in (
            ("CODEX_THREAD_ID", "codex-"),
            ("CLAUDE_CODE_SESSION_ID", "claude_code-"),
        )
        if os.environ.get(name, "").strip()
    ]
    if os.getpid() != state[1] or identities != [state[2]]:
        raise ValueError("preparation_physical_execution_changed")


def _issue(owner, kind):
    if not any(type(owner) is declared for declared in _RUNTIME_TYPES) or not any(
        owner is selected for selected in _CLIENTS.values()
    ):
        raise TypeError("original_preparation_runtime_required")
    handle = object.__new__(kind)
    _OWNERS[handle] = owner
    return handle


def _issue_plan(owner):
    return _issue(owner, RepositoryPreparationPlan)


def _issue_admission(owner):
    return _issue(owner, RepositoryPreparationAdmission)


class WorkspaceRepositoryPreparationClient:
    """Explicit FS selection; typed values alone grant no write authority."""

    __slots__ = ("__weakref__",)  # pyright: ignore[reportUninitializedInstanceVariable] -- Python initializes the weakref slot

    def __new__(cls):
        raise TypeError("use_explicit_preparation_provider_selection")

    @classmethod
    def filesystem(cls, *, repository_root: str, execution_id: str):
        # Explicit lazy owning-module selection, never an availability fallback
        # or source-path loader. Runtime and FS imports do not activate here
        # until the caller selects the preparation integration.
        physical_module = importlib.import_module(
            "aware_workspace_fs_adapter.repository_preparation"
        )
        runtime_module = importlib.import_module(
            "aware_workspace_runtime.repository_preparation"
        )
        physical = physical_module.FilesystemRepositoryPreparationPort(
            repository_root=repository_root
        )
        runtime = runtime_module.WorkspaceRepositoryPreparationRuntime(
            physical=physical,
            repository_root=repository_root,
            execution_id=execution_id,
        )
        client = object.__new__(cls)
        _CLIENTS[client] = runtime
        return client

    def _provider(self):
        if type(self) is not WorkspaceRepositoryPreparationClient:
            raise ValueError("original_preparation_client_required")
        provider = _CLIENTS.get(self)
        if provider is None:
            raise ValueError("original_preparation_client_required")
        return provider

    def plan_repository_preparation(
        self, request: RepositoryPrepareRequest
    ) -> RepositoryPreparationPlan:
        return self._provider().plan_repository_preparation(detached(request))

    def admit_repository_preparation(
        self, plan: RepositoryPreparationPlan
    ) -> RepositoryPreparationAdmission:
        return self._provider().admit_repository_preparation(plan)

    def prepare_repository(
        self,
        request: RepositoryPrepareRequest,
        *,
        admission: RepositoryPreparationAdmission | None = None,
    ) -> RepositoryPrepareResult:
        provider = self._provider()
        # Keep invocation and original-ledger return validation one dispatch.
        # FS never calls back into this owner while holding physical custody.
        with provider.lock:
            try:
                invocation = detached(request)
            except RepositoryPreparationValueError:
                # The owner must still spend/retire a genuine admission when
                # an invalid request is submitted, before refusing it.
                invocation = None
            reported = provider.prepare_repository(
                detached(invocation) if invocation is not None else request,
                admission=admission,
            )
            try:
                value = detached(reported)
                if type(value) is not RepositoryPrepareResult:
                    raise RepositoryPreparationValueError("preparation_result_required")
                if (
                    invocation is None
                    or value.request != invocation
                    or detached(request) != invocation
                    or value.execution_id != provider.execution_id
                ):
                    raise RepositoryPreparationValueError(
                        "preparation_result_correlation_failed"
                    )
                if value != provider.last_original_result:
                    raise RepositoryPreparationValueError(
                        "preparation_original_return_mismatch"
                    )
                if value.outcome in ("created", "existing", "planned") and (
                    value.cleanup_state != "completed" or not value.ledger_complete
                ):
                    raise RepositoryPreparationValueError(
                        "preparation_completion_unverified"
                    )
                if invocation.dry_run:
                    if (
                        value.effects
                        or value.provider_invoked
                        or value.attempt_ref is not None
                        or value.outcome == "created"
                    ):
                        raise RepositoryPreparationValueError("preview_effects_refused")
                elif (
                    not value.provider_invoked
                    or value.attempt_ref is None
                    or re.fullmatch(
                        r"repository-attempt:[0-9a-f]{32}", value.attempt_ref
                    )
                    is None
                ):
                    raise RepositoryPreparationValueError(
                        "preparation_attempt_required"
                    )
                if value.outcome == "created" and (
                    value.head is not None
                    or not any(
                        item.kind == "git_repository_initialization"
                        and item.state == "applied"
                        for item in value.effects
                    )
                ):
                    raise RepositoryPreparationValueError(
                        "repository_creation_unproven"
                    )
                if (
                    value.outcome in ("existing", "planned", "refused")
                    and value.effects
                ):
                    raise RepositoryPreparationValueError(
                        "unexpected_preparation_effects"
                    )
                return value
            except BaseException as error:
                raise provider.result_failure(
                    invocation if invocation is not None else request,
                    unvalidated_report(reported),
                ) from error
