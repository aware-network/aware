"""Correlated source evidence, not repository or work authorization."""

from dataclasses import dataclass

from aware_specification_fs_adapter.lowering import root_set_digest
from aware_specification_fs_source_contract import SpecificationFsSourceClosure
from aware_specification_runtime import (
    SpecificationIterationIdentity,
    resolve_iteration_identity,
)
from aware_specification_sdk import (
    SpecificationObservation,
    SpecificationOperationError,
)

SOURCE_EVIDENCE_CONTRACT = "aware.specification.iteration-source-evidence.v1"


@dataclass(frozen=True, slots=True)
class SpecificationIterationSourceEvidence:
    """One issuer-observed horizon. Reconstructed values cannot replace admission."""

    identity: SpecificationIterationIdentity
    observation: SpecificationObservation
    source_base_identity: tuple[int, int, int]
    namespace_identity: tuple[int, int, int]
    closures: tuple[SpecificationFsSourceClosure, ...]
    contract: str = SOURCE_EVIDENCE_CONTRACT

    def __post_init__(self) -> None:
        try:
            if (
                type(self) is not SpecificationIterationSourceEvidence
                or type(self.identity) is not SpecificationIterationIdentity
                or type(self.observation) is not SpecificationObservation
                or type(self.contract) is not str
                or self.contract != SOURCE_EVIDENCE_CONTRACT
            ):
                raise ValueError("invalid evidence type")
            self.identity.__post_init__()
            self.observation.__post_init__()
            if (
                resolve_iteration_identity(
                    self.observation.snapshot, self.identity.iteration_ref
                )
                != self.identity
            ):
                raise ValueError("iteration and observation disagree")
            for coordinate in (self.source_base_identity, self.namespace_identity):
                if (
                    type(coordinate) is not tuple
                    or len(coordinate) != 3
                    or any(type(v) is not int or v < 0 for v in coordinate)
                ):
                    raise ValueError("invalid local source identity")
            if type(self.closures) is not tuple or not self.closures:
                raise ValueError("invalid closures")
            for closure in self.closures:
                if type(closure) is not SpecificationFsSourceClosure:
                    raise ValueError("invalid closure type")
                closure.__post_init__()
            roots = tuple(c.spec_root for c in self.closures)
            if roots != tuple(sorted(set(roots), key=lambda r: r.encode("utf-8"))):
                raise ValueError("invalid closure order")
            if root_set_digest(self.closures) != self.observation.source_digest:
                raise ValueError("source closure and observation disagree")
        except (AttributeError, TypeError, ValueError) as error:
            raise SpecificationOperationError(
                "invalid_iteration_source_evidence"
            ) from error
