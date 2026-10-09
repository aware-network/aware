"""Renderable text templates for workspace bootstrap assets."""

from __future__ import annotations

import json
from pathlib import Path

_WORKSPACE_AWARE_CLI_MIN_VERSION = "0.9.2"
_WORKSPACE_META_MIN_VERSION = "0.1.0"
_WORKSPACE_FLAKE8_MIN_VERSION = "7.1.0"
_WORKSPACE_MYPY_MIN_VERSION = "1.11.0"
_WORKSPACE_BASEDPYRIGHT_MIN_VERSION = "1.23.0"


def render_workspace_pyproject(
    *,
    repo_root: Path,
    workspace_members: tuple[str, ...] = (),
    workspace_sources: tuple[str, ...] = (),
) -> str:
    raw_name = repo_root.name.strip().lower().replace("_", "-")
    chars = [ch if (ch.isalnum() or ch == "-") else "-" for ch in raw_name]
    project_name = "".join(chars).strip("-")
    while "--" in project_name:
        project_name = project_name.replace("--", "-")
    if not project_name:
        project_name = "aware-workspace"
    if not project_name[0].isalpha():
        project_name = f"aware-{project_name}"

    lines = [
        "[project]",
        f'name = "{project_name}"',
        'version = "0.1.0"',
        'description = "Aware external workspace scaffold."',
        'requires-python = ">=3.12"',
        "dependencies = [",
        f'  "aware-cli>={_WORKSPACE_AWARE_CLI_MIN_VERSION}",',
        f'  "aware-meta>={_WORKSPACE_META_MIN_VERSION}",',
        f'  "flake8>={_WORKSPACE_FLAKE8_MIN_VERSION}",',
        f'  "mypy>={_WORKSPACE_MYPY_MIN_VERSION}",',
        f'  "basedpyright>={_WORKSPACE_BASEDPYRIGHT_MIN_VERSION}",',
        '  "pytest>=8.2",',
        "]",
        "",
        "[tool.uv]",
        "package = false",
        "",
    ]
    if workspace_members:
        lines.extend(
            [
                "[tool.uv.workspace]",
                "members = [",
            ]
        )
        for member in workspace_members:
            lines.append(f'  "{member}",')
        lines.extend(
            [
                "]",
                "",
            ]
        )
    if workspace_sources:
        lines.append("[tool.uv.sources]")
        for source in workspace_sources:
            lines.append(f"{source} = {{ workspace = true }}")
        lines.append("")

    lines.extend(
        [
            "[tool.flake8]",
            "max-line-length = 120",
            'extend-ignore = "E266"',
            "",
            "[tool.mypy]",
            'python_version = "3.12"',
            'disable_error_code = ["import-untyped"]',
            "",
            "[tool.basedpyright]",
            'pythonVersion = "3.12"',
            'typeCheckingMode = "standard"',
            "",
            "[tool.pytest.ini_options]",
            "markers = [",
            '  "db: database-backed tests requiring AWARE_DB_TEST_ADMIN_URL",',
            '  "meta_contract: bodyless Meta index, fragment, and semantic contract proofs",',
            '  "meta_runtime: committed Meta runtime proofs using strict demand-executable authority",',
            '  "meta_materialization: explicitly leased Meta source/full-graph materialization proofs",',
            "]",
        ]
    )
    return "\n".join(lines) + "\n"


def render_workspace_ci_workflow(*, environment_file_relpath: str) -> str:
    _ = environment_file_relpath
    return (
        "name: CI\n\n"
        "on:\n"
        "  push:\n"
        "    branches: [ main ]\n"
        "  pull_request:\n"
        "    branches: [ main ]\n\n"
        "jobs:\n"
        "  aware-workspace:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - name: Checkout\n"
        "        uses: actions/checkout@v4\n\n"
        "      - name: Set up Python 3.12\n"
        "        uses: actions/setup-python@v5\n"
        "        with:\n"
        '          python-version: "3.12"\n\n'
        "      - name: Install uv\n"
        "        uses: astral-sh/setup-uv@v6\n\n"
        "      - name: Sync dependencies\n"
        "        run: uv sync\n\n"
        "      - name: Bootstrap workspace\n"
        "        run: |\n"
        "          uv run aware-cli workspace bootstrap --json\n\n"
        "      - name: Compile modules\n"
        "        shell: bash\n"
        "        run: |\n"
        "          set -euo pipefail\n"
        "          shopt -s nullglob\n"
        "          module_tomls=(modules/*/aware.module.toml)\n"
        '          if [ "${#module_tomls[@]}" -eq 0 ]; then\n'
        '            echo "No modules found yet; skipping compile step"\n'
        "            exit 0\n"
        "          fi\n"
        '          for module_toml in "${module_tomls[@]}"; do\n'
        '            module_id="$(basename "$(dirname "${module_toml}")")"\n'
        '            uv run aware-cli compile --update-lock --materialization-mode runtime module "${module_id}"\n'
        "          done\n\n"
        "      - name: Run stable module proofs\n"
        "        run: uv run aware-cli workspace test --workspace-toml aware.workspace.toml --no-commit --json\n"
    )


def render_workspace_root_placeholder_readme(*, root_name: str) -> str:
    if root_name == "modules":
        return (
            "# Modules\n\n"
            "This root holds canonical Aware modules.\n\n"
            "- Modules are semantic bundles over package-owned code truth.\n"
            "- Create modules through `aware-cli module create --repo-root <workspace> <module_id>`.\n"
            "- Do not invent placeholder module contents manually; use explicit module-create flows.\n"
        )
    if root_name == "apis":
        return (
            "# APIs\n\n"
            "This root is reserved for canonical workspace API surfaces.\n\n"
            "- API roots are explicit workspace structure, not optional ad-hoc folders.\n"
            "- Populate this root only through explicit follow-on workspace/API rails.\n"
        )
    if root_name == "services":
        return (
            "# Services\n\n"
            "This root is reserved for canonical workspace service surfaces.\n\n"
            "- Service roots are explicit workspace structure, not optional ad-hoc folders.\n"
            "- Populate this root only through explicit follow-on workspace/service rails.\n"
        )
    if root_name == "experiences":
        return (
            "# Experiences\n\n"
            "This root is reserved for canonical workspace operator surfaces.\n\n"
            "- FS-first placeholder roots come first; canonical `.aware` workspace operators are later work.\n"
            "- Populate this root only through explicit follow-on experience rails.\n"
        )
    raise ValueError(f"Unsupported workspace root placeholder: {root_name}")


def render_environment_file(
    *,
    environment_handle: str,
    environment_title: str,
    module_ids: tuple[str, ...],
) -> str:
    lines = [
        "aware = 1",
        "",
        "[environment]",
        f'handle = "{environment_handle.strip() or "external"}"',
        f'title = "{environment_title.strip() or "Aware External Workspace"}"',
        'canonical_language = "aware"',
        "",
        "modules = [",
    ]
    for module_id in module_ids:
        lines.append(f'    "{module_id}",')
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def render_workspace_manifest_file(
    *,
    workspace_handle: str,
    workspace_title: str | None,
    environment_paths: tuple[str, ...] = (),
    api_paths: tuple[str, ...] = (),
    economy_paths: tuple[str, ...] = (),
    service_paths: tuple[str, ...] = (),
    experience_paths: tuple[str, ...] = (),
    attention_paths: tuple[str, ...] = (),
    pane_paths: tuple[str, ...] = (),
    interface_paths: tuple[str, ...] = (),
    node_paths: tuple[str, ...] = (),
    inference_paths: tuple[str, ...] = (),
) -> str:
    def _render_list(name: str, values: tuple[str, ...]) -> str:
        if not values:
            return f"{name} = []"
        rendered = ", ".join(f'"{value}"' for value in values)
        return f"{name} = [{rendered}]"

    lines = [
        "aware = 1",
        "",
        "[workspace]",
        f'handle = "{workspace_handle.strip() or "workspace"}"',
    ]
    normalized_title = (workspace_title or "").strip()
    if normalized_title:
        lines.append(f'title = "{normalized_title}"')
    lines.extend(
        [
            _render_list("environments", environment_paths),
            _render_list("apis", api_paths),
            _render_list("economies", economy_paths),
            _render_list("services", service_paths),
            _render_list("experiences", experience_paths),
            _render_list("attentions", attention_paths),
            _render_list("panes", pane_paths),
            _render_list("interfaces", interface_paths),
            _render_list("nodes", node_paths),
            _render_list("inferences", inference_paths),
            "",
        ]
    )
    return "\n".join(lines)


def render_minimal_issues_protocol() -> str:
    return (
        "# Issues Protocol\n\n"
        "Use issue files as SSOT for task state.\n\n"
        "## Required Fields\n\n"
        "- `Owner`\n"
        "- `Status`\n"
        "- `Updates` (append-only)\n\n"
        "## Rules\n\n"
        "- Claim issue ownership before implementation.\n"
        "- Keep updates append-only with dated bullets.\n"
        "- One active owner per issue.\n"
    )


def render_minimal_feed_protocol() -> str:
    return (
        "# Feed Protocol\n\n"
        "Feed is a shared coordination snapshot. Issue files remain SSOT.\n\n"
        "## Required Files\n\n"
        "- `docs/feed/FEED.md` (snapshot)\n"
        "- `docs/feed/YYYY-MM-DD.md` (append-only daily log)\n\n"
        "## Rules\n\n"
        "- Keep pulse logs append-only.\n"
        "- Use stable owner/recorder ids.\n"
        "- Record evidence references for each update.\n"
    )


def render_minimal_feed_snapshot(*, timestamp: str, today_log_path: str) -> str:
    return (
        "# Agent Feed — Live coordination snapshot\n\n"
        "Issue files in `docs/issues/**` remain SSOT for issue state.\n"
        "This feed is the shared coordination rail for agents.\n\n"
        f"- Last updated: {timestamp}\n"
        "- Protocol: `docs/feed/PROTOCOL.md`\n"
        f"- Today log: `{today_log_path}`\n\n"
        "## Shipping now (P0 / In Progress)\n\n"
        "- _none yet_\n\n"
        "## Needs owner now (P0 / Open)\n\n"
        "- _none yet_\n\n"
        "## Recently closed (today)\n\n"
        "- _none yet_\n\n"
        "## Alignment checks\n\n"
        "- _pending first pulse_\n\n"
        "## Pulse log (append-only)\n\n"
        "- _initialized by workspace bootstrap_\n"
    )


def render_minimal_daily_feed_log(*, date_str: str) -> str:
    return f"# Agent Feed Log — {date_str}\n\n- _initialized by workspace bootstrap_\n"


def render_workspace_agents_md(
    *,
    workspace_manifest_relpath: str,
    environment_file_relpath: str,
    environment_seeded: bool,
    module_ids: tuple[str, ...],
    bootstrap_mode: str,
    skill_pack: str,
    exported_skill_names: tuple[str, ...],
) -> str:
    AWARE_CODE_PACK_NAME = "aware-code"
    AWARE_COLLAB_PACK_NAME = "aware-collaboration"

    module_lines = "\n".join(f"- `{module_id}`" for module_id in module_ids)
    if not module_lines:
        module_lines = "- _none discovered yet_"
    env_path = environment_file_relpath.strip() or "aware.environment.toml"
    workspace_manifest_path = (
        workspace_manifest_relpath.strip() or "aware.workspace.toml"
    )
    starter_skill_relpath = (
        f"skills/{exported_skill_names[0]}/SKILL.md"
        if exported_skill_names
        else "skills/README.md"
    )
    pack_note = ""
    if skill_pack == AWARE_COLLAB_PACK_NAME:
        pack_note = (
            "- This workspace is collaboration-first. For coding/manual rails, "
            "export `aware-code` or `aware-core`.\n"
        )
    elif skill_pack == AWARE_CODE_PACK_NAME:
        pack_note = (
            "- This workspace is code-first. For issue/feed/pulse rails, "
            "export `aware-collaboration` or `aware-core`.\n"
        )
    if bootstrap_mode == "remote-managed":
        mode_note = (
            "- Bootstrap mode: `remote-managed` (default).\n"
            "- Compile/upgrade governance is expected to be managed by remote services.\n"
            "- Local workspace bootstraps authoring/contracts/evidence rails first.\n"
        )
    else:
        mode_note = (
            "- Bootstrap mode: `full-local`.\n"
            "- Local compiler preflight is enabled and local compiler dependencies are required.\n"
            "- Use this mode when running a fully local/internal Aware stack.\n"
        )
    environment_note = (
        f"- Root environment manifest: `{env_path}`\n"
        if environment_seeded
        else "- Root environment seed: not created by default; use `--write-environment-file` when needed.\n"
    )
    return (
        "# Aware Workspace Contract\n\n"
        "This workspace is prepared for production-grade Aware development.\n"
        "Goal: maximum clarity, minimum hidden decisions, deterministic delivery.\n"
        "Bootstrap is opinionated by default: canonical workspace manifest + contracts + collaboration + CI rails "
        "are generated up front. Root environment seeding is explicit.\n\n"
        "## 0) Non-negotiable Operating Rules\n\n"
        "### A) Identity First\n\n"
        "- At the start of each new thread, publish your stable agent/session id.\n"
        "- Use the same id in issue updates and feed pulse entries.\n"
        "- If stable identity is missing, stop implementation until remapped.\n\n"
        "### B) Issue First (before coding)\n\n"
        "- Every task maps to one issue file under `docs/issues/`.\n"
        "- Claim ownership before code changes: set owner/status and append dated update.\n"
        "- Keep updates append-only.\n\n"
        "### C) Feed is the live snapshot\n\n"
        "- Keep `docs/feed/FEED.md` as point-in-time coordination snapshot.\n"
        "- Keep `docs/feed/YYYY-MM-DD.md` append-only.\n"
        "- Per-issue files remain SSOT.\n\n"
        "### D) Git Governance (External default)\n\n"
        "- Git is agent-operated by default; human should not need to perform git steps.\n"
        "- Agents may run normal mutation commands (`add`/`commit`/`branch`/`merge`) as part of automated delivery.\n"
        "- History rewrite/destructive cleanup is disallowed unless repository policy explicitly enables it.\n"
        "- If repository policy blocks mutation, switch to patch/evidence mode and log blocker in issue/feed.\n\n"
        "### E) Parallel Safety\n\n"
        "- One active owner per issue.\n"
        "- If overlap/conflict is detected, log in issue + feed alignment checks before continuing.\n"
        "- Do not rewrite prior update bullets.\n\n"
        "## 1) Read Once (SSOT map)\n\n"
        f"{mode_note}"
        f"- Workspace manifest: `{workspace_manifest_path}`\n"
        f"{environment_note}"
        "- Environment-level experience contract: `configs/contracts/environment_experience.toml`\n"
        "- Agent delivery contract: `configs/contracts/agent_delivery.toml`\n"
        "- Evidence policy: `configs/contracts/evidence_policy.toml`\n"
        "- Issues protocol: `docs/issues/PROTOCOL.md`\n"
        "- Feed protocol: `docs/feed/PROTOCOL.md`\n"
        "- Live feed snapshot: `docs/feed/FEED.md`\n"
        "- Aware grammar bundle: `docs/aware/grammar/README.md`\n"
        "- Software rules bundle: `docs/rules/SOFTWARE/index.md`\n"
        "- Seed bundle: `configs/seeds/README.md`\n"
        "- Skills index: `skills/README.md`\n"
        f"- Starter skill: `{starter_skill_relpath}`\n\n"
        "## 2) Canonical Sources\n\n"
        "- Module manifests: `modules/**/aware.module.toml`\n"
        "- Workflows: `modules/**/structure/aware.workflows.toml`\n"
        "- Ontology SSOT: `modules/**/structure/ontology/aware/**/*.aware`\n"
        "- Program assets: `modules/**/programs/**/*.aware` and `configs/seeds/**/*.aware`\n"
        "- Runtime implementation: `modules/**/runtime/**/handlers/impl/**`\n\n"
        "## 3) Generated Read-only\n\n"
        "- `modules/**/structure/**/.aware/**`\n"
        "- `modules/**/structure/**/{python,dart,sql,sqlite}/**`\n"
        "- `.aware/**`\n"
        "- `_aware/**`\n\n"
        "## 4) Two-Loop Delivery Contract\n\n"
        "Workspace Config Loop (first):\n"
        "1. Capture human-agent intent/agreement.\n"
        "2. Review local Aware grammar bundle (`docs/aware/grammar/README.md`) and lock syntax/semantics.\n"
        "3. Review software mental-model rules (`docs/rules/SOFTWARE/index.md`) and confirm template/profile routing.\n"
        "4. Create module only after agreement: `aware-cli module create <module_id>`.\n"
        "5. Implement module changes in order: config -> runtime -> representation -> programs "
        "-> policy -> reactivity.\n"
        "6. Compile module(s).\n"
        "7. Make module proof pass.\n"
        "8. Wire pane registrar.\n"
        "9. Make IPC end-to-end pass (function call -> commit -> materialization -> cross-lang verification).\n\n"
        "Workspace Instantiation Loop (after config proofs):\n"
        "1. Connect compiler authority (remote-managed or full-local).\n"
        "2. Apply environment experience (process/thread/projection topology).\n"
        "3. Apply seed experience (`configs/seeds/aware_kernel.seed.aware` + "
        "`configs/seeds/aware_kernel.seed.profile.toml`).\n"
        "4. Validate instantiation outcomes and log evidence in issue/feed rails.\n\n"
        "## 5) Compile and Validation Discipline\n\n"
        "Recommended commands:\n"
        "1. `aware-cli compile --update-lock --materialization-mode runtime module <module_id>`\n"
        "2. `aware-cli workspace quality-gates --path "
        "services/environment/tests/test_inference_service_plugin_unit.py`\n"
        "3. `uv run pytest -q modules/<module_id>/runtime/tests/test_<module_id>_module_proof.py`\n"
        "4. Environment-level compile when needed: `aware-cli compile environment <environment_handle>`\n\n"
        "Completion gate:\n"
        "- Workspace Config Loop green.\n"
        "- Workspace Instantiation Loop green.\n"
        "- Module compile green.\n"
        "- Module proof green.\n"
        "- Pane registrar aligned to projection views.\n"
        "- IPC e2e green.\n"
        "- Evidence logged.\n\n"
        "## 6) Active Modules\n\n"
        f"{module_lines}\n\n"
        "## 7) Skills\n\n"
        "- Skills live under `skills/<skill-name>/SKILL.md`.\n"
        f"- Selected skill pack: `{skill_pack}`.\n"
        f"- Starter skill: `{starter_skill_relpath}`.\n"
        f"{pack_note}"
    )


def render_module_proof_test_scaffold(*, module_id: str, module_snake: str) -> str:
    return (
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n"
        "import pytest\n\n"
        "REPO_ROOT = Path(__file__).resolve().parents[4]\n"
        "MODULE_MANIFEST_PATH = (\n"
        f'    REPO_ROOT / "modules" / "{module_id}" / "structure" / "ontology" / "aware.toml"\n'
        ")\n\n\n"
        "@pytest.mark.meta_contract\n"
        f"def test_{module_snake}_module_proof_scaffold() -> None:\n"
        "    assert MODULE_MANIFEST_PATH.exists()\n\n"
        "    pytest.skip(\n"
        f'        "TODO: replace scaffold with concrete module contract or runtime proof calls for {module_id}."\n'
        "    )\n"
    )


def render_environment_experience_contract() -> str:
    return (
        "version = 1\n"
        'scope = "environment"\n'
        'description = "Environment-level experience contract for process/thread/projection topology."\n\n'
        "[requirements]\n"
        "intent_agreement_required = true\n"
        "experience_definition_required = true\n"
        "environment_validation_required = true\n"
        'notes = "Experience is environment-level Workspace Instantiation and follows Workspace Config proof gates."\n'
    )


def render_agent_delivery_contract() -> str:
    return (
        "version = 1\n"
        'description = "Super-opinionated human-agent delivery contract for Aware workspaces."\n\n'
        "[tracks.config]\n"
        "order = [\n"
        '  "capture_intent_agreement",\n'
        '  "review_aware_grammar_docs",\n'
        '  "review_software_rules_bundle",\n'
        '  "module_create_explicit",\n'
        '  "experience_to_ontology_to_projection",\n'
        '  "programs_profile_contract",\n'
        '  "compile_pass",\n'
        '  "quality_gates_pass",\n'
        '  "module_proof_pass",\n'
        '  "pane_registrar_pass",\n'
        '  "ipc_e2e_pass",\n'
        "]\n\n"
        "[tracks.instantiation]\n"
        "order = [\n"
        '  "connect_compiler_authority",\n'
        '  "apply_environment_experience",\n'
        '  "apply_seed_experience",\n'
        '  "validate_instantiation_contract",\n'
        '  "evidence_logged",\n'
        "]\n\n"
        "[git_policy]\n"
        'mode = "external_agent_automation"\n'
        "human_git_required = false\n"
        "allow_standard_mutation = true\n"
        "allow_history_rewrite = false\n"
        'fallback_on_policy_block = "patch_and_log_blocker"\n'
    )


def render_evidence_policy_contract() -> str:
    return (
        "version = 1\n"
        'description = "Evidence policy for reproducible delivery and optimization telemetry."\n\n'
        "[required]\n"
        "issue_updates = true\n"
        "feed_updates = true\n"
        "command_transcripts = true\n"
        "proof_results = true\n"
        "ipc_e2e_results = true\n\n"
        "[telemetry]\n"
        "track_step_durations = true\n"
        "track_failures = true\n"
        "track_retries = true\n"
    )


def render_quality_gates_contract() -> str:
    return (
        "version = 1\n"
        'description = "Opinionated lint/type gates for workspace config loop."\n\n'
        "[defaults]\n"
        'command = "aware-cli workspace quality-gates"\n'
        "fail_on_missing_tool = true\n"
        "run_before_module_proof = true\n\n"
        "[defaults.profile_by_language]\n"
        'python = "standard"\n'
        'dart = "standard"\n\n'
        "[gates.python_flake8]\n"
        'gate_id = "python.flake8"\n'
        'language = "python"\n'
        'command = ["uv", "run", "flake8"]\n'
        'target_mode = "paths"\n\n'
        "[gates.python_mypy]\n"
        'gate_id = "python.mypy"\n'
        'language = "python"\n'
        'command = ["uv", "run", "mypy"]\n'
        'target_mode = "paths"\n\n'
        "[gates.python_basedpyright_error]\n"
        'gate_id = "python.basedpyright.error"\n'
        'language = "python"\n'
        'command = ["uv", "run", "basedpyright", "--level", "error"]\n'
        'target_mode = "paths"\n\n'
        "[gates.python_basedpyright_warning]\n"
        'gate_id = "python.basedpyright.warning"\n'
        'language = "python"\n'
        'command = ["uv", "run", "basedpyright", "--level", "warning", "--warnings"]\n'
        'target_mode = "paths"\n\n'
        "[gates.dart_analyze]\n"
        'gate_id = "dart.analyze"\n'
        'language = "dart"\n'
        'command = ["dart", "analyze"]\n'
        'target_mode = "paths"\n\n'
        "[profiles.python.standard]\n"
        'gates = ["python.flake8", "python.mypy", "python.basedpyright.error"]\n\n'
        "[profiles.python.strict]\n"
        'gates = ["python.flake8", "python.mypy", "python.basedpyright.warning"]\n\n'
        "[profiles.dart.standard]\n"
        'gates = ["dart.analyze"]\n\n'
        "[[path_profiles]]\n"
        'language = "python"\n'
        'path_prefix = "modules/meta"\n'
        'profile = "strict"\n'
    )


__all__ = [
    "render_agent_delivery_contract",
    "render_environment_experience_contract",
    "render_environment_file",
    "render_evidence_policy_contract",
    "render_quality_gates_contract",
    "render_minimal_daily_feed_log",
    "render_minimal_feed_protocol",
    "render_minimal_feed_snapshot",
    "render_minimal_issues_protocol",
    "render_module_proof_test_scaffold",
    "render_workspace_root_placeholder_readme",
    "render_workspace_agents_md",
    "render_workspace_ci_workflow",
    "render_workspace_pyproject",
]
