"""Owner-defined iteration identity; portable content, not work admission."""

from dataclasses import dataclass, field

from .values import (
    SpecificationContractError,
    SpecificationIterationPlan,
    SpecificationSnapshot,
    canonical_phase_ref,
    digest,
    iteration_to_wire,
    member_key,
    phase_ref,
)

ITERATION_IDENTITY_CONTRACT = "aware.specification.iteration-plan-identity.v1"


def iteration_ref(owner_phase_ref: str, iteration_key: str) -> str:
    return (
        f"{canonical_phase_ref(owner_phase_ref, 'phase_ref')}/iteration:"
        f"{member_key(iteration_key, 'iteration_key')}"
    )


@dataclass(frozen=True, slots=True)
class SpecificationIterationIdentity:
    phase_ref: str
    plan: SpecificationIterationPlan
    iteration_ref: str = field(init=False)
    plan_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is not SpecificationIterationIdentity:
            raise SpecificationContractError("iteration identity type must be exact")
        canonical_phase_ref(self.phase_ref, "phase_ref")
        if type(self.plan) is not SpecificationIterationPlan:
            raise SpecificationContractError("iteration plan type must be exact")
        self.plan.__post_init__()
        ref = iteration_ref(self.phase_ref, self.plan.iteration_key)
        expected = digest(
            ITERATION_IDENTITY_CONTRACT,
            {"phase_ref": self.phase_ref, "plan": iteration_to_wire(self.plan)},
        )
        if getattr(self, "iteration_ref", ref) != ref:
            raise SpecificationContractError("iteration_ref mismatch")
        if getattr(self, "plan_digest", expected) != expected:
            raise SpecificationContractError("plan_digest mismatch")
        object.__setattr__(self, "iteration_ref", ref)
        object.__setattr__(self, "plan_digest", expected)


def resolve_iteration_identity(
    snapshot: SpecificationSnapshot, requested_ref: str
) -> SpecificationIterationIdentity:
    if type(snapshot) is not SpecificationSnapshot or type(requested_ref) is not str:
        raise SpecificationContractError("iteration resolution inputs must be exact")
    snapshot.__post_init__()
    for definition in snapshot.definitions:
        for phase in definition.phases:
            owner = phase_ref(definition.key, phase.phase_key)
            for plan in phase.iterations:
                if iteration_ref(owner, plan.iteration_key) == requested_ref:
                    return SpecificationIterationIdentity(owner, plan)
    raise SpecificationContractError("iteration is unavailable in the exact snapshot")
