"""Internal supplier qualification using canonical selection and original owners.

No hand-authored package catalog, public release, Object operation or new store.
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
from pathlib import Path
from zipfile import ZipFile

PROFILE = "workspace_delta_capture"
ROOT = "workspaces/aware_workspace/modules/workspace"
SDK = ROOT + "/sdks/workspace/python/public/tests"
RUNTIME = ROOT + "/libs/workspace_runtime/tests"
FS = ROOT + "/sdks/workspace/filesystem_adapter/python/tests"
SELF = SDK + "/qualify_repository_delta_capture_install.py"
RECIPE = (
    "docs/specs/aware-portable-protocol/release/build_canonical_neutral_candidate_v1.py"
)
FORBIDDEN = (
    "aware_issue",
    "aware_protocol",
    "aware_meta",
    "aware_ontology",
    "aware_service",
    "aware_local_service",
)
CASES = (
    SDK + "/test_repository_delta_capture_client.py",
    SDK + "/test_repository_delta_retention_client.py",
    *(
        RUNTIME + "/" + name
        for name in (
            "test_repository_delta_capture.py",
            "test_repository_delta_retention.py",
            "test_observation.py",
            "test_repository_delta.py",
            "test_repository_delta_resident.py",
            "test_repository_delta_resolution.py",
            "test_source_observation.py",
        )
    ),
)
PHYSICAL = (
    RUNTIME + "/test_repository_delta.py",
    FS + "/test_repository_delta_store.py",
    FS + "/test_repository_delta_retention.py",
)


def sha(body):
    return hashlib.sha256(body).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def run(command, *, cwd, env=None):
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, timeout=180, check=False
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.decode(errors="replace")[-5000:]
            or result.stdout.decode(errors="replace")[-5000:]
        )
    return result.stdout


def committed(repo, revision, path):
    return run(["git", "show", revision + ":" + path], cwd=repo)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def build(repo, proof, revision, cli, registry_pool):
    """Select through Workspace; reuse original build audits and assembler."""
    proof.mkdir(mode=0o700, exist_ok=False)
    recipe = proof / "original-canonical-builder.py"
    recipe.write_bytes(committed(repo, revision, RECIPE))
    owner = load(recipe, "capture_original_builder")
    source = proof / "sources"
    command = [str(cli), "workspace", "checkout", "--repo-root", str(repo)]
    inventory = json.loads(
        run(
            [*command, "--profile", PROFILE, "--destination", str(source), "--json"],
            cwd=repo,
        )
    )["inventory"]
    verified = json.loads(run([*command, "--verify", str(source), "--json"], cwd=repo))
    if verified != inventory or inventory["profiles"]["requested"] != [PROFILE]:
        raise ValueError("original_selection_changed")
    mappings = {
        r["target_path"]: r["source_path"] for r in inventory["repository_files"]
    }
    for row in inventory["files"]:
        body = committed(repo, revision, mappings.get(row["path"], row["path"]))
        if (source / row["path"]).read_bytes() != body or row[
            "digest"
        ] != "sha256:" + sha(body):
            raise ValueError("selected_source_not_committed:" + row["path"])
    declarations = {"aware.repo.toml"}
    for package in inventory["packages"]:
        declarations.add(package["manifest_path"])
        declarations.update(m["declaration_path"] for m in package["memberships"])
    for path in declarations:
        if (repo / path).read_bytes() != committed(repo, revision, path):
            raise ValueError("selected_declaration_not_committed:" + path)
    pool = proof / "pool"
    pool.mkdir()
    for path in registry_pool.glob("*.whl"):
        if not owner.wheel_info(path)[0].startswith("aware-"):
            shutil.copyfile(path, pool / path.name)
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("UV_", "PIP_", "PYTHON"))
    }
    env.update(
        SOURCE_DATE_EPOCH="0",
        PYTHONHASHSEED="0",
        UV_OFFLINE="1",
        UV_PYTHON_DOWNLOADS="never",
    )
    local = []
    for package in inventory["packages"]:
        output = proof / "build" / package["name"]
        log = run(
            [
                "uv",
                "build",
                "--offline",
                "--wheel",
                "--no-sources",
                "--no-create-gitignore",
                "--python",
                "/usr/bin/python3.12",
                "--no-python-downloads",
                "--out-dir",
                str(output),
                str(source / package["root"]),
            ],
            cwd=proof,
            env=env,
        )
        (output / "build.log").write_bytes(log)
        (wheel,) = output.glob("*.whl")
        name, version, _, values = owner.wheel_info(wheel)
        if (name, version) != (package["name"], package["version"]):
            raise ValueError("built_identity_changed")
        for member, body in values.items():
            if (
                ".dist-info/" not in member
                and member.endswith((".py", ".typed"))
                and (source / package["root"] / member).read_bytes() != body
            ):
                raise ValueError("wheel_source_changed:" + member)
        shutil.copyfile(wheel, pool / wheel.name)
        local.append(
            {
                "name": name,
                "version": version,
                "path": package["root"],
                "hashes": [sha(wheel.read_bytes())],
            }
        )
    roots = owner.pinned_requirements(inventory)
    (proof / "requirements.in").write_text("\n".join(roots) + "\n")
    (proof / "constraints.txt").write_text(
        "\n".join(p["name"] + "==" + p["version"] for p in inventory["packages"]) + "\n"
    )
    run(
        [
            "uv",
            "pip",
            "compile",
            "--offline",
            "--no-index",
            "--no-sources",
            "--only-binary=:all:",
            "--python-version",
            "3.12",
            "--python-platform",
            owner.TARGET,
            "--no-python-downloads",
            "--generate-hashes",
            "--no-header",
            "--no-annotate",
            "--no-strip-extras",
            "--find-links",
            str(pool),
            "--constraints",
            str(proof / "constraints.txt"),
            "--output-file",
            str(proof / "requirements.lock.txt"),
            str(proof / "requirements.in"),
        ],
        cwd=proof,
        env=env,
    )
    house = proof / "wheelhouse"
    house.mkdir()
    values, registries = {}, []
    names = {p["name"] for p in local}
    for name, version, digest in owner.locked_rows(
        (proof / "requirements.lock.txt").read_text()
    ):
        matches = [
            p
            for p in pool.glob("*.whl")
            if owner.wheel_info(p)[:2] == (name, version)
            and sha(p.read_bytes()) == digest
        ]
        (wheel,) = matches
        _, _, metadata, _ = owner.wheel_info(wheel)
        values[name] = (version, metadata)
        shutil.copyfile(wheel, house / wheel.name)
        if name not in names:
            registries.append({"name": name, "version": version, "hashes": [digest]})
    checks = owner.reachable(values, roots)
    if any(name.replace("-", "_").startswith(FORBIDDEN) for name in values):
        raise ValueError("foreign_domain_in_capture_closure")
    spec = {
        "authority_mode": "filesystem",
        "profile": PROFILE,
        "platform": "linux_x86_64",
        "python_minor": "3.12",
        "bundle_prefix": "aware-workspace-capture-supplier-v1",
        "interfaces": {"capture": roots[0]},
        "launchers": [],
        "source_packages": local,
        "registry_packages": registries,
    }
    provenance = {
        "owner_revision": revision,
        "inventory_digest": inventory["inventory_digest"],
        "selected_source_files": inventory["files"],
        "recipe_sha256": sha(recipe.read_bytes()),
        "harness_sha256": sha(committed(repo, revision, SELF)),
        "registry_origin": "retained qualification wheel pool; public provenance/notice clearance not asserted",
    }
    result = owner.assembler(repo, revision).assemble_retained_distribution(
        spec, house, proof / "bundle", provenance, epoch=0
    )
    result.update(
        source_revision=revision,
        profile=PROFILE,
        source_files=len(inventory["files"]),
        local_packages=len(local),
        dependency_checks=checks,
        lock_sha256=sha((proof / "requirements.lock.txt").read_bytes()),
    )
    save(proof / "receipt.json", result)
    return result


def prepare(repo, proof, revision, tools, async_tools, refresh=False):
    """Export original test fixtures, not production source overlays."""
    fixtures = proof / "fixtures"
    if refresh:
        original = proof / "test-inputs.json"
        prior = json.loads(original.read_bytes())
        for row in prior["fixtures"]:
            if sha((fixtures / row["path"]).read_bytes()) != row["sha256"]:
                raise ValueError("prior_fixture_changed")
        history = proof / "harness-history"
        history.mkdir(exist_ok=True)
        shutil.copyfile(original, history / (sha(original.read_bytes()) + ".json"))
        shutil.copyfile(
            fixtures / SELF, history / (sha((fixtures / SELF).read_bytes()) + ".py")
        )
        fixture_revision = prior["revision"]
    else:
        fixtures.mkdir()
        fixture_revision = revision
    rows = []
    paths = (
        run(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                fixture_revision,
                "--",
                SDK,
                RUNTIME,
                FS,
            ],
            cwd=repo,
        )
        .decode()
        .splitlines()
    )
    for path in paths:
        body = committed(repo, revision if path == SELF else fixture_revision, path)
        target = fixtures / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        rows.append({"path": path, "sha256": sha(body)})
    for path, label in ((tools, "test-tools"), (async_tools, "async-test-tools")):
        if path.is_symlink() or any(
            p.is_symlink() or p.name.startswith("aware_") for p in path.rglob("*")
        ):
            raise ValueError("invalid_test_tool_input")
        if not refresh:
            shutil.copytree(
                path,
                proof / label,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
    if refresh:
        for path, digest in prior["tools"].items():
            if sha((proof / path).read_bytes()) != digest:
                raise ValueError("prior_tool_changed")
    save(
        proof / "test-inputs.json",
        {
            "revision": fixture_revision,
            "harness_revision": revision,
            "exclusions": {
                "test_explicit_rust_shadow_runs_beneath_workspace_lease_and_journal": "Optional Rust shadow/toolchain source qualification; not the selected Python command-mode capture"
            },
            "fixtures": rows,
            "tools": {
                p.relative_to(proof).as_posix(): sha(p.read_bytes())
                for label in ("test-tools", "async-test-tools")
                for p in (proof / label).rglob("*")
                if p.is_file()
            },
        },
    )


def installed(proof, physical=False, run_key="original"):
    import importlib.metadata

    record = json.loads((proof / "test-inputs.json").read_bytes())
    for row in record["fixtures"]:
        if sha((proof / "fixtures" / row["path"]).read_bytes()) != row["sha256"]:
            raise ValueError("fixture_changed")
    for path, digest in record["tools"].items():
        if sha((proof / path).read_bytes()) != digest:
            raise ValueError("test_tool_changed")
    site = (Path(sys.prefix) / "lib/python3.12/site-packages").resolve()
    for wheel in (proof / "wheelhouse").glob("*.whl"):
        with ZipFile(wheel) as archive:
            for member in archive.namelist():
                if member.endswith(("/", ".dist-info/RECORD")) or ".data/" in member:
                    continue
                if (site / member).read_bytes() != archive.read(member):
                    raise ValueError("installed_wheel_member_changed:" + member)
    if any(d.read_text("direct_url.json") for d in importlib.metadata.distributions()):
        raise ValueError("direct_url_install")
    sys.path[:0] = [
        str(proof / "test-tools"),
        str(proof / "async-test-tools"),
        *(str(proof / "fixtures" / root) for root in (SDK, RUNTIME, FS)),
    ]
    import pytest

    if not run_key.isalnum():
        raise ValueError("bounded_run_key_required")
    label = ("physical" if physical else "capture") + "-" + run_key
    xml = proof / (label + "-installed.xml")
    if xml.exists():
        raise ValueError("immutable_replay_receipt_exists")

    class Audit:
        def pytest_sessionfinish(self, session, exitstatus):
            modules = {}
            for name, module in tuple(sys.modules.items()):
                path = getattr(module, "__file__", None)
                if not name.startswith("aware_") or not path:
                    continue
                if name.startswith(FORBIDDEN) or not Path(
                    path
                ).resolve().is_relative_to(site):
                    raise ValueError("foreign_production_origin:" + name)
                modules[name] = str(Path(path).resolve())
            save(
                proof / (label + "-imports.json"),
                {"exit": exitstatus, "modules": modules},
            )

    return pytest.main(
        [
            "-q",
            "--noconftest",
            "--asyncio-mode=auto",
            "-p",
            "no:cacheprovider",
            "-p",
            "pytest_asyncio.plugin",
            "-k",
            " and ".join("not " + name for name in record.get("exclusions", {})) or "",
            "--junitxml=" + str(xml),
            *(str(proof / "fixtures" / p) for p in (PHYSICAL if physical else CASES)),
        ],
        plugins=[Audit()],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["build", "prepare", "refresh", "installed", "physical"]
    )
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--cli", type=Path)
    parser.add_argument("--pool", type=Path)
    parser.add_argument("--tools", type=Path)
    parser.add_argument("--async-tools", type=Path)
    parser.add_argument("--run-key", default="original")
    args = parser.parse_args()
    if args.command == "build":
        print(
            json.dumps(build(args.repo, args.proof, args.revision, args.cli, args.pool))
        )
    elif args.command in {"prepare", "refresh"}:
        prepare(
            args.repo,
            args.proof,
            args.revision,
            args.tools,
            args.async_tools,
            args.command == "refresh",
        )
    else:
        raise SystemExit(
            installed(args.proof, args.command == "physical", args.run_key)
        )
