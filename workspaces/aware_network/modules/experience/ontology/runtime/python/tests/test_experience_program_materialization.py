from __future__ import annotations

from pathlib import Path
import types
from uuid import uuid4

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.program.compiler import load_program_ownership_from_sources
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from ._experience_runtime_test_paths import REPO_ROOT


def test_projection_catalog_branch_ids_include_explicit_reference_branches() -> None:
    import aware_experience.materialization.service as materialization_service

    base_branch_id = uuid4()
    explicit_branch_id = uuid4()
    branch_ids = materialization_service._program_projection_catalog_branch_ids(
        base_branch_id=base_branch_id,
        ports=(types.SimpleNamespace(projection="aware_control_identity"),),
        projection_reference_branch_ids_by_name={
            "aware_control_identity": explicit_branch_id
        },
    )

    assert branch_ids[0] == base_branch_id
    assert explicit_branch_id in branch_ids

    profile_branch_ids = (
        materialization_service._environment_profile_projection_catalog_branch_ids(
            base_branch_id=base_branch_id,
            spec=types.SimpleNamespace(
                experience_name="aware_actor_roles",
                process_configs=(),
                view_event_transitions=(
                    types.SimpleNamespace(
                        source_projection_experience_name="aware_actor_roles",
                        target_projection_experience_name="aware_control_identity",
                    ),
                ),
            ),
            projection_reference_branch_ids_by_name={
                "aware_control_identity": explicit_branch_id
            },
        )
    )

    assert profile_branch_ids[0] == base_branch_id
    assert explicit_branch_id in profile_branch_ids


def test_snapshot_commit_id_includes_pre_state_for_reversion_commits() -> None:
    from aware_experience.materialization.snapshot_commit import _snapshot_commit_id

    namespace = uuid4()
    branch_id = uuid4()
    root_object_id = uuid4()
    projection_hash = "projection-hash"
    graph_hash_post = "state-a"
    first_parent_commit_id = uuid4()
    later_parent_commit_id = uuid4()

    first_commit_id = _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        parent_commit_id=first_parent_commit_id,
        graph_hash_pre="empty",
        graph_hash_post=graph_hash_post,
    )
    reversion_commit_id = _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        parent_commit_id=first_commit_id,
        graph_hash_pre="state-b",
        graph_hash_post=graph_hash_post,
    )

    assert reversion_commit_id != first_commit_id
    assert first_commit_id == _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        parent_commit_id=first_parent_commit_id,
        graph_hash_pre="empty",
        graph_hash_post=graph_hash_post,
    )
    repeated_reversion_commit_id = _snapshot_commit_id(
        namespace=namespace,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_object_id,
        parent_commit_id=later_parent_commit_id,
        graph_hash_pre="state-b",
        graph_hash_post=graph_hash_post,
    )

    assert repeated_reversion_commit_id != reversion_commit_id


def test_program_port_node_materialization_uses_full_canonical_node_ref() -> None:
    import aware_experience.materialization.service as materialization_service

    projection_id = uuid4()
    projection_node_id = uuid4()
    projection = types.SimpleNamespace(id=projection_id, name="role")
    projection_node = types.SimpleNamespace(id=projection_node_id, key="role.Role")
    node_contract = types.SimpleNamespace(
        key="role",
        node="role.Role",
        identity=None,
    )

    snapshot = materialization_service._resolve_program_port_node_snapshot(
        catalog={
            "nodes_by_projection_and_key": {
                (projection_id, "role.role"): projection_node,
            },
            "identities_by_node_and_key": {},
        },
        projection=projection,
        node_contract=node_contract,
    )

    assert snapshot.projection_experience_node_id == projection_node_id
    assert snapshot.key == "role"
    assert snapshot.identity is None


def test_program_port_node_materialization_uses_compiled_literal_identity() -> None:
    import aware_experience.materialization.service as materialization_service

    projection_id = uuid4()
    projection_node_id = uuid4()
    projection_node_identity_id = uuid4()
    projection = types.SimpleNamespace(id=projection_id, name="home_story")
    projection_node = types.SimpleNamespace(id=projection_node_id, key="home.Home")
    projection_node_identity = types.SimpleNamespace(
        id=projection_node_identity_id,
        key="home",
    )
    node_contract = types.SimpleNamespace(
        key="home",
        node="home.Home",
        identity="home",
    )

    snapshot = materialization_service._resolve_program_port_node_snapshot(
        catalog={
            "nodes_by_projection_and_key": {
                (projection_id, "home.home"): projection_node,
            },
            "identities_by_node_and_key": {
                (projection_node_id, "home"): projection_node_identity,
            },
        },
        projection=projection,
        node_contract=node_contract,
    )

    assert snapshot.projection_experience_node_id == projection_node_id
    assert snapshot.key == "home"
    assert snapshot.identity is not None
    assert (
        snapshot.identity.projection_experience_node_identity_id
        == projection_node_identity_id
    )


def test_program_invoke_port_node_id_accepts_direct_node_alias() -> None:
    from aware_experience.program.language import PlanCall, PlanSymbolRef
    import aware_experience.materialization.service as materialization_service

    port_node_id = uuid4()

    resolved = materialization_service._program_invoke_port_node_id(
        call=PlanCall(
            target="role.Role.create",
            args=(),
            object_expr=PlanSymbolRef(name="role"),
        ),
        port_node_ids_by_ref={"role": port_node_id},
    )

    assert resolved == port_node_id


def test_program_invoke_port_node_id_accepts_explicit_program_port_ref() -> None:
    from aware_experience.program.language import PlanCall, PlanSymbolRef
    import aware_experience.materialization.service as materialization_service

    port_node_id = uuid4()

    resolved = materialization_service._program_invoke_port_node_id(
        call=PlanCall(
            target="role.Role.create",
            args=(),
            object_expr=PlanSymbolRef(
                name="program.port.role_role_id.projection_node.role"
            ),
        ),
        port_node_ids_by_ref={
            "program.port.role_role_id.projection_node.role": port_node_id
        },
    )

    assert resolved == port_node_id


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_program_package_fixture(*, workspace_root: Path) -> Path:
    _write(
        workspace_root / "aware.environment.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[environment]",
                'handle = "program-materialization-workspace"',
                'modules = ["experience"]',
            ]
        )
        + "\n",
    )
    experience_toml_path = workspace_root / "aware.experience.toml"
    _write(
        experience_toml_path,
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "program-materialization"',
                'fqn_prefix = "program_materialization"',
                'title = "Program Materialization"',
                "",
                "[build]",
                'environment_handle = "program-materialization-workspace"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "aware.programs.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "program_materialization:LocalProgram_v1"',
                'path = "programs/local_program_v1.aware"',
                'name = "LocalProgram_v1"',
                'required_symbols = ["plan.message_text"]',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "experiences.aware",
        "\n".join(
            [
                "experience program_materialization on aware_test.root.Root {",
                "    observable default {",
                "        view home default api_view root.home {}",
                "    }",
                "    node aware_test.root.Root {",
                "        id default",
                "    }",
                "}",
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "programs" / "local_program_v1.aware",
        "program LocalProgram_v1(message_text String) {}\n",
    )
    return experience_toml_path


def test_source_compile_plan_payload_filters_program_sources(tmp_path: Path) -> None:
    workspace_root = tmp_path / "experience_program_source_filter"
    experience_toml_path = _write_program_package_fixture(workspace_root=workspace_root)
    _write(
        workspace_root / "actions.aware",
        "action local_action { program LocalProgram_v1() }\n",
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=experience_toml_path,
        repo_root=workspace_root,
    ).build_snapshot()

    from aware_experience.materialization import service as materialization_service

    payload = materialization_service._build_source_experience_compile_plan_payload(
        snapshot=snapshot,
    )

    assert [item["path"] for item in payload["program_ownership"]] == [
        "programs/local_program_v1.aware"
    ]


def test_aware_control_owns_unversioned_interface_boot_program() -> None:
    repo_root = REPO_ROOT
    package_root = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "interface"
        / "experiences"
        / "aware_control"
    )
    projections = load_projection_experience_ownership_from_sources(
        package_root=package_root,
        source_files=(Path("experiences.aware"),),
    )

    programs = load_program_ownership_from_sources(
        package_root=package_root,
        source_files=(Path("programs/interface/ensure_boot_interface_graph.aware"),),
        fqn_prefix="aware_control",
        projection_experience_ownership=projections,
    )

    assert [(item.ref, item.name, item.path) for item in programs] == [
        (
            "aware_control:EnsureBootInterfaceGraph",
            "EnsureBootInterfaceGraph",
            "programs/interface/ensure_boot_interface_graph.aware",
        )
    ]
    program = programs[0]
    assert "_v" not in program.ref
    assert "_v" not in program.name
    assert program.dependencies == ("interface-ontology",)
    assert program.invocation_plan_artifact is not None
    assert program.program_config_plan_artifact is not None
    assert program.program_apply_calls_artifact is not None
    assert len(program.required_projection_ids) == 2
    assert len(program.required_projection_node_ids) == 2
