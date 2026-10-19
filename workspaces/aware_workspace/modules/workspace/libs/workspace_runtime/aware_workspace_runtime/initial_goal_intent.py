"""Original-provider explicit intent permission, separate from exact CAS work.

The intent is opaque canonical JSON. Goal owns its meaning. Physical retention
and source verification remain at the selected provider; neither historical
recovery nor a detached record restores a live permission.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aware_workspace_sdk.initial_authoring.goal_source import (
    InitialGoalSourceContext,
)
from aware_workspace_sdk.initial_authoring.goal_source import (
    _state as _source_state,
)
from aware_workspace_sdk.initial_authoring.values import _canonical


def validate_intent_payload(payload: object, key: object) -> tuple[bytes, str]:
    if (
        type(payload) is not bytes
        or not 0 < len(payload) <= 131072
        or type(key) is not str
        or re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}", key) is None
    ):
        raise ValueError("initial_goal_intent_input_invalid")
    try:
        value = json.loads(payload)
        if (
            type(value) is not dict
            or json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            != payload
        ):
            raise ValueError("initial_goal_intent_noncanonical")
    except (UnicodeError, RecursionError) as error:
        raise ValueError("initial_goal_intent_input_invalid") from error
    return payload, key


def _source(owner, context):
    owner._current()
    if (
        type(context) is not InitialGoalSourceContext
        or _source_state(context).owner is not owner
    ):
        raise ValueError("original_initial_goal_source_required")
    return context.require_current()


@dataclass(frozen=True)
class InitialGoalIntentState:
    owner: Any
    context: InitialGoalSourceContext
    payload: bytes
    key: str
    source_wire: bytes
    sealed: bytes
    pid: int
    provider_ref: str
    provider_generation: str
    deadline: float

    def pins(self):
        return (
            self.owner,
            self.context,
            self.payload,
            self.key,
            self.source_wire,
            self.sealed,
            self.pid,
            self.provider_ref,
            self.provider_generation,
            self.deadline,
        )

    def observe(self, *, current):
        self.owner._current()
        if (
            self.pid != os.getpid()
            or self.provider_ref != self.owner._provider_ref
            or self.provider_generation != self.owner._generation
            or _source_state(self.context).owner is not self.owner
        ):
            raise ValueError("initial_goal_intent_provider_changed")
        historical = json.loads(self.sealed)
        if current:
            if (
                time.monotonic() >= self.deadline
                or datetime.now(UTC) >= datetime.fromisoformat(historical["expires_at"])
                or datetime.now(UTC) < datetime.fromisoformat(historical["issued_at"])
            ):
                raise ValueError("initial_goal_intent_permission_expired")
            facts = _source(self.owner, self.context)
            if _canonical(facts) != self.source_wire:
                raise ValueError("initial_goal_intent_source_changed")
            result = self.owner._physical.observe_initial_goal_intent(
                self.context, self.payload, self.key
            )
            if _canonical(result) != self.sealed:
                raise ValueError("initial_goal_intent_retention_changed")
            if _canonical(_source(self.owner, self.context)) != self.source_wire:
                raise ValueError("initial_goal_intent_source_changed")
            if (
                time.monotonic() >= self.deadline
                or datetime.now(UTC) >= datetime.fromisoformat(historical["expires_at"])
                or datetime.now(UTC) < datetime.fromisoformat(historical["issued_at"])
            ):
                raise ValueError("initial_goal_intent_permission_expired")
        return historical


def authorize_initial_goal_intent(owner, context, payload, key):
    from aware_workspace_sdk.initial_authoring.goal_intent import (
        _claim,
        _issue,
        _retire_claim,
    )

    payload, key = validate_intent_payload(payload, key)
    facts = _source(owner, context)
    claim = _claim(owner, context, payload, key, facts)
    # The physical issuer provides UTC expiry; this earlier monotonic bound
    # prevents slow issuance or wall-clock rollback extending live permission.
    deadline = time.monotonic() + 300
    try:
        record = owner._physical.authorize_initial_goal_intent(claim)
    finally:
        _retire_claim(claim)
    return _issue(
        owner,
        InitialGoalIntentState(
            owner,
            context,
            payload,
            key,
            _canonical(facts),
            _canonical(record),
            os.getpid(),
            owner._provider_ref,
            owner._generation,
            deadline,
        ),
    )


def observe_initial_goal_intent(owner, context, payload, key):
    payload, key = validate_intent_payload(payload, key)
    facts = _source(owner, context)
    record = owner._physical.observe_initial_goal_intent(context, payload, key)
    if _canonical(_source(owner, context)) != _canonical(facts):
        raise ValueError("initial_goal_intent_source_changed")
    return record  # historical data only; never _issue() a live permission


from aware_workspace_sdk.initial_authoring.goal_intent import _STATE_TYPES

_STATE_TYPES.add(InitialGoalIntentState)
