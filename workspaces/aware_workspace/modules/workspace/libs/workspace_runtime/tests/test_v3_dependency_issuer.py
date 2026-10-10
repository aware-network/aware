"""V3 direct target evidence stays on the original Workspace source issuer."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from aware_code_semantic_contract_runtime.target_context_interfaces import (
    RetainedTargetExpectation,
)
from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.declaration_scope_admission import (
    WorkspaceOriginalGraphTargetValidator,
)
from test_declaration_scope_admission import fixture
from test_materialization_declaration_selection import (
    _author_v3_repository,
    _selection,
)
from test_v3_source_admission import _Validator, _expected


def _author_imported_target(root):
    _author_v3_repository(root)
    module = root / "workspaces/network/modules/main/aware.module.toml"
    body = module.read_text()
    old = 'dependency_targets={state="present",value=[]}'
    relationship = (
        '[{dependency_kind="workspace",dependency_ref="kernel",'
        'targets=[{scope={kind="dependency",workspace_handle="Kernel"},'
        'module_id="main",package_id="example"}],constraints=[]}]'
    )
    assert body.count(old) == 2
    module.write_text(body.replace(old, (
        f'dependency_targets={{state="present",value={relationship}}}'
    ), 1))


@pytest.mark.parametrize("change", [None, "foreign", "target_body", "edge"])
async def test_v3_original_direct_target_is_retained_and_checked(tmp_path, change):
    async with fixture(tmp_path) as (root_path, _, borrowed, _, _, _):
        _author_imported_target(root_path)
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=_selection("package", "network-example")
            ) as bound:
                _, selected = bound[0]
                context = object()
                expected = replace(_expected(issuer, selected), stage="source_planning")
                issuer._bind_original_code_validator(_Validator(context, expected))
                _, inventory = issuer.issue_source_planning_pair(
                    selected, context=context, expected=expected
                )
                record = issuer._semantic[inventory]
                assert len(record.targets) == 1
                target = record.targets[0]
                graph_targets = issuer.bind_original_graph_target_validator((selected,))
                forged_graph_targets = object.__new__(
                    WorkspaceOriginalGraphTargetValidator
                )
                with pytest.raises(SourceObservationUnavailable, match="foreign"):
                    forged_graph_targets.validate_source_packages(
                        (record.context.package,)
                    )
                graph_targets.validate_source_packages((record.context.package,))
                relationship = record.inventory.entries[0]
                graph_targets.validate_target(
                    package=record.context.package,
                    dependency_kind=relationship.dependency_kind,
                    dependency_ref=relationship.dependency_ref,
                    target=relationship.targets[0],
                )
                with pytest.raises(SourceObservationUnavailable):
                    graph_targets.validate_target(
                        package=record.context.package,
                        dependency_kind=relationship.dependency_kind,
                        dependency_ref="unadmitted",
                        target=relationship.targets[0],
                    )
                assert target.address == (
                    "workspaces/kernel/aware.workspace.toml", "main", "example"
                )
                requested = RetainedTargetExpectation(
                    expected,
                    target.context.source_identity_digest,
                    target.context.package,
                )
                handle = issuer.select_dependency_target_admission(
                    inventory_admission=inventory, expected=requested
                )
                assert handle is target.membership
                issuer.validate_dependency_target_admission(
                    handle, inventory_admission=inventory, expected=requested
                )
                if change == "foreign":
                    with pytest.raises(SourceObservationUnavailable, match="foreign"):
                        issuer.validate_dependency_target_admission(
                            selected, inventory_admission=inventory,
                            expected=requested,
                        )
                elif change == "target_body":
                    (root_path / "workspaces/kernel/modules/main/package/body.bin").write_bytes(
                        b"changed"
                    )
                    with pytest.raises(SourceObservationUnavailable):
                        issuer.validate_dependency_target_admission(
                            handle, inventory_admission=inventory,
                            expected=requested,
                        )
                    with pytest.raises(SourceObservationUnavailable):
                        graph_targets.validate_target(
                            package=record.context.package,
                            dependency_kind=relationship.dependency_kind,
                            dependency_ref=relationship.dependency_ref,
                            target=relationship.targets[0],
                        )
                elif change == "edge":
                    workspace = root_path / "workspaces/network/aware.workspace.toml"
                    workspace.write_text(workspace.read_text().replace(
                        'id="Kernel"', 'id="Other"'
                    ))
                    with pytest.raises(SourceObservationUnavailable):
                        issuer.validate_dependency_target_admission(
                            handle, inventory_admission=inventory,
                            expected=requested,
                        )
                    with pytest.raises(SourceObservationUnavailable):
                        graph_targets.validate_target(
                            package=record.context.package,
                            dependency_kind=relationship.dependency_kind,
                            dependency_ref=relationship.dependency_ref,
                            target=relationship.targets[0],
                        )
            assert target.membership in issuer._target_records
        assert not issuer._target_records
        with pytest.raises(SourceObservationUnavailable):
            graph_targets.validate_source_packages((record.context.package,))


async def test_v3_dependency_source_window_detects_change_before_return(tmp_path):
    async with fixture(tmp_path) as (root_path, _, borrowed, _, _, _):
        _author_imported_target(root_path)
        with composition._compose_direct_workspace_command_resources(
            session=borrowed._session,
            store=borrowed._store,
            workspace_manifest_path="workspaces/network/aware.workspace.toml",
            source_rail="declaration_v3",
        ) as command:
            issuer = command.sources.declaration_scope_runtime
            with composition._compose_direct_workspace_selected_materialization_roots(
                command, selection=_selection("package", "network-example")
            ) as bound:
                _, selected = bound[0]
                context = object()
                expected = replace(_expected(issuer, selected), stage="source_planning")
                issuer._bind_original_code_validator(_Validator(context, expected))
                _, inventory = issuer.issue_source_planning_pair(
                    selected, context=context, expected=expected
                )
                with pytest.raises(SourceObservationUnavailable):
                    with issuer._original_dependency_source_window(
                        inventory, SimpleNamespace(source_planning=expected)
                    ):
                        (root_path / "workspaces/kernel/modules/main/package/body.bin").write_bytes(
                            b"changed during resolution"
                        )
                assert issuer._dependency_source_window is None
