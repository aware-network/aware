from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from uuid import UUID

from aware_meta_ontology.stable_ids import stable_function_config_id
from aware_ontology_service_dto.runtime.artifact_set import (
    OntologyRuntimeArtifactSet,
)


@dataclass(frozen=True, slots=True)
class EnvironmentProfileTopologyRuntimeCatalog:
    """Environment-owned coordinates for EnvironmentProfile topology install."""

    artifact_set_id: str
    package_name: str
    fqn_prefix: str
    environment_projection_hash: str
    environment_object_projection_graph_id: UUID
    environment_apply_profile_function_id: UUID
    environment_profile_config_projection_hash: str
    environment_profile_config_object_projection_graph_id: UUID
    profile_config_build_function_id: UUID
    profile_config_create_process_config_function_id: UUID
    environment_profile_projection_hash: str
    environment_profile_object_projection_graph_id: UUID
    profile_build_via_environment_function_id: UUID
    process_create_thread_config_function_id: UUID
    thread_add_object_projection_graph_function_id: UUID
    thread_add_layout_config_function_id: UUID
    layout_add_section_function_id: UUID

    @property
    def environment_create_profile_function_id(self) -> UUID:
        """Deprecated alias for pre-split Environment.create_profile consumers."""

        return self.environment_apply_profile_function_id

    @property
    def profile_create_process_config_function_id(self) -> UUID:
        """Deprecated alias for pre-split EnvironmentProfile topology consumers."""

        return self.profile_config_create_process_config_function_id


@dataclass(frozen=True, slots=True)
class _ProjectionCoordinates:
    projection_hash: str
    object_projection_graph_id: UUID


@dataclass(frozen=True, slots=True)
class _FunctionCoordinates:
    owner_key: str
    module_name: str
    class_name: str
    function_name: str


_ENVIRONMENT_APPLY_PROFILE = _FunctionCoordinates(
    owner_key="aware_environment.environment.Environment",
    module_name="aware_environment_ontology.environment.environment",
    class_name="Environment",
    function_name="apply_profile",
)
_PROFILE_CONFIG_BUILD = _FunctionCoordinates(
    owner_key="aware_environment.environment.EnvironmentProfileConfig",
    module_name="aware_environment_ontology.environment.environment_profile_config",
    class_name="EnvironmentProfileConfig",
    function_name="build_via_environment_config",
)
_PROFILE_CONFIG_CREATE_PROCESS_CONFIG = _FunctionCoordinates(
    owner_key="aware_environment.environment.EnvironmentProfileConfig",
    module_name="aware_environment_ontology.environment.environment_profile_config",
    class_name="EnvironmentProfileConfig",
    function_name="create_process_config",
)
_PROFILE_BUILD_VIA_ENVIRONMENT = _FunctionCoordinates(
    owner_key="aware_environment.environment.EnvironmentProfile",
    module_name="aware_environment_ontology.environment.environment_profile",
    class_name="EnvironmentProfile",
    function_name="build_via_environment",
)
_PROCESS_CREATE_THREAD_CONFIG = _FunctionCoordinates(
    owner_key="aware_environment.process.ProcessConfig",
    module_name="aware_environment_ontology.process.process_config",
    class_name="ProcessConfig",
    function_name="create_thread_config",
)
_THREAD_ADD_OBJECT_PROJECTION_GRAPH = _FunctionCoordinates(
    owner_key="aware_environment.thread.ThreadConfig",
    module_name="aware_environment_ontology.thread.thread_config",
    class_name="ThreadConfig",
    function_name="add_object_projection_graph",
)
_THREAD_ADD_LAYOUT_CONFIG = _FunctionCoordinates(
    owner_key="aware_environment.thread.ThreadConfig",
    module_name="aware_environment_ontology.thread.thread_config",
    class_name="ThreadConfig",
    function_name="add_layout_config",
)
_LAYOUT_ADD_SECTION = _FunctionCoordinates(
    owner_key="aware_environment.thread.ThreadConfigLayoutConfig",
    module_name="aware_environment_ontology.thread.thread_config_layout_config",
    class_name="ThreadConfigLayoutConfig",
    function_name="add_section",
)


def build_environment_profile_topology_runtime_catalog(
    *,
    artifact_set: OntologyRuntimeArtifactSet,
) -> EnvironmentProfileTopologyRuntimeCatalog:
    """Map an OntologyRuntimeArtifactSet DTO to Environment topology coordinates."""

    _require_environment_artifact_set(artifact_set)
    environment = _projection_coordinates(
        artifact_set=artifact_set,
        projection_name="Environment",
    )
    environment_profile = _projection_coordinates(
        artifact_set=artifact_set,
        projection_name="EnvironmentProfile",
    )
    environment_profile_config = _projection_coordinates(
        artifact_set=artifact_set,
        projection_name="EnvironmentProfileConfig",
    )
    return EnvironmentProfileTopologyRuntimeCatalog(
        artifact_set_id=artifact_set.artifact_set_id,
        package_name=artifact_set.package_name,
        fqn_prefix=artifact_set.fqn_prefix,
        environment_projection_hash=environment.projection_hash,
        environment_object_projection_graph_id=environment.object_projection_graph_id,
        environment_apply_profile_function_id=_function_id(_ENVIRONMENT_APPLY_PROFILE),
        environment_profile_config_projection_hash=(
            environment_profile_config.projection_hash
        ),
        environment_profile_config_object_projection_graph_id=(
            environment_profile_config.object_projection_graph_id
        ),
        profile_config_build_function_id=_function_id(_PROFILE_CONFIG_BUILD),
        profile_config_create_process_config_function_id=_function_id(
            _PROFILE_CONFIG_CREATE_PROCESS_CONFIG
        ),
        environment_profile_projection_hash=environment_profile.projection_hash,
        environment_profile_object_projection_graph_id=(
            environment_profile.object_projection_graph_id
        ),
        profile_build_via_environment_function_id=_function_id(
            _PROFILE_BUILD_VIA_ENVIRONMENT
        ),
        process_create_thread_config_function_id=_function_id(
            _PROCESS_CREATE_THREAD_CONFIG
        ),
        thread_add_object_projection_graph_function_id=_function_id(
            _THREAD_ADD_OBJECT_PROJECTION_GRAPH
        ),
        thread_add_layout_config_function_id=_function_id(_THREAD_ADD_LAYOUT_CONFIG),
        layout_add_section_function_id=_function_id(_LAYOUT_ADD_SECTION),
    )


def _require_environment_artifact_set(
    artifact_set: OntologyRuntimeArtifactSet,
) -> None:
    if artifact_set.fqn_prefix.strip() != "aware_environment":
        raise RuntimeError(
            "EnvironmentProfile topology install requires the Environment "
            "OntologyRuntimeArtifactSet DTO."
        )


def _projection_coordinates(
    *,
    artifact_set: OntologyRuntimeArtifactSet,
    projection_name: str,
) -> _ProjectionCoordinates:
    matches = [
        descriptor
        for descriptor in artifact_set.runtime_projection_descriptors
        if descriptor.projection_name.strip() == projection_name
    ]
    if not matches:
        raise RuntimeError(
            "Environment OntologyRuntimeArtifactSet does not expose projection "
            f"{projection_name!r}"
        )
    if len(matches) > 1:
        raise RuntimeError(
            "Environment OntologyRuntimeArtifactSet has ambiguous projection "
            f"{projection_name!r}"
        )
    descriptor = matches[0]
    projection_hash = (descriptor.projection_hash or "").strip()
    if not projection_hash:
        raise RuntimeError(
            "Environment OntologyRuntimeArtifactSet projection descriptor is "
            f"missing projection_hash for {projection_name!r}"
        )
    if descriptor.object_projection_graph_id is None:
        raise RuntimeError(
            "Environment OntologyRuntimeArtifactSet projection descriptor is "
            f"missing object_projection_graph_id for {projection_name!r}"
        )
    return _ProjectionCoordinates(
        projection_hash=projection_hash,
        object_projection_graph_id=descriptor.object_projection_graph_id,
    )


def _function_id(coordinates: _FunctionCoordinates) -> UUID:
    _assert_generated_function_declared(coordinates)
    return stable_function_config_id(
        owner_key=coordinates.owner_key,
        name=coordinates.function_name,
        kind="instance",
    )


def _assert_generated_function_declared(coordinates: _FunctionCoordinates) -> None:
    module = import_module(coordinates.module_name)
    functions = getattr(module, "FUNCTIONS", None)
    if not isinstance(functions, dict):
        raise RuntimeError(
            f"{coordinates.module_name} does not expose generated FUNCTIONS metadata"
        )
    class_functions = functions.get(coordinates.class_name)
    if not isinstance(class_functions, dict):
        raise RuntimeError(
            f"{coordinates.module_name} does not expose {coordinates.class_name} functions"
        )
    if coordinates.function_name not in class_functions:
        raise RuntimeError(
            "Generated Environment ontology metadata is missing function "
            f"{coordinates.class_name}.{coordinates.function_name}"
        )


__all__ = [
    "EnvironmentProfileTopologyRuntimeCatalog",
    "build_environment_profile_topology_runtime_catalog",
]
