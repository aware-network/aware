from __future__ import annotations

from typing import Any

from aware_meta_sdk.client import (
    MetaGeneratedApiClient,
    MetaGraphCallTarget,
    MetaSdkClient,
    MetaSdkError,
)

AwareMetaSdk = MetaSdkClient

_LAZY_EXPORTS = {
    "validate_compiler_identity_lanes_seeded": (
        "aware_meta_sdk.identity_lanes",
        "validate_compiler_identity_lanes_seeded",
    ),
    "OigCommitExpectation": (
        "aware_meta_sdk.ontology_proof",
        "OigCommitExpectation",
    ),
    "FunctionCallProof": (
        "aware_meta_sdk.ontology_proof",
        "FunctionCallProof",
    ),
    "FunctionCoverageSkip": (
        "aware_meta_sdk.ontology_proof",
        "FunctionCoverageSkip",
    ),
    "OntologyProofResult": (
        "aware_meta_sdk.ontology_proof",
        "OntologyProofResult",
    ),
    "OntologyProofReport": (
        "aware_meta_sdk.ontology_proof",
        "OntologyProofReport",
    ),
    "ProjectionBehaviorProof": (
        "aware_meta_sdk.ontology_proof",
        "ProjectionBehaviorProof",
    ),
    "ProjectionBehaviorProofReport": (
        "aware_meta_sdk.ontology_proof",
        "ProjectionBehaviorProofReport",
    ),
    "ProjectionBehaviorProofResult": (
        "aware_meta_sdk.ontology_proof",
        "ProjectionBehaviorProofResult",
    ),
    "ProjectionFunctionProofResult": (
        "aware_meta_sdk.ontology_proof",
        "ProjectionFunctionProofResult",
    ),
    "ProjectionProof": (
        "aware_meta_sdk.ontology_proof",
        "ProjectionProof",
    ),
    "ProjectionProofResult": (
        "aware_meta_sdk.ontology_proof",
        "ProjectionProofResult",
    ),
    "assert_oig_commit_matches": (
        "aware_meta_sdk.ontology_proof",
        "assert_oig_commit_matches",
    ),
    "prove_ontology_package": (
        "aware_meta_sdk.ontology_proof",
        "prove_ontology_package",
    ),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module 'aware_meta_sdk' has no attribute {name!r}")
    module_name, attr_name = target
    from importlib import import_module

    return getattr(import_module(module_name), attr_name)


__all__ = [
    "AwareMetaSdk",
    "FunctionCallProof",
    "FunctionCoverageSkip",
    "MetaGeneratedApiClient",
    "MetaGraphCallTarget",
    "MetaSdkClient",
    "MetaSdkError",
    "OigCommitExpectation",
    "OntologyProofReport",
    "OntologyProofResult",
    "ProjectionBehaviorProof",
    "ProjectionBehaviorProofReport",
    "ProjectionBehaviorProofResult",
    "ProjectionFunctionProofResult",
    "ProjectionProof",
    "ProjectionProofResult",
    "assert_oig_commit_matches",
    "prove_ontology_package",
    "validate_compiler_identity_lanes_seeded",
]
