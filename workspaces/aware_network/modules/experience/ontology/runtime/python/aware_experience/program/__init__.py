from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from aware_experience.compiler.models import ProgramOwnershipRecord
    from aware_experience.program.action_continuation import (
        ProgramActionContinuationContract,
        ProgramActionContinuationError,
        ProgramActionContinuationFieldBinding,
        ProgramActionContinuationReceiptFieldBinding,
        ProgramActionContinuationResult,
        ProgramActionContinuationTargetValues,
    )
    from aware_experience.program.action_continuation_graph import (
        ProgramActionContinuationActivationFieldBinding,
        ProgramActionContinuationActivationInput,
        ProgramActionContinuationCompositeResult,
        ProgramActionContinuationGraphError,
        ProgramActionContinuationGraphResult,
        ProgramActionContinuationGraphStep,
        ProgramActionContinuationOutcomeSource,
    )
    from aware_experience.program.contracts import ProgramRunIdentity
    from aware_experience.program.loader import AwareProgramsTomlError
    from aware_experience.program.registry_index import (
        ProgramAssetRef,
        ProgramRegistryError,
        ProgramRegistryIndex,
    )
    from aware_experience.program.service import ExperienceProgramRuntimeService
    from aware_experience.program.turn_semantics import (
        DefaultProgramTurnSemanticsPolicy,
        ProgramTurnDecision,
        ProgramTurnDecisionContext,
        ProgramTurnSemanticsPolicy,
        ProgramTurnTransition,
    )


def load_program_ownership_from_sources(
    *, package_root: Path, source_files: list[Path]
) -> list[ProgramOwnershipRecord]:
    from aware_experience.program.compiler import (
        load_program_ownership_from_sources as _impl,
    )

    return _impl(package_root=package_root, source_files=source_files)


def resolve_program_run_id(*args: object, **kwargs: object) -> object:
    from aware_experience.program.stable_ids import resolve_program_run_id as _impl

    return _impl(*args, **kwargs)


def load_aware_programs_toml_spec(*args: object, **kwargs: object) -> object:
    from aware_experience.program.loader import load_aware_programs_toml_spec as _impl

    return _impl(*args, **kwargs)


def load_aware_programs_toml_spec_from_text(*args: object, **kwargs: object) -> object:
    from aware_experience.program.loader import (
        load_aware_programs_toml_spec_from_text as _impl,
    )

    return _impl(*args, **kwargs)


def __getattr__(name: str) -> object:
    if name in {
        "ProgramActionContinuationContract",
        "ProgramActionContinuationError",
        "ProgramActionContinuationFieldBinding",
        "ProgramActionContinuationReceiptFieldBinding",
        "ProgramActionContinuationResult",
        "ProgramActionContinuationTargetValues",
        "compose_program_action_continuation",
    }:
        from aware_experience.program import action_continuation

        return getattr(action_continuation, name)
    if name in {
        "ProgramActionContinuationActivationFieldBinding",
        "ProgramActionContinuationActivationInput",
        "ProgramActionContinuationCompositeResult",
        "ProgramActionContinuationGraphError",
        "ProgramActionContinuationGraphResult",
        "ProgramActionContinuationGraphStep",
        "ProgramActionContinuationOutcomeSource",
        "execute_program_action_continuation_graph",
    }:
        from aware_experience.program import action_continuation_graph

        return getattr(action_continuation_graph, name)
    if name == "AwareProgramsTomlError":
        from aware_experience.program.loader import AwareProgramsTomlError

        return AwareProgramsTomlError
    if name == "ProgramAssetRef":
        from aware_experience.program.registry_index import ProgramAssetRef

        return ProgramAssetRef
    if name == "ProgramRegistryError":
        from aware_experience.program.registry_index import ProgramRegistryError

        return ProgramRegistryError
    if name == "ProgramRegistryIndex":
        from aware_experience.program.registry_index import ProgramRegistryIndex

        return ProgramRegistryIndex
    if name == "ExperienceProgramRuntimeService":
        from aware_experience.program.service import ExperienceProgramRuntimeService

        return ExperienceProgramRuntimeService
    if name == "ProgramRunIdentity":
        from aware_experience.program.contracts import ProgramRunIdentity

        return ProgramRunIdentity
    if name == "DefaultProgramTurnSemanticsPolicy":
        from aware_experience.program.turn_semantics import (
            DefaultProgramTurnSemanticsPolicy,
        )

        return DefaultProgramTurnSemanticsPolicy
    if name == "ProgramTurnDecision":
        from aware_experience.program.turn_semantics import ProgramTurnDecision

        return ProgramTurnDecision
    if name == "ProgramTurnDecisionContext":
        from aware_experience.program.turn_semantics import (
            ProgramTurnDecisionContext,
        )

        return ProgramTurnDecisionContext
    if name == "ProgramTurnSemanticsPolicy":
        from aware_experience.program.turn_semantics import ProgramTurnSemanticsPolicy

        return ProgramTurnSemanticsPolicy
    if name == "ProgramTurnTransition":
        from aware_experience.program.turn_semantics import ProgramTurnTransition

        return ProgramTurnTransition
    raise AttributeError(name)


__all__ = [
    "AwareProgramsTomlError",
    "DefaultProgramTurnSemanticsPolicy",
    "ExperienceProgramRuntimeService",
    "load_program_ownership_from_sources",
    "load_aware_programs_toml_spec",
    "load_aware_programs_toml_spec_from_text",
    "ProgramAssetRef",
    "ProgramActionContinuationContract",
    "ProgramActionContinuationError",
    "ProgramActionContinuationFieldBinding",
    "ProgramActionContinuationReceiptFieldBinding",
    "ProgramActionContinuationResult",
    "ProgramActionContinuationTargetValues",
    "ProgramActionContinuationActivationFieldBinding",
    "ProgramActionContinuationActivationInput",
    "ProgramActionContinuationCompositeResult",
    "ProgramActionContinuationGraphError",
    "ProgramActionContinuationGraphResult",
    "ProgramActionContinuationGraphStep",
    "ProgramActionContinuationOutcomeSource",
    "ProgramRegistryError",
    "ProgramRegistryIndex",
    "ProgramRunIdentity",
    "ProgramTurnTransition",
    "ProgramTurnDecision",
    "ProgramTurnDecisionContext",
    "ProgramTurnSemanticsPolicy",
    "compose_program_action_continuation",
    "execute_program_action_continuation_graph",
    "resolve_program_run_id",
]
