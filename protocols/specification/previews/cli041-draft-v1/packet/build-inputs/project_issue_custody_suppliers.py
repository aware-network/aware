"""Pinned custody successor of the accepted neutral supplier projection.

Only metadata and export facades change; operational implementations are exact
owner blobs. No builds, domain execution, or installation occurs here.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import project_issue_draft_suppliers as draft
import project_issue_setup_suppliers as setup

DRAFT_RECIPE_SHA = "bc5882d8dceaea78fd82435b1383950bc26ecda0481929cc604ebe95507f0541"
ISSUE_REVISION = "9c5ca67c580cd2a1c6ecbfe831fd8249db424cff"
FILESYSTEM_REVISION = "6be8b1aec584c5700b477b55e401386727548ca2"
PACKAGES = {
    name: (
        root,
        members + (("draft_input_custody.py",) if name == "aware-issue-sdk" else ()),
    )
    for name, (root, members) in draft.PACKAGES.items()
}
VERSIONS = {
    "aware-issue-runtime": "0.1.0+setup.1",
    "aware-issue-operational-runtime": "0.3.0+setup.1",
    "aware-issue-sdk": "0.9.0+custody.1",
    "aware-issue-fs-adapter": "0.8.0+custody.1",
    "aware-file-system": "0.3.0+custody.1",
}


def revision(name: str) -> str:
    if name == "aware-file-system":
        return FILESYSTEM_REVISION
    if name in {"aware-issue-sdk", "aware-issue-fs-adapter"}:
        return ISSUE_REVISION
    return setup.OWNER_REVISION


def committed(repo: Path, ref: str, path: str) -> tuple[str, bytes]:
    row = subprocess.check_output(["git", "ls-tree", ref, "--", path], cwd=repo)
    fields, actual = row.decode().strip().split("\t", 1)
    mode, kind, blob = fields.split()
    if mode not in {"100644", "100755"} or kind != "blob" or actual != path:
        raise ValueError("committed_regular_supplier_required:" + path)
    return blob, subprocess.check_output(["git", "cat-file", "blob", blob], cwd=repo)


def metadata(name: str, original: bytes) -> bytes:
    project = tomllib.loads(original.decode())["project"]
    dependencies = list(project.get("dependencies", []))
    if name == "aware-issue-runtime":
        dependencies.remove("aware-local-service-runtime>=0.1.0")
    if name == "aware-file-system":
        dependencies = []  # Selected confined/retained modules are stdlib-only.
    from packaging.requirements import Requirement

    dependencies = [
        Requirement(value).name + "==" + VERSIONS[Requirement(value).name]
        if Requirement(value).name in VERSIONS
        else value
        for value in dependencies
    ]
    fields = {
        "name": name,
        "version": VERSIONS[name],
        "requires-python": project["requires-python"],
        "dependencies": dependencies,
    }
    return (
        "[project]\n"
        + "".join(
            key + " = " + json.dumps(value) + "\n" for key, value in fields.items()
        )
        + '[build-system]\nrequires = ["hatchling>=1.27.0"]\nbuild-backend = "hatchling.build"\n'
        + "[tool.hatch.build.targets.wheel]\npackages = "
        + json.dumps([name.replace("-", "_")])
        + "\n"
    ).encode()


def facade(name: str, original: bytes) -> bytes:
    body = draft.facade(name, original)
    if name != "aware-issue-sdk":
        return body
    tree = ast.parse(body)
    selected = draft.export_map(tree)
    selected.update(
        (key, value)
        for key, value in draft.export_map(ast.parse(original)).items()
        if value == "aware_issue_sdk.draft_input_custody"
    )
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if "_EXPORT_MODULES" in names:
                node.value = ast.parse(repr(selected), mode="eval").body
            elif "__all__" in names:
                node.value = ast.parse(repr(sorted(selected)), mode="eval").body
    return (ast.unparse(tree) + "\n").encode()


def projection(repo: Path) -> tuple[dict[str, bytes], dict]:
    for module, expected in (
        (draft, DRAFT_RECIPE_SHA),
        (setup, draft.SETUP_RECIPE_SHA256),
    ):
        if not isinstance(module.__file__, str):
            raise TypeError("historical_projection_recipe_location_unavailable")
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != expected:
            raise ValueError("historical_projection_recipe_changed")
    output, rows = {}, []
    for name, (root, members) in PACKAGES.items():
        for path in [
            root + "/pyproject.toml",
            *[root + "/" + name.replace("-", "_") + "/" + member for member in members],
        ]:
            ref = revision(name)
            blob, original = committed(repo, ref, path)
            body = (
                metadata(name, original)
                if path.endswith("/pyproject.toml")
                else facade(name, original)
                if path.endswith("/__init__.py")
                else original
            )
            output[path] = body
            rows.append(
                {
                    "package": name,
                    "path": path,
                    "source_revision": ref,
                    "source_blob": blob,
                    "source_bytes": len(original),
                    "source_sha256": hashlib.sha256(original).hexdigest(),
                    "projected_bytes": len(body),
                    "projected_sha256": hashlib.sha256(body).hexdigest(),
                    "disposition": "byte-identical owner implementation"
                    if body == original
                    else "explicit neutral metadata/export facade",
                }
            )
    return output, {
        "schema": "aware.issue.custody-neutral-supplier-projection.v1",
        "consumer_versions": VERSIONS,
        "files": sorted(rows, key=lambda row: row["path"]),
        "status": "internal-projection-not-consumer-completion-or-public-release",
    }
