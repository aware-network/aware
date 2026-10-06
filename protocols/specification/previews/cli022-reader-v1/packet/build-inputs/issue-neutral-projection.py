"""Pinned neutral supplier projection for Bundle; no build, install or writes.

This narrows package surfaces, not domain implementations. Bundle must separately
admit versions, full dependency closure, notices and source-to-wheel accounting.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

OWNER_REVISION = "da023701bbce1e7a2779ec87a782f461213ae639"
WORKFLOW = "workspaces/aware_coordination/modules/workflow/"
FILESYSTEM = "workspaces/aware_kernel/modules/filesystem/libs/file_system/python"
PACKAGES = {
    "aware-issue-runtime": (
        WORKFLOW + "libs/issue_runtime",
        (
            "__init__.py",
            "contracts.py",
            "parser.py",
            "source_import.py",
            "development.py",
            "first_person_activity.py",
            "pulse.py",
            "py.typed",
        ),
    ),
    "aware-issue-operational-runtime": (
        WORKFLOW + "libs/issue_operational_runtime",
        (
            "__init__.py",
            "activity_observation.py",
            "activity_observation_codec.py",
            "codec.py",
            "contracts.py",
            "host.py",
            "identity.py",
            "journal.py",
            "persistence.py",
            "source_scope_policy.py",
            "state_machine.py",
            "py.typed",
        ),
    ),
    "aware-issue-sdk": (
        WORKFLOW + "sdks/issue/python",
        (
            "__init__.py",
            "operation.py",
            "local_files.py",
            "source_change.py",
            "py.typed",
        ),
    ),
    "aware-issue-fs-adapter": (
        WORKFLOW + "sdks/issue/filesystem_adapter/python",
        ("__init__.py", "provider.py", "source_change.py", "py.typed"),
    ),
    "aware-file-system": (
        FILESYSTEM,
        ("__init__.py", "confined_mutation.py", "retained_mutation.py", "py.typed"),
    ),
}
VERSIONS = {
    "aware-issue-runtime": "0.1.0+setup.1",
    "aware-issue-operational-runtime": "0.3.0+setup.1",
    "aware-issue-sdk": "0.7.0+setup.1",
    "aware-issue-fs-adapter": "0.6.0+setup.1",
    "aware-file-system": "0.1.5+setup.1",
}


def committed(repository: Path, path: str) -> tuple[str, bytes]:
    entry = (
        subprocess.check_output(
            ["git", "ls-tree", OWNER_REVISION, "--", path], cwd=repository
        )
        .decode()
        .strip()
    )
    fields, actual = entry.split("\t", 1)
    mode, kind, blob = fields.split()
    if mode not in {"100644", "100755"} or kind != "blob" or actual != path:
        raise ValueError("committed_regular_supplier_required:" + path)
    return blob, subprocess.check_output(
        ["git", "cat-file", "blob", blob], cwd=repository
    )


def facade(name: str, body: bytes) -> bytes:
    """Export-only transformations. Never rewrite an implementation function."""
    tree = ast.parse(body)
    if name == "aware-file-system":
        # Mutation-only profile: no indexer/watcher/native-backend imports.
        return b'"""Neutral filesystem mutation supplier profile; use owning submodules."""\n'
    if name == "aware-issue-sdk":
        mapping = next(
            ast.literal_eval(node.value)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "_EXPORT_MODULES"
                for t in node.targets
            )
        )
        allowed = {
            "aware_issue_sdk.operation",
            "aware_issue_sdk.local_files",
            "aware_issue_sdk.source_change",
        }
        selected = {key: value for key, value in mapping.items() if value in allowed}
        # Preserve the original lazy resolver. Its map, advertised names and
        # optional view gate must all describe the same selected surface.
        for node in tree.body:
            if isinstance(node, ast.Assign):
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
                if "_EXPORT_MODULES" in names:
                    node.value = ast.parse(repr(selected), mode="eval").body
                elif "__all__" in names:
                    node.value = ast.parse(repr(sorted(selected)), mode="eval").body
                elif "_VIEW_STATE_EXPORTS" in names:
                    node.value = ast.parse("set()", mode="eval").body
        return (ast.unparse(tree) + "\n").encode()
    if name == "aware-issue-runtime":
        excluded = next(
            set(ast.literal_eval(node.value))
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "_PARTICIPANT_EXPORTS"
                for t in node.targets
            )
        )
        tree.body = [
            node
            for node in tree.body
            if not (isinstance(node, ast.FunctionDef) and node.name == "__getattr__")
            and not (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(t, ast.Name) and t.id == "_PARTICIPANT_EXPORTS"
                    for t in node.targets
                )
            )
        ]
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets
            ):
                names = [
                    value
                    for value in ast.literal_eval(node.value)
                    if value not in excluded
                ]
                node.value = ast.parse(repr(names), mode="eval").body
        return (ast.unparse(tree) + "\n").encode()
    return body


def metadata(name: str, original: bytes) -> bytes:
    data = tomllib.loads(original.decode())["project"]
    dependencies = list(data.get("dependencies", []))
    if name == "aware-issue-runtime":
        dependencies.remove("aware-local-service-runtime>=0.1.0")
    if name == "aware-file-system":
        dependencies = []  # Both selected mutation implementations are stdlib-only.
    for index, requirement in enumerate(dependencies):
        dependency = requirement.split(">=", 1)[0]
        if dependency in VERSIONS:
            dependencies[index] = dependency + "==" + VERSIONS[dependency]
    module = name.replace("-", "_")
    # A new internal profile identity, not a restamped internal/a6 distribution.
    return (
        "[project]\n"
        + f"name = {json.dumps(name)}\nversion = {json.dumps(VERSIONS[name])}\n"
        + 'requires-python = ">=3.12"\n'
        + "dependencies = "
        + json.dumps(dependencies)
        + "\n"
        + (
            '[project.optional-dependencies]\nspecification = ["aware-specification-fs-sdk-adapter>=0.1.0"]\n'
            if name == "aware-issue-fs-adapter"
            else ""
        )
        + '[build-system]\nrequires = ["hatchling>=1.27.0"]\nbuild-backend = "hatchling.build"\n'
        + "[tool.hatch.build.targets.wheel]\npackages = "
        + json.dumps([module])
        + "\n"
    ).encode()


def projection(repository: Path) -> tuple[dict[str, bytes], dict]:
    output: dict[str, bytes] = {}
    bindings = []
    for name, (root, members) in PACKAGES.items():
        module = name.replace("-", "_")
        paths = [
            root + "/pyproject.toml",
            *(root + "/" + module + "/" + member for member in members),
        ]
        for path in paths:
            blob, original = committed(repository, path)
            if path.endswith("/pyproject.toml"):
                body = metadata(name, original)
            elif path.endswith("/__init__.py"):
                body = facade(name, original)
            else:
                body = original
            output[path] = body
            bindings.append(
                {
                    "package": name,
                    "path": path,
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
    plan = {
        "schema": "aware.issue.setup-neutral-supplier-projection.v1",
        "owner_revision": OWNER_REVISION,
        "status": "internal-source-projection-not-installed-not-public-release",
        "consumer_versions_proposed": VERSIONS,
        "files": sorted(bindings, key=lambda row: row["path"]),
        "deferred": [
            "independent projection acceptance",
            "full dependency/extras and registry-wheel closure",
            "license/notice disposition",
            "source-to-wheel accounting",
            "checkout-hidden offline installed qualification",
            "public exposure",
        ],
    }
    return output, plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-repository", type=Path, required=True)
    args = parser.parse_args()
    _, plan = projection(args.owner_repository)
    print(json.dumps(plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
