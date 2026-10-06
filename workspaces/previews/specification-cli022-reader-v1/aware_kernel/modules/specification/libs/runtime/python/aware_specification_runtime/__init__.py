"""Public dependency-free Kernel Specification runtime."""

from .codec import (
    decode_phase_acceptance,
    decode_specification_snapshot,
    encode_phase_acceptance,
    encode_specification_snapshot,
)
from .iteration import (
    ITERATION_IDENTITY_CONTRACT,
    SpecificationIterationIdentity,
    iteration_ref,
    resolve_iteration_identity,
)
from .readiness import (
    SpecificationPhaseReadiness,
    SpecificationReadinessStatus,
    evaluate_specification_readiness,
)
from .transition import (
    SpecificationMovement,
    SpecificationMovementKind,
    SpecificationTransition,
    derive_specification_transition,
)
from .values import (
    PHASE_ACCEPTANCE_CONTRACT,
    SPECIFICATION_SNAPSHOT_CONTRACT,
    SpecificationContractError,
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationPlan,
    SpecificationPhaseAcceptance,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseDependencyKind,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    invariant_closure_digest,
    invariant_ref,
    phase_ref,
    specification_ref,
)

__all__ = [
    "ITERATION_IDENTITY_CONTRACT",
    "PHASE_ACCEPTANCE_CONTRACT",
    "SPECIFICATION_SNAPSHOT_CONTRACT",
    "SpecificationContractError",
    "SpecificationDefinition",
    "SpecificationInvariantDefinition",
    "SpecificationIterationIdentity",
    "SpecificationIterationPlan",
    "SpecificationMovement",
    "SpecificationMovementKind",
    "SpecificationPhaseAcceptance",
    "SpecificationPhaseDefinition",
    "SpecificationPhaseDependency",
    "SpecificationPhaseDependencyKind",
    "SpecificationPhaseGateDefinition",
    "SpecificationPhaseReadiness",
    "SpecificationReadinessStatus",
    "SpecificationSnapshot",
    "SpecificationTransition",
    "decode_phase_acceptance",
    "decode_specification_snapshot",
    "derive_specification_transition",
    "encode_phase_acceptance",
    "encode_specification_snapshot",
    "evaluate_specification_readiness",
    "invariant_closure_digest",
    "invariant_ref",
    "iteration_ref",
    "phase_ref",
    "resolve_iteration_identity",
    "specification_ref",
]
