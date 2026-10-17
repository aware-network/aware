"""Human presentation of existing owner evidence; no admission or file access."""

from __future__ import annotations

import json

from .architecture_setup_a1_command_values import WorkspaceSetupA1CommandEvidence


def render_a1_review(
    evidence: WorkspaceSetupA1CommandEvidence,
    *,
    supplied_final_paths: tuple[str, ...] = (),
) -> str:
    lines = [
        f"Workspace governed setup: {evidence.operation} — {evidence.command_status}",
        "Review evidence only; displaying paths or guards grants no authority.",
    ]

    def paths(title: str, values: tuple[str, ...]) -> None:
        lines.append(title)
        lines.extend("  " + json.dumps(path, ensure_ascii=True) for path in values)
        if not values:
            lines.append("  (none)")

    observation = evidence.workspace_observation
    binding = observation.binding if observation is not None else None
    if binding is None:
        lines.append("Workspace plan: unavailable; no effect scope inferred.")
    else:
        paths(
            "Final files (--allowed-path; each exactly once):",
            tuple(row.path for row in binding.file_transitions),
        )
        paths(
            "Complete physical effect scope (Issue; includes temporary/auxiliary paths):",
            tuple(
                sorted(
                    {
                        path
                        for step in binding.ordered_effects
                        for path in (step.primary_path, *step.auxiliary_paths)
                    }
                )
            ),
        )
        lines.append(
            "Keep full ordered effects/preconditions in the evidence; "
            "Issue owns explicit scope binding."
        )
    if evidence.mode == "apply":
        paths(
            "Supplied final paths (original arguments; duplicates retained):",
            supplied_final_paths,
        )
    lines.append("Reviewed guards (preserve unchanged for the reviewed apply):")
    for name in (
        "issue_source_sha256",
        "authority_manifest_sha256",
        "plan_sha256",
    ):
        lines.append(
            f"  {name}: {getattr(evidence.review_guards, name) or 'unavailable'}"
        )
    admission = evidence.issue_observation
    if admission is None:
        lines.append(
            "Issue admission: not observed; preview is not apply authorization."
        )
    else:
        lines.append(
            f"Issue admission: phase={admission.phase}; "
            f"consumption_ref={admission.consumption_ref}; "
            f"verified_effect_ordinal={admission.verified_effect_ordinal}"
        )
    failure = evidence.primary_failure
    if failure.state != "none":
        lines.append(f"Refusal/failure: {failure.code}; stage={failure.stage}")
    if failure.code == "setup_write_scope_mismatch":
        lines.append(
            "Next: review expected versus supplied final paths, then explicitly "
            "choose the exact final-file allowlist. Scratch/effect scope is separate. "
            "Do not refresh guards or retry automatically."
        )
    elif evidence.command_status == "preview_completed":
        lines.append(
            "Next: review both path sets. If Issue scope changes, obtain and review "
            "a separate preview; then explicitly apply its unchanged guards."
        )
    else:
        lines.append(
            "Next: inspect original outcome and cleanup before choosing further work; "
            "no automatic guard refresh or retry."
        )
    result = evidence.workspace_result
    lines.append(
        "Historical execution release: "
        + (result.release if result is not None else "not observed")
        + " (never upgraded by later cleanup)."
    )
    lines.append("Later independent cleanup observations:")
    for name, outcome in (
        (
            "Workspace plan",
            evidence.plan_cleanup.release if evidence.plan_cleanup else None,
        ),
        (
            "Issue admission",
            evidence.admission_cleanup.outcome if evidence.admission_cleanup else None,
        ),
        (
            "Issue client",
            evidence.client_cleanup.issue.outcome
            if evidence.client_cleanup.issue
            else None,
        ),
        (
            "Workspace client",
            evidence.client_cleanup.workspace.outcome
            if evidence.client_cleanup.workspace
            else None,
        ),
    ):
        lines.append(f"  {name}: {outcome or 'not observed'}")
    lines.append(
        f"Evidence ledger complete: {evidence.ledger_complete}; "
        f"completion verified: {evidence.completion_verified}; authorizes retry: false"
    )
    lines.extend(
        "Diagnostic: " + json.dumps(row, ensure_ascii=True)
        for row in evidence.diagnostics
    )
    return "\n".join(lines)
