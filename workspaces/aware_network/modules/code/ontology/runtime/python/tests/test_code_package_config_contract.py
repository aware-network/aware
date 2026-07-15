from __future__ import annotations

from _code_runtime_test_paths import source_text


def _source(path: str) -> str:
    return source_text(path)


def test_code_package_config_owns_package_contract_vocabulary() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package_config.aware"
    )

    assert "packages CodePackage[]" in source
    assert "instances CodePackage[]" not in source
    assert "inputs CodePackageConfigInput[]" in source
    assert "outputs CodePackageConfigOutput[]" in source
    assert "runtime_contexts CodePackageConfigRuntimeContext[]" in source
    assert "manifest_kind String" in source
    assert "manifest_filename String" in source
    assert "default_surface String?" in source
    assert "materialization_capability String?" in source
    assert "workspace_manifest_kind" not in source
    assert "JsonObject" not in source
    assert "JsonArray" not in source


def test_code_package_is_config_scoped_child_not_standalone_manifest_truth() -> None:
    source = _source("workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package.aware")

    assert "manifest_kind CodePackage" not in source
    assert "manifest_kind" not in source
    assert "ann package.CodePackage identity contained" in source
    assert "ann package.CodePackage identity standalone" not in source
    assert "Identity is config-scoped" in source
    assert (
        "Semantic package kind and manifest-kind truth live on CodePackageConfig"
        in source
    )
    assert "artifacts CodePackageArtifact[]" in source
    assert "fn attach_artifact(" in source
    assert "construct artifacts.build(" in source


def test_code_package_handler_uses_contained_constructor_block() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/runtime/python/aware_code/handlers/impl/package/code_package.py"
    )

    assert "async def build_via_code_package_config(" in source
    assert "# --- AWARE: LOGIC START build_via_code_package_config" in source
    assert "# --- AWARE: LOGIC START build\n" not in source


def test_code_package_config_contract_uses_typed_rows() -> None:
    enum_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package_enums.aware"
    )
    input_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package_config_input.aware"
    )
    output_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package_config_output.aware"
    )
    runtime_context_source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package_config_runtime_context.aware"
    )

    assert "enum CodePackageConfigInputKind" in enum_source
    assert "enum CodePackageConfigOutputKind" in enum_source
    assert "enum CodePackageArtifactStatus" in enum_source
    assert "enum CodePackageConfigRuntimeContextKind" in enum_source
    assert "kind CodePackageConfigInputKind" in input_source
    assert "kind CodePackageConfigOutputKind" in output_source
    assert "kind CodePackageConfigRuntimeContextKind" in runtime_context_source

    for source in (input_source, output_source, runtime_context_source):
        assert (
            "Workspace owns" in source
            or "Workspace-owned" in source
            or "outside Code" in source
        )
        assert "JsonObject" not in source
        assert "JsonArray" not in source


def test_code_package_artifact_is_package_owned_output_evidence() -> None:
    source = _source(
        "workspaces/aware_kernel/modules/code/ontology/structure/aware/package/code_package_artifact.aware"
    )

    assert "class CodePackageArtifact {" in source
    assert "class CodePackageArtifactRef : inline_value" in source
    assert "output_key String key" in source
    assert "artifact_key String key" in source
    assert "digest String?" in source
    assert "relative_path String?" in source
    assert "uri String?" in source
    assert "provider_payload JsonObject?" in source
    assert "receipt_payload JsonObject?" in source
    assert "workspace_revision_id" not in source
    assert "WorkspaceRevision id is never an identity input here" in source
