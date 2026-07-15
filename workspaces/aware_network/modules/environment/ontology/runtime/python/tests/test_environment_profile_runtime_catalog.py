from __future__ import annotations

from uuid import uuid4

import pytest

from aware_meta_ontology.stable_ids import stable_function_config_id
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSet,
    OntologyRuntimeArtifactSetProvenance,
    OntologyRuntimeProjectionDescriptor,
)
from aware_environment.environment.profile_runtime import (
    build_environment_profile_topology_runtime_catalog,
)


def _artifact_set() -> OntologyRuntimeArtifactSet:
    return OntologyRuntimeArtifactSet(
        artifact_set_id="environment-runtime",
        package_name="environment-ontology",
        fqn_prefix="aware_environment",
        runtime_projection_descriptors=[
            OntologyRuntimeProjectionDescriptor(
                projection_name="Environment",
                projection_hash="environment.hash",
                object_projection_graph_id=uuid4(),
            ),
            OntologyRuntimeProjectionDescriptor(
                projection_name="EnvironmentProfile",
                projection_hash="environment-profile.hash",
                object_projection_graph_id=uuid4(),
            ),
            OntologyRuntimeProjectionDescriptor(
                projection_name="EnvironmentProfileConfig",
                projection_hash="environment-profile-config.hash",
                object_projection_graph_id=uuid4(),
            ),
        ],
        provenance=OntologyRuntimeArtifactSetProvenance(),
    )


def test_environment_profile_catalog_uses_ontology_artifact_set_dto() -> None:
    artifact_set = _artifact_set()

    catalog = build_environment_profile_topology_runtime_catalog(
        artifact_set=artifact_set,
    )

    assert catalog.artifact_set_id == "environment-runtime"
    assert catalog.package_name == "environment-ontology"
    assert catalog.fqn_prefix == "aware_environment"
    assert catalog.environment_projection_hash == "environment.hash"
    assert catalog.environment_object_projection_graph_id == (
        artifact_set.runtime_projection_descriptors[0].object_projection_graph_id
    )
    assert catalog.environment_profile_projection_hash == "environment-profile.hash"
    assert (
        catalog.environment_profile_config_projection_hash
        == "environment-profile-config.hash"
    )
    assert catalog.environment_apply_profile_function_id == stable_function_config_id(
        owner_key="aware_environment.environment.Environment",
        name="apply_profile",
        kind="instance",
    )
    assert catalog.profile_config_build_function_id == (
        stable_function_config_id(
            owner_key="aware_environment.environment.EnvironmentProfileConfig",
            name="build_via_environment_config",
            kind="instance",
        )
    )
    assert catalog.profile_config_create_process_config_function_id == (
        stable_function_config_id(
            owner_key="aware_environment.environment.EnvironmentProfileConfig",
            name="create_process_config",
            kind="instance",
        )
    )
    assert catalog.profile_build_via_environment_function_id == (
        stable_function_config_id(
            owner_key="aware_environment.environment.EnvironmentProfile",
            name="build_via_environment",
            kind="instance",
        )
    )


def test_environment_profile_catalog_requires_environment_artifact_set() -> None:
    artifact_set = _artifact_set().model_copy(update={"fqn_prefix": "aware_identity"})

    with pytest.raises(RuntimeError, match="Environment OntologyRuntimeArtifactSet"):
        build_environment_profile_topology_runtime_catalog(artifact_set=artifact_set)
