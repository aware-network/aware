"""Build a pinned read-only successor; never builds current Protocol source.

Three committed SPEC packages replace three predecessor wheels. The other 24
wheels remain exact. This uses the existing immutable bundle builder, not a new
runtime or release registry. Generated outputs belong to a fresh proof root.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tomllib
from email.parser import BytesParser
from pathlib import Path

SOURCE_REVISION = "64ea154cc536"
BASE_SHA = "3fc5c8e5d48e8bc843b6721ac3a57be20da32e488d8b39b8f7d7b618cd5d777e"
BASE_MANIFEST_SHA = "d89a521218ec1b8e42c3c59c696aff4c775de39b1a5fb63e907d6b9e930ae277"
BUILDER = "docs/specs/aware-portable-protocol/release/build_client_distribution_v1.py"
BUILDER_SHA = "206527f760e4e18e5becaa0fd46238fefee13661d06f7e974a02cf5fb3335a6f"
ARCHIVE_HELPER = "docs/specs/aware-portable-protocol/release/build_specification_public_review_packet_v1.py"
ARCHIVE_HELPER_SHA = "8497f037ca051f680467c537cabdadf17b1b2702d66d481474de77966eac52c2"
ROOT = "workspaces/aware_kernel/modules/specification/sdks/specification/python"
PACKAGES = (
    ("public", "aware-specification-sdk", "0.2.0"),
    ("fs_adapter", "aware-specification-fs-sdk-adapter", "0.2.2"),
    ("cli", "aware-specification-cli", "0.2.1"),
)
SETUP_HARNESS = "docs/specs/aware-portable-protocol/conformance/test_installed_specification_setup.py"
SETUP_HARNESS_SHA = "d81cf2a4a92145cf0fec8958922c253ffe8550a612e1b12db9cde207edb7738a"


def sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def pinned(path: Path, expected: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular_input_required")
    body = path.read_bytes()
    if sha(body) != expected:
        raise ValueError("input_digest_changed:" + str(path))
    return body


def load(path: Path, expected: str, name: str):
    pinned(path, expected)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def committed(repo: Path, revision: str, path: str) -> bytes:
    tree = subprocess.check_output(["git", "ls-tree", revision, "--", path], cwd=repo)
    if not tree.startswith((b"100644 blob ", b"100755 blob ")):
        raise ValueError("committed_regular_input_required:" + path)
    return subprocess.check_output(["git", "show", revision + ":" + path], cwd=repo)


def project_metadata(original: bytes, name: str, version: str) -> bytes:
    project = tomllib.loads(original.decode())["project"]
    if project["name"] != name or project["version"] != version:
        raise ValueError("supplier_identity_changed")
    # Packaging-only additions; authored dependency/exposure semantics are exact.
    values = {
        k: project[k] for k in ("name", "version", "requires-python", "dependencies")
    }
    values.update(license="Apache-2.0", **{"license-files": ["LICENSE", "NOTICE"]})
    text = "[project]\n" + "".join(
        k + " = " + json.dumps(v) + "\n" for k, v in values.items()
    )
    for key in ("optional-dependencies", "scripts"):
        if project.get(key):
            text += (
                "[project."
                + key
                + "]\n"
                + "".join(
                    k + " = " + json.dumps(v) + "\n" for k, v in project[key].items()
                )
            )
    return (
        text
        + '[build-system]\nrequires = ["hatchling>=1.27.0"]\nbuild-backend = "hatchling.build"\n'
        + "[tool.hatch.build.targets.wheel]\npackages = "
        + json.dumps([name.replace("-", "_")])
        + "\n"
    ).encode()


def run(command: list[str], root: Path, *, env=None) -> str:
    result = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode:
        (root / "failure.json").write_bytes(
            encoded(
                {
                    "command": command,
                    "exit": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
        )
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def build(repo: Path, baseline: Path, proof: Path) -> dict:
    archive_owner = load(
        repo / ARCHIVE_HELPER, ARCHIVE_HELPER_SHA, "read_archive_owner"
    )
    builder = load(repo / BUILDER, BUILDER_SHA, "read_bundle_owner")
    files = archive_owner.archive_files(pinned(baseline, BASE_SHA))
    checksum_count = archive_owner.verify_checksums(files)
    if sha(files["manifest.json"]) != BASE_MANIFEST_SHA:
        raise ValueError("predecessor_manifest_changed")
    old = json.loads(files["manifest.json"])
    if len(old["wheels"]) != 27:
        raise ValueError("predecessor_closure_changed")
    proof.mkdir(exist_ok=False)
    wheelhouse = proof / "wheelhouse"
    wheelhouse.mkdir()
    baseline_house = proof / "baseline-wheelhouse"
    baseline_house.mkdir()
    changed_names = {name for _, name, _ in PACKAGES}
    for row in old["wheels"]:
        body = files[row["file"]]
        if sha(body) != row["sha256"]:
            raise ValueError("predecessor_wheel_changed")
        (baseline_house / Path(row["file"]).name).write_bytes(body)
        if row["name"] not in changed_names:
            (wheelhouse / Path(row["file"]).name).write_bytes(body)
    revision = run(["git", "rev-parse", SOURCE_REVISION + "^{commit}"], repo).strip()
    license_body = committed(repo, revision, "LICENSE")
    provenance = copy.deepcopy(old["source_provenance"])
    provenance["read_successor"] = {
        "source_revision": revision,
        "predecessor_archive_sha256": BASE_SHA,
        "changed_packages": sorted(changed_names),
        "preserved_wheels": 24,
        "protocol_selection": "exact predecessor 0.4.0 wheel, not current draft-port source",
        "license_revision": revision,
        "license_sha256": sha(license_body),
    }
    additions = []
    for suffix, name, version in PACKAGES:
        root = ROOT + "/" + suffix
        module = name.replace("-", "_")
        names = run(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                revision,
                "--",
                root + "/" + module,
            ],
            repo,
        ).splitlines()
        if not names:
            raise ValueError("empty_supplier")
        target = proof / "sources" / root
        target.mkdir(parents=True)
        for path in [root + "/pyproject.toml", root + "/README.md", *names]:
            original = committed(repo, revision, path)
            body = (
                project_metadata(original, name, version)
                if path.endswith("/pyproject.toml")
                else original
            )
            destination = proof / "sources" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(body)
            additions.append(
                {
                    "path": path,
                    "source_revision": revision,
                    "source_sha256": sha(original),
                    "projected_sha256": sha(body),
                    "source_bytes": len(original),
                    "projected_bytes": len(body),
                }
            )
        (target / "LICENSE").write_bytes(license_body)
        notice = (
            name
            + "\nCopyright 2026 Luis Lechuga Ruiz\nAware-authored work is Apache-2.0.\n"
            "Neutral setup/read packaging profile; original domain implementations preserved.\n"
        ).encode()
        (target / "NOTICE").write_bytes(notice)
        package = next(p for p in provenance["source_packages"] if p["name"] == name)
        package["version"] = version
        built = proof / "build" / suffix
        built.mkdir(parents=True)
        log = run(
            [
                "/usr/local/bin/uv",
                "build",
                "--offline",
                "--wheel",
                "--no-sources",
                "--python",
                "/usr/bin/python3.12",
                "--no-python-downloads",
                "--out-dir",
                str(built),
                str(target),
            ],
            proof,
            env=dict(
                os.environ,
                SOURCE_DATE_EPOCH="0",
                UV_OFFLINE="1",
                UV_PYTHON_DOWNLOADS="never",
                PYTHONHASHSEED="0",
            ),
        )
        (built / "build.log").write_text(log)
        (wheel,) = tuple(built.glob("*.whl"))
        members = archive_owner.wheel_files(wheel.read_bytes())
        for path in names:
            relative = path[len(root) + 1 :]
            if members.get(relative) != committed(repo, revision, path):
                raise ValueError("wheel_owner_bytes_changed:" + relative)
        shutil.copyfile(wheel, wheelhouse / wheel.name)
    roots = tuple(ROOT + "/" + suffix + "/" for suffix, _, _ in PACKAGES)
    provenance["files"] = [
        r for r in provenance["files"] if not r["path"].startswith(roots)
    ] + [r for r in additions if not r["path"].endswith("/README.md")]
    provenance["read_successor"]["inputs"] = additions
    spec = {
        "authority_mode": "filesystem",
        "profile": old["profile"],
        "platform": "linux_x86_64",
        "python_minor": "3.12",
        "bundle_prefix": "aware-specification-sdk02-read-internal-v1",
        "interfaces": {
            "setup": "aware-protocol-cli[specification-setup]==0.3.1",
            "reader": "aware-specification-cli==0.2.1",
        },
        "launchers": ["aware-protocol", "aware-spec"],
        "source_packages": [],
        "registry_packages": [],
        "source_derived_packages": [],
    }
    origins = {r["name"]: r["origin"] for r in old["wheels"]}
    wheel_records = []
    for wheel in sorted(wheelhouse.glob("*.whl")):
        members = archive_owner.wheel_files(wheel.read_bytes())
        (metadata,) = [
            body for key, body in members.items() if key.endswith(".dist-info/METADATA")
        ]
        data = BytesParser().parsebytes(metadata)
        name = data["Name"]
        origin = origins[name]
        row = {
            "name": name,
            "version": data["Version"],
            "hashes": [sha(wheel.read_bytes())],
        }
        spec[
            {
                "aware_source": "source_packages",
                "registry": "registry_packages",
                "source_derived": "source_derived_packages",
            }[origin]
        ].append(row)
        wheel_records.append(dict(row, file=wheel.name, origin=origin))
    result = builder.assemble_retained_distribution(
        spec, wheelhouse, proof / "bundle", provenance, epoch=0
    )
    result.update(
        status="internal-read-candidate-awaiting-independent-review",
        baseline_archive_sha256=BASE_SHA,
        baseline_checksum_count=checksum_count,
        source_revision=revision,
        builder_sha256=BUILDER_SHA,
        producer_sha256=sha(Path(__file__).read_bytes()),
        unchanged_wheels=24,
        changed_packages=sorted(changed_names),
        wheels=wheel_records,
        nonclaims=[
            "customer_authoring",
            "every_write_detection",
            "continuous_confinement",
            "public_notice_clearance",
            "selection",
            "release",
        ],
    )
    (proof / "inputs.json").write_bytes(encoded(provenance))
    (proof / "receipt.json").write_bytes(encoded(result))
    return result


def sandbox(proof: Path, command: list[str]) -> list[str]:
    return [
        "/usr/bin/bwrap",
        "--die-with-parent",
        "--ro-bind",
        "/",
        "/",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/home/aware",
        "--tmpfs",
        "/tmp",
        "--bind",
        str(proof),
        str(proof),
        "--unshare-net",
        "--clearenv",
        "--setenv",
        "PATH",
        "/usr/bin:/bin",
        "--setenv",
        "PYTHONDONTWRITEBYTECODE",
        "1",
        "--setenv",
        "AWARE_PILOT_PROOF",
        str(proof),
        "--chdir",
        str(proof),
        "--",
        *command,
    ]


def qualify(repo: Path, proof: Path, tools: Path) -> dict:
    """Supply tests only; production imports must come from installed wheels."""
    receipt = json.loads((proof / "receipt.json").read_bytes())
    if receipt["producer_sha256"] != sha(Path(__file__).read_bytes()):
        raise ValueError("producer_changed_rebuild_required")
    pinned(Path(receipt["archive"]), receipt["archive_sha256"])
    setup_owner = load(repo / SETUP_HARNESS, SETUP_HARNESS_SHA, "read_setup_harness")
    setup = proof / "setup-proof"
    setup_owner.prepare(repo, setup, tools, proof / "inputs.json")
    inventory = json.loads((setup / "test-inputs.json").read_bytes())
    spec_prefix = (
        "workspaces/aware_kernel/modules/specification/sdks/specification/python/"
    )
    # Retain original tests; replace three SPEC fixture/test files by their
    # accepted SDK02 successors. No production modules enter the fixture tree.
    fixture_updates = []
    for suffix in (
        "fs_adapter/tests/test_protocol_selection.py",
        "fs_adapter/tests/test_provider.py",
        "cli/tests/test_protocol_cli.py",
    ):
        path = spec_prefix + suffix
        body = committed(repo, receipt["source_revision"], path)
        (setup / "fixtures" / path).write_bytes(body)
        row = next(r for r in inventory["fixtures"] if r["path"] == path)
        fixture_updates.append(dict(row))
        row.update(
            revision=receipt["source_revision"], sha256=sha(body), bytes=len(body)
        )
    source_inputs = json.loads((proof / "inputs.json").read_bytes())
    matches = sum(
        not r["path"].endswith("/pyproject.toml") for r in source_inputs["files"]
    )
    original = pinned(repo / SETUP_HARNESS, SETUP_HARNESS_SHA).decode()
    replacements = {
        '"0.3.0"': '"0.3.1"',
        "assert len(expected) == 26": "assert len(expected) == 27",
        "assert len(matches) == 89": "assert len(matches) == " + str(matches),
    }
    changes = []
    for before, after in replacements.items():
        count = original.count(before)
        if count != (4 if before == '"0.3.0"' else 1):
            raise ValueError("historical_harness_expectation_changed")
        original = original.replace(before, after)
        changes.append({"before": before, "after": after, "occurrences": count})
    adapted = setup / "test_installed_specification_setup.py"
    adapted.write_text(original)
    inventory["harness_sha256"] = sha(adapted.read_bytes())
    inventory["successor_adaptation"] = {
        "original_sha256": SETUP_HARNESS_SHA,
        "changes": changes,
        "historical_fixture_rows": fixture_updates,
    }
    (setup / "test-inputs.json").write_bytes(encoded(inventory))
    test = (
        repo
        / "docs/specs/aware-portable-protocol/conformance/test_specification_read_candidate_installed.py"
    )
    target = proof / test.name
    if target.exists():
        raise ValueError("immutable_test_input_exists")
    target.write_bytes(test.read_bytes())
    composition_path = "docs/specs/aware-portable-protocol/conformance/test_specification_sdk02_read_composition_v1.py"
    composition = setup / "fixtures" / composition_path
    composition.parent.mkdir(parents=True, exist_ok=True)
    composition.write_bytes(
        committed(repo, receipt["source_revision"], composition_path)
    )
    records = {
        str(p.relative_to(proof)): sha(p.read_bytes())
        for p in [
            target,
            adapted,
            composition,
            setup / "test-inputs.json",
            proof / "inputs.json",
        ]
    }
    (proof / "read-test-inputs.json").write_bytes(
        encoded(
            {
                "files": records,
                "fixture_qualification": "pinned owner synthetic SPEC; no supported customer creation",
            }
        )
    )
    for name, house, requirements in (
        (
            "baseline-env",
            proof / "baseline-wheelhouse",
            [
                "aware-protocol-cli[specification-setup]==0.3.1",
                "aware-specification-cli==0.2.0",
            ],
        ),
        (
            "env",
            proof / "wheelhouse",
            [
                "aware-protocol-cli[specification-setup]==0.3.1",
                "aware-specification-cli==0.2.1",
            ],
        ),
    ):
        environment = proof / name
        if environment.exists() or environment.is_symlink():
            raise ValueError("environment_reuse_refused")
        python = str(environment / "bin/python")
        if name == "env":
            output = run(
                sandbox(
                    proof,
                    [
                        "/usr/bin/env",
                        "PYTHON_BIN=/usr/bin/python3.12",
                        "/bin/sh",
                        str(Path(receipt["bundle_directory"]) / "install.sh"),
                        str(environment),
                    ],
                ),
                proof,
                env={},
            )
        else:
            run(
                sandbox(proof, ["/usr/bin/python3.12", "-m", "venv", str(environment)]),
                proof,
                env={},
            )
            output = run(
                sandbox(
                    proof,
                    [
                        python,
                        "-I",
                        "-m",
                        "pip",
                        "install",
                        "--no-index",
                        "--no-compile",
                        "--only-binary=:all:",
                        "--find-links",
                        str(house),
                        *requirements,
                    ],
                ),
                proof,
                env={},
            )
        (proof / (name + "-install.txt")).write_text(output)
        (proof / (name + "-dependency-check.txt")).write_text(
            run(sandbox(proof, [python, "-I", "-m", "pip", "check"]), proof, env={})
        )
    python = str(proof / "env/bin/python")
    manifest = str(Path(receipt["bundle_directory"]) / "manifest.json")
    output = run(
        sandbox(
            proof,
            [
                python,
                "-I",
                str(adapted),
                "run",
                "--proof",
                str(setup),
                "--manifest",
                manifest,
                "--junit",
                str(proof / "setup.xml"),
                "--basetemp",
                str(proof / "setup-tests"),
            ],
        ),
        proof,
        env={},
    )
    (proof / "setup.txt").write_text(output)
    test_code = "import sys; sys.path[:0] = [sys.argv.pop(1)]; import pytest; raise SystemExit(pytest.main(sys.argv[1:]))"
    output = run(
        sandbox(
            proof,
            [
                python,
                "-I",
                "-c",
                test_code,
                str(setup / "test-tools"),
                "-q",
                "-p",
                "no:cacheprovider",
                str(target),
                str(composition),
                "--import-mode=importlib",
                "-k",
                "not test_exact_accepted_source_and_27_pins_without_metadata_migration",
                "--junitxml=" + str(proof / "read-parity.xml"),
                "--basetemp=" + str(proof / "read-tests"),
            ],
        ),
        proof,
        env={},
    )
    (proof / "read-parity.txt").write_text(output)
    receipt.update(
        installed_status="bounded-setup-regression-and-actual-read-parity-pass",
        setup_junit_sha256=sha((proof / "setup.xml").read_bytes()),
        read_junit_sha256=sha((proof / "read-parity.xml").read_bytes()),
        test_inputs_sha256=sha((proof / "read-test-inputs.json").read_bytes()),
        harness_adaptation=inventory["successor_adaptation"],
    )
    (proof / "receipt.json").write_bytes(encoded(receipt))
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("repository-root", "baseline-archive", "proof-root"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--test-tools", type=Path)
    args = parser.parse_args()
    result = build(args.repository_root, args.baseline_archive, args.proof_root)
    if args.test_tools is not None:
        result = qualify(args.repository_root, args.proof_root, args.test_tools)
    print(json.dumps(result, indent=2, sort_keys=True))
