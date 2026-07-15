from __future__ import annotations

import types
from pathlib import Path
from typing import Any, Callable, cast
from uuid import UUID, uuid4

import pytest

from aware_attention_ontology.stable_ids import stable_attention_package_id
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_code_ontology.code.code import Code
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.package.code_package import CodePackage
from aware_code_ontology.stable_ids import stable_code_package_id
from aware_experience_ontology.environment.environment_experience import (
    EnvironmentExperience,
)
from aware_experience_ontology.environment.experience_package_attention_package import (
    ExperiencePackageAttentionPackage,
)
from aware_experience_ontology.environment.experience_package_dependency import (
    ExperiencePackageDependency,
)
from aware_experience_ontology.stable_ids import (
    stable_experience_package_attention_package_id,
    stable_experience_package_dependency_id,
    stable_experience_package_id,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience.materialization import lane_state
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_opgi_index,
    build_meta_graph_runtime_for_aware_package_manifests,
    find_meta_graph_projection_hash_by_name,
)
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_orm.session.session import Session
from ._experience_runtime_test_paths import REPO_ROOT


def test_package_orchestrator_derives_external_projection_lanes_from_committed_workspace_dependency() -> (
    None
):
    from aware_experience.manifest import load_aware_experience_toml_spec
    from aware_experience.materialization.branches import (
        derive_experience_reference_branch_id,
    )
    from aware_experience.materialization.package_orchestrator import (
        _resolve_dependency_projection_reference_branch_ids,
    )

    dependency_branch_id = uuid4()
    manifest_spec = load_aware_experience_toml_spec(
        toml_path=(
            REPO_ROOT
            / "workspaces/aware_coordination/modules/workflow/experiences/aware-goals/aware.experience.toml"
        )
    )

    branch_ids = _resolve_dependency_projection_reference_branch_ids(
        manifest_spec=manifest_spec,
        compile_plan_payload={
            "projection_experience_ownership": [
                {"name": "aware_goals", "projection": "Goal"}
            ],
            "environment_profile_ownership": [
                {
                    "experience_name": "aware_goals",
                    "process_configs": [
                        {
                            "thread_configs": [
                                {
                                    "projection_experiences": [
                                        {
                                            "experience_name": "aware_conversation_spaces"
                                        },
                                        {"experience_name": "aware_goals"},
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ],
        },
        semantic_materialization_context={
            "workspace_experience_package_references": (
                {
                    "package_name": "aware-conversations",
                    "semantic_branch_id": str(dependency_branch_id),
                },
            )
        },
        existing=None,
    )

    assert branch_ids == {
        "aware_conversation_spaces": derive_experience_reference_branch_id(
            base_branch_id=dependency_branch_id,
            experience_name="aware_conversation_spaces",
        )
    }

    branch_ids_from_explicit_package_base = (
        _resolve_dependency_projection_reference_branch_ids(
            manifest_spec=manifest_spec,
            compile_plan_payload={
                "projection_experience_ownership": [
                    {"name": "aware_goals", "projection": "Goal"}
                ],
                "environment_profile_ownership": [
                    {
                        "process_configs": [
                            {
                                "thread_configs": [
                                    {
                                        "projection_experiences": [
                                            {
                                                "experience_name": "aware_conversation_spaces"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
            },
            semantic_materialization_context=None,
            existing={"aware-conversations": dependency_branch_id},
        )
    )
    assert branch_ids_from_explicit_package_base[
        "aware_conversation_spaces"
    ] == derive_experience_reference_branch_id(
        base_branch_id=dependency_branch_id,
        experience_name="aware_conversation_spaces",
    )


def _experience_meta_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
    )


def _experience_meta_python_roots(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/api/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_kernel/modules/sdk/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_runtime",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/python/orm_models",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/runtime/python",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/runtime/python",
    )


def _prepend_experience_meta_python_roots(
    *,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    syspath_prepend = cast(Callable[[str], None], monkeypatch.syspath_prepend)
    for python_root in _experience_meta_python_roots(repo_root):
        if python_root.exists():
            syspath_prepend(str(python_root))


def _build_experience_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    from aware_experience.handlers._generated import (  # noqa: WPS433
        meta_handlers as experience_meta_handlers,
    )
    from aware_reactivity.handlers._generated import (  # noqa: WPS433
        meta_handlers as reactivity_meta_handlers,
    )

    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_experience_meta_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedLanguageHandlerModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
        bootstrap_modules=(
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, reactivity_meta_handlers),
            ),
            cast(
                MetaGraphGeneratedConstructorBootstrapModule,
                cast(Any, experience_meta_handlers),
            ),
        ),
    )
    assert runtime.context is not None
    return runtime


def _experience_source_code_package_config_id() -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_experience_toml",
            surface="experience",
        )
    )


def _experience_source_code_package_id(*, package_name: str) -> UUID:
    return stable_code_package_id(
        code_package_config_id=_experience_source_code_package_config_id(),
        package_name=package_name,
        language=CodeLanguage.aware.value,
    )


def test_experience_source_code_package_identity_uses_source_config() -> None:
    from aware_experience.materialization import (  # noqa: WPS433
        service as materialization_service,
    )

    assert (
        materialization_service.experience_source_code_package_config_id()
        == _experience_source_code_package_config_id()
    )
    assert materialization_service.experience_source_code_package_id(
        package_name="home-story",
    ) == _experience_source_code_package_id(package_name="home-story")


def test_identity_default_experience_projection_nodes_match_program_ports() -> None:
    from aware_experience.projection import (  # noqa: WPS433
        load_projection_experience_ownership_from_sources,
    )
    from aware_experience.program.language import (  # noqa: WPS433
        PlanLocalRef,
        compile_invocation_plans,
        compile_program_config_plans,
    )

    repo_root = REPO_ROOT
    package_root = (
        repo_root
        / "workspaces"
        / "aware_network"
        / "modules"
        / "identity"
        / "experiences"
        / "aware_identity"
    )
    ownerships = load_projection_experience_ownership_from_sources(
        package_root=package_root,
        source_files=(Path("experiences.aware"),),
    )
    ownership_by_name = {ownership.name: ownership for ownership in ownerships}

    identity_nodes = tuple(ownership_by_name["identity"].nodes)
    assert [(node.name, node.node_ref) for node in identity_nodes] == [
        ("identity.Identity", "identity.Identity")
    ]
    assert [identity.key for identity in identity_nodes[0].identities] == ["identity"]

    organization_nodes = tuple(ownership_by_name["organization"].nodes)
    assert [(node.name, node.node_ref) for node in organization_nodes] == [
        ("organization.Organization", "organization.Organization")
    ]
    assert [identity.key for identity in organization_nodes[0].identities] == [
        "organization"
    ]

    role_nodes = tuple(ownership_by_name["role"].nodes)
    assert [(node.name, node.node_ref) for node in role_nodes] == [
        ("role.Role", "role.Role")
    ]
    assert [identity.key for identity in role_nodes[0].identities] == ["role"]

    actor_role_nodes = tuple(ownership_by_name["actor_role"].nodes)
    assert [(node.name, node.node_ref) for node in actor_role_nodes] == [
        ("actor.Actor::actor_roles", "actor.Actor::actor_roles")
    ]
    assert [identity.key for identity in actor_role_nodes[0].identities] == [
        "actor_role"
    ]

    actor_subscription_nodes = tuple(ownership_by_name["actor_subscription"].nodes)
    assert [(node.name, node.node_ref) for node in actor_subscription_nodes] == [
        ("actor.Actor::actor_subscriptions", "actor.Actor::actor_subscriptions")
    ]
    assert [identity.key for identity in actor_subscription_nodes[0].identities] == [
        "actor_subscription"
    ]

    event_scope_nodes = tuple(
        ownership_by_name["event_config_condition_config_scope"].nodes
    )
    assert [(node.name, node.node_ref) for node in event_scope_nodes] == [
        (
            "event.EventConfigConditionConfigScope",
            "event.EventConfigConditionConfigScope",
        )
    ]
    assert [identity.key for identity in event_scope_nodes[0].identities] == [
        "event_config_condition_config_scope"
    ]

    role_config_nodes = tuple(ownership_by_name["role_config"].nodes)
    assert [(node.name, node.node_ref) for node in role_config_nodes] == [
        ("role.RoleConfig", "role.RoleConfig"),
        (
            "role.RoleConfig::role_config_class_configs",
            "role.RoleConfig::role_config_class_configs",
        ),
    ]
    assert [identity.key for identity in role_config_nodes[0].identities] == [
        "role_config"
    ]
    assert [identity.key for identity in role_config_nodes[1].identities] == [
        "role_config_class_config"
    ]

    expected_port_nodes = {
        "programs/seed/ensure_identity_signup_v0.aware": {
            "identity": {
                "identity": (
                    "identity.Identity",
                    "identity",
                    "identity_id",
                ),
            },
        },
        "programs/seed/ensure_agent_identity_signup_via_profile_v0.aware": {
            "identity": {
                "identity": (
                    "identity.Identity",
                    "identity",
                    "identity_id",
                ),
            },
        },
        "programs/seed/ensure_provider_organization_v0.aware": {
            "organization": {
                "organization": (
                    "organization.Organization",
                    "organization",
                    "organization_id",
                ),
            },
        },
        "programs/policy/ensure_actor_role_binding_v1.aware": {
            "role": {
                "role": (
                    "role.Role",
                    "role",
                    "role_id",
                ),
            },
            "actor_role": {
                "actor_role": (
                    "actor.Actor::actor_roles",
                    "actor_role",
                    "actor_role_id",
                ),
            },
        },
        "programs/policy/ensure_actor_role_binding_from_branch_v1.aware": {
            "role": {
                "role": (
                    "role.Role",
                    "role",
                    "role_id",
                ),
            },
            "actor_role": {
                "actor_role": (
                    "actor.Actor::actor_roles",
                    "actor_role",
                    "actor_role_id",
                ),
            },
        },
        "programs/policy/ensure_actor_subscription_binding_v1.aware": {
            "actor_subscription": {
                "actor_subscription": (
                    "actor.Actor::actor_subscriptions",
                    "actor_subscription",
                    "actor_subscription_id",
                ),
            },
        },
        "programs/policy/ensure_actor_subscription_binding_from_branch_v1.aware": {
            "actor_subscription": {
                "actor_subscription": (
                    "actor.Actor::actor_subscriptions",
                    "actor_subscription",
                    "actor_subscription_id",
                ),
            },
        },
        "programs/policy/ensure_actor_act_react_binding_from_branch_v1.aware": {
            "role": {
                "role": (
                    "role.Role",
                    "role",
                    "role_id",
                ),
            },
            "actor_role": {
                "actor_role": (
                    "actor.Actor::actor_roles",
                    "actor_role",
                    "actor_role_id",
                ),
            },
            "actor_subscription": {
                "actor_subscription": (
                    "actor.Actor::actor_subscriptions",
                    "actor_subscription",
                    "actor_subscription_id",
                ),
            },
        },
        "programs/policy/ensure_event_scope_binding_from_branch_v1.aware": {
            "event_config_condition_config_scope": {
                "event_scope": (
                    "event.EventConfigConditionConfigScope",
                    "event_config_condition_config_scope",
                    "event_config_condition_config_scope_id",
                ),
            },
        },
        "programs/policy/role_config_tool_policies_v1.aware": {
            "role_config": {
                "main": (
                    "role.RoleConfig",
                    "role_config",
                    "role_config_id",
                ),
                "role_config_class_config": (
                    "role.RoleConfig::role_config_class_configs",
                    "role_config_class_config",
                    "role_config_class_config_id",
                ),
            },
        },
    }

    for source_rel, projections in expected_port_nodes.items():
        source = (package_root / source_rel).read_text(encoding="utf-8")
        config_plan = compile_program_config_plans(
            source,
            require_config_contract_surface=True,
        )[0]
        invocation_plan = compile_invocation_plans(source)[0]
        input_names = {
            getattr(step, "name", "")
            for step in invocation_plan.steps
            if getattr(step, "name", "")
        }
        ports_by_projection = {port.projection: port for port in config_plan.ports}
        for projection, expected_nodes in projections.items():
            branch_input = f"{projection}_branch_id"
            if projection in {
                "actor_role",
                "actor_subscription",
                "event_config_condition_config_scope",
            }:
                assert branch_input in input_names
            port = ports_by_projection[projection]
            nodes_by_key = {node.key: node for node in port.projection_node_identities}
            for node_key, (node_ref, key_name, value_name) in expected_nodes.items():
                node = nodes_by_key[node_key]
                assert node.node == node_ref
                assert node.identity is None
                assert len(node.args) == 1
                assert node.args[0].name == key_name
                assert node.args[0].value_expr == PlanLocalRef(name=value_name)

        if (
            source_rel
            == "programs/policy/ensure_event_scope_binding_from_branch_v1.aware"
        ):
            invoke_targets = [
                step.call.target
                for step in invocation_plan.steps
                if getattr(getattr(step, "call", None), "target", None)
            ]
            assert (
                "event.EventConfigConditionConfigScope."
                "create_via_event_config_condition_config"
            ) in invoke_targets
            assert "event.EventConfigConditionConfigScope.create" not in invoke_targets


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_experience_package_fixture(
    *,
    workspace_root: Path,
    extra_experience: bool = False,
    dependency_package_name: str | None = None,
    dependency_kind: str = "experience_package",
    language_targets: bool = False,
) -> Path:
    _write(
        workspace_root / "aware.environment.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[environment]",
                'handle = "home-story-workspace"',
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
                'package_name = "home-story"',
                'fqn_prefix = "home_story"',
                'title = "Home Story"',
                'description = "Narrative experience package for the home workspace."',
                "",
                "[build]",
                'environment_handle = "home-story-workspace"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
            ]
        )
        + "\n",
    )
    if dependency_package_name is not None:
        with experience_toml_path.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n".join(
                    [
                        "",
                        "[[dependencies]]",
                        f'package_name = "{dependency_package_name}"',
                        f'kind = "{dependency_kind}"',
                        "version_number = 1",
                    ]
                )
                + "\n"
            )
    if language_targets:
        with experience_toml_path.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n".join(
                    [
                        "",
                        "[targets.dart]",
                        'root_dir = "languages/dart"',
                        'package_dir = "home_story"',
                        "",
                        "[targets.python]",
                        'root_dir = "languages/python"',
                        'package_dir = "home_story"',
                    ]
                )
                + "\n"
            )
    lines = [
        "experience home_story on aware_home.home.Home {",
        "    observable security {",
        "        view door default api_view home.door {",
        '            """Door state view."""',
        "        }",
        "    }",
        "",
        "    node home.Home {",
        "        id home",
        "    }",
        "}",
        "",
    ]
    if extra_experience:
        lines.extend(
            [
                "experience home_alt on aware_home.home.Home {",
                "    observable security {",
                "        view alt default api_view home.alt {",
                '            """Alternate view."""',
                "        }",
                "    }",
                "",
                "    node home.Home {",
                "        id home_alt",
                "    }",
                "}",
                "",
            ]
        )
    _write(workspace_root / "experiences.aware", "\n".join(lines))
    if language_targets:
        _write(
            workspace_root / "views" / "security" / "door" / "v1.aware",
            "\n".join(
                [
                    "class DoorViewStateV1 : inline_value {",
                    '    label String = "Door"',
                    '    status String = "closed"',
                    "}",
                    "",
                ]
            ),
        )
    return experience_toml_path


class _FailClosedSemanticRuntime:
    @property
    def manifest_path(self) -> Path:
        return Path("/tmp/aware-fail-closed-experience-runtime-manifest.json")

    @property
    def invoker(self) -> object:
        return _FailClosedSemanticInvoker()


class _FailClosedSemanticInvoker:
    async def invoke_function_with_index(self, **_: object) -> object:
        raise AssertionError(
            "Experience Workspace materialization must not route through legacy runtime harness"
        )


def test_resolve_experience_package_materialization_spec_accepts_multiple_experience_declarations(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "experience_package_spec_multiple"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
        extra_experience=True,
    )

    from aware_experience.materialization import (
        resolve_experience_package_materialization_spec,
    )  # noqa: WPS433

    spec = resolve_experience_package_materialization_spec(
        experience_toml_path=experience_toml_path,
        workspace_root=workspace_root,
    )

    assert spec.experience_names == ("home_alt", "home_story")
    assert spec.experience_name == "home_alt"


def test_experience_package_compile_resolves_canonical_repo_root(
    tmp_path: Path,
) -> None:
    from aware_experience.materialization.package_orchestrator import (  # noqa: WPS433
        _resolve_experience_compile_repo_root,
    )

    repo_root = tmp_path / "repo"
    workspace_root = repo_root / "workspaces" / "consumer"
    workspace_root.mkdir(parents=True)
    (repo_root / "aware.repo.toml").write_text("aware_repo = 1\n", encoding="utf-8")

    assert _resolve_experience_compile_repo_root(workspace_root=workspace_root) == (
        repo_root
    )
    assert (
        _resolve_experience_compile_repo_root(
            workspace_root=tmp_path / "isolated",
        )
        == (tmp_path / "isolated").resolve()
    )


@pytest.mark.asyncio
async def test_experience_package_preflights_all_generated_lanes_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.materialization import (  # noqa: WPS433
        package_orchestrator,
    )

    branch_id = uuid4()
    calls: list[tuple[str, str]] = []

    async def _reset_stale_lane(
        *,
        index: object,
        branch_id: UUID,
        projection_hash: str,
        error_context: str,
    ) -> bool:
        del index
        assert branch_id == expected_branch_id
        calls.append((projection_hash, error_context))
        return projection_hash == "experience-package-hash"

    expected_branch_id = branch_id
    monkeypatch.setattr(
        package_orchestrator,
        "reset_stale_generated_projection_lane_if_needed",
        _reset_stale_lane,
    )

    reset_projection_names = (
        await package_orchestrator._reset_stale_generated_package_lanes_if_needed(
            index=cast(Any, object()),
            branch_id=branch_id,
            projection_hashes_by_name=(
                ("EnvironmentExperience", "environment-experience-hash"),
                ("CodePackage", "code-package-hash"),
                ("ExperiencePackage", "experience-package-hash"),
            ),
        )
    )

    assert reset_projection_names == ("ExperiencePackage",)
    assert [projection_hash for projection_hash, _ in calls] == [
        "environment-experience-hash",
        "code-package-hash",
        "experience-package-hash",
    ]
    assert [error_context for _, error_context in calls] == [
        "Experience package generated lane preflight (EnvironmentExperience)",
        "Experience package generated lane preflight (CodePackage)",
        "Experience package generated lane preflight (ExperiencePackage)",
    ]


def test_source_experience_compile_plan_payload_uses_api_view_mounts_only(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "experience_package_source_payload_api_view"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
    )

    from aware_experience.compiler.compile import (  # noqa: WPS433
        compile_experience_workspace,
    )
    from aware_experience.materialization import (  # noqa: WPS433
        service as materialization_service,
    )

    compile_result = compile_experience_workspace(
        toml_path=experience_toml_path,
        repo_root=workspace_root,
    )

    payload = materialization_service._build_source_experience_compile_plan_payload(
        snapshot=compile_result.snapshot,
    )

    assert payload["view_api_ownership"] is None
    projection_ownership = cast(
        list[dict[str, Any]], payload["projection_experience_ownership"]
    )
    views = cast(
        list[dict[str, Any]],
        projection_ownership[0]["observables"][0]["views"],
    )
    assert [
        (view["key"], view.get("api_view_ref"), view.get("state_model_ref"))
        for view in views
    ] == [("door", "home.door", None)]


def test_experience_source_rejects_state_owned_view_contract(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "experience_package_state_view_rejected"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
    )
    (workspace_root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "    observable security {",
                "        view door default state aware_home.home.Door {}",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from aware_experience.compiler.builder import (  # noqa: WPS433
        build_experience_compile_plan,
    )
    from aware_experience.compiler.workspace import (  # noqa: WPS433
        ExperienceWorkspace,
    )

    with pytest.raises(ValueError, match="must not declare Experience-owned state"):
        build_experience_compile_plan(
            snapshot=ExperienceWorkspace.from_toml(
                toml_path=experience_toml_path,
                repo_root=workspace_root,
            ).build_snapshot(),
            repo_root=workspace_root,
        )


def test_experience_source_rejects_nested_view_actions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "experience_package_view_action_rejected"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
    )
    (workspace_root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "    observable security {",
                "        view door default api_view home.door {",
                "            action select view {}",
                "        }",
                "    }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from aware_experience.compiler.builder import (  # noqa: WPS433
        build_experience_compile_plan,
    )
    from aware_experience.compiler.workspace import (  # noqa: WPS433
        ExperienceWorkspace,
    )

    with pytest.raises(ValueError, match="ApiViewCapabilityEndpoint owns view actions"):
        build_experience_compile_plan(
            snapshot=ExperienceWorkspace.from_toml(
                toml_path=experience_toml_path,
                repo_root=workspace_root,
            ).build_snapshot(),
            repo_root=workspace_root,
        )


def test_code_experience_source_payload_mounts_code_api_views() -> None:
    from aware_experience.compiler.compile import (  # noqa: WPS433
        compile_experience_workspace,
    )
    from aware_experience.materialization import (  # noqa: WPS433
        service as materialization_service,
    )

    workspace_root = REPO_ROOT / "workspaces/aware_network"
    experience_toml_path = (
        workspace_root
        / "modules/code/experiences/aware_code_experience/aware.experience.toml"
    )

    compile_result = compile_experience_workspace(
        toml_path=experience_toml_path,
        repo_root=workspace_root,
    )
    payload = materialization_service._build_source_experience_compile_plan_payload(
        snapshot=compile_result.snapshot,
    )

    assert payload["view_api_ownership"] is None
    projection_ownership = cast(
        list[dict[str, Any]], payload["projection_experience_ownership"]
    )
    views = cast(
        list[dict[str, Any]],
        projection_ownership[0]["observables"][0]["views"],
    )
    assert {
        (view["key"], view.get("api_view_ref"), view.get("state_model_ref"))
        for view in views
    } == {
        ("editor.v1", "code.editor", None),
        ("selector.v1", "code.package_selector", None),
    }


def test_projection_materialization_specs_can_skip_unresolved_runtime_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.materialization import (
        service as materialization_service,
    )  # noqa: WPS433
    from aware_experience.materialization import (
        projection_contract_materialization,
    )  # noqa: WPS433

    payloads = [
        {
            "projection_experience_ownership": [
                {
                    "name": "home_story",
                    "projection": "home",
                    "source_path": "experiences.aware",
                    "branches": [],
                    "observables": [
                        {
                            "key": "security",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "door",
                                    "is_default": True,
                                    "api_view_ref": "home.door",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                    ],
                    "nodes": [],
                },
                {
                    "name": "missing_story",
                    "projection": "missing",
                    "source_path": "experiences.aware",
                    "branches": [],
                    "observables": [
                        {
                            "key": "missing",
                            "source_path": "experiences.aware",
                            "views": [
                                {
                                    "key": "default",
                                    "is_default": True,
                                    "api_view_ref": "missing.default",
                                    "source_path": "experiences.aware",
                                },
                            ],
                        },
                    ],
                    "nodes": [],
                },
            ],
        }
    ]

    class _Resolver:
        def resolve(self, **kwargs: object) -> object:
            if kwargs["experience_name"] == "missing_story":
                raise RuntimeError("projection unavailable in runtime")
            return types.SimpleNamespace(
                projection_key=kwargs["projection_key"],
                opgi_id=uuid4(),
            )

    monkeypatch.setattr(
        projection_contract_materialization,
        "build_projection_runtime_resolver",
        lambda *, index: _Resolver(),
    )

    with pytest.raises(RuntimeError, match="projection unavailable"):
        materialization_service.resolve_projection_materialization_specs(
            compile_plan_payloads=payloads,
            index=object(),
        )

    specs = materialization_service.resolve_projection_materialization_specs(
        compile_plan_payloads=payloads,
        index=object(),
        allow_unresolved_projection_experiences=True,
    )

    assert len(specs) == 1
    assert specs[0].experience_name == "home_story"


def test_environment_profile_catalog_filter_skips_unresolved_projection_refs() -> None:
    from aware_experience.materialization import (
        service as materialization_service,
    )  # noqa: WPS433

    resolved_projection_id = uuid4()
    layout_config_id = uuid4()
    spec = materialization_service.EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware_control",
        experience_name="aware_control_identity",
        key="os.default",
        source_path="profiles.aware",
        process_configs=(
            materialization_service.EnvironmentProfileProcessMaterializationSpec(
                type="continuous",
                key="control",
                process_key="control",
                source_path="profiles.aware",
                thread_configs=(
                    materialization_service.EnvironmentProfileThreadMaterializationSpec(
                        key="control.main",
                        thread_key="control.main",
                        source_path="profiles.aware",
                        projection_experiences=(
                            materialization_service.EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name="aware_control_identity",
                                projection_key="identity",
                                source_path="profiles.aware",
                            ),
                            materialization_service.EnvironmentProfileThreadProjectionMaterializationSpec(
                                projection_experience_name="aware_control_interface",
                                projection_key="interface_package",
                                source_path="profiles.aware",
                            ),
                        ),
                        layout_configs=(
                            materialization_service.EnvironmentProfileThreadLayoutMaterializationSpec(
                                layout_key="personal",
                                layout_config_id=layout_config_id,
                                source_path="profiles.aware",
                                sections=(
                                    materialization_service.EnvironmentProfileThreadLayoutSectionMaterializationSpec(
                                        section_key="identity_admission",
                                        projection_experience_name="aware_control_identity",
                                        projection_key="identity",
                                        view_key="identity.admission.v1",
                                        source_path="profiles.aware",
                                    ),
                                    materialization_service.EnvironmentProfileThreadLayoutSectionMaterializationSpec(
                                        section_key="interface_mount",
                                        projection_experience_name="aware_control_interface",
                                        projection_key="interface_package",
                                        view_key="package.mount.status.v1",
                                        source_path="profiles.aware",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        view_event_transitions=(
            materialization_service.EnvironmentProfileViewEventTransitionMaterializationSpec(
                key="mount.ready",
                source_projection_experience_name="aware_control_interface",
                source_view_key="package.mount.status.v1",
                trigger_event_config_ref="interface.mount.ready",
                target_projection_experience_name="aware_control_identity",
                target_section_graph_binding_key="identity.admission",
                source_path="profiles.aware",
            ),
        ),
    )
    catalog = {
        "projections_by_name": {
            "aware_control_identity": ProjectionExperience.model_construct(
                id=resolved_projection_id,
                name="aware_control_identity",
            )
        },
        "views_by_projection_and_name": {},
        "section_graph_bindings_by_projection_and_key": {},
        "nodes_by_projection_and_key": {},
        "identities_by_node_and_key": {},
    }

    result = (
        materialization_service._filter_environment_profile_spec_for_projection_catalog(
            spec=spec,
            catalog=catalog,
        )
    )

    thread = result.spec.process_configs[0].thread_configs[0]
    assert [
        item.projection_experience_name for item in thread.projection_experiences
    ] == ["aware_control_identity"]
    assert [
        section.projection_experience_name
        for section in thread.layout_configs[0].sections
    ] == ["aware_control_identity"]
    assert result.spec.view_event_transitions == ()
    assert result.skipped_projection_refs == ("aware_control_interface",)
    assert result.skipped_thread_projection_count == 1
    assert result.skipped_thread_layout_section_count == 1
    assert result.skipped_thread_layout_count == 0
    assert result.skipped_view_event_transition_count == 1


@pytest.mark.asyncio
async def test_reset_stale_generated_projection_lane_removes_unreplayable_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    projection_hash = "projection-hash"
    lane_dir = tmp_path / ".aware" / "oig" / str(branch_id) / projection_hash
    lane_dir.mkdir(parents=True, exist_ok=True)
    (lane_dir / "HEAD.json").write_text("{}", encoding="utf-8")

    class _FakeStore:
        aware_root = tmp_path

        async def head(self, **_kwargs: object) -> dict[str, str]:
            return {"commit_id": str(uuid4())}

    class _FakeMaterializer:
        def __init__(self, **_kwargs: object) -> None:
            pass

        async def get(self, **_kwargs: object) -> tuple[object, dict[str, object]]:
            raise RuntimeError("stale lane")

    class _FakeIndex:
        ocg = object()
        opg_by_hash = {projection_hash: object()}
        attribute_configs_by_id: dict[Any, Any] = {}
        class_configs_by_id: dict[Any, Any] = {}

    monkeypatch.setattr(lane_state, "FSCommitStore", _FakeStore)
    monkeypatch.setattr(lane_state, "OIGMaterializer", _FakeMaterializer)

    reset = await lane_state.reset_stale_generated_projection_lane_if_needed(
        index=cast(Any, _FakeIndex()),
        branch_id=branch_id,
        projection_hash=projection_hash,
        error_context="test",
    )

    assert reset is True
    assert not lane_dir.exists()


@pytest.mark.asyncio
async def test_environment_profile_lane_root_reuses_matching_committed_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.materialization import (
        service as materialization_service,
    )  # noqa: WPS433

    branch_id = uuid4()
    projection_hash = "environment-experience-projection"
    head_commit_id = uuid4()
    spec = materialization_service.EnvironmentProfileMaterializationSpec(
        fqn_prefix="aware_control",
        experience_name="aware_control_identity",
        key="os.default",
        source_path="profiles.aware",
        title="Aware OS",
        description="Control experience.",
    )
    root_id = (
        materialization_service.experience_stable_ids.stable_environment_experience_id(
            fqn_prefix=spec.fqn_prefix
        )
    )

    async def _fake_lane_head_commit_id(
        *, branch_id: UUID, projection_hash: str
    ) -> UUID:
        return head_commit_id

    async def _fake_hydrate_lane_root_from_head(
        **_kwargs: object,
    ) -> EnvironmentExperience:
        return EnvironmentExperience(
            id=root_id,
            fqn_prefix=spec.fqn_prefix,
            title=spec.title,
            description=spec.description,
        )

    async def _fake_invoke_constructor_environment_function(
        **_kwargs: object,
    ) -> object:
        raise AssertionError("matching committed root should not call opg_constructor")

    monkeypatch.setattr(
        materialization_service,
        "_lane_head_commit_id",
        _fake_lane_head_commit_id,
    )
    monkeypatch.setattr(
        materialization_service,
        "_hydrate_lane_root_from_head",
        _fake_hydrate_lane_root_from_head,
    )
    monkeypatch.setattr(
        materialization_service,
        "_invoke_constructor_environment_function",
        _fake_invoke_constructor_environment_function,
    )

    result = (
        await materialization_service._ensure_environment_experience_profile_lane_root(
            runtime=object(),
            index=object(),
            actor_id=None,
            lane=materialization_service.MaterializationLaneContext(
                branch_id=branch_id,
                projection_hash=projection_hash,
            ),
            function_id=uuid4(),
            spec=spec,
        )
    )

    assert result.commit_id is None
    assert result.head_commit_id == head_commit_id


@pytest.mark.asyncio
async def test_thread_config_lane_root_reuses_matching_committed_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from aware_experience.materialization import (
        service as materialization_service,
    )  # noqa: WPS433

    branch_id = uuid4()
    projection_hash = "thread-config-projection"
    process_config_id = uuid4()
    commit_id = uuid4()
    oig_commit_id = uuid4()
    thread_spec = materialization_service.EnvironmentProfileThreadMaterializationSpec(
        key="control.main",
        thread_key="control",
        source_path="profiles.aware",
        title="Control",
    )
    from aware_environment_ontology import stable_ids as environment_stable_ids

    thread_config_id = environment_stable_ids.stable_thread_config_id(
        process_config_id=process_config_id,
        key=thread_spec.key,
    )

    class _FakeStore:
        async def head(self, **_kwargs: object) -> dict[str, str]:
            return {
                "commit_id": str(commit_id),
                "object_instance_graph_commit_id": str(oig_commit_id),
                "root_object_id": str(thread_config_id),
            }

    async def _fake_invoke_constructor_environment_function(
        **_kwargs: object,
    ) -> object:
        raise AssertionError("matching committed root should not call opg_constructor")

    monkeypatch.setattr(materialization_service, "FSCommitStore", _FakeStore)
    monkeypatch.setattr(
        materialization_service,
        "_invoke_constructor_environment_function",
        _fake_invoke_constructor_environment_function,
    )

    result = await materialization_service._ensure_thread_config_lane_root(
        runtime=object(),
        index=object(),
        actor_id=None,
        lane=materialization_service.MaterializationLaneContext(
            branch_id=branch_id,
            projection_hash=projection_hash,
        ),
        function_id=uuid4(),
        process_config_id=process_config_id,
        thread_spec=thread_spec,
    )

    assert result.thread_config_id == thread_config_id
    assert result.commit_id is None
    assert result.head_commit_id == oig_commit_id


async def _hydrate_projection_session(
    *,
    index: Any,
    branch_id,
    projection_hash: str,
) -> Session:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    assert head.get("object_instance_graph_id") is not None
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return reify_oig_session(
        index=index,
        opg=opg,
        oig=oig,
        branch_id=branch_id,
    )


@pytest.mark.asyncio
async def test_projection_snapshot_appends_multiple_projection_experiences_on_one_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_projection_multi_snapshot",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        from aware_experience.materialization.snapshot_commit import (  # noqa: WPS433
            commit_projection_experience_snapshot,
        )

        projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ProjectionExperience",
        )
        opgi_by_key = {
            (key or "").strip().casefold(): entry
            for key, entry in build_meta_graph_opgi_index(index=index).items()
            if (key or "").strip()
        }
        projection_opgi_id = opgi_by_key["identity"][0]
        branch_id = uuid4()

        first = await commit_projection_experience_snapshot(
            index=index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_projection_graph_identity_id=projection_opgi_id,
            name="aware_actor_commits",
        )
        second = await commit_projection_experience_snapshot(
            index=index,
            actor_id=None,
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_projection_graph_identity_id=projection_opgi_id,
            name="aware_actor_roles",
        )

        assert first.head_commit_id != second.head_commit_id
        session = await _hydrate_projection_session(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        projection_experiences = {
            obj.name: obj
            for obj in session.imap_all_objects()
            if isinstance(obj, ProjectionExperience)
        }
        assert set(projection_experiences) == {
            "aware_actor_commits",
            "aware_actor_roles",
        }


@pytest.mark.asyncio
async def test_materialize_experience_package_from_manifest_commits_canonical_package_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_package_materialization",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        from aware_experience.materialization import (  # noqa: WPS433
            materialize_experience_package_from_manifest,
            resolve_experience_package_materialization_spec,
        )

        spec = resolve_experience_package_materialization_spec(
            experience_toml_path=experience_toml_path,
            workspace_root=workspace_root,
        )
        assert spec.package_name == "home-story"
        assert spec.package_fqn_prefix == "home_story"
        assert spec.experience_names == ("home_story",)
        assert spec.experience_name == "home_story"
        assert spec.experience_source_path == "experiences.aware"
        assert spec.source_files == ("experiences.aware",)

        environment_id = uuid4()
        process_id = uuid4()
        thread_id = uuid4()
        branch_id = uuid4()

        environment_experience_projection_hash = (
            find_meta_graph_projection_hash_by_name(
                index=index,
                projection_name="EnvironmentExperience",
            )
        )
        experience_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="ExperiencePackage",
        )
        code_package_projection_hash = find_meta_graph_projection_hash_by_name(
            index=index,
            projection_name="CodePackage",
        )
        assert environment_experience_projection_hash
        assert experience_package_projection_hash
        assert code_package_projection_hash

        result = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )

        assert result.experience_toml_path == experience_toml_path.resolve()
        assert result.workspace_root == workspace_root.resolve()
        assert result.manifest_spec.experience.package_name == "home-story"
        assert result.manifest_spec.experience.fqn_prefix == "home_story"
        assert result.environment_experience.fqn_prefix == "home_story"
        assert result.environment_experience.title == "Home Story"
        assert (
            result.environment_experience.description
            == "Narrative experience package for the home workspace."
        )
        assert result.experience_package.name == "home-story"
        assert (
            result.experience_package.environment_experience_id
            == result.environment_experience.id
        )
        assert result.experience_names == ("home_story",)
        assert result.experience_name == "home_story"
        assert result.experience_source_path == "experiences.aware"
        assert result.source_files == ("experiences.aware",)
        assert result.phase_timings_s["total"] >= 0.0
        assert (
            result.phase_timings_s["resolve_experience_package_materialization_spec"]
            >= 0.0
        )
        assert result.phase_timings_s["commit_code_package_text_snapshot"] >= 0.0
        assert result.phase_timings_s["preflight_generated_package_lanes"] >= 0.0
        assert (
            result.phase_timings_s["commit_experience_package_manifest_snapshot"] >= 0.0
        )
        assert result.source_code_package_id == _experience_source_code_package_id(
            package_name="home-story",
        )
        assert result.environment_experience_commit_id is not None
        assert result.environment_experience_head_commit_id is not None
        assert result.projection_experience_commit_id is None
        assert result.projection_experience_head_commit_id is None
        assert result.projection_experience_graph_commit_id is None
        assert result.projection_experience_graph_head_commit_id is None
        assert result.projection_experience_section_surface_commit_id is None
        assert result.projection_experience_section_surface_head_commit_id is None
        assert result.package_commit_id is not None
        assert result.package_head_commit_id is not None

        code_package_session = await _hydrate_projection_session(
            index=index,
            branch_id=branch_id,
            projection_hash=code_package_projection_hash,
        )
        code_packages = [
            obj
            for obj in code_package_session.imap_all_objects()
            if isinstance(obj, CodePackage)
        ]
        assert len(code_packages) == 1
        code_package = code_packages[0]
        assert code_package.id == result.source_code_package_id
        assert (
            code_package.code_package_config_id
            == _experience_source_code_package_config_id()
        )
        assert code_package.package_name == "home-story"
        assert code_package.language == CodeLanguage.aware
        assert code_package.surface == "experience"
        assert code_package.manifest_relative_path == "aware.experience.toml"
        assert code_package.package_root == "."
        assert code_package.sources_root == "."
        codes = [
            obj
            for obj in code_package_session.imap_all_objects()
            if isinstance(obj, Code)
        ]
        assert len(codes) == 1

        rerun = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )
        assert rerun.environment_experience.id == result.environment_experience.id
        assert rerun.experience_package.id == result.experience_package.id
        assert rerun.phase_timings_s["total"] >= 0.0
        assert rerun.phase_timings_s["hydrate_experience_package_from_head"] >= 0.0
        assert rerun.projection_experience_head_commit_id is None


@pytest.mark.asyncio
async def test_materialize_experience_package_from_manifest_records_experience_package_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_package_dependency_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
        dependency_package_name="aware-control",
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_package_dependency_materialization",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        from aware_experience.materialization import (  # noqa: WPS433
            materialize_experience_package_from_manifest,
        )

        result = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )

        target_experience_package_id = stable_experience_package_id(
            name="aware-control"
        )
        expected_dependency_id = stable_experience_package_dependency_id(
            experience_package_id=result.experience_package.id,
            target_experience_package_id=target_experience_package_id,
        )
        dependencies = result.experience_package.experience_package_dependencies
        assert len(dependencies) == 1
        dependency = dependencies[0]
        assert isinstance(dependency, ExperiencePackageDependency)
        assert dependency.id == expected_dependency_id
        assert dependency.experience_package_id == result.experience_package.id
        assert dependency.target_experience_package_id == target_experience_package_id
        assert dependency.target_package_name == "aware-control"
        assert dependency.target_version_number == 1


@pytest.mark.asyncio
async def test_materialize_experience_package_reconciles_removed_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_package_dependency_reconciliation"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
        dependency_package_name="aware-control",
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_package_dependency_reconciliation",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None

        from aware_experience.materialization import (  # noqa: WPS433
            materialize_experience_package_from_manifest,
        )

        branch_id = uuid4()
        initial = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=runtime_context.index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=branch_id,
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )
        assert len(initial.experience_package.experience_package_dependencies) == 1

        _write_experience_package_fixture(workspace_root=workspace_root)
        reconciled = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=runtime_context.index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=branch_id,
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )

        assert reconciled.experience_package.experience_package_dependencies == []


@pytest.mark.asyncio
async def test_materialize_experience_package_from_manifest_records_attention_package_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_attention_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
        dependency_package_name="home_story_app_shell",
        dependency_kind="attention_package",
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_attention_package_materialization",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None

        from aware_experience.materialization import (  # noqa: WPS433
            materialize_experience_package_from_manifest,
        )

        result = await materialize_experience_package_from_manifest(
            runtime=runtime,
            index=runtime_context.index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )

        attention_package_id = stable_attention_package_id(name="home_story_app_shell")
        expected_dependency_id = stable_experience_package_attention_package_id(
            experience_package_id=result.experience_package.id,
            attention_package_id=attention_package_id,
        )
        dependencies = result.experience_package.attention_packages
        assert len(dependencies) == 1
        dependency = dependencies[0]
        assert isinstance(dependency, ExperiencePackageAttentionPackage)
        assert dependency.id == expected_dependency_id
        assert dependency.experience_package_id == result.experience_package.id
        assert dependency.attention_package_id == attention_package_id


@pytest.mark.asyncio
async def test_materialize_experience_package_from_manifest_skips_api_view_language_packages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_package_language_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
        language_targets=True,
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_package_language_package_materialization",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        from aware_experience.materialization import (
            service as service_mod,
        )  # noqa: WPS433

        result = await service_mod.materialize_experience_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )

        assert result.language_contract_packages == ()
        assert not result.experience_package.language_packages


@pytest.mark.asyncio
async def test_dependency_reference_install_scope_does_not_materialize_programs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_package_dependency_reference"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root,
        dependency_package_name="aware-control",
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_package_dependency_reference",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        import aware_experience.materialization.service as service_mod  # noqa: WPS433

        async def _materialize_experience_program_ontology(**_kwargs: object):
            raise AssertionError(
                "dependency-reference Experience install must not materialize programs"
            )

        async def _materialize_experience_environment_profile_ontology(
            **_kwargs: object,
        ):
            raise AssertionError(
                "dependency-reference Experience install must not materialize "
                "Environment profile topology"
            )

        monkeypatch.setattr(
            service_mod,
            "materialize_experience_program_ontology",
            _materialize_experience_program_ontology,
        )
        monkeypatch.setattr(
            service_mod,
            "materialize_experience_environment_profile_ontology",
            _materialize_experience_environment_profile_ontology,
        )

        result = await service_mod.materialize_experience_package_from_manifest(
            runtime=runtime,
            index=index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
            allow_unresolved_projection_experiences=True,
            install_scope=service_mod.ExperiencePackageInstallScope.dependency_reference,
        )

        assert result.program_config_commit_id is None
        assert result.program_impl_commit_id is None
        assert (
            result.phase_timings_s["materialize_environment_profile_ontology.skipped"]
            == 0.0
        )
        assert result.phase_timings_s["materialize_program_ontology.skipped"] == 0.0


@pytest.mark.asyncio
async def test_materialize_experience_package_from_manifest_uses_direct_snapshots_without_runtime_harness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    workspace_root = tmp_path / "experience_package_direct_snapshot"
    workspace_root.mkdir(parents=True, exist_ok=True)
    experience_toml_path = _write_experience_package_fixture(
        workspace_root=workspace_root
    )
    _prepend_experience_meta_python_roots(repo_root=repo_root, monkeypatch=monkeypatch)

    with IsolatedMetaAwareRoot(
        tmp_path / "aware_root_experience_package_direct_snapshot",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_experience_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        runtime_context = runtime.context
        assert runtime_context is not None
        index = runtime_context.index

        from aware_experience.materialization import (  # noqa: WPS433
            materialize_experience_package_from_manifest,
        )

        result = await materialize_experience_package_from_manifest(
            runtime=cast(Any, _FailClosedSemanticRuntime()),
            index=index,
            actor_id=None,
            environment_id=uuid4(),
            process_id=uuid4(),
            thread_id=uuid4(),
            branch_id=uuid4(),
            workspace_root=workspace_root,
            experience_toml_path=experience_toml_path,
        )

        assert result.environment_experience_commit_id is not None
        assert result.package_commit_id is not None
        assert result.source_code_package_id == _experience_source_code_package_id(
            package_name="home-story",
        )
