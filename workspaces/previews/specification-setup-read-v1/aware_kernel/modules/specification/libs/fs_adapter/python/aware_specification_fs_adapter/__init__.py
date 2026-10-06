"""Strict filesystem adapter for canonical Aware Specifications."""

from .adapter import (
    SpecificationFsAdapter,
    adapt_specification_fs_roots,
    close_specification_fs_adapter,
    consume_specification_fs_adaptation,
    inspect_specification_fs_profile,
    install_specification_fs_adapter,
    lower_specification_fs_closures,
)
from .contracts import (
    SpecificationFsAdaptationResult,
    SpecificationFsAdapterError,
    SpecificationFsAdapterErrorKind,
    SpecificationFsLoweringResult,
    SpecificationFsObservationGrade,
    SpecificationFsProfileOutcome,
    SpecificationFsProfileOutcomeKind,
    SpecificationFsSchemaResolutionContext,
)

__all__ = [
    "SpecificationFsAdaptationResult",
    "SpecificationFsAdapter",
    "SpecificationFsAdapterError",
    "SpecificationFsAdapterErrorKind",
    "SpecificationFsLoweringResult",
    "SpecificationFsObservationGrade",
    "SpecificationFsProfileOutcome",
    "SpecificationFsProfileOutcomeKind",
    "SpecificationFsSchemaResolutionContext",
    "adapt_specification_fs_roots",
    "close_specification_fs_adapter",
    "consume_specification_fs_adaptation",
    "inspect_specification_fs_profile",
    "install_specification_fs_adapter",
    "lower_specification_fs_closures",
]
