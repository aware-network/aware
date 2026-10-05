"""Issue-owned a6 contract projection from a pinned public a5 baseline.

No owner refresh, domain implementation, root-bootstrap migration or promotion.
Run once, then the existing packaged-contract renderer and source-layout recorder.
"""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "8ecf22d67b834ece5aa845171c70344b2069411e"
CONTRACT = "protocols/contracts/agent-fs/"
PROJECT = "workspaces/aware_coordination/modules/workflow/clients/agent/python/"

INDEX_GUIDANCE = """
## Three distinct projection results

`issue_authority:applied` means the authoritative Issue write applied.
`issue_day_index:pending` means its day-index projection has not been updated;
`feed:unavailable` means this installation has no FEED projection operation.
Neither is the Git index. `shared_index_projection`, its error and
`index_reconciliation_pending` describe the publication owner's Git-index
reconciliation for that operation only. These statuses can legitimately differ.
A read projection is Issue state, not a fresh observation of the Git index.
Inspect actual receipts and read-only Git state; never treat pending or unknown
as clean, or hand-edit a projection to hide retained debt.
"""
ACCEPTANCE_GUIDANCE = """
## Acceptance criteria are not an automatic verdict

Acceptance boxes are authored criteria, initially unchecked. This installation
has no operation that evaluates or checks them. Recorded test evidence and a
closed Issue do not change those boxes. Report the verification and actual
outcome explicitly; do not hand-check the Markdown or claim the unchecked box
is a failed test. Issue closure, verification evidence, authored criteria and
Goal/Specification acceptance are separate. No Goal/Specification acceptance
operation is supplied by this Issue-only profile.
"""


def committed(path):
    row = subprocess.check_output(["git", "ls-tree", BASELINE, "--", path], cwd=ROOT)
    if not row.startswith((b"100644 blob ", b"100755 blob ")):
        raise ValueError("committed_regular_source_required:" + path)
    return subprocess.check_output(["git", "show", BASELINE + ":" + path], cwd=ROOT)


def corrected_assets(assets):
    metadata = json.loads(assets["contract.json"])
    if metadata["version"] != "1.2.0":
        raise ValueError("a5_contract_required")
    result = dict(assets)
    result["contract.json"] = (json.dumps(dict(metadata, version="1.2.1"), indent=2) + "\n").encode()
    root = assets["AGENTS.md.in"].decode()
    if root.count("**1.2.0**") != 1:
        raise ValueError("a5_root_label_required")
    result["AGENTS.md.in"] = root.replace("**1.2.0**", "**1.2.1**").encode()
    index = assets["docs/agents/README.md"].decode()
    if index.count("`aware.agent.fs.v1` / 1.1.0.") != 1:
        raise ValueError("reported_a5_modular_label_required")
    result["docs/agents/README.md"] = index.replace(
        "`aware.agent.fs.v1` / 1.1.0.", "`aware.agent.fs.v1` / 1.2.1."
    ).encode()
    result["docs/issues/PROTOCOL.md"] += INDEX_GUIDANCE.encode() + ACCEPTANCE_GUIDANCE.encode()
    result["docs/agents/verification-and-handoff.md"] += ACCEPTANCE_GUIDANCE.encode()
    return result


def main():
    target = ROOT / (CONTRACT + "v1.2.1")
    if target.exists() or target.is_symlink():
        raise ValueError("contract_version_coordinate_exists")
    metadata = json.loads(committed(CONTRACT + "v1.2.0/contract.json"))
    assets = {p: committed(CONTRACT + "v1.2.0/" + p)
              for p in ["contract.json", *metadata["files"].values()]}
    corrected = corrected_assets(assets)
    # Validate every preimage before writing any target; do not absorb dirty inputs.
    for relative, data in assets.items():
        path = ROOT / (CONTRACT + "v1.2.0/" + relative)
        if path.is_symlink() or path.read_bytes() != data:
            raise ValueError("a5_contract_preimage_changed:" + relative)
    provenance_path = ROOT / "protocols/agent/source-provenance.json"
    before = committed("protocols/agent/source-provenance.json")
    if provenance_path.is_symlink() or provenance_path.read_bytes() != before:
        raise ValueError("provenance_preimage_changed")
    provenance = json.loads(before)
    changed = {PROJECT + "pyproject.toml", PROJECT + "aware_agent_cli/main.py"}
    changed.update(PROJECT + "aware_agent_cli/templates/agent-fs-v1/" + p
                   for p in assets if assets[p] != corrected[p])
    adoption = provenance["owner_adoption"]
    adoption["public_changed_paths"] = sorted(set(adoption["public_changed_paths"]) | changed)
    adoption.setdefault("additional_adoptions", []).append({
        "kind": "a5-client-feedback-a6-docs-only",
        "baseline_revision": BASELINE,
        "evaluation_revision": "984d99987b1fe1ff629f954e51cfbeeaeab2da12",
        "contract_version": "1.2.1",
        "domain_implementation_changed": False,
        "status": "source-preparation-not-consumer-acceptance",
    })
    for relative, data in corrected.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"contract_version": "1.2.1", "files": len(corrected),
                      "baseline": BASELINE, "a5_preserved": True}))


if __name__ == "__main__":
    main()
