"""Explicit isolated fixtures: no Code bootstrap or namespace entitlement proof."""

import copy
import os
from contextlib import asynccontextmanager
from dataclasses import replace

import pytest
from aware_code_semantic_contract_runtime import (
    ContentDigest,
    SemanticContractRef,
    SemanticValueCoordinate,
    encode_semantic_candidate_listing,
)
from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
    RetainedSemanticAdmissionExpectation,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DECLARATION_TARGET_INVENTORY_REF,
    PACKAGE_CONTEXT_INPUT_REF,
    encode_declaration_target_inventory,
    encode_package_context_input,
)
from aware_code_semantic_contract_runtime.semantic_candidates import (
    SEMANTIC_CANDIDATE_LISTING_REF,
)
from aware_workspace_runtime import (
    SourceObservationUnavailable,
    WorkspaceObservedSemanticIssuerRuntime,
    WorkspacePackageContextAdmission,
)
from test_observed_membership import fixture

PROVIDER = """
[[plugins]]
kind="code.module_plugin"
provider_key="demo"
[[packages]]
id="provider"
kind="code"
manifest="provider/pyproject.toml"
[packages.semantic_contract]
role="demo.provider"
contract="aware.semantic_provider"
provider_key="demo"
module="demo.provider"
owns_manifest_kinds=["example_toml"]
capabilities=["materialize"]
[[packages.semantic_contract.registrations]]
key="example"
manifest_contract_kind="example_toml"
manifest_filename="aware.example.toml"
semantic_package_family="example"
semantic_package_kind="example"
semantic_contract={role="example",name="example",provider_key="demo",coordinate="contract:example"}
supported_languages=["aware"]
code_package_surface={state="absent"}
profiles=[
 {stage="authority_derivation",profile_ref="example.authority",profile_version="1",profile_digest="sha256:HASH"},
 {stage="source_planning",profile_ref="example.planning",profile_version="1",profile_digest="sha256:HASH"}
]
""".replace("HASH", "a" * 64)


def occurrence(name, mappings="[]"):
    return f'''
[packages.semantic_admission]
registration={{state="present",value={{module_id="main",package_id="provider",registration_key="example"}}}}
semantic_package_name={{state="present",value="{name}"}}
semantic_version={{state="present",value="1.0"}}
code_package_name={{state="present",value="{name}-code"}}
source_code_package_id={{state="absent"}}
configuration={{state="absent"}}
namespace={{state="present",value="{name}"}}
owned_roots={{state="present",value=["{name}.a","{name}.b"]}}
dependency_targets={{state="present",value={mappings}}}
'''


@asynccontextmanager
async def setup(tmp_path, mutate=None):
    async with fixture(tmp_path) as (root, session, observation, membership):
        module = root / "aware.module.toml"
        mapping = (
            '[{dependency_kind="module",dependency_ref="target",'
            'targets=[{module_id="main",package_id="target"}],constraints=[]}]'
        )
        body = module.read_text().replace("aware = 1", "aware = 2")
        body += occurrence("demo", mapping) + PROVIDER
        body += (
            '\n[[packages]]\nid="target"\nkind="example"\n'
            'manifest="target/aware.example.toml"\n'
        ) + occurrence("target")
        if mutate:
            body = mutate(body)
        module.write_text(body)
        for folder, filename in [
            ("provider", "pyproject.toml"),
            ("target", "aware.example.toml"),
        ]:
            (root / folder).mkdir()
            (root / folder / filename).write_bytes(b"opaque retained body")
        retained = observation.observe(root_relative_path=".")
        handle = membership.admit(
            observation=retained,
            workspace_manifest_path="aware.workspace.toml",
            module_id="main",
            package_id="demo",
        )
        issuer = WorkspaceObservedSemanticIssuerRuntime.for_isolated_proof(
            observation_runtime=observation,
            membership_runtime=membership,
            observation=retained,
        )
        try:
            yield root, session, observation, membership, retained, handle, issuer
        finally:
            issuer.close()


def expectation(issuer, membership, handle):
    context, inventory = issuer.inspect_inputs(handle)

    def coordinate(role, body, contract=None):
        return SemanticValueCoordinate(
            role,
            contract
            or SemanticContractRef(
                "fixture.bytes", "1", ContentDigest.of_bytes(b"schema")
            ),
            "fixture:" + role,
            ContentDigest.of_bytes(body),
            len(body),
        )

    # Execution placeholders intentionally prove only isolated comparison mechanics.
    # No live Code profile, host or provider admission is manufactured here.
    return RetainedSemanticAdmissionExpectation(
        runtime=object(),
        generation_identity=object(),
        operation_identity=object(),
        process_id=os.getpid(),
        selected_provider_registration=object(),
        stage="source_planning",
        profile="fixture-profile",
        provider_declaration="fixture-provider",
        binding="fixture-binding",
        package=context.package,
        source_identity_digest=context.source_identity_digest,
        manifest_coordinate=coordinate(
            "manifest_source",
            membership.read(
                handle, relative_path=membership.evidence(handle).manifest_relative_path
            ),
        ),
        candidate_coordinate=coordinate(
            "candidate_listing",
            encode_semantic_candidate_listing(
                membership.evidence(handle).candidate_listing
            ),
            SEMANTIC_CANDIDATE_LISTING_REF,
        ),
        registry_package_coordinate=coordinate("registry_package", b"fixture-registry"),
        package_context_coordinate=coordinate(
            "package_context",
            encode_package_context_input(context),
            PACKAGE_CONTEXT_INPUT_REF,
        ),
        declaration_inventory_coordinate=coordinate(
            "declaration_inventory",
            encode_declaration_target_inventory(inventory),
            DECLARATION_TARGET_INVENTORY_REF,
        ),
    )


async def test_original_pair_and_internal_assignments(tmp_path):
    async with setup(tmp_path) as (_, _, _, membership, _, handle, issuer):
        context, inventory = issuer.inspect_inputs(handle)
        assert context.package.package_ref == "package:demo@1.0"
        assert context.config_id is None
        assert (
            inventory.entries[0].targets[0].package.package_ref == "package:target@1.0"
        )
        expected = expectation(issuer, membership, handle)
        package, targets = issuer.issue_isolated_pair(handle, expected=expected)
        for _ in range(2):
            issuer.validate_package_context_admission(package, expected=expected)
            issuer.validate_declaration_inventory_admission(targets, expected=expected)
            issuer.validate_occurrence_assignments(
                package,
                expected=expected,
                namespace="demo",
                owned_roots=("demo.a", "demo.b"),
            )
        with pytest.raises(SourceObservationUnavailable):
            issuer.issue_isolated_pair(handle, expected=expected)
        for roots in [("demo.a",), ("demo.b", "demo.a"), ()]:
            with pytest.raises(SourceObservationUnavailable):
                issuer.validate_occurrence_assignments(
                    package,
                    expected=expected,
                    namespace="demo",
                    owned_roots=roots,
                )
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_occurrence_assignments(
                package,
                expected=expected,
                namespace="foreign",
                owned_roots=("demo.a", "demo.b"),
            )


@pytest.mark.parametrize(
    "field",
    [
        "runtime",
        "generation_identity",
        "operation_identity",
        "selected_provider_registration",
        "profile",
        "binding",
        "registry_package_coordinate",
        "stage",
    ],
)
async def test_context_substitution(tmp_path, field):
    async with setup(tmp_path) as (_, _, _, membership, _, handle, issuer):
        expected = expectation(issuer, membership, handle)
        package, _ = issuer.issue_isolated_pair(handle, expected=expected)
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_package_context_admission(
                package,
                expected=replace(expected, **{field: object()}),
            )


@pytest.mark.parametrize(
    "change",
    [
        "source",
        "target",
        "module",
        "addition",
        "eviction",
        "restart",
        "foreign",
        "reconstructed",
        "scope",
        "fork",
    ],
)
async def test_original_evidence_rejections(tmp_path, change, monkeypatch):
    async with setup(tmp_path) as (
        root,
        session,
        observation,
        membership,
        retained,
        handle,
        issuer,
    ):
        expected = expectation(issuer, membership, handle)
        package, targets = issuer.issue_isolated_pair(handle, expected=expected)
        if change in ("source", "target", "module"):
            path = {
                "source": "package/unselected.bin",
                "target": "target/aware.example.toml",
                "module": "aware.module.toml",
            }[change]
            (root / path).write_bytes(b"changed")
        elif change == "addition":
            (root / "added").write_bytes(b"new")
        elif change == "eviction":
            for path in (tmp_path / "state").rglob("*"):
                if path.is_file():
                    path.unlink()
        elif change == "restart":
            await session.stop()
            await session.start(background=False)
        elif change == "foreign":
            issuer = WorkspaceObservedSemanticIssuerRuntime.for_isolated_proof(
                observation_runtime=observation,
                membership_runtime=membership,
                observation=retained,
            )
        elif change == "reconstructed":
            package = object.__new__(WorkspacePackageContextAdmission)
        elif change == "scope":
            with pytest.raises(Exception):
                membership.admit(
                    observation=retained,
                    workspace_manifest_path="foreign/aware.workspace.toml",
                    module_id="main",
                    package_id="demo",
                )
            return
        else:
            monkeypatch.setattr(os, "getpid", lambda: -1)
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_package_context_admission(package, expected=expected)
        if change != "reconstructed":
            with pytest.raises(SourceObservationUnavailable):
                issuer.validate_declaration_inventory_admission(
                    targets, expected=expected
                )


async def test_unavailable_claim_and_missing_target(tmp_path):
    async with setup(
        tmp_path,
        lambda b: b.replace(
            'semantic_version={state="present",value="1.0"}',
            'semantic_version={state="unavailable"}',
            1,
        ),
    ) as (_, _, _, _, _, handle, issuer):
        with pytest.raises(SourceObservationUnavailable):
            issuer.inspect_inputs(handle)


async def test_copy_and_wrong_observation_origin(tmp_path):
    async with setup(tmp_path) as (_, _, observation, membership, _, handle, issuer):
        expected = expectation(issuer, membership, handle)
        package, _ = issuer.issue_isolated_pair(handle, expected=expected)
        with pytest.raises(TypeError):
            copy.copy(package)
        other = WorkspaceObservedSemanticIssuerRuntime.for_isolated_proof(
            observation_runtime=observation,
            membership_runtime=membership,
            observation=observation.observe(root_relative_path="."),
        )
        try:
            with pytest.raises(SourceObservationUnavailable):
                other.inspect_inputs(handle)
        finally:
            other.close()


@pytest.mark.parametrize(
    "field",
    [
        "registration",
        "semantic_package_name",
        "semantic_version",
        "code_package_name",
        "source_code_package_id",
        "configuration",
        "namespace",
        "owned_roots",
        "dependency_targets",
    ],
)
async def test_every_unavailable_occurrence_field_refuses(tmp_path, field):
    import re

    async with setup(
        tmp_path,
        lambda b: re.sub(
            "^" + field + "=.*$",
            field + '={state="unavailable"}',
            b,
            count=1,
            flags=re.MULTILINE,
        ),
    ) as (_, _, _, _, _, handle, issuer):
        with pytest.raises(SourceObservationUnavailable):
            issuer.inspect_inputs(handle)


async def test_missing_declared_target_refuses(tmp_path):
    async with setup(
        tmp_path, lambda b: b.replace('package_id="target"', 'package_id="missing"', 1)
    ) as (_, _, _, _, _, handle, issuer):
        with pytest.raises(SourceObservationUnavailable):
            issuer.inspect_inputs(handle)


async def test_coherent_portable_target_substitution_refuses(tmp_path):
    async with setup(tmp_path) as (_, _, _, membership, _, handle, issuer):
        expected = expectation(issuer, membership, handle)
        _, inventory = issuer.inspect_inputs(handle)
        target = inventory.entries[0].targets[0]
        forged = replace(
            target, package=replace(target.package, package_ref="package:foreign@1.0")
        )
        body = encode_declaration_target_inventory(
            replace(
                inventory, entries=(replace(inventory.entries[0], targets=(forged,)),)
            )
        )
        altered = replace(
            expected,
            declaration_inventory_coordinate=replace(
                expected.declaration_inventory_coordinate,
                digest=ContentDigest.of_bytes(body),
                size_bytes=len(body),
            ),
        )
        with pytest.raises(SourceObservationUnavailable):
            issuer.issue_isolated_pair(handle, expected=altered)


@pytest.mark.parametrize(
    "field,value",
    [
        ("role", "foreign-role"),
        ("value_ref", "foreign-ref"),
        ("size_bytes", 999),
    ],
)
async def test_complete_coordinate_identity_is_pinned(tmp_path, field, value):
    async with setup(tmp_path) as (_, _, _, membership, _, handle, issuer):
        expected = expectation(issuer, membership, handle)
        package, _ = issuer.issue_isolated_pair(handle, expected=expected)
        changed = replace(
            expected,
            package_context_coordinate=replace(
                expected.package_context_coordinate, **{field: value}
            ),
        )
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_package_context_admission(package, expected=changed)


async def test_closed_issuer_and_released_membership_refuse(tmp_path):
    async with setup(tmp_path) as (_, _, _, membership, _, handle, issuer):
        expected = expectation(issuer, membership, handle)
        package, _ = issuer.issue_isolated_pair(handle, expected=expected)
        membership.release(handle)
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_package_context_admission(package, expected=expected)
        issuer.close()
        with pytest.raises(SourceObservationUnavailable):
            issuer.validate_package_context_admission(package, expected=expected)


async def test_source_inspection_preserves_declared_kind_for_code_admission(tmp_path):
    async with setup(
        tmp_path, lambda b: b.replace('kind="example"', 'kind="foreign"', 1)
    ) as (_, _, _, _, _, handle, issuer):
        context, _ = issuer.inspect_inputs(handle)
        assert context.package.package_kind == "foreign"
