"""Portable private-stage plans declare meaning without granting child use."""

from __future__ import annotations

import copy
import json
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
    SemanticConfigurationCoordinate,
    SemanticContractRef,
    SemanticImplementationCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime.private_stage_contract import (
    CodePrivateStagePlanV1,
    PrivateStageBarrier,
    PrivateStageEntry,
    PrivateStageProfileIdentity,
    PrivateStageRoleContract,
    decode_private_stage_plan,
    encode_private_stage_plan,
)


def _digest(marker: str) -> ContentDigest:
    return ContentDigest("sha256:" + marker * 64)


def _contract(key: str, marker: str) -> SemanticContractRef:
    return SemanticContractRef(key, "1", _digest(marker))


def _plan() -> CodePrivateStagePlanV1:
    private_profile = PrivateStageProfileIdentity("meta.profile", "1", _digest("a"))
    public_profile = PrivateStageProfileIdentity("ontology.profile", "1", _digest("b"))
    candidate = PrivateStageRoleContract("candidate", _contract("candidate.contract", "c"))
    committed = PrivateStageRoleContract("committed", _contract("committed.contract", "d"))
    private = PrivateStageEntry(
        "meta", "private", "meta.provider", private_profile,
        SemanticImplementationCoordinate("meta.impl", _digest("e")),
        SemanticConfigurationCoordinate("meta.config", _digest("f")),
        (), candidate,
    )
    terminal = PrivateStageEntry(
        "ontology", "public_terminal", "ontology.provider", public_profile,
        SemanticImplementationCoordinate("ontology.impl", _digest("1")),
        SemanticConfigurationCoordinate("ontology.config", _digest("2")),
        (PrivateStageRoleContract("committed_input", committed.contract),),
        PrivateStageRoleContract("preparation", _contract("preparation.contract", "3")),
    )
    barrier = PrivateStageBarrier(
        "committed_product", "meta", "ontology", candidate, committed,
        "committed_input",
    )
    return CodePrivateStagePlanV1(1, public_profile, (private, terminal), barrier)


def test_round_trip_and_exact_canonical_digest() -> None:
    plan = _plan()
    body = encode_private_stage_plan(plan)
    decoded = decode_private_stage_plan(body)
    assert decoded == plan
    assert decoded is not plan
    assert decoded.digest == ContentDigest.of_bytes(body)
    assert body == canonical_json_bytes(plan.to_wire())
    assert decoded.stages[0].terminal.contract != decoded.barrier.committed_product.contract


def test_candidate_cannot_be_relabelled_as_committed_product() -> None:
    plan = _plan()
    with pytest.raises(ContractViolation):
        replace(plan.barrier, committed_product=plan.barrier.candidate)
    with pytest.raises(ContractViolation):
        replace(
            plan.barrier,
            committed_product=replace(
                plan.barrier.committed_product,
                contract=plan.barrier.candidate.contract,
            ),
        )
    with pytest.raises(ContractViolation):
        replace(
            plan,
            barrier=replace(
                plan.barrier,
                committed_product=replace(
                    plan.barrier.committed_product,
                    contract=_contract("other.contract", "4"),
                ),
            ),
        )


def test_stage_order_profile_and_barrier_correlation_reject() -> None:
    plan = _plan()
    with pytest.raises(ContractViolation):
        replace(plan, stages=(plan.stages[1], plan.stages[0]))
    with pytest.raises(ContractViolation):
        replace(plan, public_profile=plan.stages[0].profile)
    with pytest.raises(ContractViolation):
        replace(
            plan,
            stages=(
                replace(plan.stages[0], provider_key=plan.stages[1].provider_key),
                plan.stages[1],
            ),
        )
    with pytest.raises(ContractViolation):
        replace(plan, barrier=replace(plan.barrier, after_stage="other"))
    with pytest.raises(ContractViolation):
        replace(plan, barrier=replace(plan.barrier, candidate=replace(
            plan.barrier.candidate, contract=_contract("other.contract", "4")
        )))


def test_decoder_rejects_noncanonical_duplicate_and_extra_fields() -> None:
    body = encode_private_stage_plan(_plan())
    with pytest.raises(ContractViolation):
        decode_private_stage_plan(b" " + body)
    with pytest.raises(ContractViolation):
        decode_private_stage_plan(body.replace(b'"version":1}', b'"version":1,"version":1}'))
    wire = json.loads(body)
    wire["authority"] = True
    with pytest.raises(ContractViolation):
        decode_private_stage_plan(canonical_json_bytes(wire))
    with pytest.raises(ContractViolation):
        decode_private_stage_plan(body + b"\n")


def test_bounds_and_mutated_frozen_values_reject_on_use() -> None:
    plan = _plan()
    with pytest.raises(ContractViolation):
        replace(plan.stages[0], provider_key="x" * 193)
    with pytest.raises(ContractViolation):
        replace(plan.stages[0], provider_key="e\u0301")
    with pytest.raises(ContractViolation):
        replace(plan.stages[0], inputs=tuple(
            PrivateStageRoleContract(f"r{i:03}", _contract("input.contract", "5"))
            for i in range(65)
        ))
    long_contract = SemanticContractRef("k" * 192, "v" * 192, _digest("5"))
    long_inputs = tuple(
        PrivateStageRoleContract(f"r{i:03}" + "x" * 188, long_contract)
        for i in range(63)
    )
    with pytest.raises(ContractViolation, match="canonical byte bound"):
        replace(
            plan,
            stages=(
                replace(plan.stages[0], inputs=long_inputs),
                replace(
                    plan.stages[1],
                    inputs=(plan.stages[1].inputs[0], *long_inputs),
                ),
            ),
        )
    forged = copy.copy(plan)
    object.__setattr__(forged.barrier, "before_stage", "wrong")
    with pytest.raises(ContractViolation):
        encode_private_stage_plan(forged)
