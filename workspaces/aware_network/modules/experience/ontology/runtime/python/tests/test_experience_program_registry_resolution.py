from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from aware_experience.program.registry_index import (
    ProgramAssetRef,
    ProgramRegistryError,
    resolve_program_asset_path_from_manifest,
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


def _manifest_with_registry(
    *, entry: ProgramRegistryEntry
) -> _ManifestWithProgramRegistry:
    return _ManifestWithProgramRegistry(program_registry=[entry])


def test_resolve_program_asset_path_from_manifest_happy_path(tmp_path: Path) -> None:
    repo_root = tmp_path.resolve()
    src = repo_root / "modules" / "agent" / "programs" / "boot" / "boot.aware"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("program EnsureBootAgentGraph_v0 {}", encoding="utf-8")

    manifest = _manifest_with_registry(
        entry=ProgramRegistryEntry(
            ref="agent:EnsureBootAgentGraph_v0",
            module_id="agent",
            program_name="EnsureBootAgentGraph_v0",
            program_path="modules/agent/programs/boot/boot.aware",
            content_hash="sha256:test",
            dependencies=[],
            required_symbols=[],
            optional_symbols=[],
        )
    )

    resolved = resolve_program_asset_path_from_manifest(
        repo_root=repo_root,
        manifest=manifest,
        ref=ProgramAssetRef(module_id="agent", program_name="EnsureBootAgentGraph_v0"),
    )
    assert resolved == src


def test_resolve_program_asset_path_from_manifest_missing_ref_fails(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    src = repo_root / "modules" / "agent" / "programs" / "boot" / "boot.aware"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("program EnsureBootAgentGraph_v0 {}", encoding="utf-8")

    manifest = _manifest_with_registry(
        entry=ProgramRegistryEntry(
            ref="agent:EnsureBootAgentGraph_v0",
            module_id="agent",
            program_name="EnsureBootAgentGraph_v0",
            program_path="modules/agent/programs/boot/boot.aware",
            content_hash="sha256:test",
            dependencies=[],
            required_symbols=[],
            optional_symbols=[],
        )
    )

    with pytest.raises(
        ProgramRegistryError, match=r"not found in manifest program_registry"
    ):
        resolve_program_asset_path_from_manifest(
            repo_root=repo_root,
            manifest=manifest,
            ref=ProgramAssetRef(module_id="agent", program_name="MissingProgram"),
        )


def test_resolve_program_asset_path_from_manifest_allows_namespaced_ref_owner_mismatch(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    src = (
        repo_root
        / "modules"
        / "conversation"
        / "experience"
        / "default"
        / "programs"
        / "conversation_turn_v1.aware"
    )
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("program ConversationTurn_v1 {}", encoding="utf-8")

    manifest = _manifest_with_registry(
        entry=ProgramRegistryEntry(
            ref="conversation_default:ConversationTurn_v1",
            module_id="conversation",
            program_name="ConversationTurn_v1",
            program_path="modules/conversation/experience/default/programs/conversation_turn_v1.aware",
            content_hash="sha256:test",
            dependencies=[],
            required_symbols=[],
            optional_symbols=[],
        )
    )

    resolved = resolve_program_asset_path_from_manifest(
        repo_root=repo_root,
        manifest=manifest,
        ref=ProgramAssetRef(
            module_id="conversation_default",
            program_name="ConversationTurn_v1",
        ),
    )
    assert resolved == src
