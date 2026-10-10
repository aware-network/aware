from __future__ import annotations

import argparse
import json

import pytest

from aware_workspace_command.materialize_command import (
    WorkspaceMaterializeCommandError,
    WorkspaceMaterializeCommandProposalV2,
    WorkspaceMaterializeCommandProposalV3,
    WorkspaceMaterializeCommandResult,
    handle_workspace_materialize_command,
    register_workspace_materialize_parser,
)
from aware_workspace_command.workspace_command import register_workspace_parser
from aware_workspace_materialize_transport import (
    WorkspaceMaterializeCommandSelectorV2,
    WorkspaceMaterializeHostResultV2,
    WorkspaceMaterializeHostResultV4,
    WorkspaceMaterializeSelectedRootV1,
    empty_workspace_materialize_host_counters_v2,
)
from aware_workspace_materialize_transport.contracts import (
    WorkspaceMaterializeHostOperationReceiptV1,
    WorkspaceMaterializeHostResultV3,
)
from test_observed_semantic_issuers import occurrence


@pytest.mark.parametrize("help_flag", ["-h", "--help"])
def test_workspace_parent_help_lists_materialize(
    help_flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = argparse.ArgumentParser()
    register_workspace_parser(
        parser.add_subparsers(dest="command"),
        args_list=("workspace", help_flag),
    )

    with pytest.raises(SystemExit) as exit_result:
        parser.parse_args(["workspace", help_flag])

    assert exit_result.value.code == 0
    assert "materialize" in capsys.readouterr().out


class _Transport:
    def __init__(self) -> None:
        self.proposals: list[dict[str, object]] = []

    def invoke(self, proposal_wire: bytes) -> WorkspaceMaterializeHostResultV2:
        self.proposals.append(json.loads(proposal_wire))
        proposal = WorkspaceMaterializeCommandProposalV2.from_wire(proposal_wire)
        counters = dict(empty_workspace_materialize_host_counters_v2(proposal))
        counters.update(
            authority_preflight_count=1,
            catalog_observation_count=2,
            selected_package_count=1,
            graph_node_count=1,
            graph_admission_count=1,
            graph_execution_count=1,
        )
        return WorkspaceMaterializeHostResultV2.create(
            proposal=proposal,
            outcome="succeeded",
            terminal_stage="graph_execution",
            host_timing_ns=tuple(
                (stage, 1)
                for stage in (
                    "request_decode",
                    "host_admission",
                    "catalog_observation",
                    "selection",
                    "graph_plan",
                    "graph_admission",
                    "graph_execution",
                )
            ),
            host_total_ns=8,
            host_counters=tuple(counters.items()),
            plan_result_wire=b'{"contract":"plan"}',
            graph_result_wire=b'{"contract":"graph"}',
            failure_kind=None,
            failure_code=None,
        )


def _args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "workspace_root": None,
        "repo_root": None,
        "workspace_toml": "workspaces/aware_dev/aware.workspace.toml",
        "package": ["aware_dev_sdk"],
        "module": [],
        "workspace": [],
        "repository": [],
        "plan": False,
        "json": True,
        "_aware_cli_module_started_ns": 1,
        "_aware_cli_command_discovery_ns": 2,
        "_aware_cli_command_import_parser_ns": 3,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.mark.parametrize("explicit_root", [None, "/explicit/repository"])
def test_explicit_repo_root_precedes_inherited_workspace_root(
    explicit_root: str | None, capsys: pytest.CaptureFixture[str],
) -> None:
    transport = _Transport()
    assert handle_workspace_materialize_command(
        args=_args(repo_root=explicit_root, workspace_root="/inherited/repository"),
        transport=transport,
    ) == 0
    assert transport.proposals[0]["participant_checkout_root"] == (
        explicit_root or "/inherited/repository"
    )
    assert json.loads(capsys.readouterr().out)["outcome"] == "succeeded"


def test_command_without_repository_refuses_at_direct_host_admission(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert handle_workspace_materialize_command(args=_args()) == 2
    payload = json.loads(capsys.readouterr().out)

    assert payload["outcome"] == "blocked"
    assert payload["terminal_stage"] == "host_admission"
    assert payload["failure_code"] == "caller_not_admitted"
    assert [item["stage"] for item in payload["host_timing_ns"]] == [
        "request_decode", "host_admission",
    ]
    assert [item["stage"] for item in payload["timing_ns"]] == [
        "cli_startup",
        "command_discovery",
        "command_import_parser",
        "proposal_encode",
        "transport",
        "output_encode",
        "total",
    ]
    assert payload["imported_module_family_counts"]["aware_workspace_command"] > 0
    assert set(payload["imported_module_family_counts"]) == {
        "aware_code_semantic_contract_runtime",
        "aware_meta",
        "aware_ontology",
        "aware_orm",
        "aware_workspace",
        "aware_workspace_command",
        "aware_workspace_materialize_transport",
        "aware_workspace_runtime",
        "pydantic",
        "sqlalchemy",
    }
    assert payload["non_claims"] == [
        "canonical_replica",
        "checkout_apply",
        "oig_commit",
        "workspace_revision",
    ]


def test_cli_context_does_not_select_local_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from aware_workspace_materialize_transport import local_service

    def unexpected_service_route():
        raise AssertionError("CLI must not require a Local Service route")

    monkeypatch.setattr(
        local_service, "default_workspace_materialize_transport", unexpected_service_route
    )
    assert handle_workspace_materialize_command(args=_args(), context=object()) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcome"] == "blocked"
    assert payload["failure_code"] == "caller_not_admitted"


def test_public_direct_host_admits_retained_repository_before_graph(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    package = repository / "workspaces/kernel/modules/storage/ontology"
    package.mkdir(parents=True)
    (repository / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\n'
        '[[workspaces]]\nhandle="Kernel"\npath="workspaces/kernel"\n'
    )
    (repository / "workspaces/kernel/aware.workspace.toml").write_text(
        'aware=2\n[workspace]\nhandle="Kernel"\n'
        '[[workspace.modules]]\nid="storage"\npath="modules/storage"\n'
    )
    (repository / "workspaces/kernel/modules/storage/aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="ontology"\nkind="ontology"\n'
        'manifest="ontology/aware.ontology.toml"\nvisibility="module"\n'
    )
    (package / "aware.ontology.toml").write_text(
        'aware_ontology=1\n[ontology]\npackage_name="storage-ontology"\n'
    )
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(repository),
        workspace_toml="workspaces/kernel/aware.workspace.toml",
        package=["storage-ontology"],
        plan=True,
    )) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["terminal_stage"] == "host_admission"
    assert payload["failure_code"] == "graph_host_not_ready"
    assert payload["host_counters"][0] == {
        "counter": "authority_preflight_count", "value": 1,
    }
    assert payload["contract"] == "aware.workspace.materialize-command-result.v3"
    receipt = WorkspaceMaterializeHostOperationReceiptV1.from_value(
        payload["operation"]["host_receipt"]
    )
    assert receipt.attempt_ref == payload["attempt_ref"]
    assert receipt.operation_ref != receipt.attempt_ref
    assert receipt.declaration_scope_digest.startswith("sha256:")
    assert next(
        row["value"] for row in payload["host_counters"]
        if row["counter"] == "selected_package_count"
    ) == 0
    assert next(
        row["value"] for row in payload["host_counters"]
        if row["counter"] == "graph_execution_count"
    ) == 0
    assert not (tmp_path / "state" / "aware" / "workspace-direct").is_symlink()

    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(repository),
        workspace_toml="workspaces/foreign/aware.workspace.toml",
        package=["storage-ontology"],
        plan=True,
    )) == 2
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["failure_code"] == "workspace_manifest_not_admitted"
    assert rejected["operation"] is None


def test_public_exact_address_selects_one_v3_source_among_v1_modules(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = tmp_path / "repository"
    storage = repository / "workspaces/kernel/modules/storage"
    ontology = storage / "ontology"
    legacy = repository / "workspaces/kernel/modules/legacy"
    (legacy / "package").mkdir(parents=True)
    ontology.mkdir(parents=True)
    (repository / "aware.repo.toml").write_text(
        'aware_repo=1\n[repo]\nhandle="demo"\n'
        '[[workspaces]]\nhandle="Kernel"\npath="workspaces/kernel"\n'
    )
    (repository / "workspaces/kernel/aware.workspace.toml").write_text(
        'aware=2\n[workspace]\nhandle="Kernel"\n'
        '[[workspace.modules]]\nid="storage"\npath="modules/storage"\n'
        '[[workspace.modules]]\nid="legacy"\npath="modules/legacy"\n'
    )
    admission = occurrence("storage-ontology").replace(
        'value={module_id="main",package_id="provider",',
        'value={scope={kind="local"},module_id="storage",package_id="ontology",',
    )
    (storage / "aware.module.toml").write_text(
        'aware=3\n[module]\n[[packages]]\nid="ontology"\nkind="ontology"\n'
        'manifest="ontology/aware.ontology.toml"\nvisibility="module"\n'
        + admission
    )
    (ontology / "aware.ontology.toml").write_text(
        'aware_ontology=1\n[ontology]\npackage_name="storage-ontology"\n'
    )
    (legacy / "aware.module.toml").write_text(
        'aware=1\n[[packages]]\nid="old"\nkind="example"\n'
        'manifest="package/aware.example.toml"\nvisibility="module"\n'
    )
    (legacy / "package/aware.example.toml").write_text("legacy")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))

    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(repository),
        workspace_toml="workspaces/kernel/aware.workspace.toml",
        package=[], package_address="Kernel:storage:ontology", plan=True,
    )) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["contract"] == "aware.workspace.materialize-command-result.v4"
    assert payload["outcome"] == "blocked"
    assert payload["terminal_stage"] == "selection"
    assert payload["failure_code"] == "graph_host_not_ready"
    selected = payload["operation"]["selected_root"]
    assert (selected["workspace_handle"], selected["module_id"], selected["package_id"]) == (
        "Kernel", "storage", "ontology",
    )
    assert selected["semantic_package_name"] == "storage-ontology"
    assert selected["source_identity_digest"].startswith("sha256:")
    assert next(row["value"] for row in payload["host_counters"] if row["counter"] == "selected_package_count") == 1
    assert next(row["value"] for row in payload["host_counters"] if row["counter"] == "graph_execution_count") == 0
    assert WorkspaceMaterializeHostOperationReceiptV1.from_value(
        payload["operation"]["host_receipt"]
    ).attempt_ref == payload["attempt_ref"]

    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(repository),
        workspace_toml="workspaces/kernel/aware.workspace.toml",
        package=["storage-ontology"], plan=True,
    )) == 2
    broad = json.loads(capsys.readouterr().out)
    assert broad["terminal_stage"] == "host_admission"
    assert broad["operation"].get("selected_root") is None

    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(repository),
        workspace_toml="workspaces/kernel/aware.workspace.toml",
        package=[], package_address="Kernel:storage:missing", plan=True,
    )) == 2
    missing = json.loads(capsys.readouterr().out)
    assert missing["outcome"] == "blocked"
    assert missing["operation"] is None
    assert next(row["value"] for row in missing["host_counters"] if row["counter"] == "selected_package_count") == 0

    assert handle_workspace_materialize_command(args=_args(
        repo_root=str(repository),
        workspace_toml="workspaces/kernel/aware.workspace.toml",
        package=[], package_address="Kernel:legacy:old", plan=True,
    )) == 2
    old = json.loads(capsys.readouterr().out)
    assert old["operation"] is None
    assert next(row["value"] for row in old["host_counters"] if row["counter"] == "selected_package_count") == 0


def test_exact_address_refuses_malformed_and_mixed_selectors_before_host(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for address, broad in (
        ("Kernel:storage", []),
        ("Kernel:storage:ontology:extra", []),
        ("Kernel:storage/foreign:ontology", []),
        ("Kernel:storage:ontology", ["storage-ontology"]),
    ):
        assert handle_workspace_materialize_command(args=_args(
            package=broad, package_address=address,
        )) == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["terminal_stage"] == "proposal_encode"
        assert payload["failure_code"] == "proposal_invalid"
        assert payload["operation"] is None


def test_caller_transport_cannot_supply_direct_host_operation_receipt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _ForgedTransport:
        def invoke(self, proposal_wire: bytes) -> WorkspaceMaterializeHostResultV3:
            proposal = WorkspaceMaterializeCommandProposalV2.from_wire(proposal_wire)
            predecessor = WorkspaceMaterializeHostResultV2.create(
                proposal=proposal,
                outcome="blocked",
                terminal_stage="host_admission",
                host_timing_ns=(("request_decode", 1), ("host_admission", 1)),
                host_total_ns=2,
                host_counters=tuple({
                    **dict(empty_workspace_materialize_host_counters_v2(proposal)),
                    "authority_preflight_count": 1,
                }.items()),
                plan_result_wire=None,
                graph_result_wire=None,
                failure_kind="authority",
                failure_code="graph_host_not_ready",
            )
            receipt = WorkspaceMaterializeHostOperationReceiptV1.create(
                operation_ref="workspace-materialize-operation:00000000-0000-4000-8000-000000000001",
                parent_ref="workspace-command-parent:00000000-0000-4000-8000-000000000002",
                epoch_ref="workspace-command-epoch:00000000-0000-4000-8000-000000000003",
                attempt_ref=proposal.attempt_ref,
                proposal_digest=proposal.proposal_digest,
                declaration_scope_digest="sha256:" + "a" * 64,
            )
            return WorkspaceMaterializeHostResultV3.create(
                predecessor=predecessor, operation_receipt=receipt
            )

    assert handle_workspace_materialize_command(
        args=_args(), transport=_ForgedTransport()
    ) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["terminal_stage"] == "transport"
    assert payload["failure_code"] == "transport_failed"
    assert payload["operation"] is None


def test_command_success_uses_exact_canonical_proposal_and_same_result_projection(
    capsys: pytest.CaptureFixture[str],
) -> None:
    transport = _Transport()
    assert handle_workspace_materialize_command(args=_args(), transport=transport) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["outcome"] == "succeeded"
    assert payload["terminal_stage"] == "graph_execution"
    assert payload["operation"]["plan_result"] == {"contract": "plan"}
    assert payload["operation"]["graph_result"] == {"contract": "graph"}
    assert payload["host_total_ns"] == 8
    assert [item["stage"] for item in payload["host_timing_ns"]] == [
        "request_decode",
        "host_admission",
        "catalog_observation",
        "selection",
        "graph_plan",
        "graph_admission",
        "graph_execution",
    ]
    assert len(transport.proposals) == 1
    assert transport.proposals[0]["selectors"] == [
        {"selector_kind": "package", "selector_ref": "aware_dev_sdk"}
    ]
    assert transport.proposals[0]["workspace_manifest_name"] == (
        "workspaces/aware_dev/aware.workspace.toml"
    )


def test_parser_is_owned_without_product_runtime() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    workspace = subparsers.add_parser("workspace")
    workspace_subparsers = workspace.add_subparsers(
        dest="workspace_command", required=True
    )
    register_workspace_materialize_parser(workspace_subparsers)

    parsed = parser.parse_args(
        [
            "workspace", "materialize", "--package", "sdk", "--module", "api",
            "--workspace", "kernel", "--repository", "aware", "--json",
        ]
    )
    assert parsed.workspace_command == "materialize"
    assert parsed.package == ["sdk"]
    assert parsed.module == ["api"]
    assert parsed.workspace == ["kernel"]
    assert parsed.repository == ["aware"]


def test_command_values_reject_foreign_and_reordered_shapes() -> None:
    with pytest.raises(TypeError, match="exact tuple"):
        WorkspaceMaterializeCommandProposalV2(
            attempt_ref="attempt:test",
            participant_checkout_root=None,
            workspace_manifest_name="aware.workspace.toml",
            selectors=[WorkspaceMaterializeCommandSelectorV2("package", "sdk")],  # type: ignore[arg-type]
            plan_only=False,
            proposal_digest="sha256:" + "0" * 64,
        )

    with pytest.raises(ValueError, match="canonical-byte order"):
        WorkspaceMaterializeCommandProposalV2(
            attempt_ref="attempt:test",
            participant_checkout_root=None,
            workspace_manifest_name="aware.workspace.toml",
            selectors=(
                WorkspaceMaterializeCommandSelectorV2("package", "z"),
                WorkspaceMaterializeCommandSelectorV2("package", "a"),
            ),
            plan_only=False,
            proposal_digest="sha256:" + "0" * 64,
        )

    with pytest.raises(WorkspaceMaterializeCommandError, match="exact stage prefix"):
        WorkspaceMaterializeCommandResult(
            attempt_ref="attempt:test",
            outcome="blocked",
            terminal_stage="transport",
            timing_ns=(("transport", 1), ("output_encode", 1)),
            imported_module_family_counts=tuple(
                (name, 0)
                for name in (
                    "aware_code_semantic_contract_runtime",
                    "aware_meta",
                    "aware_ontology",
                    "aware_orm",
                    "aware_workspace",
                    "aware_workspace_command",
                    "aware_workspace_materialize_transport",
                    "aware_workspace_runtime",
                    "pydantic",
                    "sqlalchemy",
                )
            ),
            operation_payload=None,
            failure_code="transport_unavailable",
        )


@pytest.mark.parametrize("proposal_version", (2, 3))
@pytest.mark.parametrize("json_output", (True, False))
def test_public_source_contention_is_blocked_and_preserves_original_observer(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    proposal_version: int,
    json_output: bool,
) -> None:
    from aware_workspace_runtime.contracts import WorkspaceRepositoryBinding
    from aware_workspace_runtime.lease import (
        FileWorkspaceRepositoryObservationLease,
        WorkspaceObservationLeaseUnavailable,
    )

    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "aware.repo.toml").write_text("aware = 1\n")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    binding = WorkspaceRepositoryBinding(repository)
    original = FileWorkspaceRepositoryObservationLease(binding=binding)
    contender = FileWorkspaceRepositoryObservationLease(binding=binding)
    original.acquire()
    before = original.lease_path.read_bytes()
    try:
        arguments = _args(repo_root=str(repository), plan=True, json=json_output)
        if proposal_version == 3:
            arguments.package = []
            arguments.package_address = "kernel:storage:ontology"
        assert handle_workspace_materialize_command(args=arguments) == 2
        output = capsys.readouterr()
        if json_output:
            payload = json.loads(output.out)
            assert payload["outcome"] == "blocked"
            assert payload["terminal_stage"] == "host_admission"
            assert payload["failure_code"] == "participant_checkout_overlap"
            assert payload["operation"] is None
            counters = {
                row["counter"]: row["value"] for row in payload["host_counters"]
            }
            assert counters["authority_preflight_count"] == 1
            for name in (
                "selected_package_count", "graph_node_count", "graph_edge_count",
                "graph_admission_count", "graph_execution_count",
            ):
                assert counters[name] == 0
        else:
            assert "Workspace materialize blocked (stage=host_admission" in output.out
            assert "A maintained Workspace observer already owns" in output.err
        assert original.lease_path.read_bytes() == before
        with pytest.raises(WorkspaceObservationLeaseUnavailable):
            contender.acquire()
        assert original.lease_path.read_bytes() == before
    finally:
        original.release()
    # The failed command neither stole the lease nor left another writer live.
    contender.acquire()
    contender.release()


def _installed_route_proposal(version: int = 2):
    if version == 3:
        return WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="attempt:installed-route", participant_checkout_root="/repo",
            workspace_manifest_name="workspaces/example/aware.workspace.toml",
            package_address=("example", "module", "package"), plan_only=False,
        )
    return WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="attempt:installed-route", participant_checkout_root="/repo",
        workspace_manifest_name="workspaces/example/aware.workspace.toml",
        selectors=(WorkspaceMaterializeCommandSelectorV2("package", "package"),),
        plan_only=False,
    )


def _installed_route_result(proposal, version: int = 2):
    counters = dict(empty_workspace_materialize_host_counters_v2(proposal))
    counters["authority_preflight_count"] = 1
    if version == 4:
        counters["selected_package_count"] = 1
    predecessor = WorkspaceMaterializeHostResultV2.create(
        proposal=proposal, outcome="blocked",
        terminal_stage="selection" if version == 4 else "host_admission",
        host_timing_ns=(
            ("request_decode", 1), ("host_admission", 1),
            ("catalog_observation", 1), ("selection", 1),
        ) if version == 4 else (("request_decode", 1), ("host_admission", 1)),
        host_total_ns=4 if version == 4 else 2, host_counters=tuple(counters.items()),
        plan_result_wire=None, graph_result_wire=None,
        failure_kind="authority", failure_code="graph_host_not_ready",
    )
    if version == 2:
        return predecessor
    receipt = WorkspaceMaterializeHostOperationReceiptV1.create(
        operation_ref="workspace-materialize-operation:00000000-0000-4000-8000-000000000001",
        parent_ref="workspace-command-parent:00000000-0000-4000-8000-000000000002",
        epoch_ref="workspace-command-epoch:00000000-0000-4000-8000-000000000003",
        attempt_ref=proposal.attempt_ref, proposal_digest=proposal.proposal_digest,
        declaration_scope_digest="sha256:" + "a" * 64,
    )
    if version == 3:
        return WorkspaceMaterializeHostResultV3.create(
            predecessor=predecessor, operation_receipt=receipt,
        )
    return WorkspaceMaterializeHostResultV4.create(
        predecessor=predecessor, operation_receipt=receipt,
        selected_root=WorkspaceMaterializeSelectedRootV1.create(
            workspace_handle="example", workspace_manifest_path=proposal.workspace_manifest_name,
            module_id="module", package_id="package", semantic_package_name="example-package",
            semantic_version="0.1.0", source_identity_digest="sha256:" + "b" * 64,
        ),
    )


@pytest.mark.parametrize("proposal_version,result_version", [(2, 2), (2, 3), (3, 2), (3, 4)])
def test_installed_route_preserves_existing_wire_contracts(proposal_version, result_version):
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_host_result,
        _decode_installed_workspace_proposal_wire,
    )

    proposal = _installed_route_proposal(proposal_version)
    result = _installed_route_result(proposal, result_version)
    assert _decode_installed_workspace_proposal_wire(proposal.to_wire()).to_wire() == proposal.to_wire()
    decoded = _decode_installed_workspace_host_result(
        proposal_wire=proposal.to_wire(), result_wire=result.to_wire(),
    )
    assert decoded.to_wire() == result.to_wire()
    # These are portable fixture values, never installed operation authority.


@pytest.mark.parametrize("limit", [65_536, 131_072])
def test_installed_route_byte_limit_is_inclusive(limit):
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_json,
    )

    body = b'{"text":"' + b"a" * (limit - 11) + b'"}'
    assert len(body) == limit
    assert len(_decode_installed_workspace_json(body, maximum_bytes=limit)["text"]) == limit - 11
    with pytest.raises(WorkspaceMaterializeCommandError, match="size or type"):
        _decode_installed_workspace_json(body + b" ", maximum_bytes=limit)


def test_installed_route_depth_counts_containers_not_quoted_braces():
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_json,
    )

    body = b'{"value":' + b"[" * 11 + b"0" + b"]" * 11 + b"}"
    _decode_installed_workspace_json(body, maximum_bytes=65_536)
    with pytest.raises(WorkspaceMaterializeCommandError, match="depth"):
        _decode_installed_workspace_json(
            b'{"value":' + b"[" * 12 + b"0" + b"]" * 12 + b"}", maximum_bytes=65_536,
        )
    escaped = json.dumps({"value": '[{\\"' * 100}, separators=(",", ":")).encode()
    assert _decode_installed_workspace_json(escaped, maximum_bytes=65_536)["value"] == '[{\\"' * 100


@pytest.mark.parametrize("body", [b"", b"[]", b'{"x":[}', b'{"x":', b'{"x":"unterminated}', b"\xff"])
def test_installed_route_rejects_bad_json(body):
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_json,
    )

    with pytest.raises(WorkspaceMaterializeCommandError):
        _decode_installed_workspace_json(body, maximum_bytes=65_536)


def test_installed_route_rejects_noncanonical_and_duplicate_proposals():
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_proposal_wire,
    )

    wire = _installed_route_proposal().to_wire()
    for poison in (wire + b"\n", wire[:-1] + b',"plan_only":false}', wire.replace(b'"plan_only":false', b'"plan_only":0')):
        with pytest.raises(ValueError):
            _decode_installed_workspace_proposal_wire(poison)


def test_installed_route_rejects_correlated_bytes_for_another_attempt():
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_host_result,
    )

    proposal = _installed_route_proposal()
    other = WorkspaceMaterializeCommandProposalV2.create(
        attempt_ref="attempt:another", participant_checkout_root=proposal.participant_checkout_root,
        workspace_manifest_name=proposal.workspace_manifest_name,
        selectors=proposal.selectors, plan_only=False,
    )
    with pytest.raises(ValueError, match="correlation"):
        _decode_installed_workspace_host_result(
            proposal_wire=other.to_wire(), result_wire=_installed_route_result(proposal).to_wire(),
        )


def test_installed_route_rejects_deep_json_hidden_in_graph_text():
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_host_result,
    )

    proposal = _installed_route_proposal()
    nested = b'{"value":' + b"[" * 12 + b"0" + b"]" * 12 + b"}"
    result = WorkspaceMaterializeHostResultV2.create(
        proposal=proposal, outcome="succeeded", terminal_stage="graph_plan",
        host_timing_ns=(
            ("request_decode", 1), ("host_admission", 1),
            ("catalog_observation", 1), ("selection", 1), ("graph_plan", 1),
        ),
        host_total_ns=5,
        host_counters=empty_workspace_materialize_host_counters_v2(proposal),
        plan_result_wire=nested, graph_result_wire=None,
        failure_kind=None, failure_code=None,
    )
    with pytest.raises(WorkspaceMaterializeCommandError, match="depth"):
        _decode_installed_workspace_host_result(
            proposal_wire=proposal.to_wire(), result_wire=result.to_wire(),
        )


def test_installed_route_rejects_hostile_byte_subclasses_without_behavior():
    from aware_workspace_command.materialize_command import (
        _decode_installed_workspace_proposal_wire,
    )

    class Hostile(bytes):
        def __len__(self):
            raise AssertionError("foreign length must not run")

        def __iter__(self):
            raise AssertionError("foreign iterator must not run")

    with pytest.raises(WorkspaceMaterializeCommandError, match="size or type"):
        _decode_installed_workspace_proposal_wire(Hostile(_installed_route_proposal().to_wire()))
