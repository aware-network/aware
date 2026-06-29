from __future__ import annotations

import aware_code.semantic_contract as code_semantic_contract


def test_code_provider_uses_runtime_ontology_package_names() -> None:
    descriptors = code_semantic_contract.AWARE_CODE_SEMANTIC_CONTRACT.materialization_runtime_for(
        semantic_owner="aware_code.provider",
    )

    assert len(descriptors) == 1
    descriptor = descriptors[0]
    assert descriptor.runtime_ontology_package_names == ("code-ontology",)
    assert descriptor.lane_projection_name == "CodePackage"
    assert descriptor.required_projection_names == ("CodePackage",)
    assert descriptor.include_package_dependency_closure is True
