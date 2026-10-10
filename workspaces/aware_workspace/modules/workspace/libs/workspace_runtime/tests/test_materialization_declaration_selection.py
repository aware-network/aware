"""Four scopes share one original v3 declaration occurrence hierarchy."""

import pytest

from aware_workspace_runtime import SourceObservationUnavailable
from aware_workspace_runtime.materialization_selection import (
    WorkspaceMaterializationRootSelector,
    WorkspaceMaterializationSelectionProposal,
)
from test_declaration_scope_admission import fixture
from test_observed_semantic_issuers import occurrence


def _v3_occurrence(name: str) -> str:
    return occurrence(name).replace(
        'value={module_id=', 'value={scope={kind="local"},module_id='
    )


def _author_v3_repository(
    root, *, duplicate_name: bool = False, cross_scope_name: bool = False
) -> None:
    for handle in ("kernel", "network"):
        module = root / f"workspaces/{handle}/modules/main/aware.module.toml"
        packages = [
            (
                "example",
                "package/aware.example.toml",
                "shared-example" if cross_scope_name else f"{handle}-example",
            )
        ]
        if handle == "network":
            packages.append(
                (
                    "nested",
                    "package/child/aware.example.toml",
                    "network-example" if duplicate_name else "network-nested",
                )
            )
        body = "aware=3\n[module]\n"
        for package_id, manifest, name in packages:
            body += (
                f'[[packages]]\nid="{package_id}"\nkind="example"\n'
                f'manifest="{manifest}"\nvisibility="module"\n'
                + _v3_occurrence(name)
            )
        module.write_text(body)


def _selection(kind: str, ref: str) -> WorkspaceMaterializationSelectionProposal:
    return WorkspaceMaterializationSelectionProposal.create(
        selectors=(
            WorkspaceMaterializationRootSelector.create(
                selector_kind=kind, selector_ref=ref
            ),
        )
    )


async def test_original_v3_issuer_preselects_all_four_scopes(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        _author_v3_repository(root)
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )

        package = issuer.inspect_materialization_roots(
            declaration, selection=_selection("package", "network-example")
        )
        module = issuer.inspect_materialization_roots(
            declaration, selection=_selection("module", "main")
        )
        workspace = issuer.inspect_materialization_roots(
            declaration, selection=_selection("workspace", "Kernel")
        )
        repository = issuer.inspect_materialization_roots(
            declaration, selection=_selection("repository", "demo")
        )

        assert [
            (r.module_id, r.package_id, r.semantic_package_name) for r in package
        ] == [
            ("main", "example", "network-example")
        ]
        assert [r.semantic_package_name for r in module] == [
            "network-example", "network-nested"
        ]
        assert [r.semantic_package_name for r in workspace] == ["kernel-example"]
        assert [r.semantic_package_name for r in repository] == [
            "kernel-example", "network-example", "network-nested"
        ]
        assert package[0] is not module[0]
        assert package[0] == module[0]

        # The detached candidate still needs the original selected-source
        # entrance; inspection alone grants neither source nor Code authority.
        selected_observation = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path=package[0].workspace_manifest_path,
            module_id=package[0].module_id,
            package_id=package[0].package_id,
        )
        selected_source = issuer.bind_selected_package_source(
            declaration=declaration, selected=selected_observation
        )
        assert (
            issuer.read_selected_package_source(selected_source)
            .expectation.package_id
            == package[0].package_id
        )


async def test_original_v3_selection_refuses_ambiguity_and_changed_source(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        _author_v3_repository(root, duplicate_name=True)
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )
        with pytest.raises(SourceObservationUnavailable, match="ambiguous"):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("package", "network-example")
            )
        with pytest.raises(SourceObservationUnavailable, match="unavailable"):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("package", "ontology")
            )
        with pytest.raises(SourceObservationUnavailable, match="unavailable"):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("repository", "other")
            )
        module = root / "workspaces/network/modules/main/aware.module.toml"
        module.write_text(module.read_text() + "\n# changed\n")
        with pytest.raises(SourceObservationUnavailable):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("workspace", "Network")
            )


async def test_package_selection_is_local_and_repository_collision_refuses(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        _author_v3_repository(root, cross_scope_name=True)
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )
        selected = issuer.inspect_materialization_roots(
            declaration, selection=_selection("package", "shared-example")
        )
        assert [
            (root.workspace_manifest_path, root.package_id) for root in selected
        ] == [
            ("workspaces/network/aware.workspace.toml", "example")
        ]
        with pytest.raises(SourceObservationUnavailable, match="coordinate_ambiguous"):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("repository", "demo")
            )


async def test_v1_module_cannot_supply_v3_semantic_root_selection(tmp_path):
    async with fixture(tmp_path) as (_, _, observer, issuer, _, expectation):
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )
        with pytest.raises(SourceObservationUnavailable, match="v3_required"):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("package", "network-example")
            )


async def test_exact_address_selects_one_v3_module_with_unrelated_v1(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        _author_v3_repository(root)
        workspace = root / "workspaces/network/aware.workspace.toml"
        workspace.write_text(
            workspace.read_text()
            + '\n[[workspace.modules]]\nid="legacy"\npath="modules/legacy"\n'
        )
        legacy = root / "workspaces/network/modules/legacy"
        (legacy / "package").mkdir(parents=True)
        (legacy / "package/aware.example.toml").write_bytes(b"legacy")
        (legacy / "aware.module.toml").write_text(
            'aware=1\n[module]\n[[packages]]\nid="example"\n'
            'kind="example"\nmanifest="package/aware.example.toml"\n'
            'visibility="module"\n'
        )
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )

        selected = issuer.inspect_exact_materialization_root(
            declaration,
            workspace_handle="Network",
            module_id="main",
            package_id="example",
        )
        assert (
            selected.workspace_manifest_path,
            selected.module_id,
            selected.package_id,
            selected.semantic_package_name,
        ) == (
            "workspaces/network/aware.workspace.toml",
            "main",
            "example",
            "network-example",
        )
        with pytest.raises(SourceObservationUnavailable, match="v3_required"):
            issuer.inspect_materialization_roots(
                declaration, selection=_selection("package", "network-example")
            )
        with pytest.raises(SourceObservationUnavailable, match="v3_required"):
            issuer.inspect_exact_materialization_root(
                declaration,
                workspace_handle="Network",
                module_id="legacy",
                package_id="example",
            )

        source_observation = observer.observe_selected_package(
            declaration=observed,
            workspace_manifest_path=selected.workspace_manifest_path,
            module_id=selected.module_id,
            package_id=selected.package_id,
        )
        source = issuer.bind_selected_package_source(
            declaration=declaration, selected=source_observation
        )
        assert issuer.read_selected_package_source(source).expectation.package_id == (
            selected.package_id
        )


async def test_exact_address_refuses_substitution_and_changed_source(tmp_path):
    async with fixture(tmp_path) as (root, _, observer, issuer, _, expectation):
        _author_v3_repository(root)
        observed = observer.observe_declarations()
        declaration = issuer.capture_declaration_scope(
            observation=observed,
            consumer_scope_key="workspaces/network/aware.workspace.toml",
            expectation=expectation,
        )
        for address in (
            ("Other", "main", "example"),
            ("Network", "other", "example"),
            ("Network", "main", "other"),
        ):
            with pytest.raises(SourceObservationUnavailable, match="unavailable"):
                issuer.inspect_exact_materialization_root(
                    declaration,
                    workspace_handle=address[0],
                    module_id=address[1],
                    package_id=address[2],
                )
        with pytest.raises(TypeError, match="address fields"):
            issuer.inspect_exact_materialization_root(
                declaration,
                workspace_handle="Network",
                module_id="main",
                package_id="",
            )
        module = root / "workspaces/network/modules/main/aware.module.toml"
        module.write_text(module.read_text() + "\n# changed\n")
        with pytest.raises(SourceObservationUnavailable):
            issuer.inspect_exact_materialization_root(
                declaration,
                workspace_handle="Network",
                module_id="main",
                package_id="example",
            )
