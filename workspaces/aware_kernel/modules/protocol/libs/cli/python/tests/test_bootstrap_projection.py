"""Public lazy projection reuses the genuine bootstrap SDK and strict codec."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from aware_protocol_cli.bootstrap import (
    bootstrap_evidence_payload,
    prepare_bootstrap_input,
)
from aware_protocol_sdk.bootstrap import (
    ProtocolBootstrapClient,
    protocol_bootstrap_value_to_payload,
)
from packaging.requirements import Requirement


@pytest.mark.parametrize("templates", [False, True])
@pytest.mark.parametrize("summary", [False, True])
def test_input_projection_delegates_to_real_sdk(
    tmp_path, monkeypatch, templates, summary
):
    monkeypatch.setenv("CODEX_THREAD_ID", "bootstrap-projection")
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    root = tmp_path / "absent"
    before = set(os.listdir("/proc/self/fd"))
    client = ProtocolBootstrapClient.filesystem(
        repository_root=str(root), execution_id="codex-bootstrap-projection"
    )
    request, rendered = prepare_bootstrap_input(
        client,
        issue_root="custom/issues",
        install_agent_contract=templates,
        dry_run=True,
    )
    assert rendered == client.render_bootstrap_input(request)
    assert request.directory_paths == ("custom", "custom/issues")
    original = protocol_bootstrap_value_to_payload(rendered)
    projected = bootstrap_evidence_payload(rendered, summary=summary)
    if summary:
        for record in original["files"]:
            del record["content_utf8"]
    assert projected == original
    json.dumps(projected)
    assert not root.exists() and set(os.listdir("/proc/self/fd")) == before


def test_import_projection_does_not_activate_optional_supplier():
    script = """
import sys, importlib.abc
sys.path[:0] = ROOTS
class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('aware_protocol_sdk', 'aware_protocol_fs', 'aware_workspace', 'aware_file_system')):
            raise AssertionError(fullname)
sys.meta_path.insert(0, Refuse())
import aware_protocol_cli.bootstrap
""".replace("ROOTS", repr(sys.path))
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_bootstrap_extra_preserves_default_neutral_dependencies():
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())[
        "project"
    ]
    assert project["version"] == "0.3.5"
    defaults = {r.name: r for r in map(Requirement, project["dependencies"])}
    assert set(defaults) == {
        "aware-command-runtime",
        "aware-protocol-sdk",
        "aware-protocol-fs-adapter",
    }
    assert "0.3.0" not in defaults["aware-protocol-sdk"].specifier
    assert "0.3.1" in defaults["aware-protocol-sdk"].specifier
    assert "0.6.3" not in defaults["aware-protocol-fs-adapter"].specifier
    bootstrap = Requirement(project["optional-dependencies"]["bootstrap"][0])
    assert bootstrap.name == "aware-protocol-fs-adapter" and bootstrap.extras == {
        "bootstrap"
    }
    assert "0.6.4" in bootstrap.specifier and "0.7.0" not in bootstrap.specifier
