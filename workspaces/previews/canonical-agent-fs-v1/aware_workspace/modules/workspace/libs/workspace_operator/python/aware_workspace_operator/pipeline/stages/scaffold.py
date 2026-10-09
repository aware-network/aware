"""Workspace scaffold generation stages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import tomllib

from aware_workspace_operator.models import (
    AgentFilesStatus,
    AgentsMdStatus,
    CollaborationScaffoldStatus,
    DeliveryContractsStatus,
    EnvironmentFileStatus,
    GrammarDocsBundleStatus,
    ProofTestModuleStatus,
    ProofTestsStatus,
    ScaffoldFileStatus,
    SeedBundleStatus,
    SkillPackExporterProtocol,
    SkillPackExportResultProtocol,
    SkillsStatus,
    SoftwareRulesBundleStatus,
    WorkspaceBootstrapOptions,
    WorkspaceBootstrapMode,
    WorkspaceManifestStatus,
    WorkspacePreflightState,
    WorkspaceScaffoldState,
    WorkspaceScaffoldStatus,
)
from aware_workspace_operator.prompt_composition import (
    compose_software_templates,
    load_software_prompt_profile,
    load_software_template_files,
)
from aware_workspace_operator.renderers import (
    render_agent_delivery_contract,
    render_environment_experience_contract,
    render_environment_file,
    render_evidence_policy_contract,
    render_quality_gates_contract,
    render_minimal_daily_feed_log,
    render_minimal_feed_protocol,
    render_minimal_feed_snapshot,
    render_minimal_issues_protocol,
    render_module_proof_test_scaffold,
    render_workspace_agents_md,
    render_workspace_ci_workflow,
    render_workspace_manifest_file,
    render_workspace_pyproject,
    render_workspace_root_placeholder_readme,
)

_WORKSPACE_MANIFEST_RELPATH = Path("aware.workspace.toml")
_GRAMMAR_DOCS_TARGET_DIR = Path("docs") / "aware" / "grammar"
_SOFTWARE_RULES_TARGET_DIR = Path("docs") / "rules" / "SOFTWARE"
_SEEDS_TARGET_DIR = Path("configs") / "seeds"


@dataclass(frozen=True, slots=True)
class _WorkspaceManifestSnapshot:
    handle: str
    title: str
    environments: tuple[str, ...]
    apis: tuple[str, ...]
    economies: tuple[str, ...]
    services: tuple[str, ...]
    experiences: tuple[str, ...]
    attentions: tuple[str, ...]
    panes: tuple[str, ...]
    interfaces: tuple[str, ...]
    nodes: tuple[str, ...]
    inferences: tuple[str, ...]


def run_scaffold_stage(
    *,
    request: WorkspaceBootstrapOptions,
    preflight: WorkspacePreflightState,
    repo_root: Path,
    export_skill_pack_fn: SkillPackExporterProtocol | None,
) -> WorkspaceScaffoldState:
    """Write scaffold artifacts according to effective write flags."""

    write_environment_file = bool(request.write_environment_file) and not bool(
        request.skip_environment_file
    )
    write_agent_files = bool(request.write_agent_files) and not bool(
        request.skip_agent_files
    )
    write_proof_tests = bool(request.write_proof_tests) and not bool(
        request.skip_proof_tests
    )
    write_collaboration_scaffold = bool(
        request.write_collaboration_scaffold
    ) and not bool(request.skip_collaboration_scaffold)
    write_workspace_scaffold = bool(request.write_workspace_scaffold) and not bool(
        request.skip_workspace_scaffold
    )
    write_delivery_contracts = bool(request.write_delivery_contracts) and not bool(
        request.skip_delivery_contracts
    )
    write_grammar_docs_bundle = bool(request.write_grammar_docs_bundle) and not bool(
        request.skip_grammar_docs_bundle
    )
    write_software_rules_bundle = bool(
        request.write_software_rules_bundle
    ) and not bool(request.skip_software_rules_bundle)
    write_seed_bundle = (
        bool(request.write_seed_bundle)
        and not bool(request.skip_seed_bundle)
        and request.automation_phase == "phase-2"
    )

    module_ids = tuple(preflight.module_ids)

    environment_file = ensure_environment_file(
        repo_root=repo_root,
        module_ids=module_ids,
        write_environment_file=write_environment_file,
        environment_file_relpath=request.environment_file_relpath,
        environment_handle=request.environment_handle,
        environment_title=request.environment_title,
    )
    workspace_manifest = ensure_workspace_manifest(
        repo_root=repo_root,
        environment_file=environment_file,
    )
    agent_files = ensure_agent_files(
        repo_root=repo_root,
        workspace_manifest_relpath=_WORKSPACE_MANIFEST_RELPATH.as_posix(),
        module_ids=module_ids,
        environment_file_relpath=request.environment_file_relpath,
        environment_seeded=environment_file.exists,
        bootstrap_mode=request.bootstrap_mode,
        write_agent_files=write_agent_files,
        skill_pack=request.skill_pack,
        skill_export_mode=request.skill_export_mode,
        export_skill_pack_fn=export_skill_pack_fn,
    )
    collaboration_scaffold = ensure_collaboration_scaffold(
        repo_root=repo_root,
        write_collaboration_scaffold=write_collaboration_scaffold,
    )
    proof_tests = ensure_proof_tests(
        repo_root=repo_root,
        module_ids=module_ids,
        write_proof_tests=write_proof_tests,
    )
    workspace_scaffold = ensure_workspace_scaffold(
        repo_root=repo_root,
        module_ids=module_ids,
        environment_file_relpath=request.environment_file_relpath,
        write_workspace_scaffold=write_workspace_scaffold,
    )
    delivery_contracts = ensure_delivery_contracts(
        repo_root=repo_root,
        write_delivery_contracts=write_delivery_contracts,
    )
    grammar_docs_bundle = ensure_grammar_docs_bundle(
        repo_root=repo_root,
        write_grammar_docs_bundle=write_grammar_docs_bundle,
    )
    software_rules_bundle = ensure_software_rules_bundle(
        repo_root=repo_root,
        write_software_rules_bundle=write_software_rules_bundle,
        template_id=request.software_template_id,
        profile_id=request.software_profile_id,
    )
    seed_bundle = ensure_seed_bundle(
        repo_root=repo_root,
        write_seed_bundle=write_seed_bundle,
    )

    return WorkspaceScaffoldState(
        workspace_manifest=workspace_manifest,
        environment_file=environment_file,
        agent_files=agent_files,
        collaboration_scaffold=collaboration_scaffold,
        proof_tests=proof_tests,
        workspace_scaffold=workspace_scaffold,
        delivery_contracts=delivery_contracts,
        grammar_docs_bundle=grammar_docs_bundle,
        software_rules_bundle=software_rules_bundle,
        seed_bundle=seed_bundle,
    )


def ensure_environment_file(
    *,
    repo_root: Path,
    module_ids: tuple[str, ...],
    write_environment_file: bool,
    environment_file_relpath: str,
    environment_handle: str,
    environment_title: str,
) -> EnvironmentFileStatus:
    env_rel = environment_file_relpath.strip() or "aware.environment.toml"
    env_path = (repo_root / env_rel).resolve()
    try:
        _ = env_path.relative_to(repo_root.resolve())
    except Exception as exc:
        raise ValueError(
            f"Environment file escapes repo root: {environment_file_relpath!r}"
        ) from exc

    existed = env_path.exists()
    created = False
    if write_environment_file and not existed:
        env_path.parent.mkdir(parents=True, exist_ok=True)
        _ = env_path.write_text(
            render_environment_file(
                environment_handle=environment_handle,
                environment_title=environment_title,
                module_ids=module_ids,
            ),
            encoding="utf-8",
        )
        created = True

    return EnvironmentFileStatus(
        path=env_path.as_posix(),
        exists=existed or created,
        created=created,
        write_requested=write_environment_file,
    )


def ensure_workspace_manifest(
    *,
    repo_root: Path,
    environment_file: EnvironmentFileStatus,
) -> WorkspaceManifestStatus:
    manifest_path = (repo_root / _WORKSPACE_MANIFEST_RELPATH).resolve()
    existed = manifest_path.exists()
    current_environment_paths: tuple[str, ...] = ()
    if environment_file.exists:
        current_environment_paths = (
            _normalize_repo_relative_path(
                repo_root=repo_root,
                path=Path(environment_file.path),
            ),
        )

    if existed:
        try:
            workspace_spec = _load_workspace_manifest_snapshot(toml_path=manifest_path)
        except Exception:
            return WorkspaceManifestStatus(
                path=manifest_path.as_posix(),
                exists=True,
                created=False,
                write_requested=True,
            )
        desired_environments = _merge_unique_paths(
            workspace_spec.environments,
            current_environment_paths,
        )
        desired_content = render_workspace_manifest_file(
            workspace_handle=workspace_spec.handle,
            workspace_title=workspace_spec.title,
            environment_paths=desired_environments,
            api_paths=workspace_spec.apis,
            economy_paths=workspace_spec.economies,
            service_paths=workspace_spec.services,
            experience_paths=workspace_spec.experiences,
            attention_paths=workspace_spec.attentions,
            pane_paths=workspace_spec.panes,
            interface_paths=workspace_spec.interfaces,
            node_paths=workspace_spec.nodes,
            inference_paths=workspace_spec.inferences,
        )
        current_content = manifest_path.read_text(encoding="utf-8")
        if current_content != desired_content:
            _ = manifest_path.write_text(desired_content, encoding="utf-8")
        return WorkspaceManifestStatus(
            path=manifest_path.as_posix(),
            exists=True,
            created=False,
            write_requested=True,
        )

    workspace_handle = _default_workspace_handle(repo_root=repo_root)
    workspace_title = _default_workspace_title(workspace_handle=workspace_handle)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _ = manifest_path.write_text(
        render_workspace_manifest_file(
            workspace_handle=workspace_handle,
            workspace_title=workspace_title,
            environment_paths=current_environment_paths,
        ),
        encoding="utf-8",
    )
    return WorkspaceManifestStatus(
        path=manifest_path.as_posix(),
        exists=True,
        created=True,
        write_requested=True,
    )


def ensure_agent_files(
    *,
    repo_root: Path,
    workspace_manifest_relpath: str,
    module_ids: tuple[str, ...],
    environment_file_relpath: str,
    environment_seeded: bool,
    bootstrap_mode: WorkspaceBootstrapMode,
    write_agent_files: bool,
    skill_pack: str,
    skill_export_mode: str,
    export_skill_pack_fn: SkillPackExporterProtocol | None,
) -> AgentFilesStatus:
    agents_path = (repo_root / "AGENTS.md").resolve()
    skills_root = (repo_root / "skills").resolve()
    skills_readme_path = (skills_root / "README.md").resolve()

    created_paths: list[str] = []
    exported_skill_names: tuple[str, ...] = ()
    source_root: str | None = None
    resolved_references: dict[str, dict[str, str]] = {}

    if write_agent_files:
        if export_skill_pack_fn is None:
            raise ValueError(
                "Skill-pack exporter is required when write_agent_files is enabled"
            )
        export_result: SkillPackExportResultProtocol = export_skill_pack_fn(
            destination_root=skills_root,
            pack_name=skill_pack,
            export_mode=skill_export_mode,
        )
        exported_skill_names = tuple(export_result.skill_names)
        source_root = export_result.source_root.as_posix()
        resolved_references = dict(export_result.resolved_references)
        created_paths.extend(path.as_posix() for path in export_result.created_paths)
        if not agents_path.exists():
            agents_path.parent.mkdir(parents=True, exist_ok=True)
            _ = agents_path.write_text(
                render_workspace_agents_md(
                    workspace_manifest_relpath=workspace_manifest_relpath,
                    environment_file_relpath=environment_file_relpath,
                    environment_seeded=environment_seeded,
                    module_ids=module_ids,
                    bootstrap_mode=bootstrap_mode,
                    skill_pack=skill_pack,
                    exported_skill_names=exported_skill_names,
                ),
                encoding="utf-8",
            )
            created_paths.append(agents_path.as_posix())

    primary_skill = (
        f"{exported_skill_names[0]}/SKILL.md" if exported_skill_names else None
    )
    primary_skill_path = (
        (skills_root / primary_skill).resolve() if primary_skill else None
    )
    primary_skill_exists = bool(primary_skill_path and primary_skill_path.exists())

    return AgentFilesStatus(
        write_requested=write_agent_files,
        created_paths=sorted(created_paths),
        agents_md=AgentsMdStatus(
            path=agents_path.as_posix(),
            exists=agents_path.exists(),
            created=agents_path.as_posix() in created_paths,
        ),
        skills=SkillsStatus(
            root_path=skills_root.as_posix(),
            exists=skills_root.exists(),
            pack_name=skill_pack,
            export_mode=skill_export_mode,
            source_root=source_root,
            skill_names=list(exported_skill_names),
            resolved_references=resolved_references,
            readme_path=skills_readme_path.as_posix(),
            readme_exists=skills_readme_path.exists(),
            primary_skill_path=(
                primary_skill_path.as_posix() if primary_skill_path else None
            ),
            primary_skill_exists=primary_skill_exists,
            created=any(
                path.startswith(skills_root.as_posix()) for path in created_paths
            ),
        ),
    )


def ensure_proof_tests(
    *,
    repo_root: Path,
    module_ids: tuple[str, ...],
    write_proof_tests: bool,
) -> ProofTestsStatus:
    entries: list[ProofTestModuleStatus] = []
    created_paths: list[str] = []

    for module_id in module_ids:
        module_snake = module_id.replace("-", "_")
        test_path = (
            repo_root
            / "modules"
            / module_id
            / "runtime"
            / "tests"
            / f"test_{module_snake}_module_proof.py"
        ).resolve()
        created = False
        if write_proof_tests and not test_path.exists():
            test_path.parent.mkdir(parents=True, exist_ok=True)
            _ = test_path.write_text(
                render_module_proof_test_scaffold(
                    module_id=module_id,
                    module_snake=module_snake,
                ),
                encoding="utf-8",
            )
            created = True
            created_paths.append(test_path.as_posix())
        entries.append(
            ProofTestModuleStatus(
                module_id=module_id,
                path=test_path.as_posix(),
                exists=test_path.exists(),
                created=created,
            )
        )

    return ProofTestsStatus(
        write_requested=write_proof_tests,
        created_paths=sorted(created_paths),
        modules=entries,
    )


def ensure_collaboration_scaffold(
    *, repo_root: Path, write_collaboration_scaffold: bool
) -> CollaborationScaffoldStatus:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    date_str = now.date().isoformat()
    docs_root = (repo_root / "docs").resolve()
    issues_protocol_path = (docs_root / "issues" / "PROTOCOL.md").resolve()
    feed_protocol_path = (docs_root / "feed" / "PROTOCOL.md").resolve()
    feed_snapshot_path = (docs_root / "feed" / "FEED.md").resolve()
    daily_log_path = (docs_root / "feed" / f"{date_str}.md").resolve()

    file_specs = (
        (
            "issues_protocol",
            issues_protocol_path,
            render_minimal_issues_protocol(),
        ),
        (
            "feed_protocol",
            feed_protocol_path,
            render_minimal_feed_protocol(),
        ),
        (
            "feed_snapshot",
            feed_snapshot_path,
            render_minimal_feed_snapshot(
                timestamp=now.strftime("%Y-%m-%dT%H:%MZ"),
                today_log_path=f"docs/feed/{date_str}.md",
            ),
        ),
        (
            "daily_log",
            daily_log_path,
            render_minimal_daily_feed_log(date_str=date_str),
        ),
    )

    created_paths: list[str] = []
    files_payload: list[ScaffoldFileStatus] = []
    for key, path, content in file_specs:
        created = False
        if write_collaboration_scaffold and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(content, encoding="utf-8")
            created = True
            created_paths.append(path.as_posix())
        files_payload.append(
            ScaffoldFileStatus(
                key=key,
                path=path.as_posix(),
                exists=path.exists(),
                created=created,
            )
        )

    return CollaborationScaffoldStatus(
        write_requested=write_collaboration_scaffold,
        created_paths=sorted(created_paths),
        files=files_payload,
        today_log_path=daily_log_path.as_posix(),
    )


def ensure_workspace_scaffold(
    *,
    repo_root: Path,
    module_ids: tuple[str, ...],
    environment_file_relpath: str,
    write_workspace_scaffold: bool,
) -> WorkspaceScaffoldStatus:
    pyproject_path = (repo_root / "pyproject.toml").resolve()
    ci_path = (repo_root / ".github" / "workflows" / "ci.yml").resolve()
    modules_readme_path = (repo_root / "modules" / "README.md").resolve()
    apis_readme_path = (repo_root / "apis" / "README.md").resolve()
    services_readme_path = (repo_root / "services" / "README.md").resolve()
    experiences_readme_path = (repo_root / "experiences" / "README.md").resolve()

    file_specs = (
        (
            "root_pyproject",
            pyproject_path,
            render_workspace_pyproject(repo_root=repo_root),
        ),
        (
            "ci_workflow",
            ci_path,
            render_workspace_ci_workflow(
                environment_file_relpath=environment_file_relpath
            ),
        ),
        (
            "modules_root_readme",
            modules_readme_path,
            render_workspace_root_placeholder_readme(root_name="modules"),
        ),
        (
            "apis_root_readme",
            apis_readme_path,
            render_workspace_root_placeholder_readme(root_name="apis"),
        ),
        (
            "services_root_readme",
            services_readme_path,
            render_workspace_root_placeholder_readme(root_name="services"),
        ),
        (
            "experiences_root_readme",
            experiences_readme_path,
            render_workspace_root_placeholder_readme(root_name="experiences"),
        ),
    )

    created_paths: list[str] = []
    files_payload: list[ScaffoldFileStatus] = []
    for key, path, content in file_specs:
        created = False
        if write_workspace_scaffold and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(content, encoding="utf-8")
            created = True
            created_paths.append(path.as_posix())
        files_payload.append(
            ScaffoldFileStatus(
                key=key,
                path=path.as_posix(),
                exists=path.exists(),
                created=created,
            )
        )

    return WorkspaceScaffoldStatus(
        write_requested=write_workspace_scaffold,
        created_paths=sorted(created_paths),
        files=files_payload,
    )


def ensure_delivery_contracts(
    *,
    repo_root: Path,
    write_delivery_contracts: bool,
) -> DeliveryContractsStatus:
    contracts_root = (repo_root / "configs" / "contracts").resolve()
    env_contract_path = (contracts_root / "environment_experience.toml").resolve()
    delivery_contract_path = (contracts_root / "agent_delivery.toml").resolve()
    evidence_policy_path = (contracts_root / "evidence_policy.toml").resolve()
    quality_gates_path = (contracts_root / "quality_gates.toml").resolve()

    file_specs = (
        (
            "environment_experience",
            env_contract_path,
            render_environment_experience_contract(),
        ),
        (
            "agent_delivery",
            delivery_contract_path,
            render_agent_delivery_contract(),
        ),
        (
            "evidence_policy",
            evidence_policy_path,
            render_evidence_policy_contract(),
        ),
        (
            "quality_gates",
            quality_gates_path,
            render_quality_gates_contract(),
        ),
    )

    created_paths: list[str] = []
    files_payload: list[ScaffoldFileStatus] = []
    for key, path, content in file_specs:
        created = False
        if write_delivery_contracts and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            _ = path.write_text(content, encoding="utf-8")
            created = True
            created_paths.append(path.as_posix())
        files_payload.append(
            ScaffoldFileStatus(
                key=key,
                path=path.as_posix(),
                exists=path.exists(),
                created=created,
            )
        )

    return DeliveryContractsStatus(
        write_requested=write_delivery_contracts,
        created_paths=sorted(created_paths),
        files=files_payload,
        contracts_root=contracts_root.as_posix(),
    )


def _default_workspace_handle(*, repo_root: Path) -> str:
    raw_name = repo_root.name.strip().lower().replace(" ", "_")
    normalized_chars = [
        char if (char.isalnum() or char in {"_", "-"}) else "_" for char in raw_name
    ]
    normalized = "".join(normalized_chars).strip("_-")
    return normalized or "workspace"


def _default_workspace_title(*, workspace_handle: str) -> str:
    normalized = workspace_handle.replace("-", " ").replace("_", " ").strip()
    if not normalized:
        return "Aware Workspace"
    return " ".join(part.capitalize() for part in normalized.split())


def _normalize_repo_relative_path(*, repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _merge_unique_paths(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in (*existing, *additions):
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return tuple(ordered)


def _load_workspace_manifest_snapshot(*, toml_path: Path) -> _WorkspaceManifestSnapshot:
    payload = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Workspace manifest is not a TOML table: {toml_path}")
    workspace = payload.get("workspace")
    if not isinstance(workspace, dict):
        raise ValueError(f"Workspace manifest lacks [workspace]: {toml_path}")
    handle = _string_value(workspace.get("handle")) or "workspace"
    title = _string_value(workspace.get("title")) or handle.replace("_", " ").title()
    return _WorkspaceManifestSnapshot(
        handle=handle,
        title=title,
        environments=_string_tuple(payload.get("environments")),
        apis=_string_tuple(payload.get("apis")),
        economies=_string_tuple(payload.get("economies")),
        services=_string_tuple(payload.get("services")),
        experiences=_string_tuple(payload.get("experiences")),
        attentions=_string_tuple(payload.get("attentions")),
        panes=_string_tuple(payload.get("panes")),
        interfaces=_string_tuple(payload.get("interfaces")),
        nodes=_string_tuple(payload.get("nodes")),
        inferences=_string_tuple(payload.get("inferences")),
    )


def _string_value(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip() for item in value if isinstance(item, str) and item.strip()
    )


def ensure_grammar_docs_bundle(
    *,
    repo_root: Path,
    write_grammar_docs_bundle: bool,
) -> GrammarDocsBundleStatus:
    source_root = _resolve_grammar_docs_source_root(required=write_grammar_docs_bundle)
    docs_root = (repo_root / _GRAMMAR_DOCS_TARGET_DIR).resolve()

    source_files = sorted(source_root.glob("*.md")) if source_root else []
    if write_grammar_docs_bundle and not source_files:
        raise FileNotFoundError(
            f"No grammar docs found in source bundle: {source_root}"
        )

    created_paths: list[str] = []
    files_payload: list[ScaffoldFileStatus] = []
    for source_path in source_files:
        target_path = (docs_root / source_path.name).resolve()
        created = False
        if write_grammar_docs_bundle and not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            _ = target_path.write_text(
                source_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            created = True
            created_paths.append(target_path.as_posix())
        files_payload.append(
            ScaffoldFileStatus(
                key=source_path.name.replace(".", "_").lower(),
                path=target_path.as_posix(),
                exists=target_path.exists(),
                created=created,
            )
        )

    return GrammarDocsBundleStatus(
        write_requested=write_grammar_docs_bundle,
        created_paths=sorted(created_paths),
        files=files_payload,
        docs_root=docs_root.as_posix(),
        source_root=source_root.as_posix() if source_root else "",
    )


def ensure_software_rules_bundle(
    *,
    repo_root: Path,
    write_software_rules_bundle: bool,
    template_id: str,
    profile_id: str,
) -> SoftwareRulesBundleStatus:
    source_root = _resolve_software_configs_source_root(
        required=write_software_rules_bundle,
    )
    docs_root = (repo_root / _SOFTWARE_RULES_TARGET_DIR).resolve()
    normalized_template_id = str(template_id).strip() or "mental-model-v1"
    normalized_profile_id = str(profile_id).strip() or "external-default-v1"

    if source_root is None:
        return SoftwareRulesBundleStatus(
            write_requested=write_software_rules_bundle,
            created_paths=[],
            files=[],
            docs_root=docs_root.as_posix(),
            source_root="",
            template_id=normalized_template_id,
            profile_id=normalized_profile_id,
            strict_unresolved=False,
            unresolved_tokens=[],
            unresolved_by_file={},
        )

    template_root = (source_root / "templates" / normalized_template_id).resolve()
    profile_path = (
        source_root / "profiles" / f"{normalized_profile_id}.toml"
    ).resolve()
    template_files = load_software_template_files(template_root=template_root)
    profile = load_software_prompt_profile(
        profile_path=profile_path,
        profile_id=normalized_profile_id,
        assets_root=(source_root / "assets").resolve(),
    )
    composed = compose_software_templates(
        template_id=normalized_template_id,
        profile=profile,
        template_files=template_files,
    )

    created_paths: list[str] = []
    files_payload: list[ScaffoldFileStatus] = []
    for item in composed.files:
        target_path = (docs_root / item.name).resolve()
        created = False
        if write_software_rules_bundle and not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            _ = target_path.write_text(item.rendered_text, encoding="utf-8")
            created = True
            created_paths.append(target_path.as_posix())
        files_payload.append(
            ScaffoldFileStatus(
                key=item.name.replace(".md", "").lower(),
                path=target_path.as_posix(),
                exists=target_path.exists(),
                created=created,
            )
        )

    source_assets_root = (source_root / "assets").resolve()
    if source_assets_root.exists() and source_assets_root.is_dir():
        for source_asset in sorted(
            path for path in source_assets_root.rglob("*") if path.is_file()
        ):
            relative_path = source_asset.relative_to(source_assets_root)
            target_path = (docs_root / "assets" / relative_path).resolve()
            created = False
            if write_software_rules_bundle and not target_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                _ = target_path.write_bytes(source_asset.read_bytes())
                created = True
                created_paths.append(target_path.as_posix())
            files_payload.append(
                ScaffoldFileStatus(
                    key=f"asset_{str(relative_path).replace('/', '_').replace('.', '_').lower()}",
                    path=target_path.as_posix(),
                    exists=target_path.exists(),
                    created=created,
                )
            )

    return SoftwareRulesBundleStatus(
        write_requested=write_software_rules_bundle,
        created_paths=sorted(created_paths),
        files=files_payload,
        docs_root=docs_root.as_posix(),
        source_root=source_root.as_posix(),
        template_id=composed.template_id,
        profile_id=composed.profile_id,
        strict_unresolved=composed.strict_unresolved,
        unresolved_tokens=composed.unresolved_tokens,
        unresolved_by_file=composed.unresolved_by_file,
    )


def ensure_seed_bundle(
    *,
    repo_root: Path,
    write_seed_bundle: bool,
) -> SeedBundleStatus:
    source_root = _resolve_seed_bundle_source_root(required=write_seed_bundle)
    seeds_root = (repo_root / _SEEDS_TARGET_DIR).resolve()
    source_files = sorted(source_root.glob("*")) if source_root else []
    source_files = [path for path in source_files if path.is_file()]
    if write_seed_bundle and not source_files:
        raise FileNotFoundError(f"No seed bundle files found in source: {source_root}")

    created_paths: list[str] = []
    files_payload: list[ScaffoldFileStatus] = []
    for source_path in source_files:
        target_path = (seeds_root / source_path.name).resolve()
        created = False
        if write_seed_bundle and not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            _ = target_path.write_text(
                source_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            created = True
            created_paths.append(target_path.as_posix())
        files_payload.append(
            ScaffoldFileStatus(
                key=source_path.name.replace(".", "_").lower(),
                path=target_path.as_posix(),
                exists=target_path.exists(),
                created=created,
            )
        )

    return SeedBundleStatus(
        write_requested=write_seed_bundle,
        created_paths=sorted(created_paths),
        files=files_payload,
        seeds_root=seeds_root.as_posix(),
        source_root=source_root.as_posix() if source_root else "",
    )


def _resolve_grammar_docs_source_root(*, required: bool) -> Path | None:
    package_assets = (
        Path(__file__).resolve().parents[2] / "assets" / "aware_grammar_docs"
    ).resolve()
    if package_assets.exists() and package_assets.is_dir():
        return package_assets

    source_tree_docs = (
        Path(__file__).resolve().parents[5] / "languages" / "aware" / "grammar" / "docs"
    ).resolve()
    if source_tree_docs.exists() and source_tree_docs.is_dir():
        return source_tree_docs

    if not required:
        return None

    raise FileNotFoundError(
        "Aware grammar docs bundle not found in package assets or source tree."
    )


def _resolve_software_configs_source_root(*, required: bool) -> Path | None:
    package_assets = (
        Path(__file__).resolve().parents[2] / "assets" / "software"
    ).resolve()
    if package_assets.exists() and package_assets.is_dir():
        return package_assets

    if not required:
        return None

    raise FileNotFoundError(
        "Software prompt-composition bundle not found in Workspace operator package assets."
    )


def _resolve_seed_bundle_source_root(*, required: bool) -> Path | None:
    package_assets = (
        Path(__file__).resolve().parents[2] / "assets" / "seeds"
    ).resolve()
    if package_assets.exists() and package_assets.is_dir():
        return package_assets

    if not required:
        return None

    raise FileNotFoundError(
        "Seed bundle source not found in Workspace operator package assets."
    )


__all__ = [
    "run_scaffold_stage",
    "ensure_agent_files",
    "ensure_collaboration_scaffold",
    "ensure_delivery_contracts",
    "ensure_environment_file",
    "ensure_grammar_docs_bundle",
    "ensure_proof_tests",
    "ensure_seed_bundle",
    "ensure_software_rules_bundle",
    "ensure_workspace_scaffold",
]
