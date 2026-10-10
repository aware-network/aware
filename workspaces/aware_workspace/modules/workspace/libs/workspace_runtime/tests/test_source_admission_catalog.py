from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticValueCoordinate,
)
from aware_code_semantic_contract_runtime.retained_input_projections import (
    CodeSemanticDeclarationTargetInventory,
)
from aware_environment_semantic_contract_runtime_provider.manifest_contracts import (
    MANIFEST_SOURCE_REF,
)
from aware_workspace_runtime.source_admission import (
    WorkspaceOwnerDefinedSourceAdmission,
    WorkspaceOwnerDefinedSourceAdmissionRuntime,
    WorkspaceOwnerDefinedSourceInspection,
)
from aware_workspace_runtime.source_admission_catalog import (
    derive_owner_defined_catalog_entry,
)
from owner_fixtures import inputs


def test_owner_defined_admission_is_nominal():
    try:
        WorkspaceOwnerDefinedSourceAdmission()
    except TypeError as error:
        assert "Workspace issues" in str(error)
    else:
        raise AssertionError("public source-admission construction succeeded")


def test_catalog_entry_is_mechanical_and_does_not_admit_catalog(monkeypatch):
    _, authority, _, _, package = inputs(paths=("aware/main.aware",))
    inventory = CodeSemanticDeclarationTargetInventory(
        package, ContentDigest.of_bytes(b"source"), ()
    )
    coordinate = SemanticValueCoordinate(
        "package_authority",
        SemanticContractRef("aware.code.portable-semantic-package-authority", "1", ContentDigest.of_bytes(b"codec")),
        "authority:fixture",
        authority.authority_digest,
        len(authority.canonical_bytes()),
    )
    inspection = WorkspaceOwnerDefinedSourceInspection(
        "repository:fixture",
        "consumer/aware.workspace.toml",
        "main",
        "example-environment",
        "modules/main/packages/example",
        "environment",
        "aware.environment.toml",
        ContentDigest.of_bytes(b"source"),
        package,
        MANIFEST_SOURCE_REF,
        "environment.authority",
        ("materialize",),
        ("package_authority",),
        False,
        authority,
        inventory,
        coordinate,
    )
    runtime = object.__new__(WorkspaceOwnerDefinedSourceAdmissionRuntime)
    admission = object.__new__(WorkspaceOwnerDefinedSourceAdmission)
    monkeypatch.setattr(
        WorkspaceOwnerDefinedSourceAdmissionRuntime,
        "inspect",
        lambda self, value: inspection if value is admission else None,
    )
    entry = derive_owner_defined_catalog_entry(runtime, admission)
    assert entry.package == package
    assert entry.manifest_contract == MANIFEST_SOURCE_REF
    assert entry.source_authority_ref == "authority:fixture"
    assert entry.participation_policy.admits(
        __import__("aware_code_semantic_contract_runtime").CodeSemanticMaterializationIntent.create(
            operation_kind="materialize",
            requested_semantic_root_refs=("home-story",),
            requested_terminal_output_roles=("package_authority",),
            semantic_configuration_coordinate=None,
        )
    )
