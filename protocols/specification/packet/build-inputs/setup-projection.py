"""Pinned setup/read candidate wrapper over the existing wheel/bundle builder.

Generated files are confined to a fresh scratch directory. No domain operation
logic, public checkout mutation or source-development fallback is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path
from typing import Any

OWNER_REVISION = "b6bcae3c4a54295f4174f69eae507e242f9e4794"
PROJECTION_REVISION = "9033e5b2f57665f785572c6891174426243e3dee"
OBSERVATION_REVISION = "fc850b31080cb7c2cc2ff20cf730d564cd0b1e20"
COMMAND_REVISION = "56a4d10b9d2e3b7cd480798c2f4d1ff7cc9d4071"
COMMAND_ROOT = "workspaces/aware_kernel/modules/protocol/libs/cli/python"
COMMAND_PATHS = (
    COMMAND_ROOT + "/pyproject.toml",
    COMMAND_ROOT + "/aware_protocol_cli/main.py",
    COMMAND_ROOT + "/aware_protocol_cli/specification_setup.py",
)
OBSERVATION_PATH = (
    "workspaces/aware_kernel/modules/filesystem/libs/file_system/python/"
    "aware_file_system/retained_mutation.py"
)
PROJECTION_PATH = (
    "docs/specs/aware-portable-protocol/conformance/project_issue_setup_suppliers.py"
)
PUBLIC_REVISION = "a2ba162dad42edb6a4b4a3dfe917cf79fc286dd8"
PUBLIC_RELEASE_PATH = "protocols/agent/release.json"
PUBLIC_WORKSPACE = (
    "workspaces/aware_workspace/modules/workspace/libs/workspace_operator/python"
)
WORKSPACE = PUBLIC_WORKSPACE
ROOTS = (
    "workspaces/aware_kernel/modules/protocol/libs/runtime/python",
    "workspaces/aware_kernel/modules/protocol/sdks/protocol/python",
    "workspaces/aware_kernel/modules/protocol/libs/fs_adapter/python",
    "workspaces/aware_kernel/modules/protocol/libs/cli/python",
    "workspaces/aware_kernel/modules/specification/libs/runtime/python",
    "workspaces/aware_kernel/modules/specification/libs/fs_source_contract/python",
    "workspaces/aware_kernel/modules/specification/libs/fs_adapter/python",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/public",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter",
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/cli",
)


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def committed(repo: Path, revision: str, path: str) -> bytes:
    row = subprocess.check_output(["git", "ls-tree", revision, "--", path], cwd=repo)
    if not row.startswith((b"100644 blob ", b"100755 blob ")):
        raise ValueError("committed_regular_input_required:" + path)
    return subprocess.check_output(["git", "show", revision + ":" + path], cwd=repo)


def projected(repo: Path, public: Path) -> tuple[dict[str, bytes], dict]:
    """Compose accepted byte selections; only packaging metadata/facades differ."""
    namespace: dict[str, Any] = {"__name__": "pinned_issue_projection"}
    recipe = committed(repo, PROJECTION_REVISION, PROJECTION_PATH)
    exec(compile(recipe, PROJECTION_PATH, "exec"), namespace)  # noqa: S102 -- exact reviewed immutable recipe
    bodies, issue_plan = namespace["projection"](repo)
    inputs = [
        dict(r, source_revision=issue_plan["owner_revision"])
        for r in issue_plan["files"]
    ]
    # Keep the reviewed five-profile recipe and every other owner anchor fixed.
    # Only this independently accepted docstring/source successor is selected.
    observation = committed(repo, OBSERVATION_REVISION, OBSERVATION_PATH)
    selected = next(row for row in inputs if row["path"] == OBSERVATION_PATH)
    supersedes = {
        key: selected[key]
        for key in ("source_revision", "source_sha256", "source_blob")
    }
    entry = subprocess.check_output(
        ["git", "ls-tree", OBSERVATION_REVISION, "--", OBSERVATION_PATH], cwd=repo
    )
    selected.update(
        source_revision=OBSERVATION_REVISION,
        source_sha256=sha(observation),
        source_bytes=len(observation),
        source_blob=entry.decode().split()[2],
        supersedes=supersedes,
        disposition="byte-identical accepted observed-state owner source; executable behavior unchanged",
    )
    bodies[OBSERVATION_PATH] = observation
    roots = [namespace["PACKAGES"][n][0] for n in namespace["PACKAGES"]]
    for root in (*ROOTS, WORKSPACE):
        roots.append(root)
        module = tomllib.loads(
            committed(repo, OWNER_REVISION, root + "/pyproject.toml").decode()
        )["project"]["name"].replace("-", "_")
        members = subprocess.check_output(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                OWNER_REVISION,
                "--",
                root + "/" + module,
            ],
            cwd=repo,
            text=True,
        ).splitlines()
        if root == WORKSPACE:
            members = [
                root + "/" + module + "/" + p
                for p in ("__init__.py", "commit.py", "models.py", "py.typed")
            ]
        for path in [root + "/pyproject.toml", *members]:
            original = committed(repo, OWNER_REVISION, path)
            bodies[path] = original
            inputs.append(
                {
                    "path": path,
                    "source_revision": OWNER_REVISION,
                    "source_sha256": sha(original),
                    "source_bytes": len(original),
                }
            )
    command_overrides = []
    for path in COMMAND_PATHS:
        body = committed(repo, COMMAND_REVISION, path)
        row = next(r for r in inputs if r["path"] == path)
        prior = {k: row[k] for k in ("source_revision", "source_sha256")}
        row.update(
            source_revision=COMMAND_REVISION,
            source_sha256=sha(body),
            source_bytes=len(body),
            source_blob=subprocess.check_output(
                ["git", "rev-parse", COMMAND_REVISION + ":" + path], cwd=repo
            )
            .decode()
            .strip(),
            supersedes=prior,
            disposition="accepted command source; no copied policy or physical writer",
        )
        bodies[path] = body
        command_overrides.append(
            {"path": path, "revision": COMMAND_REVISION, "sha256": sha(body)}
        )
    # Preserve the existing a6 commit-only facade, with current original owners.
    facade = WORKSPACE + "/aware_workspace_operator/__init__.py"
    bodies[facade] = committed(
        public,
        PUBLIC_REVISION,
        PUBLIC_WORKSPACE + "/aware_workspace_operator/__init__.py",
    )
    license_body = committed(repo, OWNER_REVISION, "LICENSE")
    packages = []
    for root in roots:
        path = root + "/pyproject.toml"
        original = bodies[path]
        data = tomllib.loads(original.decode())
        project = data["project"]
        name = project["name"]
        version = "0.4.0+setup.1" if root == WORKSPACE else project["version"]
        if name == "aware-file-system":
            version = "0.1.5+setup.2"
        elif name == "aware-issue-fs-adapter":
            version = "0.6.0+setup.2"
        # Exact inter-profile constraints; lazy optional owner integrations stay explicit.
        dependencies = project.get("dependencies", [])
        if name == "aware-issue-fs-adapter":
            dependencies = [
                "aware-file-system==0.1.5+setup.2"
                if dependency == "aware-file-system==0.1.5+setup.1"
                else dependency
                for dependency in dependencies
            ]
        if root == WORKSPACE:
            dependencies = [
                "aware-issue-operational-runtime==0.3.0+setup.1",
                "pydantic>=2.8.2,<3.0.0",
            ]
        text = (
            "[project]\n"
            + "\n".join(
                key + " = " + json.dumps(value)
                for key, value in {
                    "name": name,
                    "version": version,
                    "requires-python": ">=3.12",
                    "dependencies": dependencies,
                    "license": "Apache-2.0",
                    "license-files": ["LICENSE", "NOTICE"],
                }.items()
            )
            + "\n"
        )
        extras = {
            k: v
            for k, v in project.get("optional-dependencies", {}).items()
            if k in {"protocol", "specification", "specification-setup"}
        }
        if extras:
            text += "[project.optional-dependencies]\n" + "".join(
                k + " = " + json.dumps(v) + "\n" for k, v in extras.items()
            )
        if project.get("scripts"):
            text += "[project.scripts]\n" + "".join(
                k + " = " + json.dumps(v) + "\n" for k, v in project["scripts"].items()
            )
        module = name.replace("-", "_")
        text += (
            '[build-system]\nrequires = ["hatchling>=1.27.0"]\n'
            'build-backend = "hatchling.build"\n[tool.hatch.build.targets.wheel]\n'
            "packages = " + json.dumps([module]) + "\n"
        )
        bodies[path] = text.encode()
        bodies[root + "/LICENSE"] = license_body
        bodies[root + "/NOTICE"] = (
            name + "\nCopyright 2026 Luis Lechuga Ruiz\n"
            "Aware-authored work is Apache-2.0.\n"
            "Neutral setup/read packaging profile; original domain implementations preserved.\n"
        ).encode()
        packages.append({"name": name, "version": version, "path": root})
    for row in inputs:
        row.update(
            projected_sha256=sha(bodies[row["path"]]),
            projected_bytes=len(bodies[row["path"]]),
        )
    return bodies, {
        "owner_revision": OWNER_REVISION,
        "projection_revision": PROJECTION_REVISION,
        "projection_recipe_sha256": sha(recipe),
        "candidate_generation": 3,
        "command_revision": COMMAND_REVISION,
        "command_source_overrides": command_overrides,
        "source_overrides": [
            {
                "path": OBSERVATION_PATH,
                "revision": OBSERVATION_REVISION,
                "sha256": sha(observation),
                "reason": "accepted observation-contract/docstring qualification, not a new writer",
            }
        ],
        "observation_boundary": {
            "accepted_for": "cooperative filesystem SPEC setup",
            "currentness": "exact bytes and retained identities/observed metadata at checks",
            "every_intervening_write_detection": "unsupported",
            "continuous_confinement": "unsupported",
            "historical_candidate": "60d4a61816be87926ccd1a22d8f6481fef13c6787c5126af8a41b182e5735fd1",
            "historical_failures": "retained unchanged, not relabeled as passing",
        },
        "issue_inventory": issue_plan,
        "public_facade_revision": PUBLIC_REVISION,
        "files": inputs,
        "source_packages": packages,
        "generated_legal_inputs": {
            p: sha(b) for p, b in bodies.items() if p.endswith(("/LICENSE", "/NOTICE"))
        },
        "status": "internal-source-build-input-not-public-clearance",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-repository", type=Path, required=True)
    parser.add_argument("--public-repository", type=Path, required=True)
    parser.add_argument("--output-parent", type=Path, required=True)
    parser.add_argument("--inputs-only", action="store_true")
    args = parser.parse_args()
    bodies, provenance = projected(args.owner_repository, args.public_repository)
    if args.inputs_only:
        print(json.dumps(provenance, indent=2, sort_keys=True))
        return
    scratch = Path(
        tempfile.mkdtemp(
            prefix="specification-setup-", dir=args.output_parent.resolve(strict=True)
        )
    )
    source = scratch / "source"
    for path, body in bodies.items():
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    release_raw = committed(
        args.public_repository, PUBLIC_REVISION, PUBLIC_RELEASE_PATH
    )
    release = json.loads(release_raw)
    archive = args.public_repository / "protocols/agent" / release["archive"]
    if sha(archive.read_bytes()) != release["archive_sha256"]:
        raise ValueError("accepted_a6_archive_hash_mismatch")
    wheelhouse = scratch / "wheelhouse"
    wheelhouse.mkdir()
    expected = {
        w["filename"]: w["sha256"]
        for w in release["wheels"]
        if not w["filename"].startswith("aware_")
    }
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            name = Path(member.name).name
            if name not in expected:
                continue
            if not member.isfile():
                raise ValueError("registry_member_not_regular")
            stream = tar.extractfile(member)
            assert stream is not None
            body = stream.read()
            if sha(body) != expected.pop(name):
                raise ValueError("registry_wheel_hash_mismatch")
            (wheelhouse / name).write_bytes(body)
    if expected:
        raise ValueError("registry_wheel_missing")
    environment = dict(
        os.environ,
        UV_OFFLINE="1",
        UV_PYTHON_DOWNLOADS="never",
        SOURCE_DATE_EPOCH="0",
        PYTHONHASHSEED="0",
    )
    for package in provenance["source_packages"]:
        subprocess.run(
            [
                "uv",
                "build",
                "--offline",
                "--wheel",
                "--no-sources",
                "--python",
                sys.executable,
                "--no-python-downloads",
                "--out-dir",
                str(wheelhouse),
                str(source / package["path"]),
            ],
            env=environment,
            check=True,
        )
    import email
    import zipfile

    inventory = []
    for path in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(path) as wheel:
            metadata = email.message_from_bytes(
                wheel.read(
                    next(
                        p for p in wheel.namelist() if p.endswith(".dist-info/METADATA")
                    )
                )
            )
        inventory.append(
            {
                "name": metadata["Name"],
                "version": metadata["Version"],
                "hashes": [sha(path.read_bytes())],
            }
        )
    aware_names = {p["name"] for p in provenance["source_packages"]}
    spec = {
        "authority_mode": "filesystem",
        "profile": "aware.collaboration.fs_v1",
        "platform": "linux_x86_64",
        "python_minor": "3.12",
        "bundle_prefix": "aware-specification-setup-read-internal-v3",
        "interfaces": {
            "setup": "aware-protocol-cli[specification-setup]==0.3.0",
            "reader": "aware-specification-cli==0.2.0",
        },
        "launchers": ["aware-protocol", "aware-spec"],
        "source_packages": [p for p in inventory if p["name"] in aware_names],
        "registry_packages": [
            p
            for p in inventory
            if p["name"] not in aware_names and p["name"] != "jsonschema"
        ],
        "source_derived_packages": [p for p in inventory if p["name"] == "jsonschema"],
    }
    builder_path = Path(__file__).parents[1] / "release/build_client_distribution_v1.py"
    module_spec = importlib.util.spec_from_file_location(
        "existing_bundle_builder", builder_path
    )
    assert module_spec is not None and module_spec.loader is not None
    builder = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(builder)
    provenance["retained_third_party"] = {
        "public_release_sha256": sha(release_raw),
        "archive_sha256": release["archive_sha256"],
        "origin": "unchanged bytes from accepted a6; jsonschema is source-derived, not registry",
        "notice_disclosure_acceptance": "held for this new candidate",
    }
    # uv writes a .gitignore in build output. Keep its scratch bookkeeping out
    # of the exact wheel-only assembly input; do not relax the builder refusal.
    retained = scratch / "retained-wheelhouse"
    retained.mkdir()
    for wheel in sorted(wheelhouse.glob("*.whl")):
        shutil.copyfile(wheel, retained / wheel.name)
    result = builder.assemble_retained_distribution(
        spec, retained, scratch / "bundle", provenance, epoch=0
    )
    result.update(
        status="internal-candidate-built-not-installed",
        scratch=str(scratch),
        owner_revision=OWNER_REVISION,
        projection_revision=PROJECTION_REVISION,
        observation_revision=OBSERVATION_REVISION,
        command_revision=COMMAND_REVISION,
        wrapper_sha256=sha(Path(__file__).read_bytes()),
        builder_sha256=sha(builder_path.read_bytes()),
    )
    (scratch / "candidate-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
