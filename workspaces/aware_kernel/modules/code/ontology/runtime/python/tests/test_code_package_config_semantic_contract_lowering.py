from __future__ import annotations

from aware_code.module_semantic_contract import (
    ModuleSemanticContract,
    ModuleSemanticManifestResolutionDescriptor,
    ModuleSemanticMaterializationArtifactOutputDescriptor,
    ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor,
    ModuleSemanticMaterializationPackageOutputDescriptor,
    ModuleSemanticMaterializationRuntimeContextDescriptor,
    ModuleSemanticMaterializationRuntimeDescriptor,
)
from aware_code.semantic_contract_config import (
    PACKAGE_MANAGER_CODE_PACKAGE_SURFACE,
    PACKAGE_MANAGER_PYPROJECT_MANIFEST_KIND,
    build_code_package_config_from_semantic_contract,
    code_package_config_descriptor_from_manifest_resolution_descriptor,
    code_package_config_ref_from_manifest_resolution_descriptor,
    package_manager_pyproject_code_package_config_ref,
    source_code_package_config_descriptor,
)
from aware_code.semantic_materialization import SEMANTIC_MATERIALIZATION_CAPABILITY
from aware_code.semantic_package.schemas import CapabilityParticipationDescriptor
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_code_ontology.package.code_package_enums import (
    CodePackageConfigOutputKind,
    CodePackageConfigRuntimeContextKind,
)


_FAKE_PROVIDER_KEY = "aware_fake"
_FAKE_OWNER = "aware_fake.provider"
_FAKE_MANIFEST_RESOLUTION = ModuleSemanticManifestResolutionDescriptor(
    semantic_owner=_FAKE_OWNER,
    manifest_kind="aware_fake_toml",
    filename="aware.fake.toml",
    contract="aware.fake",
    loader_module="aware_fake.manifest.loader",
    loader_name="load_aware_fake_toml_spec",
    workspace_manifest_kind="fake",
    package_role=_FAKE_OWNER,
    semantic_package_family="fake",
    semantic_package_kind="fake_package",
    semantic_projection_name="FakePackage",
    semantic_root_kind="fake",
    code_package_surface="fake",
    workspace_materialization_order=50,
    workspace_materialization_branch="semantic",
    workspace_materialization_commit=True,
    workspace_materialization_primary=True,
)
_FAKE_SEMANTIC_CONTRACT = ModuleSemanticContract(
    provider_key=_FAKE_PROVIDER_KEY,
    capability_participation=(
        CapabilityParticipationDescriptor(
            capability=SEMANTIC_MATERIALIZATION_CAPABILITY,
            semantic_owner=_FAKE_OWNER,
        ),
    ),
    manifest_resolution=(_FAKE_MANIFEST_RESOLUTION,),
    materialization_artifact_outputs=(
        ModuleSemanticMaterializationArtifactOutputDescriptor(
            semantic_owner=_FAKE_OWNER,
            producer_key="fake.runtime",
            output_key="fake.runtime_artifact",
            artifact_family="fake_runtime",
            artifact_role="runtime",
        ),
    ),
    materialization_code_package_delta_outputs=(
        ModuleSemanticMaterializationCodePackageDeltaOutputDescriptor(
            semantic_owner=_FAKE_OWNER,
            producer_key="fake.delta",
            output_key="fake.code_package_delta",
        ),
    ),
    materialization_package_outputs=(
        ModuleSemanticMaterializationPackageOutputDescriptor(
            semantic_owner=_FAKE_OWNER,
            producer_key="fake.package",
            output_key="fake.package_output",
            target_provider_key="aware_target",
            target_input_key="aware_target.input",
            target_semantic_owner="aware_target.provider",
            target_package_family="target",
            target_semantic_kind="target_package",
        ),
    ),
    materialization_runtime=(
        ModuleSemanticMaterializationRuntimeDescriptor(
            semantic_owner=_FAKE_OWNER,
            runtime_ontology_package_names=("fake-ontology",),
            lane_projection_name="FakePackage",
            required_projection_names=("CodePackage",),
            environment_handle="fake-environment",
        ),
    ),
    materialization_runtime_context=(
        ModuleSemanticMaterializationRuntimeContextDescriptor(
            semantic_owner=_FAKE_OWNER,
            callable_module="aware_fake.runtime_context",
            callable_name="build_fake_context",
            required=True,
        ),
    ),
)


def test_fake_semantic_contract_lowers_to_code_package_config_rows() -> None:
    config = build_code_package_config_from_semantic_contract(
        contract=_FAKE_SEMANTIC_CONTRACT,
        manifest_resolution=_FAKE_MANIFEST_RESOLUTION,
    )

    expected_key = code_package_source_config_key(
        manifest_kind="aware_fake_toml",
        surface="fake",
    )
    assert config.id == stable_code_package_config_id(config_key=expected_key)
    assert config.config_key == expected_key
    assert config.provider_key == _FAKE_PROVIDER_KEY
    assert config.semantic_owner == _FAKE_OWNER
    assert config.contract == "aware.fake"
    assert config.manifest_kind == "aware_fake_toml"
    assert config.manifest_filename == "aware.fake.toml"
    assert config.semantic_package_family == "fake"
    assert config.semantic_package_kind == "fake_package"
    assert config.semantic_projection_name == "FakePackage"
    assert config.semantic_root_kind == "fake"
    assert config.default_surface == "fake"
    assert config.materialization_capability == SEMANTIC_MATERIALIZATION_CAPABILITY

    outputs_by_key = {row.output_key: row for row in config.outputs}
    assert outputs_by_key["fake.runtime_artifact"].kind == (
        CodePackageConfigOutputKind.artifact
    )
    assert outputs_by_key["fake.runtime_artifact"].artifact_family == "fake_runtime"
    assert outputs_by_key["fake.code_package_delta"].kind == (
        CodePackageConfigOutputKind.code_package_delta
    )
    assert outputs_by_key["fake.package_output"].kind == (
        CodePackageConfigOutputKind.package
    )
    assert outputs_by_key["fake.package_output"].target_provider_key == "aware_target"

    runtime_by_key = {row.context_key: row for row in config.runtime_contexts}
    assert runtime_by_key["ontology_package:fake-ontology"].kind == (
        CodePackageConfigRuntimeContextKind.ontology_package
    )
    assert runtime_by_key["lane_projection:FakePackage"].projection_name == (
        "FakePackage"
    )
    assert runtime_by_key["projection:CodePackage"].kind == (
        CodePackageConfigRuntimeContextKind.projection
    )
    assert runtime_by_key["environment:fake-environment"].kind == (
        CodePackageConfigRuntimeContextKind.environment
    )
    assert (
        runtime_by_key["runtime_context:aware_fake.runtime_context.build_fake_context"].kind
        == CodePackageConfigRuntimeContextKind.execution_context
    )


def test_code_package_config_does_not_lower_workspace_selector_fields() -> None:
    config = build_code_package_config_from_semantic_contract(
        contract=_FAKE_SEMANTIC_CONTRACT,
        manifest_resolution=_FAKE_MANIFEST_RESOLUTION,
    )

    payload = config.model_dump(mode="json")
    assert "workspace_manifest_kind" not in payload
    assert "workspace_materialization_order" not in payload
    assert "workspace_materialization_branch" not in payload
    assert "workspace_materialization_commit" not in payload
    assert "workspace_materialization_primary" not in payload


def test_manifest_resolution_descriptor_config_ref_is_stable() -> None:
    ref = code_package_config_ref_from_manifest_resolution_descriptor(
        descriptor=_FAKE_MANIFEST_RESOLUTION,
    )

    assert ref.config_key == "source:aware_fake_toml:fake"
    assert ref.config_id == stable_code_package_config_id(config_key=ref.config_key)
    assert ref.manifest_kind == "aware_fake_toml"
    assert ref.surface == "fake"


def test_manifest_resolution_descriptor_is_code_package_config_authority() -> None:
    descriptor = code_package_config_descriptor_from_manifest_resolution_descriptor(
        provider_key=_FAKE_SEMANTIC_CONTRACT.provider_key,
        descriptor=_FAKE_MANIFEST_RESOLUTION,
        semantic_contract=_FAKE_SEMANTIC_CONTRACT,
    )

    assert descriptor.provider_key == _FAKE_PROVIDER_KEY
    assert descriptor.semantic_owner == _FAKE_OWNER
    assert descriptor.package_role == _FAKE_MANIFEST_RESOLUTION.package_role
    assert descriptor.ref.config_key == "source:aware_fake_toml:fake"
    assert descriptor.manifest_filename == "aware.fake.toml"
    assert descriptor.semantic_package_family == "fake"
    assert descriptor.semantic_package_kind == "fake_package"
    assert descriptor.semantic_projection_name == "FakePackage"
    assert descriptor.semantic_root_kind == "fake"
    assert descriptor.materialization_capability == SEMANTIC_MATERIALIZATION_CAPABILITY


def test_source_code_package_config_descriptor_covers_code_defaults() -> None:
    descriptor = source_code_package_config_descriptor(
        manifest_kind="pyproject_toml",
        surface="runtime",
    )

    assert descriptor.provider_key == "aware_code"
    assert descriptor.semantic_owner == "aware_code.provider"
    assert descriptor.package_role == "aware_code.provider"
    assert descriptor.ref.config_key == "source:pyproject_toml:runtime"
    assert descriptor.manifest_filename == "pyproject.toml"
    assert descriptor.semantic_package_family == "code"
    assert descriptor.semantic_package_kind == "code_package"
    assert descriptor.semantic_projection_name == "CodePackage"


def test_package_manager_pyproject_config_ref_is_manifest_only() -> None:
    ref = package_manager_pyproject_code_package_config_ref()

    expected_key = code_package_source_config_key(
        manifest_kind=PACKAGE_MANAGER_PYPROJECT_MANIFEST_KIND,
        surface=PACKAGE_MANAGER_CODE_PACKAGE_SURFACE,
    )
    assert ref.config_key == expected_key
    assert ref.config_id == stable_code_package_config_id(config_key=expected_key)
    assert ref.manifest_kind == PACKAGE_MANAGER_PYPROJECT_MANIFEST_KIND
    assert ref.surface == PACKAGE_MANAGER_CODE_PACKAGE_SURFACE
