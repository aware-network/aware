"""Read-only controls for the bounded adoption guidance integration."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

BASE = "b3c19b5d03229a795e8539c94f7c1cfdcc3d90d5"
ROOT = Path(
    os.environ.get("AWARE_ADOPTION_PUBLIC_ROOT", Path(__file__).resolve().parents[2])
)
REL = "releases/canonical-issue084-fs-v1"
GUIDE = "protocols/EXISTING-REPOSITORY.md"
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-protocol-adoption-public-guidance-integration-v0.md"
CHANGED = {"README.md", "protocols/README.md", "protocols/WORKFLOW.md"}
SCOPE = CHANGED | {
    GUIDE,
    ISSUE,
    REL + "/PUBLIC-INSTRUCTIONS.json",
    REL + "/ADOPTION-GUIDANCE.md",
    REL + "/test_adoption_guidance.py",
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def original(path: str) -> bytes:
    return git("show", f"{BASE}:{path}")


def verify_pins(pins: dict) -> None:
    assert len(pins["files"]) == 22
    for path, account in pins["files"].items():
        raw = (ROOT / path).read_bytes()
        assert len(raw) == account["bytes"], path
        assert hashlib.sha256(raw).hexdigest() == account["sha256"], path


def test_guide_exact_and_qualified():
    raw = (ROOT / GUIDE).read_bytes()
    assert len(raw) == 7826
    assert (
        hashlib.sha256(raw).hexdigest()
        == "9445596fc4f7010805c96b0c953215331366676a797710a68e272c395ee83835"
    )
    body = raw.decode()
    assert "review candidate" in body
    assert "--no-agent-contract" in body and "both" in body
    assert "migration command" in body


def test_all_current_pins():
    verify_pins(json.loads((ROOT / REL / "PUBLIC-INSTRUCTIONS.json").read_text()))


@pytest.mark.parametrize("mutation", ["digest", "missing", "size"])
def test_pin_negative_controls(mutation):
    pins = json.loads((ROOT / REL / "PUBLIC-INSTRUCTIONS.json").read_text())
    if mutation == "missing":
        del pins["files"][GUIDE]
    elif mutation == "digest":
        pins["files"][GUIDE]["sha256"] = "0" * 64
    else:
        pins["files"][GUIDE]["bytes"] += 1
    with pytest.raises(AssertionError):
        verify_pins(pins)


def test_inherited_pins_and_metadata():
    before = json.loads(original(REL + "/PUBLIC-INSTRUCTIONS.json"))
    after = json.loads((ROOT / REL / "PUBLIC-INSTRUCTIONS.json").read_text())
    assert set(after["files"]) == set(before["files"]) | {GUIDE}
    for path, account in before["files"].items():
        if path not in CHANGED:
            assert after["files"][path] == account
    for key, value in before.items():
        if key != "files":
            assert after[key] == value
    assert after["adoption_guidance_publication_authorized"] is False


def test_navigation_and_original_shell_blocks():
    for path in CHANGED:
        before, after = original(path).decode(), (ROOT / path).read_text()
        assert after.startswith(before)
        assert re.findall(r"```(?:bash|sh)\n.*?```", after, re.DOTALL) == re.findall(
            r"```(?:bash|sh)\n.*?```", before, re.DOTALL
        )
        target = GUIDE if path == "README.md" else "EXISTING-REPOSITORY.md"
        assert f"]({target})" in after


def test_guide_pinned_links_and_fragments():
    body = (ROOT / GUIDE).read_text()
    links = re.findall(
        r"https://github.com/aware-network/aware/blob/([0-9a-f]{40})/([^\s)]+)", body
    )
    assert links
    for revision, target in links:
        assert revision == BASE
        path, _, fragment = target.partition("#")
        linked = git("show", f"{revision}:{path}").decode()
        if fragment:
            headings = re.findall(r"^#+ (.+)$", linked, re.MULTILINE)
            assert fragment in {
                re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-") for h in headings
            }


def test_unaffected_committed_bytes_and_modes():
    count = 0
    for row in git("ls-tree", "-rz", BASE).split(b"\0"):
        if not row:
            continue
        meta, name = row.split(b"\t", 1)
        path = name.decode()
        if path in SCOPE:
            continue
        mode, kind, oid = meta.split()
        assert kind == b"blob"
        current = ROOT / path
        assert current.is_file() and not current.is_symlink(), path
        raw = current.read_bytes()
        framed = b"blob " + str(len(raw)).encode() + b"\0" + raw
        assert hashlib.sha1(framed).hexdigest().encode() == oid, path
        assert bool(current.stat().st_mode & 0o111) == (mode == b"100755"), path
        count += 1
    assert count == 1871


def test_new_file_set_and_no_out_of_scope_changes():
    tracked = {r.decode() for r in git("diff", "--name-only", BASE).splitlines()}
    untracked = {
        r.decode()
        for r in git("ls-files", "--others", "--exclude-standard").splitlines()
    }
    assert tracked | untracked == SCOPE
    for path in SCOPE:
        assert (ROOT / path).is_file()
