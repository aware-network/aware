"""Storage's authored migration selects an occurrence without inventing authority."""

import tomllib
from pathlib import Path
from shutil import copytree, ignore_patterns

import pytest
from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV3,
    decode_module_manifest_meaning,
    encode_module_manifest_meaning,
    parse_module_manifest,
)
from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
    derive_selected_participant_view,
)
from aware_code_semantic_contract_runtime import ContractViolation
from aware_workspace_runtime import SourceObservationUnavailable
from test_declaration_scope_admission import fixture

_REPOSITORY = Path(__file__).resolve().parents[7]
_STORAGE = _REPOSITORY / "workspaces/aware_kernel/modules/storage"


def test_storage_v3_preserves_legacy_module_meaning_and_package_slots():
    body = (_STORAGE / "aware.module.toml").read_bytes()
    value = parse_module_manifest(body)
    assert type(value) is AwareModuleSpecV3
    assert decode_module_manifest_meaning(encode_module_manifest_meaning(value)) == value
    # Strip only the new version and occurrence declaration: all historical
    # module options, package membership, manifests and exposure must survive.
    start = body.index(b"[packages.semantic_admission]")
    end = body.index(b"[[packages]]", start)
    legacy_body = (body[:start] + body[end:]).replace(b"aware = 3", b"aware = 1", 1)
    legacy = parse_module_manifest(legacy_body)
    for field in legacy.__dataclass_fields__:
        if field != "aware":
            assert getattr(value, field) == getattr(legacy, field)
    assert [(p.id, p.kind, p.manifest, p.visibility) for p in value.packages] == [
        ("ontology", "ontology", "ontology/aware.ontology.toml", "module"),
        ("storage_service_api", "api", "apis/storage/aware.api.toml", "module"),
        ("storage_sdk", "sdk", "sdks/storage/aware/aware.sdk.toml", "module"),
        ("storage_sdk_dart", "code", "sdks/storage/dart/aware_storage_sdk/pubspec.yaml", "module"),
        ("libs_data_plane_python", "code", "libs/data_plane/python/pyproject.toml", "module"),
    ]


def test_storage_occurrence_matches_existing_owner_manifests():
    value = parse_module_manifest((_STORAGE / "aware.module.toml").read_bytes())
    occurrence = value.package_declarations[0].occurrence
    outer = tomllib.loads((_STORAGE / "ontology/aware.ontology.toml").read_text())
    inner = tomllib.loads((_STORAGE / "ontology/structure/aware.toml").read_text())
    runtime = tomllib.loads((_STORAGE / "ontology/runtime/python/pyproject.toml").read_text())
    assert occurrence.semantic_package_name.value == outer["ontology"]["package_name"]
    assert occurrence.semantic_package_name.value == inner["package"]["package_name"]
    assert occurrence.semantic_version.value == str(outer["ontology"]["version_number"])
    assert occurrence.semantic_version.value == str(inner["package"]["version_number"])
    assert occurrence.code_package_name.value == runtime["project"]["name"]
    assert occurrence.code_package_name.value == outer["runtime"]["project_name"]
    assert occurrence.namespace.value == outer["ontology"]["fqn_prefix"]
    assert occurrence.namespace.value == inner["package"]["fqn_prefix"]
    assert not outer.get("dependencies") and not inner.get("dependencies")
    assert occurrence.dependency_targets.value == ()
    # No invented registration, root enumeration, source UUID or configuration.
    assert occurrence.registration.state == "unavailable"
    assert occurrence.owned_roots.state == "unavailable"
    assert occurrence.source_code_package_id.state == "absent"
    assert occurrence.configuration.state == "absent"
    assert all(not p.occurrence_declared for p in value.package_declarations[1:])


async def test_original_issuer_selects_storage_but_refuses_incomplete_provider(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        workspace = root / "workspaces/kernel/aware.workspace.toml"
        workspace.write_text(
            workspace.read_text()
            + '\n[[workspace.modules]]\nid="storage"\npath="modules/storage"\n'
        )
        copytree(
            _STORAGE, root / "workspaces/kernel/modules/storage",
            ignore=ignore_patterns(".venv", "__pycache__", ".aware"),
        )
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/kernel/aware.workspace.toml",
            expectation=expectation,
        )
        selected = issuer.inspect_exact_materialization_root(
            declaration, workspace_handle="Kernel", module_id="storage",
            package_id="ontology",
        )
        assert (selected.semantic_package_name, selected.semantic_version) == (
            "storage-ontology", "1",
        )
        with pytest.raises(SourceObservationUnavailable, match="occurrence_unavailable"):
            issuer.inspect_exact_materialization_root(
                declaration, workspace_handle="Kernel", module_id="storage",
                package_id="storage_sdk",
            )
        with pytest.raises(ContractViolation, match="selected v3 participant incomplete"):
            derive_selected_participant_view(
                issuer.read_declaration_scope(declaration),
                scope_key=selected.workspace_manifest_path,
                module_id=selected.module_id, package_id=selected.package_id,
            )
        module = root / "workspaces/kernel/modules/storage/aware.module.toml"
        module.write_bytes(module.read_bytes() + b"\n# after observation\n")
        with pytest.raises(SourceObservationUnavailable):
            issuer.inspect_exact_materialization_root(
                declaration, workspace_handle="Kernel", module_id="storage",
                package_id="ontology",
            )
