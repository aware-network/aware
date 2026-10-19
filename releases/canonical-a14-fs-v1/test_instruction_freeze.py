"""A14 exact current instruction pins; original guards and retained reads."""

import hashlib
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from types import FunctionType

ROOT = Path(
    os.environ.get("AWARE_FREEZE_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
RELEASE = ROOT / "releases/canonical-a14-fs-v1"
BASELINE = "028233459847c88252c62f7264488c2053b6a075"
ENVELOPE_SHA = "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6"
PAYLOAD_SHA = "4d1bf3b5ab43e904d463ba307840cf681889339d7197b089083add866d692c58"
SOURCE_SHA = "3d43a253a59418256c78880fa817ab3eed762f4c1511eca61ba402996477109b"
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-a14-instruction-freeze-v0.md"
INSTRUCTIONS = {
    "README.md",
    "protocols/README.md",
    "protocols/COHERENCE.md",
    "protocols/INITIALIZATION.md",
    "protocols/INIT.md",
    "protocols/WORKFLOW.md",
    "protocols/issues/README.md",
    "protocols/issues/FIRST-ISSUE.md",
    "protocols/repository/README.md",
    "protocols/specification/README.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/workspace/RESOURCE-RELEASES.md",
    "protocols/FIRST-USEFUL-TASK.md",
    "protocols/tasks/JSON-CHECKER.md",
    "protocols/EVIDENCE-MAP.json",
    "releases/README.md",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/examples/prepare_draft_input.py",
    "releases/canonical-a14-fs-v1/README.md",
}
CURRENT = (
    "README.md",
    "protocols/WORKFLOW.md",
    "protocols/INIT.md",
    "protocols/workspace/README.md",
    "protocols/workspace/REVIEWED-SETUP.md",
    "protocols/workspace/REFERENCE-NAVIGATION.md",
    "protocols/workspace/RESOURCE-RELEASES.md",
    "docs/alignment/CURRENT.md",
    "releases/README.md",
    "releases/canonical-a14-fs-v1/README.md",
)
SCOPE = {
    ISSUE,
    *CURRENT,
    "releases/SELECTED.json",
    "releases/canonical-a14-fs-v1/INSTRUCTIONS.json",
    "releases/canonical-a14-fs-v1/INSTRUCTION-FREEZE.md",
    "releases/canonical-a14-fs-v1/test_instruction_freeze.py",
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load(path, digest, name):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_instruction_helper_required")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bind(function, replacements):
    code = function.__code__
    if not all(
        any(type(c) is type(k) and c == k for c in code.co_consts) for k in replacements
    ):
        raise ValueError("original_receiving_constant_required")
    result = FunctionType(
        code.replace(
            co_consts=tuple(
                next(
                    (
                        v
                        for k, v in replacements.items()
                        if type(c) is type(k) and c == k
                    ),
                    c,
                )
                for c in code.co_consts
            )
        ),
        function.__globals__,
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )
    assert result.__code__.co_code == code.co_code
    return result


def original():
    module = load(
        ROOT / "releases/canonical-init-summary-fs-v1/test_instruction_freeze.py",
        "4b7e470c217a0eeba87c7a02850e214c97060660858e35414131d19c74edcebc",
        "a14_original_instruction_owner",
    )
    for name in (
        "ROOT",
        "RELEASE",
        "BASELINE",
        "ENVELOPE_SHA",
        "PAYLOAD_SHA",
        "SOURCE_SHA",
        "INSTRUCTIONS",
    ):
        setattr(module, name, globals()[name])
    return module


def derive_instruction_record(root):
    return bind(
        original().derive_instruction_record,
        {
            "releases/canonical-init-summary-fs-v1": "releases/canonical-a14-fs-v1",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-a14-source-notice-review-v1.tar.gz",
        },
    )(root)


owner = load(
    ROOT / "releases/canonical-reference-fs-v1/test_instruction_freeze.py",
    "d95407f9d0164d7f600996c0a81986eae6f14bd50c64e7f8f04d90bccde475b1",
    "a14_original_instruction_accounting",
)
for name in (
    "ROOT",
    "RELEASE",
    "BASELINE",
    "ENVELOPE_SHA",
    "PAYLOAD_SHA",
    "SOURCE_SHA",
    "ISSUE",
    "INSTRUCTIONS",
    "SCOPE",
    "original",
    "derive_instruction_record",
):
    setattr(owner, name, globals()[name])


class Instructions(owner.Instructions):
    test_exact_pins_and_original_negative_controls = bind(
        owner.Instructions.test_exact_pins_and_original_negative_controls, {19: 20}
    )
    test_exact_scope_conservation_and_issue_guard_boundary = bind(
        owner.Instructions.test_exact_scope_conservation_and_issue_guard_boundary,
        {
            (1752, 1756, 1742): (1825, 1829, 1814),
        },
    )
    test_artifacts_pointer_and_historical_records_preserved = bind(
        owner.Instructions.test_artifacts_pointer_and_historical_records_preserved,
        {
            "canonical-reference-fs-v1/INSTRUCTIONS.json": "canonical-a14-fs-v1/INSTRUCTIONS.json",
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee": "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c",
        },
    )
    test_current_guidance_and_unchanged_command_blocks = bind(
        owner.Instructions.test_current_guidance_and_unchanged_command_blocks,
        {
            (
                "README.md",
                "protocols/WORKFLOW.md",
                "protocols/INIT.md",
                "protocols/workspace/README.md",
                "protocols/workspace/REVIEWED-SETUP.md",
                "protocols/workspace/REFERENCE-NAVIGATION.md",
                "docs/alignment/CURRENT.md",
                "releases/README.md",
                "releases/canonical-reference-fs-v1/README.md",
            ): CURRENT,
        },
    )
    test_retained_installation_help_and_origins = bind(
        owner.Instructions.test_retained_installation_help_and_origins,
        {
            "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee": "725ed1b5b681efdc7a6a944e96ceae6df074a8494fa065c7fd20f43b9a6b831c",
        },
    )


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--instruction-record":
        print(
            json.dumps(
                derive_instruction_record(Path(sys.argv[2])), sort_keys=True, indent=2
            )
        )
    else:
        unittest.main()
