"""V3 retained meaning and membership only; qualified semantic issuance stays held."""

from pathlib import Path

import pytest
from aware_code_module_manifest_contract_runtime import (
    AwareModuleSpecV3,
    encode_module_manifest_meaning,
    parse_module_manifest,
)
from aware_workspace_runtime.complete_scope_observation import (
    WorkspaceCompleteScopeObservationRuntime,
)
from aware_workspace_runtime.composition import (
    LocalCheckoutWorkspaceCompositionProvider,
    RetainedWorkspaceCompositionProvider,
    WorkspaceCompositionFailure,
)
from aware_workspace_runtime.source_observation_io import SourceObservationUnavailable
from test_observed_membership import fixture
from test_observed_semantic_issuers import setup


def qualified(body):
    return (
        body.replace("aware = 2", "aware = 3")
        .replace(
            'value={module_id="main",package_id="provider"',
            'value={scope={kind="dependency",workspace_handle="Kernel"},module_id="main",package_id="provider"',
        )
        .replace(
            'targets=[{module_id="main",package_id="target"}]',
            'targets=[{scope={kind="dependency",workspace_handle="Kernel"},module_id="main",package_id="target"},'
            '{scope={kind="local"},module_id="main",package_id="target"}]',
        )
    )


async def test_retained_v3_scope_preserves_qualified_meaning_without_live_reads(
    tmp_path, monkeypatch
):
    async with setup(tmp_path, mutate=qualified) as (
        root,
        _,
        observer,
        membership,
        observed,
        member,
        issuer,
    ):
        live = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        expected_body = (root / "aware.module.toml").read_bytes()
        expected_model = parse_module_manifest(expected_body)
        original_read = Path.read_bytes

        def forbid(path):
            if path.is_relative_to(root):
                raise AssertionError("checkout read instead of retained bytes")
            return original_read(path)

        monkeypatch.setattr(Path, "read_bytes", forbid)
        retained = RetainedWorkspaceCompositionProvider().describe_retained(
            observation_runtime=observer, observation=observed
        )
        assert retained == live
        assert retained["authority_ref"] is None
        scope = WorkspaceCompleteScopeObservationRuntime(
            observation_runtime=observer, membership_runtime=membership
        )
        try:
            snapshot = scope.capture_complete_scope(
                observation=observed, workspace_manifest_path="aware.workspace.toml"
            )
            source = scope.read_complete_scope(snapshot)
            assert len(source.packages) == 3
            module = source.modules[0]
            assert type(module.meaning) is AwareModuleSpecV3
            assert module.body == expected_body
            assert encode_module_manifest_meaning(
                module.meaning
            ) == encode_module_manifest_meaning(expected_model)
            demo = next(
                d for d in module.meaning.package_declarations if d.package_id == "demo"
            )
            address = dict(demo.occurrence.registration.value.entries)
            assert dict(address["scope"].entries) == {
                "kind": "dependency",
                "workspace_handle": "Kernel",
            }
            mapping = dict(demo.occurrence.dependency_targets.value[0].entries)
            scopes = [
                dict(dict(t.entries)["scope"].entries) for t in mapping["targets"]
            ]
            assert scopes == [
                {"kind": "dependency", "workspace_handle": "Kernel"},
                {"kind": "local"},
            ]
            assert membership.evidence(member).package_id == "demo"
            # A local same-named provider and target exist. They must not satisfy
            # the qualified import through the old semantic issuer's local lookup.
            with pytest.raises(
                SourceObservationUnavailable, match="v2_occurrence_required"
            ):
                issuer.inspect_inputs(member)
        finally:
            scope.close()


@pytest.mark.parametrize("change", ["handle", "unqualified", "boolean", "unsupported"])
async def test_invalid_v3_rejects_live_and_retained_before_membership(tmp_path, change):
    async with fixture(tmp_path) as (root, _, observer, _):
        # Use the complete accepted owner fixture declaration, not an incomplete
        # table whose shape would hide the targeted rejection.
        from test_observed_semantic_issuers import occurrence

        body = (
            'aware = 3\n[[packages]]\nid="demo"\nkind="example"\nmanifest="package/aware.example.toml"\n'
            + qualified(occurrence("demo"))
        )
        if change == "handle":
            body = body.replace(
                'workspace_handle="Kernel"', 'workspace_handle=" Kernel"'
            )
        elif change == "unqualified":
            body = body.replace(
                'scope={kind="dependency",workspace_handle="Kernel"},', ""
            )
        elif change == "boolean":
            body = body.replace("aware = 3", "aware = true")
        else:
            body = body.replace("aware = 3", "aware = 4")
        (root / "aware.module.toml").write_text(body)
        retained = observer.observe(root_relative_path=".")
        with pytest.raises(WorkspaceCompositionFailure):
            LocalCheckoutWorkspaceCompositionProvider().describe(root)
        with pytest.raises(WorkspaceCompositionFailure):
            RetainedWorkspaceCompositionProvider().describe_retained(
                observation_runtime=observer, observation=retained
            )


async def test_v3_scope_uses_original_bound_exclusion(tmp_path):
    from test_source_exclusion import chain

    async with chain(tmp_path) as (
        runtime,
        parent,
        expected,
        _,
        observer,
        _,
        scopes,
        _,
        _,
    ):
        module = observer._session.binding.root_path / "aware.module.toml"
        module.write_text(qualified(module.read_text()))
        observed = observer.observe(root_relative_path=".")
        snapshot = scopes.capture_complete_scope(
            observation=observed, workspace_manifest_path="aware.workspace.toml"
        )
        source = scopes.read_complete_scope(snapshot)
        assert type(source.modules[0].meaning) is AwareModuleSpecV3
        original = scopes._record(snapshot)
        guard = runtime.acquire_catalog_epoch_exclusion(parent, expected=expected)
        try:
            assert (
                scopes._check_record_locked(
                    snapshot, guard=guard, expected_record=original
                )
                is original
            )
        finally:
            runtime.release_catalog_epoch_exclusion(guard)
        scopes.release(snapshot)
