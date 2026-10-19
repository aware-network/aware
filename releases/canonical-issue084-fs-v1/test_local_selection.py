"""Original delivery derivation and conservation tests with finite coordinates."""

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(
    os.environ.get("AWARE_ISSUE084_SELECTION_ROOT", Path(__file__).resolve().parents[2])
)
BASELINE = "583fae85d9c986032b03eb5181c0e547a2eff68d"
RELEASE = "releases/canonical-issue084-fs-v1"
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-issue084-local-selection-v0.md"
SCOPE = {
    ISSUE,
    "README.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/SELECTED.json",
    RELEASE + "/README.md",
    RELEASE + "/LOCAL-SELECTION.md",
    RELEASE + "/test_local_selection.py",
}
LAYOUT_SHA = "d22712a18b175971d4064231ee1a277770a3804c1f803bd398015f30409aaa09"
INDEX_SHA = "6c532eb4ace4df423f0f0a666742900a2ebc65919475523d4ff175dcb2d6673d"
ENVELOPE_SHA = "d1326d1465a5bfbaf13293ce09e3b1a763e5ae98371f04f750fb4b81e76ebcee"
PAYLOAD_SHA = "f5e65fefa12ac6a778bf39e7efdffacf3a8a8b1fb261a6332a9656388ab94b5a"
ROOT_OLD = """## Prepared Issue observation input

Issue CLI **0.8.4** is prepared and unselected; these instructions remain draft.
The proposed installer targets this successor, not the delivered a14 envelope.
[Observation input](protocols/issues/OBSERVATION-INPUT.md) carries one explicit
Issue snapshot into original scope, progress and publish-close commands.
The same observation does not freeze previewed HEAD or source bytes.
Customer implementation and optional SPEC branches remain unchanged."""
ROOT_NEW = """## Locally selected Issue observation input

Issue CLI **0.8.4** is selected locally; public delivery is not yet authorized.
Instructions remain draft. Use this reviewed checkout, not unchanged public main.
The [delivery pointer](releases/SELECTED.json) binds the complete envelope;
[local selection](releases/canonical-issue084-fs-v1/LOCAL-SELECTION.md) records its limits.
[Observation input](protocols/issues/OBSERVATION-INPUT.md) carries one explicit
Issue snapshot into original scope, progress and publish-close commands.
The same observation does not freeze previewed HEAD or source bytes; apply plans
afresh. Customer implementation and optional SPEC branches, both review decisions
and contributor commands remain unchanged. Instruction freeze and publication
remain separate; no automatic guard refresh, approval or retry."""

path = ROOT / "releases/canonical-a14-fs-v1/test_local_selection.py"
if (
    path.is_symlink()
    or hashlib.sha256(path.read_bytes()).hexdigest()
    != "45a4a2b5c913ad8339d4ee78028b2f33cb359c8c9e40603da2f93074e62970f7"
):
    raise ValueError("original_selection_reader_required")
spec = importlib.util.spec_from_file_location("issue084_original_selection", path)
assert spec and spec.loader
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)
ORIGINAL_DERIVE = owner.derive_delivery_record


def derive_delivery_record(root):
    return owner.bind(
        ORIGINAL_DERIVE,
        {
            "canonical-a14-fs-v1": "canonical-issue084-fs-v1",
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
        },
    )(root)


for name in (
    "ROOT",
    "BASELINE",
    "RELEASE",
    "ISSUE",
    "SCOPE",
    "LAYOUT_SHA",
    "INDEX_SHA",
    "ENVELOPE_SHA",
    "PAYLOAD_SHA",
    "ROOT_OLD",
    "ROOT_NEW",
):
    setattr(owner, name, globals()[name])
    setattr(owner.owner, name, globals()[name])
owner.owner.derive_delivery_record = derive_delivery_record


class Selection(owner.Selection):
    test_exact_scope_and_conservation = owner.bind(
        owner.Selection.test_exact_scope_and_conservation,
        {(1822, 1825, 1817): (1864, 1867, 1859)},
    )
    test_predecessor_contributor_installer_and_guides_preserved = owner.bind(
        owner.Selection.test_predecessor_contributor_installer_and_guides_preserved,
        {
            (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-reference-fs-v1/",
            ): (
                ".aware/",
                "docs/agents/",
                "protocols/",
                "releases/canonical-a14-fs-v1/",
            ),
            "canonical-reference-fs-v1": "canonical-a14-fs-v1",
        },
    )
    test_retained_installation_reads = owner.bind(
        owner.Selection.test_retained_installation_reads,
        {
            "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c": "9d99f4c8ddab23cfaface4c635d502c2bf463a78ffd72fe064b2b79b7a851640",
        },
    )
    test_artifacts_software_and_legal_unchanged = owner.bind(
        owner.Selection.test_artifacts_software_and_legal_unchanged,
        {
            1372: 1374,
            "canonical-a14-source-notice-review-v1.tar.gz": "canonical-issue084-source-notice-review-v1.tar.gz",
        },
    )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--delivery-record":
        print(
            json.dumps(
                derive_delivery_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        import unittest

        unittest.main()
