"""The public command consumes original source evidence before retirement."""

import json

import pytest
from aware_workspace_command.materialize_command import (
    handle_workspace_materialize_command,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from test_materialize_command import _args
from test_observed_semantic_issuers import PROVIDER, occurrence


def _repository(root, *, unavailable=None, provider_key="demo"):
    module = root / "workspaces/kernel/modules/main"
    package = module / "package"
    package.mkdir(parents=True)
    (module / "provider").mkdir()
    (root / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\n'
        '[[workspaces]]\nhandle="Kernel"\npath="workspaces/kernel"\n'
    )
    (root / "workspaces/kernel/aware.workspace.toml").write_text(
        'aware=2\n[workspace]\nhandle="Kernel"\n'
        '[[workspace.modules]]\nid="main"\npath="modules/main"\n'
        '[[workspace.modules]]\nid="legacy"\npath="modules/legacy"\n'
    )
    admission = occurrence("demo").replace(
        'value={module_id=', 'value={scope={kind="local"},module_id='
    )
    if unavailable is not None:
        admission = "\n".join(
            f'{unavailable}={{state="unavailable"}}'
            if line.startswith(unavailable + "=") else line
            for line in admission.splitlines()
        ) + "\n"
    (module / "aware.module.toml").write_text(
        'aware=3\n[module]\n[[packages]]\nid="example"\nkind="example"\n'
        'manifest="package/aware.example.toml"\nvisibility="module"\n'
        + admission + PROVIDER.replace('provider_key="demo"', f'provider_key="{provider_key}"')
    )
    (package / "aware.example.toml").write_bytes(b"authored package manifest")
    (package / "body.aware").write_bytes(b"original authored body")
    (module / "provider/pyproject.toml").write_bytes(b"declared provider package")
    legacy = root / "workspaces/kernel/modules/legacy"
    (legacy / "old").mkdir(parents=True)
    (legacy / "aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="old"\nkind="example"\n'
        'manifest="old/aware.example.toml"\nvisibility="module"\n'
    )
    (legacy / "old/aware.example.toml").write_bytes(b"observed unrelated v1")
    return package


def _run(root, capsys):
    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(root),
        workspace_toml="workspaces/kernel/aware.workspace.toml",
        package=[], package_address="Kernel:main:example", plan=True,
    )) == 2
    captured = capsys.readouterr()
    return json.loads(captured.out), captured.err.strip()


def _imported_repository(root):
    _repository(root)
    module = root / "workspaces/kernel/modules/main/aware.module.toml"
    body = module.read_text().split("[[plugins]]", 1)[0].replace(
        'scope={kind="local"}',
        'scope={kind="dependency",workspace_handle="Provider"}',
    )
    module.write_text(body)
    repo = root / "aware.repo.toml"
    repo.write_text(repo.read_text() + (
        '[[workspaces]]\nhandle="Provider"\npath="workspaces/provider"\n'
    ))
    workspace = root / "workspaces/kernel/aware.workspace.toml"
    workspace.write_text(workspace.read_text() + (
        '[[workspace.dependencies]]\nid="Provider"\nkind="workspace"\n'
        'source="workspace://Provider"\nchannel="local"\n'
        'revision="workspace-revision:local"\n'
        '[[workspace.dependencies.code_semantic_contract_profile_packages]]\n'
        'profile_package_ref="workspace://Provider#arbitrary.profile"\n'
        'profile_key="arbitrary.profile"\nsemantic_contract_provider_keys=["demo"]\n'
    ))
    provider = root / "workspaces/provider/modules/main/provider"
    provider.mkdir(parents=True)
    (provider / "pyproject.toml").write_bytes(b"original declared imported provider")
    (provider.parent / "aware.module.toml").write_text("aware=3\n" + PROVIDER)
    (root / "workspaces/provider/aware.workspace.toml").write_text(
        'aware=2\n[workspace]\nhandle="Provider"\n'
        '[[workspace.modules]]\nid="main"\npath="modules/main"\n'
        '[[workspace.code_semantic_contract_profile_packages]]\n'
        'profile_key="arbitrary.profile"\n'
        'profile_package_ref="workspace://Provider#arbitrary.profile"\n'
    )
    profile = root / "workspaces/provider/semantic_contract/profiles/arbitrary.profile"
    profile.mkdir(parents=True)
    manifest = profile / "aware.semantic_contract_profile.toml"
    manifest.write_text(
        'aware_semantic_contract_profile=1\n[profile]\n'
        'key="arbitrary.profile"\npackage_key="arbitrary.profile"\n'
        '[[providers]]\nmodule_id="main"\nprovider_key="demo"\n'
    )
    return workspace, manifest


@pytest.mark.parametrize("poison", [None, "profile", "edge"])
def test_public_import_resolves_original_profile_and_complete_edge_restrictions(
    tmp_path, monkeypatch, capsys, poison,
):
    root = tmp_path / "repository"
    workspace, profile = _imported_repository(root)
    if poison is not None:
        path = profile if poison == "profile" else workspace
        path.write_text(path.read_text().replace('"demo"', '"foreign"'))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    payload, diagnostic = _run(root, capsys)
    if poison is None:
        assert diagnostic == "original_selected_provider_factory_binding_unavailable: demo"
    else:
        assert diagnostic.startswith("selected_participant_admission_unavailable: ")
        assert "factory_binding_unavailable" not in diagnostic
    assert payload["outcome"] == "blocked"
    assert payload["terminal_stage"] == "selection"
    assert payload["operation"]["selected_root"]["workspace_handle"] == "Kernel"
    assert not list((tmp_path / "state").rglob("command-*"))


@pytest.mark.parametrize("provider_key", ["demo", "arbitrary_owner"])
def test_public_command_checks_genuine_selected_view_in_its_live_context(
    tmp_path, monkeypatch, capsys, provider_key,
):
    root = tmp_path / "repository"
    _repository(root, provider_key=provider_key)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    resolve = composition._resolve_direct_workspace_exact_provider_key
    retained = []

    def inspect_original(command, selected):
        composition._require_live_direct_workspace_command(command)
        key = resolve(command, selected)
        retained.append((command, selected, key))
        return key

    monkeypatch.setattr(
        composition, "_resolve_direct_workspace_exact_provider_key", inspect_original
    )
    payload, diagnostic = _run(root, capsys)
    assert diagnostic == (
        "original_selected_provider_factory_binding_unavailable: " + provider_key
    )
    assert payload["terminal_stage"] == "selection"
    assert payload["operation"]["selected_root"]["package_id"] == "example"
    assert payload["failure_code"] == "graph_host_not_ready"
    assert len(retained) == 1 and retained[0][2] == provider_key
    command, selected, _ = retained[0]
    with pytest.raises((RuntimeError, SourceObservationUnavailable)):
        composition._require_live_direct_workspace_command(command)
    with pytest.raises(SourceObservationUnavailable):
        command.sources.declaration_scope_runtime.read_selected_package_source(selected)
    assert not list((tmp_path / "state").rglob("command-*"))


@pytest.mark.parametrize("field", ["registration", "owned_roots"])
def test_public_command_reports_code_refusal_for_incomplete_original_declaration(
    tmp_path, monkeypatch, capsys, field,
):
    root = tmp_path / "repository"
    _repository(root, unavailable=field)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    payload, diagnostic = _run(root, capsys)
    assert diagnostic == (
        "selected_participant_admission_unavailable: selected v3 participant incomplete"
    )
    assert payload["operation"]["selected_root"]["package_id"] == "example"
    assert payload["outcome"] == "blocked"
    counters = {row["counter"]: row["value"] for row in payload["host_counters"]}
    assert counters["selected_package_count"] == 1
    assert counters["graph_admission_count"] == counters["graph_execution_count"] == 0
    assert not list((tmp_path / "state").rglob("command-*"))


@pytest.mark.parametrize("refuse", [False, True])
def test_changed_source_during_code_validation_cannot_emit_old_operation_receipt(
    tmp_path, monkeypatch, capsys, refuse,
):
    from aware_code_retained_registry_policy_runtime import declaration_eligibility
    from aware_code_semantic_contract_runtime.contracts import ContractViolation

    root = tmp_path / "repository"
    package = _repository(root)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    calculate = declaration_eligibility.calculate_declaration_eligibility
    calls = []

    def move_source(*args, **kwargs):
        value = calculate(*args, **kwargs)
        calls.append(value)
        (package / "body.aware").write_bytes(b"changed after source admission")
        if refuse:
            raise ContractViolation("diagnostic refusal cannot hide moved source")
        return value

    monkeypatch.setattr(
        declaration_eligibility, "calculate_declaration_eligibility", move_source
    )
    payload, _ = _run(root, capsys)
    assert len(calls) == 1
    assert payload["failure_code"] == "workspace_manifest_not_admitted"
    assert payload["operation"] is None
    assert payload["terminal_stage"] == "host_admission"
    assert not list((tmp_path / "state").rglob("command-*"))
