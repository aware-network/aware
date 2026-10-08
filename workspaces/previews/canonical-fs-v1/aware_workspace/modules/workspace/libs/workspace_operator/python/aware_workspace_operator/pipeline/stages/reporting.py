"""Report assembly and CLI-print formatting stage."""

from __future__ import annotations

from aware_workspace_operator.models import (
    NextRequiredAction,
    WorkspaceBootstrapOptions,
    WorkspaceAutomationPhase,
    WorkspaceBootstrapMode,
    WorkspaceBootstrapReport,
    WorkspacePreflightState,
    WorkspaceScaffoldState,
)


def build_report(
    *,
    request: WorkspaceBootstrapOptions,
    preflight: WorkspacePreflightState,
    scaffold: WorkspaceScaffoldState,
    repo_root: str,
) -> WorkspaceBootstrapReport:
    """Build final typed report from stage outputs."""

    missing_blocking = bool(preflight.missing_dependencies) and not bool(
        request.allow_missing_dependencies
    )
    failed = bool(preflight.has_errors) or missing_blocking

    return WorkspaceBootstrapReport(
        repo_root=repo_root,
        bootstrap_mode=request.bootstrap_mode,
        module_ids=list(preflight.module_ids),
        modules=list(preflight.modules),
        missing_dependencies=list(preflight.missing_dependencies),
        discovered_packages=list(preflight.discovered_packages),
        duplicate_packages=list(preflight.duplicate_packages),
        workspace_manifest=scaffold.workspace_manifest,
        environment_file=scaffold.environment_file,
        agent_files=scaffold.agent_files,
        collaboration_scaffold=scaffold.collaboration_scaffold,
        proof_tests=scaffold.proof_tests,
        workspace_scaffold=scaffold.workspace_scaffold,
        delivery_contracts=scaffold.delivery_contracts,
        grammar_docs_bundle=scaffold.grammar_docs_bundle,
        software_rules_bundle=scaffold.software_rules_bundle,
        seed_bundle=scaffold.seed_bundle,
        next_required_actions=_build_next_required_actions(
            bootstrap_mode=request.bootstrap_mode,
            automation_phase=request.automation_phase,
            module_ids=tuple(preflight.module_ids),
            failed=failed,
        ),
        status="failed" if failed else "ok",
    )


def _build_next_required_actions(
    *,
    bootstrap_mode: WorkspaceBootstrapMode,
    automation_phase: WorkspaceAutomationPhase,
    module_ids: tuple[str, ...],
    failed: bool,
) -> list[NextRequiredAction]:
    actions: list[NextRequiredAction] = []
    if failed:
        actions.append(
            NextRequiredAction(
                code="fix_bootstrap_errors",
                track="bootstrap",
                description=(
                    "Resolve bootstrap failures first "
                    "(missing dependencies, module manifest errors, or workflow preflight errors)."
                ),
            )
        )

    actions.append(
        NextRequiredAction(
            code="capture_intent_agreement",
            track="config",
            description="Capture human-agent intent/agreement before implementation.",
        )
    )
    actions.append(
        NextRequiredAction(
            code="review_aware_grammar_docs",
            track="config",
            description="Review bundled Aware grammar docs (`docs/aware/grammar/README.md`) before authoring `.aware`.",
        )
    )
    actions.append(
        NextRequiredAction(
            code="review_software_rules_bundle",
            track="config",
            description=(
                "Review software mental-model rules (`docs/rules/SOFTWARE/index.md`) "
                "and confirm template/profile alignment before implementation."
            ),
        )
    )

    if not module_ids:
        actions.append(
            NextRequiredAction(
                code="module_create_explicit",
                track="config",
                description=(
                    "Start the Workspace Config Loop by creating a module explicitly "
                    "with `aware-cli module create <module_id> --repo-root <repo_root>`."
                ),
            )
        )
    else:
        actions.extend(
            [
                NextRequiredAction(
                    code="experience_to_ontology_to_projection",
                    track="config",
                    description=(
                        "Implement module rails in canonical order: "
                        "config -> runtime -> representation."
                    ),
                ),
                NextRequiredAction(
                    code="programs_profile_contract",
                    track="config",
                    description=(
                        "Define deterministic program rails and profile symbol contract "
                        "(programs -> policy -> reactivity)."
                    ),
                ),
                NextRequiredAction(
                    code="compile_pass",
                    track="config",
                    description=(
                        "Continue the Workspace Config Loop by compiling module(s) "
                        "with `aware-cli compile --update-lock --materialization-mode runtime module <module_id>`."
                    ),
                ),
                NextRequiredAction(
                    code="quality_gates_pass",
                    track="config",
                    description=(
                        "Run opinionated lint/type gates before module proofs "
                        "with `aware-cli workspace quality-gates --path <target>` "
                        "(Python defaults: flake8 + mypy + basedpyright; Dart: dart analyze)."
                    ),
                ),
                NextRequiredAction(
                    code="module_proof_pass",
                    track="config",
                    description=(
                        "Pass module proof tests for the Workspace Config Loop "
                        "(replace scaffold TODOs with concrete assertions)."
                    ),
                ),
                NextRequiredAction(
                    code="pane_registrar_pass",
                    track="config",
                    description="Pass pane registrar alignment with declared projection views.",
                ),
                NextRequiredAction(
                    code="ipc_e2e_pass",
                    track="config",
                    description=(
                        "Pass IPC end-to-end validation for the Workspace Config Loop "
                        "(function call -> commit -> materialization -> python/dart verification)."
                    ),
                ),
            ]
        )

    if automation_phase == "day-1":
        actions.append(
            NextRequiredAction(
                code="phase_2_deferred",
                track="instantiation",
                description=(
                    "Workspace Instantiation Loop is intentionally deferred in day-1. "
                    "Use `--automation-phase phase-2` to include compiler authority "
                    "+ environment/seed application steps."
                ),
            )
        )
    else:
        if bootstrap_mode == "remote-managed":
            actions.append(
                NextRequiredAction(
                    code="connect_compiler_authority",
                    track="instantiation",
                    description=(
                        "Start the Workspace Instantiation Loop by configuring remote compiler/upgrade authority "
                        "(managed service ownership of compile/governance rails; remote-managed mode)."
                    ),
                )
            )
        else:
            actions.append(
                NextRequiredAction(
                    code="connect_compiler_authority",
                    track="instantiation",
                    description=(
                        "Start the Workspace Instantiation Loop by validating full-local compiler stack availability "
                        "(Workspace materialize, aware-meta, local preflight; full-local mode)."
                    ),
                )
            )

        actions.append(
            NextRequiredAction(
                code="apply_environment_experience",
                track="instantiation",
                description=(
                    "Apply environment-level experience (process/thread/projection topology) "
                    "after Workspace Config Loop proof gates are green."
                ),
            )
        )
        actions.append(
            NextRequiredAction(
                code="apply_seed_experience",
                track="instantiation",
                description=(
                    "Apply seed experience using `configs/seeds/aware_kernel.seed.aware` "
                    "with `configs/seeds/aware_kernel.seed.profile.toml`."
                ),
            )
        )

        actions.append(
            NextRequiredAction(
                code="validate_instantiation_contract",
                track="instantiation",
                description=(
                    "Validate instantiation outcomes (environment + seed apply) and confirm gates are green."
                ),
            )
        )
    actions.append(
        NextRequiredAction(
            code="evidence_logged",
            track="evidence",
            description="Append issue/feed updates with exact commands, outputs, and validation evidence.",
        )
    )
    return actions


def print_workspace_bootstrap_report(*, report: WorkspaceBootstrapReport) -> None:
    """Render human-readable bootstrap summary for CLI mode."""

    status = str(report.status).upper()
    print(f"Workspace bootstrap: {status}")
    print(f"Repo root: {report.repo_root}")
    print(f"Mode: {report.bootstrap_mode}")
    print("Modules:")
    for module in report.modules:
        marker = "ok"
        if module.errors:
            marker = "error"
        elif module.missing_dependencies:
            marker = "missing-deps"
        package_text = (
            ", ".join(module.package_names) if module.package_names else "(none)"
        )
        print(f"- [{marker}] {module.module_id} packages={package_text}")
        for item in module.errors:
            print(f"    error: {item}")
        for dep in module.missing_dependencies:
            print(
                "    missing dependency: "
                f"{dep.dependency_package_name} "
                f"(package={dep.package_name} source={dep.dependency_aware_toml_path})"
            )

    if report.missing_dependencies:
        print("Missing dependencies summary:")
        for dep in report.missing_dependencies:
            print(
                "- "
                f"module={dep.module_id} "
                f"package={dep.package_name} "
                f"missing={dep.dependency_package_name}"
            )

    if report.duplicate_packages:
        print("Duplicate package names discovered:")
        for item in report.duplicate_packages:
            print(
                f"- {item.package_name} kept={item.kept_aware_toml_path} "
                f"ignored={item.ignored_aware_toml_paths}"
            )

    env_file = report.environment_file
    marker = "created" if env_file.created else "existing"
    if not env_file.exists:
        marker = "missing"
    print(
        "Environment file: "
        f"{env_file.path} [{marker}] "
        f"write_requested={env_file.write_requested}"
    )

    print(
        "Agent files: "
        f"write_requested={report.agent_files.write_requested} "
        f"agents_md={report.agent_files.agents_md.path} "
        f"skills_pack={report.agent_files.skills.pack_name}"
    )
    print(
        "Collaboration scaffold: "
        f"write_requested={report.collaboration_scaffold.write_requested} "
        f"created={len(report.collaboration_scaffold.created_paths)}"
    )
    print(
        "Proof tests: "
        f"write_requested={report.proof_tests.write_requested} "
        f"created={len(report.proof_tests.created_paths)}"
    )
    print(
        "Workspace scaffold: "
        f"write_requested={report.workspace_scaffold.write_requested} "
        f"created={len(report.workspace_scaffold.created_paths)}"
    )
    print(
        "Delivery contracts: "
        f"write_requested={report.delivery_contracts.write_requested} "
        f"created={len(report.delivery_contracts.created_paths)}"
    )
    print(
        "Grammar docs bundle: "
        f"write_requested={report.grammar_docs_bundle.write_requested} "
        f"created={len(report.grammar_docs_bundle.created_paths)}"
    )
    print(
        "Software rules bundle: "
        f"write_requested={report.software_rules_bundle.write_requested} "
        f"template={report.software_rules_bundle.template_id} "
        f"profile={report.software_rules_bundle.profile_id} "
        f"created={len(report.software_rules_bundle.created_paths)} "
        f"unresolved_tokens={len(report.software_rules_bundle.unresolved_tokens)}"
    )
    print(
        "Seed bundle: "
        f"write_requested={report.seed_bundle.write_requested} "
        f"created={len(report.seed_bundle.created_paths)}"
    )

    if report.next_required_actions:
        print("Next required actions:")
        for item in report.next_required_actions:
            print(f"- [{item.track}] {item.code}: {item.description}")


__all__ = ["build_report", "print_workspace_bootstrap_report"]
