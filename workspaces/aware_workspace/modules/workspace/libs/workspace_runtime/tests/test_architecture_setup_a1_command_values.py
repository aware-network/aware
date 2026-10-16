"""Original authored type lowering and closed owner-codec parity, not admission."""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

import pytest
from aware_issue_sdk import workspace_setup_admission_codec as ic
from aware_issue_sdk import workspace_setup_admission_values as i
from aware_language_parsed_document_contract import NEUTRAL_SYNTAX_IR_SCHEMA
from aware_meta_type_schema import (
    ScalarKind,
    TypeKind,
    TypeSchemaBundle,
    ValueShape,
    decode_schema_bundle,
    encode_schema_bundle,
    validate_typed_value,
)
from aware_meta_type_schema_aware_source import project_parsed_type_schema
from aware_workspace_command import architecture_setup_a1_command_values as c
from aware_workspace_sdk import architecture_setup_admission_codec as wc
from aware_workspace_sdk import architecture_setup_admission_values as w
from tree_sitter_aware.parsed_document import (
    TREE_SITTER_AWARE_PARSER_PROFILE,
    AwarePortableParseInput,
    AwareSemanticPackageProjectionRequest,
    parse_aware_document_batch,
)

ROOT = next(
    p for p in Path(__file__).resolve().parents if (p / "aware.repo.toml").exists()
)
WORKSPACE = ROOT / "workspaces/aware_workspace/modules/workspace/sdks/workspace/aware"
ISSUE = ROOT / "workspaces/aware_coordination/modules/workflow/sdks/issue/aware"
TABLES: tuple[tuple[str, Any, Any], ...] = (
    ("aware_workspace_sdk", w.SETUP_FIELD_TYPES, w.SETUP_ENUMS),
    ("aware_issue_sdk", i.ISSUE_SETUP_FIELD_TYPES, i.ISSUE_SETUP_ENUMS),
    ("aware_workspace_sdk", c._FIELD_TYPES, c._ENUMS),
)
ROWS: tuple[tuple[str, Any, Any], ...] = tuple(
    (ns, cls, rows) for ns, table, _ in TABLES for cls, rows in table.items()
)
TYPE_REFS: dict[str, str] = {
    cls.__name__: ns + "." + cls.__name__ for ns, cls, _ in ROWS
}


def digest(body):
    return "sha256:" + hashlib.sha256(body).hexdigest()


def project(base, pattern, names, *, omit=None):
    """Use the original parser and Meta projection with actual authored bytes."""
    body = (base / "aware.sdk.toml").read_bytes()
    manifest = tomllib.loads(body.decode())["sdk"]
    name, ns = manifest["package_name"], manifest["fqn_prefix"]
    ref = f"package:{name}@{manifest['version_number']}"
    sources = tuple(
        (p.name, p.read_bytes()) for p in sorted(base.glob(pattern)) if p.name != omit
    )
    batch = parse_aware_document_batch(
        tuple(
            AwarePortableParseInput(
                ref,
                name,
                "sdk/sources/" + path,
                "cas://" + digest(source),
                digest(source),
                len(source),
                source.decode(),
            )
            for path, source in sources
        )
    ).batch
    # Portable input coordinates are descriptive, not authenticated Workspace
    # occurrences or an original provider/operation enrollment.
    request = AwareSemanticPackageProjectionRequest.create(
        composition_authority_digest=digest(body),
        parent_operation_authority_digest=digest(body),
        package_ref=ref,
        package_name=name,
        package_kind="sdk",
        fqn_prefix=ns,
        semantic_version=str(manifest["version_number"]),
        package_root="sdk",
        sources_root="sdk/sources",
        manifest_path="sdk/aware.sdk.toml",
        manifest_ref="cas://" + digest(body),
        manifest_digest=digest(body),
        manifest_size_bytes=len(body),
        declared_source_paths=tuple("sdk/sources/" + path for path, _ in sources),
        direct_dependency_package_refs=(),
        dependency_package_refs=(),
        requested_root_refs=tuple(sorted(ns + "." + name for name in names)),
        source_lifecycle="genesis",
        parser_contract=NEUTRAL_SYNTAX_IR_SCHEMA,
        parser_profile=TREE_SITTER_AWARE_PARSER_PROFILE,
        parsed_batch_ref=batch.batch_ref,
    )
    return project_parsed_type_schema(request, batch)


def lower(*, omit=None):
    wp = project(
        WORKSPACE,
        "architecture_setup_admission_*.aware",
        [cls.__name__ for cls in (*w.SETUP_VALUE_TYPES, *c._TYPES)],
        omit=omit,
    )
    ip = project(
        ISSUE,
        "workspace_setup_admission_*.aware",
        [cls.__name__ for cls in i.ISSUE_SETUP_VALUE_TYPES],
        omit=omit,
    )
    # Preserve both original namespaces; no duplicate enums or copied Issue
    # class may replace a Workspace-owned definition in this joined data proof.
    bundle = TypeSchemaBundle.create(
        namespace="aware_workspace_sdk",
        semantic_version="1",
        types=tuple(row.definition for p in (wp, ip) for row in p.definitions),
    )
    return bundle, (wp, ip)


@pytest.fixture(scope="module")
def lowered():
    return lower()


def expected_shape(kind: str, ns: str) -> ValueShape:
    if kind.startswith("Nullable["):
        return expected_shape(kind[9:-1], ns)
    if kind.startswith("Array["):
        return ValueShape.list_of(expected_shape(kind[6:-1], ns))
    if kind == "Identity":
        return ValueShape.list_of(ValueShape.scalar(ScalarKind.INTEGER))
    if kind in ("Bool", "False"):
        return ValueShape.scalar(ScalarKind.BOOLEAN)
    if kind in ("U64", "I64"):
        return ValueShape.scalar(ScalarKind.INTEGER)
    if kind in (
        "Code",
        "Diagnostic",
        "Digest",
        "Ref",
        "RelativePath",
        "ResourcePath",
        "RootPath",
        "RequestText",
        "CommandContract",
    ):
        return ValueShape.scalar(ScalarKind.STRING)
    return ValueShape.named(TYPE_REFS.get(kind, ns + "." + kind))


@pytest.mark.parametrize("ns,cls,rows", ROWS, ids=[cls.__name__ for _, cls, _ in ROWS])
def test_original_lowering_preserves_every_owner_field_shape_and_required_null(
    lowered, ns, cls, rows
):
    bundle, _ = lowered
    definition = next(t for t in bundle.types if t.type_ref == ns + "." + cls.__name__)
    assert definition.kind is TypeKind.VALUE_OBJECT
    assert tuple(f.name for f in definition.fields) == tuple(name for name, _ in rows)
    for field, (_, kind) in zip(definition.fields, rows, strict=True):
        assert field.shape == expected_shape(kind, ns)
        assert field.required  # A nullable member is present with null, never omitted.
        assert field.nullable is kind.startswith("Nullable[")


def test_original_lowered_bundle_roundtrip_and_two_package_attribution(lowered):
    bundle, projections = lowered
    assert decode_schema_bundle(encode_schema_bundle(bundle)) == bundle
    assert len({t.type_ref for t in bundle.types}) == len(bundle.types)
    for projection in projections:
        refs = {r.type_ref for r in projection.definitions}
        attributed = {
            b.type_ref for a in projection.source_attributions for b in a.bindings
        }
        assert refs == attributed
        assert (
            all(t.startswith("aware_issue_sdk.") for t in refs)
            if "issue-sdk" in projection.package_ref
            else all(t.startswith("aware_workspace_sdk.") for t in refs)
        )
    assert {t.type_ref for t in bundle.types if t.name == "Phase"} == {
        "aware_issue_sdk.Phase",
        "aware_workspace_sdk.Phase",
    }


def test_all_original_enum_vocabularies_lower_without_cross_owner_substitution(lowered):
    bundle, _ = lowered
    definitions = {d.type_ref: d for d in bundle.types}
    for ns, _, enums in TABLES:
        for name, values in enums.items():
            if (
                name == "CommandContract"
            ):  # Exact wire constant is an owner-codec constraint.
                continue
            assert definitions[ns + "." + name].enum_values == tuple(values)


@pytest.mark.parametrize(
    "omitted",
    (
        "architecture_setup_admission_errors.aware",
        "architecture_setup_admission_ports.aware",
        "workspace_setup_admission_errors.aware",
        "workspace_setup_admission_ports.aware",
    ),
)
def test_missing_original_type_leaf_cannot_establish_complete_lowering(omitted):
    try:
        bundle, _ = lower(omit=omitted)
    except ValueError:
        return
    actual = {d.type_ref for d in bundle.types}
    assert set(TYPE_REFS.values()) - actual


def semantic(value: Any) -> Any:
    """Test-only view of decoded values; never a new wire decoder/provider."""
    if type(value).__name__ in TYPE_REFS:
        return {
            field.name: semantic(getattr(value, field.name)) for field in fields(value)
        }
    if type(value) is tuple:
        return [semantic(item) for item in value]
    return value


def issue_values(workspace: tuple[Any, ...]) -> tuple[Any, ...]:
    by_name = {type(item).__name__: item for item in workspace}
    failure, resource = (
        by_name["WorkspaceSetupPrimaryFailure"],
        by_name["WorkspaceSetupResourceEvidence"],
    )
    request = i.IssueWorkspaceSetupRequest(
        "docs/issues/2026/10/14/fb-2026-10-14-a1.md",
        digest(b"issue"),
        None,
        None,
        "intent:lowering",
        "workspace_setup_a1_v1",
        digest(b"authority"),
    )
    binding = i.IssueWorkspaceSetupBinding(
        "provider:issue",
        "generation:issue",
        "codex:lowering",
        request.issue_ref,
        request.expected_issue_source_sha256,
        "aware.protocol.toml",
        request.expected_authority_manifest_sha256,
        request.client_intent_id,
        by_name["WorkspaceSetupPlanBinding"],
        ("src/body.py",),
        "filesystem_harness_observed_v1",
        "declared_metadata_v1",
    )
    cleanup = i.IssueWorkspaceSetupCleanup(
        binding, "released", True, "confirmed", (), True, (resource,), failure
    )
    client = i.IssueWorkspaceSetupClientCleanup(
        "provider:issue",
        "generation:issue",
        "client:issue",
        (resource,),
        True,
        "confirmed",
        failure,
        (),
        True,
    )
    observation = i.IssueWorkspaceSetupObservation(
        binding, "spent", "consumption:issue", 0, (), True, (resource,), failure
    )
    source = i.IssueWorkspaceSetupSourcesObservation(
        request.issue_ref,
        "aware.protocol.toml",
        by_name["WorkspaceSetupFileObservation"],
        by_name["WorkspaceSetupFileObservation"],
        "codex:lowering",
        "filesystem_harness_observed_v1",
        "declared_metadata_v1",
        failure,
        True,
    )
    refusal = i.IssueWorkspaceSetupAdmissionRefusalEvidence(
        "refusal",
        None,
        binding,
        observation,
        by_name["WorkspaceAuthorizedSetupResult"],
        cleanup,
        failure,
        True,
        client,
    )
    return (request, binding, cleanup, client, observation, source, refusal)


@pytest.fixture(scope="module")
def values() -> tuple[Any, ...]:
    # Reuse original committed owner conformance vectors without constructing
    # alternate suppliers or converting detached records into live authority.
    import importlib.util

    path = WORKSPACE.parent / "python/public/tests/test_architecture_setup_admission.py"
    spec = importlib.util.spec_from_file_location("a1_original_owner_vectors", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workspace = module.vectors()
    issued = issue_values(workspace)
    by_name = {type(item).__name__: item for item in (*workspace, *issued)}
    request = c.WorkspaceSetupA1CommandRequest(
        by_name["ArchitectureSetupRequest"],
        by_name["IssueWorkspaceSetupRequest"],
        "/tmp/a1-authored-proof",
        "aware.protocol.toml",
        "docs/issues/2026/10/14/fb-2026-10-14-a1.md",
        "codex:lowering",
        "intent:lowering",
    )
    guards = c.WorkspaceSetupA1ReviewGuards(
        digest(b"issue"), digest(b"authority"), digest(b"plan")
    )
    cleanup = c.WorkspaceSetupA1ClientCleanup(
        by_name["IssueWorkspaceSetupClientCleanup"],
        by_name["WorkspaceSetupClientCleanup"],
    )
    report = c.WorkspaceSetupA1UnvalidatedReport(
        "issue", "wire:issue", "admission", "invalid"
    )
    evidence = c.WorkspaceSetupA1CommandEvidence(
        "aware.workspace.architecture-setup-a1-command.v1",
        "apply",
        "repository",
        "incomplete",
        False,
        request,
        guards,
        by_name["WorkspaceSetupPlanObservation"],
        by_name["IssueWorkspaceSetupSourcesObservation"],
        by_name["IssueWorkspaceSetupObservation"],
        by_name["WorkspaceAuthorizedSetupResult"],
        by_name["WorkspaceSetupPrimaryFailure"],
        by_name["WorkspaceSetupCleanup"],
        by_name["IssueWorkspaceSetupCleanup"],
        cleanup,
        (report,),
        (),
        True,
        False,
    )
    return (*workspace, *issued, request, guards, cleanup, report, evidence)


@pytest.mark.parametrize("ns,cls,_", ROWS, ids=[cls.__name__ for _, cls, _ in ROWS])
def test_original_owner_codec_roundtrip_matches_lowered_structural_value(
    lowered, values, ns, cls, _
):
    original = next(value for value in values if type(value) is cls)
    encode, decode = (
        (wc.setup_value_to_payload, wc.setup_value_from_payload)
        if cls in w.SETUP_VALUE_TYPES
        else (ic.issue_setup_value_to_payload, ic.issue_setup_value_from_payload)
        if cls in i.ISSUE_SETUP_VALUE_TYPES
        else (c.command_value_to_payload, c.command_value_from_payload)
    )
    decoded = decode(cls, encode(original))
    assert decoded == original and decoded is not original
    data = semantic(decoded)
    bundle, _ = lowered
    ref = ns + "." + cls.__name__
    assert validate_typed_value(bundle, ref, data).is_valid
    for name in data:
        assert not validate_typed_value(
            bundle, ref, {k: v for k, v in data.items() if k != name}
        ).is_valid
    assert not validate_typed_value(
        bundle, ref, {**data, "extra": "unrecognized"}
    ).is_valid


def test_structural_lowering_does_not_replace_domain_bounds_or_false_retry_guard(
    lowered, values
):
    bundle, _ = lowered
    request = next(v for v in values if type(v) is i.IssueWorkspaceSetupRequest)
    bad = replace(request, expected_issue_source_sha256="malformed")
    assert validate_typed_value(
        bundle, TYPE_REFS[type(bad).__name__], semantic(bad)
    ).is_valid
    with pytest.raises(ValueError):
        ic.issue_setup_value_to_payload(bad)
    evidence = next(v for v in values if type(v) is c.WorkspaceSetupA1CommandEvidence)
    bad = replace(evidence, authorizes_retry=True)
    assert validate_typed_value(
        bundle, TYPE_REFS[type(bad).__name__], semantic(bad)
    ).is_valid
    with pytest.raises(ValueError):
        c.command_value_to_payload(bad)
