"""Typed native-genesis document record; not authenticated creation authority."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import cast

from .native_creation_claims import (
    GENESIS_SCHEMA, NativeCreationClaimError,
    decode_native_creation_claim, make_native_creation_claim,
)


@dataclass(frozen=True, slots=True)
class GoalPhaseExecutionAuthorityV2:
    """Strict nested genesis provenance. Issuance verification is separate."""

    creation_intent_ref: str
    authority_ref: str = field(init=False)
    origin_profile: str = "native_genesis_v1"
    target_execution_authority_profile: str = "phase_native_operational_v1"
    legacy_execution_disposition: str = "not_applicable"
    schema_id: str = GENESIS_SCHEMA

    def __post_init__(self) -> None:
        if type(self) is not GoalPhaseExecutionAuthorityV2 or self.schema_id != GENESIS_SCHEMA:
            raise NativeCreationClaimError("genesis_execution_type_or_schema")
        claim = make_native_creation_claim(self.schema_id, self._body())
        object.__setattr__(self, "authority_ref", claim.reference)

    def _body(self) -> dict[str, object]:
        return {
            "origin_profile": self.origin_profile,
            "target_execution_authority_profile": self.target_execution_authority_profile,
            "legacy_execution_disposition": self.legacy_execution_disposition,
            "creation_intent_ref": self.creation_intent_ref,
        }

    def to_wire(self) -> dict[str, object]:
        if type(self) is not GoalPhaseExecutionAuthorityV2 or self.schema_id != GENESIS_SCHEMA:
            raise NativeCreationClaimError("genesis_execution_type_or_schema")
        # Validate the actual stored reference, without repairing a mutated record.
        return decode_native_creation_claim(json.dumps({
            "schema_id": self.schema_id, **self._body(), "authority_ref": self.authority_ref,
        })).to_wire()


def decode_goal_genesis_execution_authority(payload: str) -> GoalPhaseExecutionAuthorityV2:
    claim = decode_native_creation_claim(payload)
    body = claim.to_wire()
    if body["schema_id"] != GENESIS_SCHEMA:
        raise NativeCreationClaimError("genesis_execution_schema")
    return GoalPhaseExecutionAuthorityV2(
        creation_intent_ref=cast(str, body["creation_intent_ref"]),
        origin_profile=cast(str, body["origin_profile"]),
        target_execution_authority_profile=cast(str, body["target_execution_authority_profile"]),
        legacy_execution_disposition=cast(str, body["legacy_execution_disposition"]),
        schema_id=cast(str, body["schema_id"]),
    )
