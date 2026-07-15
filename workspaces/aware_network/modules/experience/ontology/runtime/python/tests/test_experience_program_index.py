from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from aware_experience.program.registry_index import (
    ProgramAssetRef,
    ProgramRegistryError,
    ProgramRegistryIndex,
    resolve_program_asset_paths,
)


@dataclass(frozen=True, slots=True)
class ProgramRegistryEntry:
    ref: str
    module_id: str
    program_name: str
    program_path: str
    content_hash: str
    dependencies: list[str]
    required_symbols: list[str]
    optional_symbols: list[str]
    invocation_plan_path: str | None = None


@dataclass(frozen=True, slots=True)
class _ManifestWithProgramRegistry:
    program_registry: list[ProgramRegistryEntry]


def _manifest_with_entries(
    *, entries: list[ProgramRegistryEntry]
) -> _ManifestWithProgramRegistry:
    return _ManifestWithProgramRegistry(program_registry=entries)


def test_program_registry_index_build_and_lookup() -> None:
    entry = ProgramRegistryEntry(
        ref="agent:EnsureBootAgentGraph_v0",
        module_id="agent",
        program_name="EnsureBootAgentGraph_v0",
        program_path="modules/agent/programs/boot/boot.aware",
        content_hash="sha256:test",
        dependencies=[],
        required_symbols=[],
        optional_symbols=[],
    )
    index = ProgramRegistryIndex.build(manifest=_manifest_with_entries(entries=[entry]))
    found = index.get(
        ProgramAssetRef(module_id="agent", program_name="EnsureBootAgentGraph_v0")
    )
    assert found is not None
    assert found.program_path == "modules/agent/programs/boot/boot.aware"


def test_program_registry_index_duplicate_refs_fail() -> None:
    entry = ProgramRegistryEntry(
        ref="agent:EnsureBootAgentGraph_v0",
        module_id="agent",
        program_name="EnsureBootAgentGraph_v0",
        program_path="modules/agent/programs/boot/boot.aware",
        content_hash="sha256:test",
        dependencies=[],
        required_symbols=[],
        optional_symbols=[],
    )
    with pytest.raises(ProgramRegistryError, match="Ambiguous program ref"):
        ProgramRegistryIndex.build(
            manifest=_manifest_with_entries(entries=[entry, entry])
        )


def test_resolve_program_asset_paths_prefers_aware_programs_toml(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    programs_root = repo_root / "modules" / "agent" / "programs"
    src = programs_root / "boot" / "boot.aware"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("program EnsureBootAgentGraph_v0 {}", encoding="utf-8")
    (programs_root / "aware.programs.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "agent:EnsureBootAgentGraph_v0"',
                'path = "boot/boot.aware"',
                'name = "EnsureBootAgentGraph_v0"',
                "dependencies = []",
                "required_symbols = []",
                "optional_symbols = []",
            ]
        ),
        encoding="utf-8",
    )

    resolved = resolve_program_asset_paths(
        repo_root=repo_root,
        program_refs=["agent:EnsureBootAgentGraph_v0"],
    )
    assert resolved == [src]


def test_resolve_program_asset_paths_without_registry_toml_fails(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    src = repo_root / "modules" / "agent" / "programs" / "boot" / "boot.aware"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("program EnsureBootAgentGraph_v0 {}", encoding="utf-8")

    with pytest.raises(ProgramRegistryError, match="requires aware.programs.toml"):
        resolve_program_asset_paths(
            repo_root=repo_root,
            program_refs=["agent:EnsureBootAgentGraph_v0"],
        )


def test_resolve_program_asset_paths_supports_experience_namespace_refs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    package_root = repo_root / "modules" / "conversation" / "experience" / "default"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "conversation-default"',
                'fqn_prefix = "conversation_default"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "programs" / "integration").mkdir(parents=True, exist_ok=True)
    src = package_root / "programs" / "integration" / "human_message.aware"
    src.write_text("program HumanConversationMessage_v1 {}", encoding="utf-8")
    (package_root / "aware.programs.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "conversation_default:HumanConversationMessage_v1"',
                'path = "programs/integration/human_message.aware"',
                'name = "HumanConversationMessage_v1"',
            ]
        ),
        encoding="utf-8",
    )

    resolved = resolve_program_asset_paths(
        repo_root=repo_root,
        program_refs=["conversation_default:HumanConversationMessage_v1"],
    )
    assert resolved == [src]


def test_resolve_program_asset_paths_supports_declared_workspace_experience_packages(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    module_root = repo_root / "workspaces" / "aware_network" / "modules" / "identity"
    package_root = module_root / "experiences" / "aware_identity"
    package_root.mkdir(parents=True, exist_ok=True)
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[module]",
                'runtime_root = "ontology/runtime/python"',
                "",
                "[[packages]]",
                'id = "identity_experience"',
                'kind = "experience"',
                'manifest = "experiences/aware_identity/aware.experience.toml"',
                'visibility = "module"',
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "identity-default"',
                'fqn_prefix = "identity"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "programs" / "seed").mkdir(parents=True, exist_ok=True)
    src = package_root / "programs" / "seed" / "ensure_identity_signup_v0.aware"
    src.write_text("program EnsureIdentitySignup_v0 {}", encoding="utf-8")
    (package_root / "aware.programs.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "identity:EnsureIdentitySignup_v0"',
                'path = "programs/seed/ensure_identity_signup_v0.aware"',
                'name = "EnsureIdentitySignup_v0"',
            ]
        ),
        encoding="utf-8",
    )

    resolved = resolve_program_asset_paths(
        repo_root=repo_root,
        program_refs=["identity:EnsureIdentitySignup_v0"],
    )
    assert resolved == [src]


def test_resolve_program_asset_paths_with_compile_plan_contract_valid(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    src = _seed_experience_program_package(repo_root=repo_root)
    compile_plan_path = (
        repo_root
        / ".aware"
        / "experience"
        / "runtime"
        / "conversation-default"
        / "experience.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    compile_plan_path.write_text(
        json.dumps(
            {
                "program_ownership": [],
                "action_ownership": [],
                "environment_ownership": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    resolved = resolve_program_asset_paths(
        repo_root=repo_root,
        program_refs=["conversation_default:HumanConversationMessage_v1"],
    )
    assert resolved == [src]


def test_resolve_program_asset_paths_fails_when_compile_plan_missing_action_ownership(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    _seed_experience_program_package(repo_root=repo_root)
    compile_plan_path = (
        repo_root
        / ".aware"
        / "experience"
        / "runtime"
        / "conversation-default"
        / "experience.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    compile_plan_path.write_text(
        json.dumps({"program_ownership": [], "environment_ownership": []}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ProgramRegistryError, match="missing required field action_ownership"
    ):
        resolve_program_asset_paths(
            repo_root=repo_root,
            program_refs=["conversation_default:HumanConversationMessage_v1"],
        )


def test_resolve_program_asset_paths_fails_when_compile_plan_missing_environment_ownership(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    _seed_experience_program_package(repo_root=repo_root)
    compile_plan_path = (
        repo_root
        / ".aware"
        / "experience"
        / "runtime"
        / "conversation-default"
        / "experience.compile_plan.json"
    )
    compile_plan_path.parent.mkdir(parents=True, exist_ok=True)
    compile_plan_path.write_text(
        json.dumps({"program_ownership": [], "action_ownership": []}, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ProgramRegistryError, match="missing required field environment_ownership"
    ):
        resolve_program_asset_paths(
            repo_root=repo_root,
            program_refs=["conversation_default:HumanConversationMessage_v1"],
        )


def _seed_experience_program_package(*, repo_root: Path) -> Path:
    package_root = repo_root / "modules" / "conversation" / "experience" / "default"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "conversation-default"',
                'fqn_prefix = "conversation_default"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
            ]
        ),
        encoding="utf-8",
    )
    (package_root / "programs" / "integration").mkdir(parents=True, exist_ok=True)
    src = package_root / "programs" / "integration" / "human_message.aware"
    src.write_text("program HumanConversationMessage_v1 {}", encoding="utf-8")
    (package_root / "aware.programs.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[programs]]",
                'ref = "conversation_default:HumanConversationMessage_v1"',
                'path = "programs/integration/human_message.aware"',
                'name = "HumanConversationMessage_v1"',
            ]
        ),
        encoding="utf-8",
    )
    return src
