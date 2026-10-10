from __future__ import annotations

import copy

import pytest
from aware_specification_fs_adapter import (
    SpecificationFsAdapterError,
    SpecificationFsAdapterErrorKind,
    SpecificationFsProfileOutcome,
    SpecificationFsProfileOutcomeKind,
    SpecificationFsSchemaResolutionContext,
)


def test_schema_context_is_exact_and_reconstructable() -> None:
    value = SpecificationFsSchemaResolutionContext()
    assert value.context_digest.startswith("sha256:")
    assert copy.copy(value) == value
    value.__post_init__()


def test_profile_outcome_digest_and_error_grammar() -> None:
    outcome = SpecificationFsProfileOutcome(
        "specs/example",
        SpecificationFsProfileOutcomeKind.MALFORMED_V1,
        "malformed_specification_fs_v1",
    )
    error = SpecificationFsAdapterError(
        SpecificationFsAdapterErrorKind.PROFILE,
        "noncanonical_specification_profile",
        spec_root="specs/example",
        profile_outcome=outcome,
    )
    assert error.args == ("noncanonical_specification_profile",)
    with pytest.raises(TypeError):
        SpecificationFsAdapterError(SpecificationFsAdapterErrorKind.INPUT, "unknown")
