"""Pinned draft supplier source profile; not a build or installed qualification.

Reuse the accepted setup facade transformations, extending only the selected
SDK export map and owner file inventory. Domain implementations stay identical.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

import project_issue_setup_suppliers as setup

OWNER_REVISION = "b510b2117d737e34f10314bd221417e6364081a0"
SETUP_RECIPE_SHA256 = "2a2f6cbbe8c5e4c68411e113f65011ab97ca51418f84c5d0350e8f6791faa662"
PACKAGES = {
    name: (root, members + additions)
    for name, (root, members) in setup.PACKAGES.items()
    for additions in [
        ("draft_package.py",)
        if name in {"aware-issue-sdk", "aware-issue-fs-adapter"}
        else ("retained_package.py",)
        if name == "aware-file-system"
        else ()
    ]
}
VERSIONS = {
    "aware-issue-runtime": "0.1.0+draft.1",
    "aware-issue-operational-runtime": "0.3.0+draft.1",
    "aware-issue-sdk": "0.8.0+draft.1",
    "aware-issue-fs-adapter": "0.7.0+draft.1",
    "aware-file-system": "0.2.0+draft.1",
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


def export_map(tree: ast.Module) -> dict[str, str]:
    return next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "_EXPORT_MODULES" for t in node.targets
        )
    )


def facade(name: str, body: bytes) -> bytes:
    narrowed = setup.facade(name, body)
    if name != "aware-issue-sdk":
        return narrowed
    original = export_map(ast.parse(body))
    tree = ast.parse(narrowed)
    selected = export_map(tree)
    selected.update(
        (key, value)
        for key, value in original.items()
        if value == "aware_issue_sdk.draft_package"
    )
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {t.id for t in node.targets if isinstance(t, ast.Name)}
            if "_EXPORT_MODULES" in names:
                node.value = ast.parse(repr(selected), mode="eval").body
            elif "__all__" in names:
                node.value = ast.parse(repr(sorted(selected)), mode="eval").body
    return (ast.unparse(tree) + "\n").encode()


def metadata(name: str, original: bytes) -> bytes:
    # Reuse the original neutral selection. Rewrite dependency identities from
    # parsed requirements, never source strings or advancing checkout metadata.
    data = tomllib.loads(setup.metadata(name, original).decode())["project"]
    dependencies = []
    for requirement in data["dependencies"]:
        dependency = requirement.split("==", 1)[0].split(">=", 1)[0]
        dependencies.append(
            dependency + "==" + VERSIONS[dependency]
            if dependency in VERSIONS
            else requirement
        )
    return (
        "[project]\n"
        + f"name = {json.dumps(name)}\nversion = {json.dumps(VERSIONS[name])}\n"
        + 'requires-python = ">=3.12"\n'
        + "dependencies = "
        + json.dumps(dependencies)
        + "\n"
        + '[build-system]\nrequires = ["hatchling>=1.27.0"]\nbuild-backend = "hatchling.build"\n'
        + "[tool.hatch.build.targets.wheel]\npackages = "
        + json.dumps([name.replace("-", "_")])
        + "\n"
    ).encode()


def projection(repository: Path) -> tuple[dict[str, bytes], dict]:
    if (
        hashlib.sha256(Path(setup.__file__).read_bytes()).hexdigest()
        != SETUP_RECIPE_SHA256
    ):
        raise ValueError("setup_projection_recipe_pin_mismatch")
    output = {}
    bindings = []
    for name, (root, members) in PACKAGES.items():
        paths = [root + "/pyproject.toml"] + [
            root + "/" + name.replace("-", "_") + "/" + member for member in members
        ]
        for path in paths:
            blob, original = committed(repository, path)
            body = (
                metadata(name, original)
                if path.endswith("/pyproject.toml")
                else facade(name, original)
                if path.endswith("/__init__.py")
                else original
            )
            output[path] = body
            bindings.append(
                {
                    "package": name,
                    "path": path,
                    "source_blob": blob,
                    "source_sha256": hashlib.sha256(original).hexdigest(),
                    "projected_sha256": hashlib.sha256(body).hexdigest(),
                    "disposition": "byte-identical owner implementation"
                    if body == original
                    else "explicit neutral metadata/export facade",
                }
            )
    return output, {
        "schema": "aware.issue.draft-neutral-supplier-projection.v1",
        "owner_revision": OWNER_REVISION,
        "setup_recipe_owner_revision": setup.OWNER_REVISION,
        "setup_recipe_sha256": SETUP_RECIPE_SHA256,
        "status": "internal-source-projection-not-installed-not-public-release",
        "consumer_versions_proposed": VERSIONS,
        "files": sorted(bindings, key=lambda row: row["path"]),
        "deferred": [
            "independent acceptance",
            "resolver/extras closure",
            "license/notices",
            "source-to-wheel accounting",
            "checkout-hidden offline installed qualification",
            "public release",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-repository", type=Path, required=True)
    _, plan = projection(parser.parse_args().owner_repository)
    print(json.dumps(plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
