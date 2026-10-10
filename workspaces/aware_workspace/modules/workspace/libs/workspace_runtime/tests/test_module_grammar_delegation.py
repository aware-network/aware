from pathlib import Path

import pytest
from aware_workspace_runtime.composition import (
    LocalCheckoutWorkspaceCompositionProvider,
    RetainedWorkspaceCompositionProvider,
    WorkspaceCompositionFailure,
)
from test_observed_membership import fixture


async def test_full_module_grammar_and_retained_read_only(tmp_path, monkeypatch):
    async with fixture(tmp_path) as (root, _, runtime, _):
        module = root / 'aware.module.toml'
        module.write_text(module.read_text() + '''
[packages.semantic_contract]
role = "demo.provider"
contract = "aware.semantic_provider"
provider_key = "demo"
module = "demo.provider"
owns_manifest_kinds = ["aware_demo_toml"]
capabilities = ["materialize"]
[[plugins]]
kind = "code.module_plugin"
provider_key = "demo"
semantic_contract_module = "demo.provider"
''')
        expected = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        observed = runtime.observe(root_relative_path='.')
        original_read = Path.read_bytes

        def forbidden(path):
            if path.is_relative_to(root):
                raise AssertionError('live checkout read after retention')
            return original_read(path)
        monkeypatch.setattr(Path, 'read_bytes', forbidden)
        actual = RetainedWorkspaceCompositionProvider().describe_retained(
            observation_runtime=runtime, observation=observed
        )
        assert actual == expected
        package = actual['repository']['workspaces'][0]['modules'][0]['packages'][0]
        assert package['provider_key'] is None
        assert package['capabilities'] == []


@pytest.mark.parametrize('suffix', [
    '\n[unexpected]\nvalue=1\n',
    '\n[packages.semantic_contract]\nrole="incomplete"\n',
])
async def test_both_compositions_use_owner_grammar_rejection(tmp_path, suffix):
    async with fixture(tmp_path) as (root, _, runtime, _):
        module = root / 'aware.module.toml'
        module.write_text(module.read_text() + suffix)
        observed = runtime.observe(root_relative_path='.')
        with pytest.raises(WorkspaceCompositionFailure) as live:
            LocalCheckoutWorkspaceCompositionProvider().describe(root)
        with pytest.raises(WorkspaceCompositionFailure) as retained:
            RetainedWorkspaceCompositionProvider().describe_retained(
                observation_runtime=runtime, observation=observed
            )
        assert live.value.code == retained.value.code
        assert live.value.code == 'workspace_composition_manifest_invalid'


async def test_module_digest_keeps_comment_only_changes(tmp_path):
    async with fixture(tmp_path) as (root, _, _, _):
        before = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        module = root / 'aware.module.toml'
        module.write_text(module.read_text() + '\n# comment only\n')
        after = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        assert before['repository'] == after['repository']
        assert before['observation_digest'] != after['observation_digest']


async def test_v2_occurrence_keeps_membership_projection_authority_free(tmp_path):
    async with fixture(tmp_path) as (root, _, runtime, membership):
        module = root / 'aware.module.toml'
        before = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        module.write_text(module.read_text().replace('aware = 1', 'aware = 2') + '''
[packages.semantic_admission]
registration = {state="unavailable"}
semantic_package_name = {state="present", value="demo-example"}
semantic_version = {state="present", value="1.0"}
code_package_name = {state="present", value="demo-code"}
source_code_package_id = {state="absent"}
configuration = {state="absent"}
namespace = {state="present", value="demo"}
owned_roots = {state="present", value=["demo"]}
dependency_targets = {state="present", value=[]}
''')
        live = LocalCheckoutWorkspaceCompositionProvider().describe(root)
        observed = runtime.observe(root_relative_path='.')
        retained = RetainedWorkspaceCompositionProvider().describe_retained(
            observation_runtime=runtime, observation=observed
        )
        assert live == retained
        assert live['repository'] == before['repository']
        assert live['authority_ref'] is None
        assert live['observation_digest'] != before['observation_digest']
        handle = membership.admit(
            observation=observed,
            workspace_manifest_path='aware.workspace.toml',
            module_id='main', package_id='demo',
        )
        assert membership.evidence(handle).package_kind == 'example'
        assert membership.read(handle, relative_path='aware.example.toml') == (
            b'opaque owner manifest'
        )


@pytest.mark.parametrize('version', ['true', 'false', '0', '4', '1.0', '2.0', '3.0', '"2"', '"3"'])
async def test_invalid_module_versions_reject_in_both_readers(tmp_path, version):
    async with fixture(tmp_path) as (root, _, runtime, _):
        module = root / 'aware.module.toml'
        module.write_text(module.read_text().replace('aware = 1', 'aware = ' + version))
        observed = runtime.observe(root_relative_path='.')
        with pytest.raises(WorkspaceCompositionFailure):
            LocalCheckoutWorkspaceCompositionProvider().describe(root)
        with pytest.raises(WorkspaceCompositionFailure):
            RetainedWorkspaceCompositionProvider().describe_retained(
                observation_runtime=runtime, observation=observed
            )
