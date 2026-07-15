from __future__ import annotations

import json
from pathlib import Path

import pytest

from aware_experience.compiler.builder import (
    build_experience_compile_plan,
    emit_experience_compile_plan_artifact,
)
from aware_experience.compiler.structure import (
    load_environment_projection_truth,
    load_environment_projection_truth_from_runtime_manifests,
)
from aware_experience.compiler.models import (
    ExperienceEventBindingOwnership,
    ExperienceEventOwnership,
    ExperienceProjectionExperienceOwnership,
    ExperienceProjectionObservableOwnership,
    ExperienceProjectionViewOwnership,
)
from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.environment_profile.compiler import (
    load_environment_profile_ownership_from_sources,
)
from aware_experience.graph.compiler import load_graph_ownership_from_sources
from aware_experience.projection.contracts import (
    decode_projection_experience_ownership_payload,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)


_COMPOSITION_MANIFEST_PATH = (
    "modules/conversation/structure/ontology/.aware/environment/runtime/"
    "environment.manifest.json"
)
_CONVERSATION_EVENT_CREATED_HEADER = (
    'event ConversationMessageCreated name "conversation.message.created" '
    'renderer "conversation.message.created" title "Conversation Message Created" '
    'description "Conversation message append domain event." {'
)
_CONVERSATION_EVENT_CREATED_COMPACT_HEADER = (
    'event ConversationMessageCreated name "conversation.message.created" '
    'renderer "conversation.message.created" {'
)


def _composition_runtime_manifest_path(root: Path) -> Path:
    return root / _COMPOSITION_MANIFEST_PATH


def _api_view_mount(
    view_key: str,
    api_view_ref: str,
    *,
    default: bool = True,
    suffix: str = "{}",
) -> str:
    default_token = " default" if default else ""
    return f"    view {view_key}{default_token} api_view {api_view_ref} {suffix}"


_CONVERSATION_EVENT_UPDATED_HEADER = (
    'event ConversationMessageUpdated name "conversation.message.updated" '
    'renderer "conversation.message.updated" title "Conversation Message Updated" '
    'description "Conversation message update domain event." {'
)
_DISTRIBUTED_GRAPH_ROOT_CASES = (
    ("aware-actor", "actor_roles_default", "aware_actor_roles"),
    ("aware-network", "network_territory_default", "aware_network"),
    ("aware-environment", "environments_default", "aware_environment_experience"),
    ("aware-hub", "hub_default", "aware_hub"),
)


def _write_experience_toml(*, root: Path) -> Path:
    content = "\n".join(
        [
            "aware_experience = 1",
            "",
            "[experience]",
            'package_name = "assistance"',
            'fqn_prefix = "assistance"',
            "",
            "[build]",
            'environment_handle = "kernel"',
            'sources_dir = "."',
            'include_paths = ["**/*.aware"]',
            "exclude_paths = []",
            "force_fresh_scan = true",
            "",
        ]
    )
    target = root / "aware.experience.toml"
    target.write_text(content, encoding="utf-8")
    return target


def _write_named_experience_toml(
    *,
    root: Path,
    package_name: str,
    fqn_prefix: str,
    dependencies: tuple[str, ...] = (),
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    lines = [
        "aware_experience = 1",
        "",
        "[experience]",
        f'package_name = "{package_name}"',
        f'fqn_prefix = "{fqn_prefix}"',
        "",
        "[build]",
        'environment_handle = "kernel"',
        'sources_dir = "."',
        'include_paths = ["**/*.aware"]',
        "exclude_paths = []",
        "force_fresh_scan = true",
        "",
    ]
    for dependency in dependencies:
        lines.extend(
            [
                "[[dependencies]]",
                f'package_name = "{dependency}"',
                'kind = "experience_package"',
                "",
            ]
        )
    target = root / "aware.experience.toml"
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def _actor_home_projection_experience_ownership() -> (
    ExperienceProjectionExperienceOwnership
):
    return ExperienceProjectionExperienceOwnership(
        name="actor_home",
        projection="Home",
        source_path="actor.aware",
        branches=(),
        observables=(
            ExperienceProjectionObservableOwnership(
                key="actor",
                source_path="actor.aware",
                views=(
                    ExperienceProjectionViewOwnership(
                        key="home",
                        is_default=True,
                        api_view_ref="actor.home",
                        source_path="actor.aware",
                    ),
                ),
            ),
        ),
    )


def _identity_admitted_dependency_event_ownership() -> ExperienceEventOwnership:
    return ExperienceEventOwnership(
        symbol="IdentityAdmitted",
        event_name="identity.admitted",
        renderer_key="identity.admitted",
        title=None,
        description=None,
        source_path="events/identity_admission.aware",
        bindings=(
            ExperienceEventBindingOwnership(
                projection="Identity",
                type_ref="Identity.Identity",
                class_fqn=None,
                operation="create",
            ),
        ),
        package_name="aware-control",
        fqn_prefix="aware_control",
        is_dependency=True,
    )


def _write_programs_toml(*, root: Path) -> None:
    content = "\n".join(
        [
            "aware = 1",
            "",
            "[[programs]]",
            'ref = "assistance:AssistantRun_v1"',
            'path = "programs/assistant_run_v1.aware"',
            'name = "AssistantRun_v1"',
            'dependencies = ["conversation-ontology"]',
            'required_symbols = ["plan.message_text"]',
            'optional_symbols = ["plan.thread_id"]',
            "",
        ]
    )
    (root / "aware.programs.toml").write_text(content, encoding="utf-8")


def _write_composition_truth(
    *,
    root: Path,
    projection: str = "Conversation",
    class_names: tuple[str, ...] = ("ConversationMessage",),
    class_fqns: tuple[str, ...] | None = None,
    extra_entries: tuple[tuple[str, tuple[str, ...]], ...] = (),
    class_attributes_by_token: dict[str, tuple[str, ...]] | None = None,
    observables_by_projection: dict[str, tuple[str, ...]] | None = None,
    compiler_observables_by_projection: dict[str, tuple[str, ...]] | None = None,
    binding_id_field: str = "canonical_class_config_id",
) -> Path:
    module_runtime_dir = (
        root
        / "modules"
        / "conversation"
        / "structure"
        / "ontology"
        / ".aware"
        / "environment"
        / "runtime"
    )
    module_runtime_dir.mkdir(parents=True, exist_ok=True)
    module_manifest = {
        "opg_index": {"file": "opg.index.json"},
        "bindings": {"file": "bindings.manifest.json"},
    }
    (module_runtime_dir / "environment.manifest.json").write_text(
        json.dumps(module_manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    resolved_fqns = (
        class_fqns
        if class_fqns is not None
        else tuple(
            f"aware_conversation_ontology.conversation.conversation.{class_name}"
            for class_name in class_names
        )
    )
    class_rows: list[dict[str, object]] = []
    node_rows: list[dict[str, object]] = []
    for idx, class_fqn in enumerate(resolved_fqns):
        class_config_id = f"class-config-{idx}"
        class_token = class_fqn.rsplit(".", 1)[-1]
        attributes = (
            class_attributes_by_token.get(class_token, ("id",))
            if class_attributes_by_token is not None
            else ("id",)
        )
        class_rows.append(
            {
                "class_fqn": class_fqn,
                binding_id_field: class_config_id,
                "sql_mapping": [
                    {"attribute_name": attribute_name} for attribute_name in attributes
                ],
            }
        )
        node_rows.append({"class_config_id": class_config_id, "is_root": idx == 0})

    entries: list[dict[str, object]] = [
        {
            "model": projection,
            "projection_hash": "h",
            "file": "opgs/h.json",
        }
    ]

    def _build_opg_payload(
        *,
        projection_name: str,
        nodes: list[dict[str, object]],
    ) -> dict[str, object]:
        observables: list[dict[str, str]] = []
        if observables_by_projection is not None:
            for observable_key in observables_by_projection.get(projection_name, ()):
                observables.append(
                    {
                        "observable_key": observable_key,
                        "key": f"{projection_name}:{observable_key}",
                    }
                )
        return {
            "object_projection_graph_nodes": nodes,
            "object_projection_graph_identity": {
                "object_projection_graph_observables": observables
            },
        }

    opgs_dir = module_runtime_dir / "opgs"
    opgs_dir.mkdir(parents=True, exist_ok=True)
    (opgs_dir / "h.json").write_text(
        json.dumps(
            _build_opg_payload(projection_name=projection, nodes=node_rows),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for entry_idx, (entry_projection, entry_classes) in enumerate(
        extra_entries, start=1
    ):
        file_name = f"h{entry_idx}.json"
        entries.append(
            {
                "model": entry_projection,
                "projection_hash": f"h{entry_idx}",
                "file": f"opgs/{file_name}",
            }
        )
        entry_nodes: list[dict[str, object]] = []
        for class_idx, class_fqn in enumerate(entry_classes, start=1000 * entry_idx):
            class_config_id = f"class-config-{class_idx}"
            class_token = class_fqn.rsplit(".", 1)[-1]
            attributes = (
                class_attributes_by_token.get(class_token, ("id",))
                if class_attributes_by_token is not None
                else ("id",)
            )
            class_rows.append(
                {
                    "class_fqn": class_fqn,
                    binding_id_field: class_config_id,
                    "sql_mapping": [
                        {"attribute_name": attribute_name}
                        for attribute_name in attributes
                    ],
                }
            )
            entry_nodes.append(
                {"class_config_id": class_config_id, "is_root": not entry_nodes}
            )
        (opgs_dir / file_name).write_text(
            json.dumps(
                _build_opg_payload(
                    projection_name=entry_projection,
                    nodes=entry_nodes,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    (module_runtime_dir / "opg.index.json").write_text(
        json.dumps({"entries": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    (module_runtime_dir / "bindings.manifest.json").write_text(
        json.dumps(
            {"bindings": class_rows},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if compiler_observables_by_projection is not None:
        compiler_dir = (
            root
            / "modules"
            / "conversation"
            / "structure"
            / "ontology"
            / ".aware"
            / "compiler"
        )
        compiler_dir.mkdir(parents=True, exist_ok=True)
        object_config_graph_identity_id = "00000000-0000-0000-0000-000000000010"
        compiler_env = {
            "canonical_language": "aware",
            "handle": "test",
            "title": "Test Environment",
            "repository_id": "00000000-0000-0000-0000-000000000001",
            "languages": ["aware"],
            "object_config_graphs": [
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "language": "aware",
                    "name": "aware_test",
                    "hash": "sha256:test",
                    "fqn_prefix": "aware_test",
                    "object_config_graph_identity": {
                        "id": object_config_graph_identity_id,
                        "key": "aware_test",
                        "object_projection_graph_identities": [
                            {
                                "id": f"00000000-0000-0000-0000-0000000001{index:02d}",
                                "projection_name": projection_name,
                                "object_config_graph_identity_id": object_config_graph_identity_id,
                                "object_projection_graph_id": f"00000000-0000-0000-0000-0000000002{index:02d}",
                                "object_projection_graph_observables": [
                                    {
                                        "id": f"00000000-0000-0000-0000-00000003{index:02d}{observable_index:02d}",
                                        "observable_key": observable_key,
                                        "key": f"{projection_name}:{observable_key}",
                                        "object_projection_graph_identity_id": (
                                            f"00000000-0000-0000-0000-0000000001{index:02d}"
                                        ),
                                    }
                                    for observable_index, observable_key in enumerate(
                                        observable_keys, start=1
                                    )
                                ],
                            }
                            for index, (projection_name, observable_keys) in enumerate(
                                sorted(compiler_observables_by_projection.items()),
                                start=1,
                            )
                        ],
                    },
                }
            ],
        }
        (compiler_dir / "environment.json").write_text(
            json.dumps(compiler_env, indent=2) + "\n",
            encoding="utf-8",
        )
    composition = {
        "modules": [
            {
                "module_id": "conversation",
                "manifest_path": _COMPOSITION_MANIFEST_PATH,
            }
        ]
    }
    composition_path = root / ".aware" / "tmp" / "environment.composition.manifest.json"
    composition_path.parent.mkdir(parents=True, exist_ok=True)
    composition_path.write_text(
        json.dumps(composition, indent=2) + "\n", encoding="utf-8"
    )
    return composition_path


def test_environment_projection_truth_accepts_canonical_entity_id_bindings(
    tmp_path: Path,
) -> None:
    composition_path = _write_composition_truth(
        root=tmp_path,
        projection="Home",
        class_names=("Home",),
        class_attributes_by_token={"Home": ("id", "name")},
        binding_id_field="canonical_entity_id",
    )

    truth = load_environment_projection_truth(
        composition_manifest_path=composition_path,
        repo_root=tmp_path,
    )

    assert truth["home"]["Home"].class_fqn.endswith(".Home")
    assert truth["home"]["Home"].attributes == frozenset({"id", "name"})


def test_environment_projection_truth_accepts_runtime_manifest_paths(
    tmp_path: Path,
) -> None:
    _ = _write_composition_truth(
        root=tmp_path,
        projection="Home",
        class_names=("Home",),
        class_attributes_by_token={"Home": ("id", "name")},
        binding_id_field="canonical_entity_id",
    )

    truth = load_environment_projection_truth_from_runtime_manifests(
        environment_runtime_manifest_paths=(
            _composition_runtime_manifest_path(tmp_path),
        ),
        repo_root=tmp_path,
    )

    assert truth["home"]["Home"].class_fqn.endswith(".Home")
    assert truth["home"]["Home"].attributes == frozenset({"id", "name"})


def test_build_experience_compile_plan_program_and_event_ownership(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    _ = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation", "ConversationMessage"),
    )

    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_runtime_manifest_paths=(_composition_runtime_manifest_path(root),),
        repo_root=root,
    )
    assert plan.package_name == "assistance"
    assert plan.fqn_prefix == "assistance"
    assert plan.actor_role_contract is None
    assert plan.role_ownership == ()
    assert plan.actor_ownership == ()
    assert plan.environment_actor_bindings == ()
    assert plan.action_ownership == ()
    assert plan.environment_ownership == ()
    assert plan.projection_experience_ownership == ()
    assert len(plan.program_ownership) == 1
    assert plan.program_ownership[0].ref == "assistance:AssistantRun_v1"
    assert plan.program_ownership[0].path == "programs/assistant_run_v1.aware"
    assert plan.program_ownership[0].dependencies == ("conversation-ontology",)
    assert plan.program_ownership[0].required_projection_ids == ()
    assert plan.program_ownership[0].required_projection_node_ids == ()
    assert plan.program_ownership[0].required_projection_node_identity_ids == ()
    assert plan.program_ownership[0].invocation_plan_artifact is not None
    assert len(plan.event_ownership) == 1
    assert plan.event_ownership[0].event_name == "conversation.message.created"
    assert plan.event_ownership[0].renderer_key == "conversation.message.created"
    assert plan.event_ownership[0].source_path == "events/conversation_events.aware"
    assert len(plan.event_ownership[0].bindings) == 1
    assert plan.event_ownership[0].bindings[0].projection == "Conversation"
    assert (
        plan.event_ownership[0].bindings[0].class_fqn
        == "aware_conversation_ontology.conversation.conversation.ConversationMessage"
    )

    emitted_path = root / "experience.compile_plan.json"
    emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root,
        repo_root=root,
    )
    emitted = json.loads(emitted_path.read_text(encoding="utf-8"))
    ownership = emitted["program_ownership"][0]
    assert ownership["dependencies"] == ["conversation-ontology"]
    assert ownership["required_projection_ids"] == []
    assert ownership["required_projection_node_ids"] == []
    assert ownership["required_projection_node_identity_ids"] == []


def test_build_experience_compile_plan_rejects_executable_config_without_impl(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "\n".join(
            [
                "program AssistantRun_v1(message_text String) {",
                "  bind main conversation.home",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
    )

    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "config declarations cannot include executable statements" in str(exc)
    else:  # pragma: no cover - fail closed
        raise AssertionError(
            "Expected ValueError for executable statements in config-only program surface"
        )


def test_build_experience_compile_plan_fails_on_unknown_projection(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_HEADER,
                "  bind ghost ghost.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown projection" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown projection")


def test_build_experience_compile_plan_fails_on_unknown_class_token(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_HEADER,
                "  bind Conversation Conversation.GhostMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown class token" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown class token")


def test_build_experience_compile_plan_fails_on_ambiguous_class_token_mapping(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_fqns=(
            "aware_conversation_ontology.conversation.conversation.ConversationMessage",
            "aware_other_ontology.conversation.conversation.ConversationMessage",
        ),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "Ambiguous class token mapping" in str(exc)
    else:
        raise AssertionError("Expected ValueError for ambiguous class token mapping")


def test_build_experience_compile_plan_fails_on_cross_projection_class_leakage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_HEADER,
                "  bind Conversation Conversation.Agent create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
        extra_entries=(("Agent", ("aware_agent_ontology.agent.agent.Agent",)),),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown class token" in str(exc)
    else:
        raise AssertionError("Expected ValueError for cross-projection class leakage")


def test_build_experience_compile_plan_fails_on_unknown_attribute_path(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_UPDATED_HEADER,
                "  bind Conversation Conversation.ConversationMessage update ghost",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
        class_attributes_by_token={
            "ConversationMessage": ("id", "conversation_id"),
        },
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown attribute path root" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown attribute path root")


def test_build_experience_compile_plan_action_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "actions" / "assistance_actions.aware").write_text(
        "\n".join(
            [
                "action agent_run(intent String? = null) {",
                '  """Run AI agent with optional intent."""',
                "  program assistance.AssistantRun_v1(intent=intent)",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(snapshot=snapshot)
    assert len(plan.action_ownership) == 1
    action = plan.action_ownership[0]
    assert action.symbol == "agent_run"
    assert action.action_name == "agent_run"
    assert action.params == ("intent",)
    assert len(action.program_bindings) == 1
    assert action.program_bindings[0].program == "assistance.AssistantRun_v1"
    assert action.program_bindings[0].args == ("intent=intent",)


def test_build_experience_compile_plan_connector_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "connectors").mkdir(parents=True, exist_ok=True)
    (root / "connectors" / "music.aware").write_text(
        "\n".join(
            [
                "connector music {",
                "  kind media",
                '  label "Music";',
                "  provider youtube_music {",
                "    kind music_streaming",
                "    ref youtube.music",
                '    label "YouTube Music";',
                "  }",
                "  sensor now_playing {",
                "    kind media_state",
                "    source_ref youtube.now_playing",
                "    observed_state_node clinic.Room::devices",
                "    invocation poll api MusicApi.Playback.now_playing {",
                '      label "Poll";',
                "      receipt event;",
                "    }",
                "    invocation subscribe sdk MusicSdk.Player.subscribe_now_playing {",
                "      confirmation none;",
                "    }",
                "  }",
                "  actuator play_track {",
                "    kind media_control",
                "    target_ref youtube.play",
                "    affected_state_node clinic.Room::devices",
                "    invocation play sdk MusicSdk.Player.play;",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    plan = build_experience_compile_plan(snapshot=snapshot)

    assert len(plan.connector_ownership) == 1
    connector = plan.connector_ownership[0]
    assert connector.connector_key == "music"
    assert connector.connector_kind == "media"
    assert connector.label == "Music"
    assert connector.providers[0].provider_key == "youtube_music"
    assert connector.providers[0].provider_ref == "youtube.music"
    assert connector.sensor_configs[0].sensor_key == "now_playing"
    assert connector.sensor_configs[0].source_ref == "youtube.now_playing"
    assert connector.sensor_configs[0].observed_state_node_refs == (
        "clinic.Room::devices",
    )
    assert [
        item.action_key
        for item in connector.sensor_configs[0].invocation_action_configs
    ] == [
        "poll",
        "subscribe",
    ]
    assert connector.sensor_configs[0].invocation_action_configs[0].target_ref == (
        "MusicApi.Playback.now_playing"
    )
    assert connector.sensor_configs[0].invocation_action_configs[0].receipt_policy == (
        "event"
    )
    assert connector.actuator_configs[0].actuator_key == "play_track"
    assert connector.actuator_configs[0].affected_state_node_refs == (
        "clinic.Room::devices",
    )
    assert connector.actuator_configs[0].invocation_action_configs[0].target_ref == (
        "MusicSdk.Player.play"
    )

    artifact = emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root / ".aware" / "experience" / "runtime" / "music",
        repo_root=root,
    )
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert payload["connector_ownership"][0]["sensor_configs"][0][
        "observed_state_node_refs"
    ] == ["clinic.Room::devices"]
    assert payload["connector_ownership"][0]["actuator_configs"][0][
        "affected_state_node_refs"
    ] == ["clinic.Room::devices"]
    assert payload["connector_ownership"][0]["sensor_configs"][0][
        "invocation_action_configs"
    ][0] == {
        "action_key": "poll",
        "action_kind": "api",
        "target_ref": "MusicApi.Playback.now_playing",
        "label": "Poll",
        "receipt_policy": "event",
        "confirmation_policy": None,
        "optimistic_policy": None,
        "source_path": "connectors/music.aware",
    }


def test_build_experience_compile_plan_fails_on_unknown_action_program_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.GhostProgram() }\n",
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(snapshot=snapshot)
    except ValueError as exc:
        assert "references unknown program" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown action program ref")


def test_build_experience_compile_plan_fails_on_duplicate_action_symbol(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "actions" / "a1.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "actions" / "a2.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(snapshot=snapshot)
    except ValueError as exc:
        assert "Duplicate action symbol" in str(exc)
    else:
        raise AssertionError("Expected ValueError for duplicate action symbol")


def test_build_experience_compile_plan_fails_on_duplicate_action_name(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "actions" / "a1.aware").write_text(
        "action AgentRun { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "actions" / "a2.aware").write_text(
        "action agEntrun { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(snapshot=snapshot)
    except ValueError as exc:
        assert "Duplicate action name" in str(exc)
    else:
        raise AssertionError("Expected ValueError for duplicate action name")


def test_build_experience_compile_plan_environment_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  experience assistance_conversation",
                "  program AssistantRun_v1 AssistantRun_v1",
                "  event ConversationMessageCreated {",
                "    // @aware node_scope conversation_message",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )
    assert len(plan.environment_ownership) == 1
    env = plan.environment_ownership[0]
    assert env.name == "assistance"
    assert env.experiences == ("assistance_conversation",)
    assert len(env.programs) == 1
    assert env.programs[0].program_config == "AssistantRun_v1"
    assert env.programs[0].program_impl == "AssistantRun_v1"
    assert len(env.events) == 1
    assert env.events[0].event == "ConversationMessageCreated"
    assert [scope.node_ref for scope in env.events[0].node_scopes] == [
        "conversation_message"
    ]
    assert len(env.events[0].actions) == 1
    assert env.events[0].actions[0].action == "agent_run"

    artifact = emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root / ".aware" / "experience" / "runtime",
        repo_root=root,
    )
    artifact_payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert artifact_payload["environment_ownership"][0]["events"][0]["node_scopes"] == [
        {"node_ref": "conversation_message"}
    ]


def test_build_experience_compile_plan_environment_fails_on_unknown_experience_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  experience ghost_experience",
                "  event ConversationMessageCreated {",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "references unknown experience" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown environment experience")


def test_build_experience_compile_plan_environment_resolves_event_reference_variants(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                'event HomeDoorStateChanged name "home.door.state.changed" renderer "home.door.state.changed" {',
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  program AssistantRun_v1 AssistantRun_v1",
                "  event home_door_state_changed {",
                "    action agent_run",
                "  }",
                "  event home.door.state.changed {",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )
    assert len(plan.environment_ownership) == 1
    env = plan.environment_ownership[0]
    assert len(env.events) == 2
    assert {item.event for item in env.events} == {
        "home_door_state_changed",
        "home.door.state.changed",
    }


def test_build_experience_compile_plan_environment_fails_on_unknown_event_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  event GhostEvent {",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "references unknown event" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown environment event")


def test_build_experience_compile_plan_environment_fails_on_unknown_program_config_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  program GhostConfig AssistantRun_v1",
                "  event ConversationMessageCreated {",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown program_config" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for unknown environment program_config"
        )


def test_build_experience_compile_plan_environment_fails_on_unknown_program_impl_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  program AssistantRun_v1 GhostImpl",
                "  event ConversationMessageCreated {",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown program_impl" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown environment program_impl")


def test_build_experience_compile_plan_environment_fails_when_action_binding_program_not_program_config(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "programs" / "assistant_config_v1.aware").write_text(
        "program AssistantConfig_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  program AssistantConfig_v1 AssistantRun_v1",
                "  event ConversationMessageCreated {",
                "    action agent_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "aware.programs.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "assistance:AssistantRun_v1"',
                'path = "programs/assistant_run_v1.aware"',
                'name = "AssistantRun_v1"',
                "",
                "[[programs]]",
                'ref = "assistance:AssistantConfig_v1"',
                'path = "programs/assistant_config_v1.aware"',
                'name = "AssistantConfig_v1"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "not declared as environment program_config" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError when action binding program is not an environment program_config"
        )


def test_build_experience_compile_plan_environment_fails_on_unknown_action_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actions").mkdir(parents=True, exist_ok=True)
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "environments").mkdir(parents=True, exist_ok=True)
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "program AssistantRun_v1(message_text String) {}\n",
        encoding="utf-8",
    )
    (root / "actions" / "assistance_actions.aware").write_text(
        "action agent_run { program assistance.AssistantRun_v1() }\n",
        encoding="utf-8",
    )
    (root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "environments" / "assistance_environment.aware").write_text(
        "\n".join(
            [
                "environment assistance {",
                "  event ConversationMessageCreated {",
                "    action ghost_run",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "references unknown action" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown environment action")


def test_build_experience_compile_plan_projection_experience_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat", "history")},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )
    assert len(plan.projection_experience_ownership) == 1
    ownership = plan.projection_experience_ownership[0]
    assert ownership.name == "assistance_conversation"
    assert ownership.projection == "Conversation"
    assert len(ownership.branches) == 1
    assert ownership.branches[0].name == "assistance"
    assert ownership.branches[0].is_default is True
    assert len(ownership.observables) == 1
    assert ownership.observables[0].key == "chat"
    assert len(ownership.observables[0].views) == 1
    assert ownership.observables[0].views[0].key == "home"
    assert ownership.observables[0].views[0].is_default is True
    assert ownership.observables[0].views[0].api_view_ref == "conversation.home"
    assert ownership.observables[0].views[0].state_model_ref is None
    assert ownership.observables[0].views[0].state_provider_ref is None
    assert ownership.observables[0].views[0].invocation_actions == ()
    assert ownership.nodes == ()

    artifact = emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root / ".aware" / "experience" / "runtime" / "conversation",
        repo_root=root,
    )
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    encoded_view = payload["projection_experience_ownership"][0]["observables"][0][
        "views"
    ][0]
    assert encoded_view["api_view_ref"] == "conversation.home"
    assert encoded_view["state_model_ref"] is None
    assert encoded_view["state_provider_ref"] is None
    assert encoded_view["invocation_actions"] == []
    decoded_ownership = decode_projection_experience_ownership_payload(
        payload=payload["projection_experience_ownership"],
    )[0]
    decoded_view = decoded_ownership.observables[0].views[0]
    assert decoded_view.api_view_ref == "conversation.home"
    assert decoded_view.state_model_ref is None
    assert decoded_view.invocation_actions == ()


def test_build_experience_compile_plan_projection_experience_uses_compiler_environment_observable_fallback(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        compiler_observables_by_projection={"Conversation": ("chat", "history")},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.projection_experience_ownership) == 1
    ownership = plan.projection_experience_ownership[0]
    assert ownership.name == "assistance_conversation"
    assert ownership.projection == "Conversation"
    assert len(ownership.observables) == 1
    assert ownership.observables[0].key == "chat"


def test_build_experience_compile_plan_projection_experience_accepts_projection_and_observable_aliases(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "issue_experience.aware").write_text(
        "\n".join(
            [
                "experience aware_issues on aware_workflow.issue.Issue {",
                "  observable workflow {",
                _api_view_mount("issue", "workflow.issue"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Issue",
        class_fqns=("aware_workflow.issue.Issue",),
        compiler_observables_by_projection={"Issue": ("workflow.issue",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.projection_experience_ownership) == 1
    ownership = plan.projection_experience_ownership[0]
    assert ownership.name == "aware_issues"
    assert ownership.projection == "Issue"
    assert len(ownership.observables) == 1
    assert ownership.observables[0].key == "workflow"
    assert len(ownership.observables[0].views) == 1
    assert ownership.observables[0].views[0].key == "issue"


def test_build_experience_compile_plan_projection_experience_fails_without_default_view(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home", default=False),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    with pytest.raises(ValueError, match="exactly one default view"):
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


def test_build_experience_compile_plan_projection_experience_fails_multiple_default_branches(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  branch fallback default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    with pytest.raises(ValueError, match="at most one default branch"):
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


def test_build_experience_compile_plan_projection_experience_node_identities_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "  node conversation.Conversation::messages {",
                "    id latest_message",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )
    assert len(plan.projection_experience_ownership) == 1
    ownership = plan.projection_experience_ownership[0]
    assert len(ownership.nodes) == 1
    assert ownership.nodes[0].name == "conversation.Conversation::messages"
    assert ownership.nodes[0].node_ref == "conversation.Conversation::messages"
    assert ownership.nodes[0].params == ()
    assert len(ownership.nodes[0].identities) == 1
    assert ownership.nodes[0].identities[0].key == "latest_message"


def test_build_experience_compile_plan_program_port_fails_on_unknown_projection_experience(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "  node conversation.Conversation::messages {",
                "    id latest_message",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "\n".join(
            [
                "program AssistantRun_v1(message_text String) {",
                "  port main ghost_projection {",
                "    node message conversation.Conversation::messages.latest_message",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown projection experience" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for unknown program port projection experience"
        )


def test_build_experience_compile_plan_program_port_fails_on_unknown_projection_node(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "  node conversation.Conversation::messages {",
                "    id latest_message",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "\n".join(
            [
                "program AssistantRun_v1(message_text String) {",
                "  port main assistance_conversation {",
                "    node message ghost.latest_message",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown projection node" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for unknown program port projection node"
        )


def test_build_experience_compile_plan_program_port_fails_on_node_key_contract_mismatch(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "  node conversation.Conversation::messages {",
                "    id latest_message",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "programs").mkdir(parents=True, exist_ok=True)
    (root / "programs" / "assistant_run_v1.aware").write_text(
        "\n".join(
            [
                "program AssistantRun_v1(message_id UUID) {",
                "  port main assistance_conversation {",
                "    node message conversation.Conversation::messages(value=message_id)",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_programs_toml(root=root)
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "key contract mismatch" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for program port node key contract mismatch"
        )


def test_build_experience_compile_plan_projection_experience_fails_on_unknown_projection(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_ghost.Ghost {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown projection" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown projection in experience")


def test_build_experience_compile_plan_projection_experience_fails_on_unknown_observable(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable ghost {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        observables_by_projection={"Conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown observable" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown observable in experience")


def test_build_experience_compile_plan_projection_observables_accept_compiler_case_alias(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("Conversation",),
        compiler_observables_by_projection={"conversation": ("chat",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    ownership = plan.projection_experience_ownership[0]
    assert ownership.name == "assistance_conversation"
    assert ownership.projection == "Conversation"
    assert len(ownership.observables) == 1
    assert ownership.observables[0].key == "chat"


def test_build_experience_compile_plan_projection_experience_requires_structure_truth(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences").mkdir(parents=True, exist_ok=True)
    (root / "experiences" / "conversation_experience.aware").write_text(
        "\n".join(
            [
                "experience assistance_conversation on aware_conversation.conversation.Conversation {",
                "  branch assistance default {}",
                "  observable chat {",
                _api_view_mount("home", "conversation.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
        )
    except ValueError as exc:
        assert (
            "Experience projection declarations require composed projection observable truth"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected ValueError when projection experience lacks structure truth"
        )


def test_build_experience_compile_plan_actor_role_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "assistance_actor_roles.aware").write_text(
        "\n".join(
            [
                "role requester {",
                "  conversation.Conversation",
                "}",
                "",
                "actor human_requester identity.human {",
                "}",
                "",
                "environment assistance {",
                "  actor human_requester {",
                "    role requester",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
            "aware_conversation_ontology.conversation.conversation.Conversation",
        ),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )
    assert plan.actor_role_contract is not None
    assert (
        plan.actor_role_contract.actor_config_class_fqn
        == "aware_identity_ontology.actor.actor_config.ActorConfig"
    )
    assert (
        plan.actor_role_contract.role_config_class_fqn
        == "aware_identity_ontology.role.role_config.RoleConfig"
    )
    assert len(plan.role_ownership) == 1
    assert plan.role_ownership[0].name == "requester"
    assert len(plan.actor_ownership) == 1
    assert plan.actor_ownership[0].name == "human_requester"
    assert plan.actor_ownership[0].roles == ()
    assert len(plan.environment_actor_bindings) == 1
    assert plan.environment_actor_bindings[0].environment == "assistance"
    assert plan.environment_actor_bindings[0].actor == "human_requester"
    assert plan.environment_actor_bindings[0].roles == ("requester",)


def test_build_experience_compile_plan_actor_role_ownership_parses_home_story_syntax(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "home_actor_roles.aware").write_text(
        "\n".join(
            [
                "role home_resident {",
                '  """Resident role for home control."""',
                "  aware_home.home.Door.unlock",
                "}",
                "",
                "actor resident Human {",
                '  """Home resident actor."""',
                "}",
                "",
                "environment home_story {",
                "  actor resident {",
                "    role home_resident",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Home",
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
            "aware_home_ontology.home.home.Home",
        ),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )
    assert len(plan.role_ownership) == 1
    assert plan.role_ownership[0].name == "home_resident"
    assert plan.role_ownership[0].capabilities == ("aware_home.home.Door.unlock",)
    assert len(plan.actor_ownership) == 1
    assert plan.actor_ownership[0].name == "resident"
    assert plan.actor_ownership[0].kind == "Human"
    assert len(plan.environment_actor_bindings) == 1
    assert plan.environment_actor_bindings[0].environment == "home_story"
    assert plan.environment_actor_bindings[0].actor == "resident"
    assert plan.environment_actor_bindings[0].roles == ("home_resident",)


def test_build_experience_compile_plan_fails_on_unknown_actor_role_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "assistance_actor_roles.aware").write_text(
        "\n".join(
            [
                "role requester {}",
                "actor human_requester identity.human {",
                "}",
                "environment assistance {",
                "  actor human_requester {",
                "    role ghost",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
        ),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert "unknown role" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown role reference")


def test_build_experience_compile_plan_fails_when_actor_role_contract_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "assistance_actor_roles.aware").write_text(
        "\n".join(
            [
                "role requester {}",
                "actor human_requester identity.human {",
                "}",
                "environment assistance {",
                "  actor human_requester {",
                "    role requester",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    try:
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
    except ValueError as exc:
        assert (
            "Actor/role declarations require ActorConfig+RoleConfig contracts"
            in str(exc)
        )
    else:
        raise AssertionError("Expected ValueError for missing actor-role contract")


def test_build_experience_compile_plan_environment_profile_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "  observable overview {",
                _api_view_mount("home", "home.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "home_actor_roles.aware").write_text(
        "\n".join(
            [
                "role home_resident {",
                "  aware_home.home.Home.view",
                "}",
                "",
                "actor resident Human {",
                "}",
                "",
                "environment home_story {",
                "  actor resident {",
                "    role home_resident",
                "  }",
                "  experience home_story",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "events").mkdir(parents=True, exist_ok=True)
    (root / "events" / "home_events.aware").write_text(
        "\n".join(
            [
                'event HomeOpened name "home.opened" renderer "home.opened" title "Home Opened" description "Home opened." {',
                "  bind Home Home.Home create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience home_story {",
                "  profile os.default {",
                '    title "Home Story OS"',
                '    narrative "Primary home environment experience."',
                "    transition home.open.main {",
                "      source projection home_story view overview.home",
                "      trigger event HomeOpened",
                "      target projection home_story binding home.main",
                '      name "Open main home"',
                '      rationale "Home opened event focuses the main home surface."',
                '      idempotency_policy "event_commit"',
                "    }",
                "    process continuous home default {",
                "      intent workspace",
                "      thread home.main default {",
                "        workspace_view thread.workspace",
                "        projection home_story view overview.home default",
                "        layout configuration_map default {",
                "          section main projection home_story view overview.home binding home.main default",
                "        }",
                "        layout scene_view",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Home",
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
            "aware_home.home.Home",
        ),
        observables_by_projection={"Home": ("overview",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.environment_profile_ownership) == 1
    profile = plan.environment_profile_ownership[0]
    assert profile.experience_name == "home_story"
    assert profile.key == "os.default"
    assert profile.title == "Home Story OS"
    assert profile.narrative == "Primary home environment experience."
    assert [role.name for role in profile.roles] == ["home_resident"]
    assert profile.roles[0].capabilities == ("aware_home.home.Home.view",)
    assert len(profile.actors) == 1
    assert profile.actors[0].key == "resident"
    assert profile.actors[0].actor_type == "Human"
    assert profile.actors[0].role_names == ("home_resident",)
    assert len(profile.process_configs) == 1
    assert len(profile.view_event_transitions) == 1
    transition = profile.view_event_transitions[0]
    assert transition.key == "home.open.main"
    assert transition.source_projection_experience_name == "home_story"
    assert transition.source_view_key == "overview.home"
    assert transition.trigger_event_ref == "HomeOpened"
    assert transition.trigger_event_config_ref == "home.opened"
    assert transition.target_projection_experience_name == "home_story"
    assert transition.target_section_graph_binding_key == "home.main"
    assert transition.name == "Open main home"
    assert transition.rationale == "Home opened event focuses the main home surface."
    assert transition.idempotency_policy == "event_commit"

    process = profile.process_configs[0]
    assert process.type == "continuous"
    assert process.key == "home"
    assert process.process_key == "home"
    assert process.is_bootstrap_default is True
    assert process.intent == "workspace"
    assert len(process.thread_configs) == 1

    thread = process.thread_configs[0]
    assert thread.key == "home.main"
    assert thread.thread_key == "home.main"
    assert thread.is_default is True
    assert thread.workspace_view_key == "thread.workspace"
    assert len(thread.projection_experiences) == 1
    assert len(thread.layout_configs) == 2

    projection = thread.projection_experiences[0]
    assert projection.projection_experience_name == "home_story"
    assert projection.view_key == "overview.home"
    assert projection.is_default is True

    layout = thread.layout_configs[0]
    assert layout.layout_key == "configuration_map"
    assert layout.key == "configuration_map"
    assert layout.is_default is True
    assert len(layout.sections) == 1
    assert layout.sections[0].section_key == "main"
    assert layout.sections[0].projection_experience_name == "home_story"
    assert layout.sections[0].view_key == "overview.home"
    assert layout.sections[0].section_graph_binding_key == "home.main"
    assert layout.sections[0].is_default is True

    artifact = emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root / ".aware" / "experience" / "runtime" / "home_story",
        repo_root=root,
    )
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert payload["environment_profile_ownership"][0]["key"] == "os.default"
    assert payload["environment_profile_ownership"][0]["roles"] == [
        {
            "name": "home_resident",
            "description": None,
            "capabilities": ["aware_home.home.Home.view"],
        }
    ]
    assert payload["environment_profile_ownership"][0]["actors"] == [
        {
            "key": "resident",
            "title": None,
            "description": None,
            "type": "Human",
            "role_names": ["home_resident"],
        }
    ]
    assert (
        payload["environment_profile_ownership"][0]["process_configs"][0][
            "thread_configs"
        ][0]["projection_experiences"][0]["projection_experience_name"]
        == "home_story"
    )
    assert payload["environment_profile_ownership"][0]["view_event_transitions"] == [
        {
            "key": "home.open.main",
            "source_projection_experience_name": "home_story",
            "source_view_key": "overview.home",
            "trigger_event_ref": "HomeOpened",
            "trigger_event_config_ref": "home.opened",
            "target_projection_experience_name": "home_story",
            "target_section_graph_binding_key": "home.main",
            "source_path": "profiles.aware",
            "name": "Open main home",
            "rationale": "Home opened event focuses the main home surface.",
            "idempotency_policy": "event_commit",
        }
    ]
    assert payload["environment_profile_ownership"][0]["process_configs"][0][
        "thread_configs"
    ][0]["layout_configs"][0] == {
        "layout_key": "configuration_map",
        "source_path": "profiles.aware",
        "key": "configuration_map",
        "position": None,
        "is_default": True,
        "narrative": None,
        "intent": None,
        "sections": [
            {
                "section_key": "main",
                "projection_experience_name": "home_story",
                "view_key": "overview.home",
                "source_path": "profiles.aware",
                "key": "main",
                "section_graph_binding_key": "home.main",
                "position": None,
                "is_default": True,
                "narrative": None,
                "intent": None,
            }
        ],
    }


def test_environment_profile_compiler_allows_dependency_scoped_transition_source(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience actor_home {",
                "  profile os.default {",
                "    transition identity.actor_home {",
                "      source projection aware_control_identity view identity.admission.v1",
                "      trigger event IdentityCreated",
                "      target projection actor_home binding actor.home",
                "    }",
                "    process continuous actor default {",
                "      thread actor.home default {",
                "        projection actor_home view actor.home default",
                "        layout configuration_map default {",
                "          section main projection actor_home view actor.home binding actor.home default",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    projection_ownership = ExperienceProjectionExperienceOwnership(
        name="actor_home",
        projection="Home",
        source_path="actor.aware",
        branches=(),
        observables=(
            ExperienceProjectionObservableOwnership(
                key="actor",
                source_path="actor.aware",
                views=(
                    ExperienceProjectionViewOwnership(
                        key="home",
                        is_default=True,
                        api_view_ref="actor.home",
                        source_path="actor.aware",
                    ),
                ),
            ),
        ),
    )

    profiles = load_environment_profile_ownership_from_sources(
        package_root=root,
        source_files=(Path("profiles.aware"),),
        projection_experience_ownership=(projection_ownership,),
        external_projection_experience_prefixes=("aware-control",),
    )

    transition = profiles[0].view_event_transitions[0]
    assert transition.source_projection_experience_name == "aware_control_identity"
    assert transition.source_view_key == "identity.admission.v1"
    assert transition.target_projection_experience_name == "actor_home"
    assert transition.target_section_graph_binding_key == "actor.home"


def test_environment_profile_compiler_allows_dependency_qualified_thread_layout(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience actor_home {",
                "  profile os.default {",
                "    process continuous actor default {",
                "      thread actor.home default {",
                "        projection aware_control.identity_projection view identity.admission.v1",
                "        projection actor_home view actor.home default",
                "        layout configuration_map default {",
                "          section orchestration projection aware_control.identity_projection view identity.admission.v1 binding identity.admission",
                "          section main projection actor_home view actor.home binding actor.home default",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    profiles = load_environment_profile_ownership_from_sources(
        package_root=root,
        source_files=(Path("profiles.aware"),),
        projection_experience_ownership=(
            _actor_home_projection_experience_ownership(),
        ),
        external_projection_experience_prefixes=("aware-control",),
    )

    thread = profiles[0].process_configs[0].thread_configs[0]
    assert {
        (item.projection_experience_name, item.view_key)
        for item in thread.projection_experiences
    } == {
        ("actor_home", "actor.home"),
        ("identity_projection", "identity.admission.v1"),
    }
    sections = {item.section_key: item for item in thread.layout_configs[0].sections}
    assert sections["orchestration"].projection_experience_name == "identity_projection"
    assert sections["orchestration"].section_graph_binding_key == ("identity.admission")


def test_environment_profile_compiler_rejects_undeclared_qualified_thread_layout(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience actor_home {",
                "  profile os.default {",
                "    process continuous actor default {",
                "      thread actor.home default {",
                "        projection unknown_package.external_projection view external.home",
                "        layout configuration_map default {",
                "          section main projection unknown_package.external_projection view external.home binding external.home default",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown projection experience"):
        load_environment_profile_ownership_from_sources(
            package_root=root,
            source_files=(Path("profiles.aware"),),
            projection_experience_ownership=(
                _actor_home_projection_experience_ownership(),
            ),
            external_projection_experience_prefixes=("aware-control",),
        )


def test_environment_profile_compiler_resolves_dependency_qualified_transition_event_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience actor_home {",
                "  profile os.default {",
                "    transition identity.actor_home {",
                "      source projection aware_control_identity view identity.admission.v1",
                "      trigger event aware_control.IdentityAdmitted",
                "      target projection actor_home binding actor.home",
                "    }",
                "    process continuous actor default {",
                "      thread actor.home default {",
                "        projection actor_home view actor.home default",
                "        layout configuration_map default {",
                "          section main projection actor_home view actor.home binding actor.home default",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    profiles = load_environment_profile_ownership_from_sources(
        package_root=root,
        source_files=(Path("profiles.aware"),),
        projection_experience_ownership=(
            _actor_home_projection_experience_ownership(),
        ),
        event_ownership=(_identity_admitted_dependency_event_ownership(),),
        external_projection_experience_prefixes=("aware-control",),
    )

    transition = profiles[0].view_event_transitions[0]
    assert transition.trigger_event_ref == "aware_control.IdentityAdmitted"
    assert transition.trigger_event_config_ref == "identity.admitted"


def test_environment_profile_compiler_requires_qualified_dependency_event_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience actor_home {",
                "  profile os.default {",
                "    transition identity.actor_home {",
                "      source projection aware_control_identity view identity.admission.v1",
                "      trigger event IdentityAdmitted",
                "      target projection actor_home binding actor.home",
                "    }",
                "    process continuous actor default {",
                "      thread actor.home default {",
                "        projection actor_home view actor.home default",
                "        layout configuration_map default {",
                "          section main projection actor_home view actor.home binding actor.home default",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="references unknown event"):
        load_environment_profile_ownership_from_sources(
            package_root=root,
            source_files=(Path("profiles.aware"),),
            projection_experience_ownership=(
                _actor_home_projection_experience_ownership(),
            ),
            event_ownership=(_identity_admitted_dependency_event_ownership(),),
            external_projection_experience_prefixes=("aware-control",),
        )


def test_build_experience_compile_plan_loads_dependency_event_catalog(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    control_root = root / "experiences" / "aware-control"
    actor_root = root / "experiences" / "aware-actor"
    _write_named_experience_toml(
        root=control_root,
        package_name="aware-control",
        fqn_prefix="aware_control",
    )
    _write_named_experience_toml(
        root=actor_root,
        package_name="aware-actor",
        fqn_prefix="aware_actor",
        dependencies=("aware-control",),
    )
    (control_root / "events").mkdir(parents=True, exist_ok=True)
    (control_root / "events" / "identity_admission.aware").write_text(
        "\n".join(
            [
                'event IdentityAdmitted name "identity.admitted" renderer "identity.admitted" {',
                "  bind Identity Identity.Identity create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (actor_root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience actor_home on aware_identity.identity.Identity {",
                "  observable actor {",
                _api_view_mount("home", "actor.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (actor_root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience actor_home {",
                "  profile os.default {",
                "    transition identity.actor_home {",
                "      source projection aware_control_identity view identity.admission.v1",
                "      trigger event aware_control.IdentityAdmitted",
                "      target projection actor_home binding actor.home",
                "    }",
                "    process continuous actor default {",
                "      thread actor.home default {",
                "        projection actor_home view actor.home default",
                "        layout configuration_map default {",
                "          section main projection actor_home view actor.home binding actor.home default",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=actor_root / "aware.experience.toml",
        repo_root=root,
    ).build_snapshot()
    composition_path = _write_composition_truth(
        root=root,
        projection="Identity",
        class_fqns=("aware_identity_ontology.identity.identity.Identity",),
        observables_by_projection={"Identity": ("actor",)},
    )
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert [event.event_name for event in plan.event_ownership] == ["identity.admitted"]
    assert plan.event_ownership[0].is_dependency is True
    transition = plan.environment_profile_ownership[0].view_event_transitions[0]
    assert transition.trigger_event_ref == "aware_control.IdentityAdmitted"
    assert transition.trigger_event_config_ref == "identity.admitted"


def _write_memory_action_catalog(
    *, root: Path, package_name: str = "aware-memory", fqn_prefix: str = "aware_memory"
) -> Path:
    memory_root = root / "experiences" / package_name
    _write_named_experience_toml(
        root=memory_root,
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    (memory_root / "actions").mkdir(parents=True, exist_ok=True)
    (memory_root / "actions" / "memory_actions.aware").write_text(
        "\n".join(
            [
                "action MemoryRememberEvent {",
                '  name "memory.remember_event";',
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return memory_root


def _write_conversation_event_action_package(
    *,
    root: Path,
    action_ref: str,
    dependencies: tuple[str, ...] = ("aware-memory",),
) -> Path:
    conversation_root = root / "experiences" / "aware-conversations"
    _write_named_experience_toml(
        root=conversation_root,
        package_name="aware-conversations",
        fqn_prefix="aware_conversations",
        dependencies=dependencies,
    )
    (conversation_root / "events").mkdir(parents=True, exist_ok=True)
    (conversation_root / "events" / "conversation_events.aware").write_text(
        "\n".join(
            [
                _CONVERSATION_EVENT_CREATED_COMPACT_HEADER,
                "  bind Conversation Conversation.ConversationMessage create",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (conversation_root / "environments").mkdir(parents=True, exist_ok=True)
    (conversation_root / "environments" / "conversation_environment.aware").write_text(
        "\n".join(
            [
                "environment aware_conversations {",
                "  event ConversationMessageCreated {",
                f"    action {action_ref}",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return conversation_root / "aware.experience.toml"


def test_build_experience_compile_plan_loads_dependency_action_catalog(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    _write_memory_action_catalog(root=root)
    spec_path = _write_conversation_event_action_package(
        root=root,
        action_ref="aware_memory.memory.remember_event",
    )
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=spec_path,
        repo_root=root,
    ).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.action_ownership) == 1
    action = plan.action_ownership[0]
    assert action.symbol == "MemoryRememberEvent"
    assert action.action_name == "memory.remember_event"
    assert action.package_name == "aware-memory"
    assert action.fqn_prefix == "aware_memory"
    assert action.is_dependency is True
    assert plan.environment_ownership[0].events[0].actions[0].action == (
        "aware_memory.memory.remember_event"
    )


def test_build_experience_compile_plan_requires_qualified_dependency_action_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    _write_memory_action_catalog(root=root)
    spec_path = _write_conversation_event_action_package(
        root=root,
        action_ref="memory.remember_event",
    )
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=spec_path,
        repo_root=root,
    ).build_snapshot()
    with pytest.raises(ValueError, match="references unknown action"):
        build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


def test_build_experience_compile_plan_requires_declared_action_dependency(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    _write_memory_action_catalog(root=root)
    spec_path = _write_conversation_event_action_package(
        root=root,
        action_ref="aware_memory.memory.remember_event",
        dependencies=(),
    )
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=spec_path,
        repo_root=root,
    ).build_snapshot()
    with pytest.raises(ValueError, match="references unknown action"):
        build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


def test_build_experience_compile_plan_fails_ambiguous_dependency_action_ref(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    _write_memory_action_catalog(root=root, package_name="aware-memory")
    _write_memory_action_catalog(
        root=root,
        package_name="other-memory",
        fqn_prefix="aware_memory",
    )
    spec_path = _write_conversation_event_action_package(
        root=root,
        action_ref="aware_memory.memory.remember_event",
        dependencies=("aware-memory", "other-memory"),
    )
    composition_path = _write_composition_truth(
        root=root,
        projection="Conversation",
        class_names=("ConversationMessage",),
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=spec_path,
        repo_root=root,
    ).build_snapshot()
    with pytest.raises(ValueError, match="Ambiguous action reference key"):
        build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


@pytest.mark.parametrize(
    ("package_dir", "graph_name", "experience_name"),
    _DISTRIBUTED_GRAPH_ROOT_CASES,
)
def test_distributed_experience_graph_roots_use_bare_identity_refs(
    package_dir: str,
    graph_name: str,
    experience_name: str,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    package_root = repo_root / "experiences" / package_dir
    _write_named_experience_toml(
        root=package_root,
        package_name=package_dir,
        fqn_prefix=package_dir.replace("-", "_"),
    )
    (package_root / "experiences.aware").write_text(
        "\n".join(
            [
                f"experience {experience_name} on aware_identity.identity.Identity {{",
                "  observable actor {",
                _api_view_mount("home", "identity.home"),
                "  }",
                "  node identity.Identity {",
                "    id now",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "graphs.aware").write_text(
        "\n".join(
            [
                f"graph {graph_name} on {experience_name} {{",
                "  root now",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    snapshot = ExperienceWorkspace.from_toml(
        toml_path=package_root / "aware.experience.toml",
        repo_root=repo_root,
    ).build_snapshot()
    projection_ownership = load_projection_experience_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
    )

    graph_ownership = load_graph_ownership_from_sources(
        package_root=package_root,
        source_files=snapshot.source_files,
        projection_experience_ownership=projection_ownership,
    )

    graph_by_name = {graph.name: graph for graph in graph_ownership}
    assert graph_by_name[graph_name].experience == experience_name
    assert graph_by_name[graph_name].root == "now"


def test_build_experience_compile_plan_environment_profile_accepts_multiple_views_for_one_projection(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "  observable overview {",
                _api_view_mount("home", "home.home"),
                _api_view_mount("detail", "home.detail", default=False),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience home_story {",
                "  profile os.default {",
                "    process continuous home default {",
                "      thread home.main default {",
                "        projection home_story view overview.home default",
                "        projection home_story view overview.detail",
                "        layout configuration_map default {",
                "          section main projection home_story view overview.home binding home.main default",
                "          section detail projection home_story view overview.detail binding home.detail",
                "        }",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Home",
        class_fqns=("aware_home.home.Home",),
        observables_by_projection={"Home": ("overview",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    thread = plan.environment_profile_ownership[0].process_configs[0].thread_configs[0]
    assert len(thread.projection_experiences) == 1
    assert thread.projection_experiences[0].projection_experience_name == "home_story"
    assert thread.projection_experiences[0].view_key == "overview.home"
    assert [section.view_key for section in thread.layout_configs[0].sections] == [
        "overview.detail",
        "overview.home",
    ]


def test_build_experience_compile_plan_projection_section_surface_ownership_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "  observable overview {",
                _api_view_mount("home", "home.home"),
                "  }",
                "  observable security {",
                _api_view_mount("door", "home.door"),
                "  }",
                "  node home.Home {",
                "    id home",
                "  }",
                "  node home.Home::doors {",
                "    id front_door",
                "  }",
                "  surface home.primary {",
                "    section primary;",
                "    view overview.home;",
                "    graph home;",
                "  }",
                "  surface security.front_door {",
                "    section orchestration;",
                "    view security.door;",
                "    graph home.front_door;",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Home",
        class_fqns=("aware_home.home.Home",),
        observables_by_projection={"Home": ("overview", "security")},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.projection_experience_ownership) == 1
    ownership = plan.projection_experience_ownership[0]
    assert ownership.name == "home_story"
    assert ownership.projection == "Home"
    assert len(ownership.section_surfaces) == 2

    surfaces_by_key = {
        surface.surface_key: surface for surface in ownership.section_surfaces
    }
    assert surfaces_by_key["home.primary"].section_key == "primary"
    assert surfaces_by_key["home.primary"].observable_key == "overview"
    assert surfaces_by_key["home.primary"].view_key == "home"
    assert surfaces_by_key["home.primary"].graph_identity_ref == "home"
    assert surfaces_by_key["home.primary"].node_identity_ref is None
    assert surfaces_by_key["home.primary"].source_surface_key is None
    assert surfaces_by_key["security.front_door"].section_key == "orchestration"
    assert surfaces_by_key["security.front_door"].observable_key == "security"
    assert surfaces_by_key["security.front_door"].view_key == "door"
    assert (
        surfaces_by_key["security.front_door"].graph_identity_ref == "home.front_door"
    )
    assert surfaces_by_key["security.front_door"].node_identity_ref is None
    assert surfaces_by_key["security.front_door"].source_surface_key is None

    artifact = emit_experience_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=root / ".aware" / "experience" / "runtime" / "home_story",
        repo_root=root,
    )
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert payload["projection_experience_ownership"][0]["section_surfaces"] == [
        {
            "surface_key": "security.front_door",
            "section_key": "orchestration",
            "observable_key": "security",
            "view_key": "door",
            "source_path": "experiences.aware",
            "source_surface_key": None,
            "graph_identity_ref": "home.front_door",
            "node_identity_ref": None,
        },
        {
            "surface_key": "home.primary",
            "section_key": "primary",
            "observable_key": "overview",
            "view_key": "home",
            "source_path": "experiences.aware",
            "source_surface_key": None,
            "graph_identity_ref": "home",
            "node_identity_ref": None,
        },
    ]


def test_build_experience_compile_plan_environment_profile_issue_assignee_contract_valid(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience issue_lifecycle on aware_workflow.issue.Issue {",
                "  observable workflow {",
                _api_view_mount("issue", "workflow.issue"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "workflow_issue_actor_roles.aware").write_text(
        "\n".join(
            [
                "role issue_assignee {",
                "  aware_workflow.issue.Issue.start_progress",
                "  aware_workflow.issue.Issue.block",
                "  aware_workflow.issue.Issue.resume",
                "  aware_workflow.issue.Issue.close",
                "}",
                "",
                "actor issue_assignee_bot System {",
                "}",
                "",
                "environment workflow_issue {",
                "  actor issue_assignee_bot {",
                "    role issue_assignee",
                "  }",
                "  experience issue_lifecycle",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience issue_lifecycle {",
                "  profile os.default {",
                '    title "Workflow Issue OS"',
                '    narrative "Issue-centric assignee contract published through Experience."',
                "    process continuous workflow default {",
                "      intent workspace",
                "      thread workflow.issue default {",
                "        workspace_view thread.workspace",
                "        projection issue_lifecycle view workflow.issue default",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Issue",
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
            "aware_workflow.issue.Issue",
        ),
        observables_by_projection={"Issue": ("workflow",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()
    plan = build_experience_compile_plan(
        snapshot=snapshot,
        environment_composition_manifest_path=composition_path,
        repo_root=root,
    )

    assert len(plan.environment_profile_ownership) == 1
    profile = plan.environment_profile_ownership[0]
    assert profile.experience_name == "issue_lifecycle"
    assert profile.key == "os.default"
    assert profile.title == "Workflow Issue OS"
    assert profile.roles[0].name == "issue_assignee"
    assert profile.roles[0].capabilities == tuple(
        sorted(
            (
                "aware_workflow.issue.Issue.start_progress",
                "aware_workflow.issue.Issue.block",
                "aware_workflow.issue.Issue.resume",
                "aware_workflow.issue.Issue.close",
            )
        )
    )
    assert len(profile.actors) == 1
    assert profile.actors[0].key == "issue_assignee_bot"
    assert profile.actors[0].actor_type == "System"
    assert profile.actors[0].role_names == ("issue_assignee",)
    assert len(profile.process_configs) == 1
    assert (
        profile.process_configs[0].thread_configs[0].projection_experiences[0].view_key
        == "workflow.issue"
    )


def test_build_experience_compile_plan_environment_profile_fails_on_unknown_projection_experience(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "  observable overview {",
                _api_view_mount("home", "home.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience home_story {",
                "  profile os.default {",
                "    process continuous home default {",
                "      thread home.main default {",
                "        projection ghost_story view overview.home default",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Home",
        class_names=("Home",),
        class_fqns=("aware_home.home.Home",),
        observables_by_projection={"Home": ("overview",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    with pytest.raises(ValueError, match="unknown projection experience"):
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )


def test_build_experience_compile_plan_environment_profile_actor_publication_fails_when_ambiguous(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text(
        'aware = 1\n[environment]\nhandle = "kernel"\nmodules = ["experience"]\n',
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience home_story on aware_home.home.Home {",
                "  observable overview {",
                _api_view_mount("home", "home.home"),
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "actors").mkdir(parents=True, exist_ok=True)
    (root / "actors" / "home_actor_roles.aware").write_text(
        "\n".join(
            [
                "role home_resident {",
                "  aware_home.home.Home.view",
                "}",
                "",
                "actor resident Human {",
                "}",
                "",
                "environment home_story_main {",
                "  actor resident {",
                "    role home_resident",
                "  }",
                "  experience home_story",
                "}",
                "",
                "environment home_story_backup {",
                "  actor resident {",
                "    role home_resident",
                "  }",
                "  experience home_story",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "profiles.aware").write_text(
        "\n".join(
            [
                "experience home_story {",
                "  profile os.default {",
                "    process continuous home default {",
                "      thread home.main default {",
                "        projection home_story view overview.home default",
                "      }",
                "    }",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = _write_experience_toml(root=root)
    composition_path = _write_composition_truth(
        root=root,
        projection="Home",
        class_fqns=(
            "aware_identity_ontology.actor.actor_config.ActorConfig",
            "aware_identity_ontology.role.role_config.RoleConfig",
            "aware_home.home.Home",
        ),
        observables_by_projection={"Home": ("overview",)},
    )
    snapshot = ExperienceWorkspace.from_toml(toml_path=spec_path).build_snapshot()

    with pytest.raises(ValueError, match="ambiguous across multiple environments"):
        _ = build_experience_compile_plan(
            snapshot=snapshot,
            environment_composition_manifest_path=composition_path,
            repo_root=root,
        )
