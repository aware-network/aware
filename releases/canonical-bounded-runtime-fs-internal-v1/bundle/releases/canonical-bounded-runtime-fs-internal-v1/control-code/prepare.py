"""Bind a completed internal envelope to the original standalone bootstrap.

Producer preparation only: no installer, environment, activation or copied
envelope. The bundle view's zero-byte archive slot MUST be overmounted with
the exact original envelope read-only before any invocation.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
COHORT = Path("/tmp/aware-supplied-closure.iFqhwxWU")
ENVELOPE = COHORT / "envelope-source-audit"
ARCHIVE = "canonical-supplied-runtime-source-notice-review-v1.tar.gz"
ENVELOPE_SHA = "47e0f75e4cadf173c5ef0959462c3db50f7c8cd4f4a6575eedbda74b6a0aa5b2"
PAYLOAD_SHA = "0682db4d5bcd55c44444890073a3b7f25c2909e72679150312df7a8c50e61242"
PAYLOAD_MEMBER = "payload/aware-canonical-supplied-runtime-fs-internal-v1.tar.gz"
RELEASE_ID = "canonical-supplied-runtime-fs-internal-v1"
PRODUCT_REVISION = "b7b18c34a3b68e187ce11df21951ee46781c5e34"
RELEASE_REVISION = "5d9cca30980e6f3e29bef8df5d122c9afa601727"
STAGING_RELEASE_REVISION = "7154a91465c181cdce8433ea1502d98b20fc9008"
ORIGINAL = Path("/tmp/aware-refusal-public-layout.5NhdASt1/build-record-final/public")
DRIVER_SHA = "25cc2841319637e7b75bc434e7114f75c600035da194601e5d2427b1ba10f8a2"
VERIFIER_SHA = "032febe109cf145c65f5edaf14403fc58e7b4e93397535d0327e5ce1a65c6ca9"
OLD_RELEASE = "canonical-refusal-successor-fs-v1"
PACKAGE = (
    REPO / "workspaces/aware_network/modules/interface/libs/release_distribution/python"
)
LIMIT = 8 * 1024**2


def sha(body):
    return hashlib.sha256(body).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def pinned(path, digest):
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular_original_input_required")
    body = path.read_bytes()
    if sha(body) != digest:
        raise ValueError("original_input_digest_changed")
    return body


def _bytecode_free_original_driver(body):
    """Preserve original driver logic; suppress writes in both child probes."""
    substitutions = (
        (b'"-I",\n            "-c",', b'"-I",\n            "-B",\n            "-c",'),
        (b'"-I", "-m", "pip", "check"', b'"-I", "-B", "-m", "pip", "check"'),
    )
    result = body
    for before, after in substitutions:
        if result.count(before) != 1:
            raise ValueError("exact_original_driver_child_calls_required")
        result = result.replace(before, after)
    restored = result
    for before, after in reversed(substitutions):
        restored = restored.replace(after, before)
    if restored != body:
        raise ValueError("original_driver_child_conservation_required")
    ast.parse(result)
    return result


def driver_bytes(body):
    if sha(body) != DRIVER_SHA:
        raise ValueError("qualified_original_driver_required")
    replacements = {
        "e96946272b7812e833d41370ec5bfbba722f2f6f91720f994abcf9f407c975f7": ENVELOPE_SHA,
        "34c3c9d16d5bec1aba75add5ce03e55d32b25c828da78e878288b19453d6a51c": PAYLOAD_SHA,
        "canonical-refusal-successor-source-notice-review-v1.tar.gz": ARCHIVE,
        OLD_RELEASE: RELEASE_ID,
        "payload/aware-canonical-neutral-fs-internal-v1.tar.gz": PAYLOAD_MEMBER,
    }
    result = body
    for before, after in replacements.items():
        if result.count(before.encode()) != (2 if before == OLD_RELEASE else 1):
            raise ValueError("original_driver_coordinate_count_changed")
        result = result.replace(before.encode(), after.encode())
    # Inverse exact substitution proves no dispatch, cleanup or parser rewrite.
    restored = result
    for before, after in reversed(tuple(replacements.items())):
        restored = restored.replace(after.encode(), before.encode())
    if restored != body:
        raise ValueError("driver_behavior_changed")
    ast.parse(result)
    return result


def selected_runtime_inputs(selection):
    """Bind producer-supplied runtime coordinates; never execute or extract.

    Source/native/resource qualification remains external to this packaging
    port. A new runtime is explicit and cannot fall back to the old selection.
    """
    profile_keys = {
        "python_sha256",
        "python_version",
        "bootstrap_sha256",
        "archive_sha256",
        "roster_sha256",
    }
    if type(selection) is not dict or set(selection) != profile_keys | {
        "postimage_path",
        "inventory_path",
        "inventory_sha256",
    }:
        raise ValueError("complete_explicit_runtime_inputs_required")
    profile = {key: selection[key] for key in profile_keys}
    for key in profile_keys - {"python_version"} | {"inventory_sha256"}:
        value = selection[key]
        if (
            type(value) is not str
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("exact_runtime_input_digest_required")
    if (
        type(profile["python_version"]) not in (list, tuple)
        or list(profile["python_version"]) != [3, 12, 15]
        or any(type(v) is not int for v in profile["python_version"])
    ):
        raise ValueError("qualified_runtime_version_required")
    paths = [Path(selection[key]) for key in ("postimage_path", "inventory_path")]
    if any(not path.is_absolute() for path in paths):
        raise ValueError("absolute_runtime_input_paths_required")
    roster = pinned(paths[0], profile["roster_sha256"])
    inventory = json.loads(pinned(paths[1], selection["inventory_sha256"]))
    if inventory.get("archive_sha256") != profile["archive_sha256"]:
        raise ValueError("runtime_inventory_archive_mismatch")
    executable = [
        row
        for row in json.loads(roster)["entries"]
        if row["path"] == "python/bin/python3.12"
    ]
    original = [
        row for row in inventory["members"] if row["path"] == "python/bin/python3.12"
    ]
    if (
        len(executable) != 1
        or len(original) != 1
        or executable[0].get("kind") != "file"
        or original[0].get("kind") != "file"
        or executable[0].get("sha256") != profile["python_sha256"]
        or original[0].get("sha256") != profile["python_sha256"]
        or executable[0].get("size") != original[0].get("size")
    ):
        raise ValueError("runtime_interpreter_roster_mismatch")
    return roster, profile, selection["inventory_sha256"]


def prepare(
    output, *, staging_inputs=None, runtime_inputs=None, bytecode_free_driver=False
):
    if type(bytecode_free_driver) is not bool:
        raise ValueError("explicit_driver_bytecode_policy_required")
    if bytecode_free_driver and staging_inputs is None:
        raise ValueError("explicit_original_staging_driver_required")
    if output.parent != COHORT or output.exists() or output.is_symlink():
        raise ValueError("fresh_explicit_bootstrap_output_required")
    sys.path.insert(0, str(PACKAGE))
    from aware_release.install_distribution import whole_envelope as port
    from aware_release.install_distribution import whole_envelope_bootstrap as builder

    # Every production package byte is bound to the received complete successor.
    # Git is producer-only; this preparation does not enter the consumer rail.
    source_bindings = {}
    selected_release_revision = (
        RELEASE_REVISION
        if staging_inputs is None
        else staging_inputs.get("control_source_revision", STAGING_RELEASE_REVISION)
    )
    paths = [
        Path(port.__file__),
        Path(builder.__file__),
        Path(builder.__file__).with_name("whole_envelope_bootstrap_main.py"),
        PACKAGE / "LICENSE",
    ]
    for path in paths:
        relative = str(path.relative_to(REPO))
        original = subprocess.check_output(
            ["git", "show", selected_release_revision + ":" + relative], cwd=REPO
        )
        if path.read_bytes() != original:
            raise ValueError("original_bootstrap_source_changed:" + relative)
        source_bindings[relative] = sha(original)
    archive = ENVELOPE / ARCHIVE
    pinned(archive, ENVELOPE_SHA)
    if staging_inputs is None:
        driver = driver_bytes(pinned(ORIGINAL / "protocols/install.py", DRIVER_SHA))
    else:
        # The explicit successor uses exact authored original bytes, not a
        # vanished temporary public checkout. Historical preparation is intact.
        driver = pinned(
            Path(__file__).with_name("original_supplied_install_driver_v1.py"),
            "2841e7017b6bd83d986d3ed06c3190bf1312bce830862bbd7035ce873e055c9e",
        )
    staging_sources = None
    staging_record = None
    control_sources = {}
    if staging_inputs is not None:
        from aware_release.install_distribution import (
            preinstall_source_binding as loader,
        )
        from aware_release.install_distribution import (
            product_bootstrap_driver as renderer,
        )

        required = {
            "profile",
            "source_root",
            "plan_path",
            "plan_sha256",
            "maximum_outer_decoded_bytes",
            "maximum_inner_decoded_bytes",
        }
        extended = required | {"control_source_revision", "source_manifest"}
        if set(staging_inputs) not in (required, extended):
            raise ValueError("explicit_complete_staging_inputs_required")
        profiles = {
            renderer.PROFILE: (loader.STAGING_BOUND_PINS, renderer.SEEDS),
            renderer.COMPACT_PROFILE: (
                loader.COMPACT_STAGING_PINS,
                renderer.COMPACT_SEEDS,
            ),
            renderer.RECORDED_PROFILE: (
                loader.RECORDED_STAGING_PINS,
                renderer.RECORDED_SEEDS,
            ),
            renderer.SEALED_PROFILE: (
                loader.SEALED_STAGING_PINS,
                renderer.SEALED_SEEDS,
            ),
            renderer.BORROWED_PROFILE: (
                loader.BORROWED_STAGING_PINS,
                renderer.BORROWED_SEEDS,
            ),
            renderer.RECEIPT_PROFILE: (
                loader.RECEIPT_STAGING_PINS,
                renderer.RECEIPT_SEEDS,
            ),
            renderer.RETIRED_PROFILE: (
                loader.RETIRED_STAGING_PINS,
                renderer.RETIRED_SEEDS,
            ),
        }
        if staging_inputs["profile"] not in profiles:
            raise ValueError("explicit_qualified_staging_profile_required")
        pins, seed_pins = profiles[staging_inputs["profile"]]
        source_root = Path(staging_inputs["source_root"])
        if not source_root.is_absolute() or source_root.is_symlink():
            raise ValueError("explicit_original_source_root_required")
        staging_sources = {
            name: pinned(source_root / (name.replace(".", "/") + ".py"), digest)
            for name, (digest, _) in pins.items()
        }
        source_manifest = None
        if set(staging_inputs) == extended:
            revision = staging_inputs["control_source_revision"]
            if (
                type(revision) is not str
                or len(revision) != 40
                or any(c not in "0123456789abcdef" for c in revision)
            ):
                raise ValueError("exact_control_source_revision_required")
            source_manifest = staging_inputs["source_manifest"]
            if type(source_manifest) is not dict or set(source_manifest) != set(pins):
                raise ValueError("complete_control_source_provenance_required")
            prefixes = {
                "filesystem": "workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/",
                "release": "workspaces/aware_network/modules/interface/libs/release_distribution/python/aware_release/install_distribution/",
            }
            for name, body in staging_sources.items():
                family, module = name.split(".", 1)
                row = source_manifest[name]
                expected_path = prefixes[family] + module + ".py"
                if (
                    type(row) is not dict
                    or set(row) != {"source_path", "source_revision", "sha256", "bytes"}
                    or row["source_path"] != expected_path
                    or row["sha256"] != sha(body)
                    or row["bytes"] != len(body)
                ):
                    raise ValueError("control_source_provenance_mismatch:" + name)
                origin = row["source_revision"]
                if (
                    type(origin) is not str
                    or len(origin) != 40
                    or any(c not in "0123456789abcdef" for c in origin)
                ):
                    raise ValueError("exact_control_member_revision_required")
                actual = subprocess.check_output(
                    ["git", "show", origin + ":" + expected_path], cwd=REPO
                )
                if actual != body:
                    raise ValueError("committed_control_source_changed:" + name)
            for module in (loader, renderer):
                path = Path(module.__file__)
                relative = str(path.relative_to(REPO))
                if path.read_bytes() != subprocess.check_output(
                    ["git", "show", revision + ":" + relative], cwd=REPO
                ):
                    raise ValueError("qualified_control_source_changed:" + relative)
                source_bindings[relative] = sha(path.read_bytes())
        elif staging_inputs["profile"] in (
            renderer.SEALED_PROFILE,
            renderer.BORROWED_PROFILE,
            renderer.RETIRED_PROFILE,
            renderer.RECEIPT_PROFILE,
        ):
            raise ValueError("sealed_control_source_provenance_required")
        plan_path = Path(staging_inputs["plan_path"])
        if plan_path.stat().st_size > 4 * 1024**2:
            raise ValueError("bounded_staging_plan_required")
        plan_body = pinned(plan_path, staging_inputs["plan_sha256"])
        config = {
            "release_id": RELEASE_ID,
            "archive": ARCHIVE,
            "envelope_sha256": ENVELOPE_SHA,
            "payload_sha256": PAYLOAD_SHA,
            "payload_member": PAYLOAD_MEMBER,
            "envelope_size": archive.stat().st_size,
            "maximum_outer_decoded_bytes": staging_inputs[
                "maximum_outer_decoded_bytes"
            ],
            "maximum_inner_decoded_bytes": staging_inputs[
                "maximum_inner_decoded_bytes"
            ],
            "plan": json.loads(plan_body),
        }
        seeds = {
            "loader": pinned(Path(loader.__file__), seed_pins["loader"]),
            "observer": staging_sources["release.whole_envelope"],
            "driver": pinned(
                PACKAGE
                / "aware_release/install_distribution/product_driver_staging.py",
                seed_pins["driver"],
            ),
        }
        driver = renderer.render_original_driver(
            driver,
            seeds=seeds,
            source_bodies=staging_sources,
            staging=config,
            profile=staging_inputs["profile"],
        )
        if bytecode_free_driver:
            driver = _bytecode_free_original_driver(driver)
        source_bindings[str(Path(renderer.__file__).relative_to(REPO))] = sha(
            Path(renderer.__file__).read_bytes()
        )
        staging_record = {
            "profile": staging_inputs["profile"],
            "plan_sha256": sha(plan_body),
            "original_seed_sha256": {name: sha(body) for name, body in seeds.items()},
            "source_capsule": {
                name: {"sha256": sha(body), "bytes": len(body)}
                for name, body in staging_sources.items()
            },
            "candidate_partition_capacity": "unqualified",
            "memory_fit": "unqualified",
        }
        if source_manifest is not None:
            staging_record["control_source_revision"] = staging_inputs[
                "control_source_revision"
            ]
            staging_record["source_manifest"] = source_manifest
            control_sources = {
                "loader.py": seeds["loader"],
                "observer.py": seeds["observer"],
                "driver.py": seeds["driver"],
                "renderer.py": Path(renderer.__file__).read_bytes(),
                "bootstrap_builder.py": Path(builder.__file__).read_bytes(),
                "prepare.py": Path(__file__).read_bytes(),
            }
    verifier = pinned(
        ORIGINAL / "releases" / OLD_RELEASE / "archive_verifier.py"
        if staging_inputs is None
        else Path(__file__).with_name("original_archive_verifier_v1.py"),
        VERIFIER_SHA,
    )
    artifact = port.WholeEnvelopeArtifact(
        release_id=RELEASE_ID,
        product_revision=PRODUCT_REVISION,
        envelope_name=ARCHIVE,
        envelope_size=archive.stat().st_size,
        envelope_sha256=ENVELOPE_SHA,
        payload_sha256=PAYLOAD_SHA,
        driver_sha256=sha(driver),
        verifier_sha256=VERIFIER_SHA,
        runtime_mode="supplied",
    )
    # Archive inventory and original postimage roster have distinct schemas.
    # Carry the latter as a pinned small bootstrap attachment, not a relabelled
    # archive inventory or replacement native materialization receipt.
    if runtime_inputs is None:
        roster = pinned(
            Path("/tmp/aware-runtime-policy.mJG10g2S/qualified/postimage.json"),
            "9c10c9b3953fdbf84c928bcf88806a59e9a23b9f530db95d5e0c22af03f4123f",
        )
        executable = next(
            row
            for row in json.loads(roster)["entries"]
            if row["path"] == "python/bin/python3.12"
        )
        runtime = {
            "python_sha256": executable["sha256"],
            "python_version": [3, 12, 15],
            "bootstrap_sha256": "39ee0e879d313b37a0b239509a220d1d163667d10c0e72d21bf432485f46493a",
            "archive_sha256": "5d546fc004fc2435fa142eb8f42ed8de5eb4725963dc22f7e6671014a80eb560",
            "roster_sha256": sha(roster),
        }
        inventory_sha256 = (
            "1fc54f4a96adfdd2c3361fcc251e6a80c5aeecd92e8058845c3295bde23dab8f"
        )
    else:
        roster, runtime, inventory_sha256 = selected_runtime_inputs(runtime_inputs)
    output.mkdir(mode=0o700)
    with (output / "runtime-postimage.json").open("xb") as stream:
        stream.write(roster)
    release = output / "bundle/releases" / RELEASE_ID
    release.mkdir(parents=True)
    if staging_sources is not None:
        for name, body in staging_sources.items():
            destination = release / "driver-sources" / (name.replace(".", "/") + ".py")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(body)
        if staging_record is not None and "source_manifest" in staging_record:
            with (release / "CONTROL-SOURCE.json").open("xb") as stream:
                stream.write(
                    encoded(
                        {
                            "profile": staging_record["profile"],
                            "control_source_revision": staging_record[
                                "control_source_revision"
                            ],
                            "members": staging_record["source_manifest"],
                            "role": "bootstrap-control-source;not-package-catalog-or-authority",
                        }
                    )
                )
            for label, relative in (
                (
                    "FILESYSTEM-LICENSE",
                    "workspaces/aware_kernel/modules/filesystem/libs/file_system/python/LICENSE",
                ),
                (
                    "RELEASE-LICENSE",
                    "workspaces/aware_network/modules/interface/libs/release_distribution/python/LICENSE",
                ),
            ):
                body = subprocess.check_output(
                    [
                        "git",
                        "show",
                        staging_inputs["control_source_revision"] + ":" + relative,
                    ],
                    cwd=REPO,
                )
                with (release / label).open("xb") as stream:
                    stream.write(body)
            for name, body in control_sources.items():
                destination = release / "control-code" / name
                destination.parent.mkdir(exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(body)
    (output / "bundle/protocols").mkdir()
    with (output / "bundle/protocols/install.py").open("xb") as stream:
        stream.write(driver)
    with (release / "archive_verifier.py").open("xb") as stream:
        stream.write(verifier)
    # Mount target, explicitly not a candidate archive outside the private view.
    with (release / ARCHIVE).open("xb"):
        pass
    for name in ("bootstrap-a.pyz", "bootstrap-b.pyz"):
        builder.build_supplied_runtime_bootstrap(
            artifact=artifact,
            runtime_profile=runtime,
            source_revision=selected_release_revision,
            expected_port_sha256=sha(paths[0].read_bytes()),
            expected_main_sha256=sha(paths[2].read_bytes()),
            expected_license_sha256=sha(paths[3].read_bytes()),
            output=output / name,
        )
    if (output / "bootstrap-a.pyz").read_bytes() != (
        output / "bootstrap-b.pyz"
    ).read_bytes():
        raise ValueError("repeat_small_bootstrap_changed")
    with zipfile.ZipFile(output / "bootstrap-a.pyz") as bundle:
        if set(bundle.namelist()) != {
            "__main__.py",
            "whole_envelope.py",
            "LICENSE",
            "release.json",
        }:
            raise ValueError("original_four_member_bootstrap_required")
        if bundle.read("whole_envelope.py") != paths[0].read_bytes():
            raise ValueError("original_port_bytes_changed")
        descriptor = json.loads(bundle.read("release.json"))
    result = {
        "schema": "aware.supplied-runtime.bootstrap-preparation.v1",
        "preparer_sha256": sha(Path(__file__).read_bytes()),
        "artifact": asdict(artifact),
        "supplied_runtime": runtime,
        "runtime_postimage_attachment": "runtime-postimage.json",
        "runtime_archive_inventory_sha256": inventory_sha256,
        "source_revision": selected_release_revision,
        "source_bindings": source_bindings,
        "descriptor": descriptor,
        "payload_member": PAYLOAD_MEMBER,
        "required_readonly_archive_bind": [
            str(archive),
            "/bundle/releases/" + RELEASE_ID + "/" + ARCHIVE,
        ],
        "bundle_view": str(output / "bundle"),
        "archive_slot_is_placeholder": True,
        "repeat_small_builds_equal": True,
        "new_installations": 0,
        "new_envelope_copies": 0,
        "source_notice_disclosure_acceptance": "pending_candidate_specific_review",
        "authorizes_dispatch": False,
    }
    if staging_record is not None:
        result["bounded_staging"] = staging_record
    result["files"] = {
        str(path.relative_to(output)): {
            "sha256": sha(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    total = sum(row["bytes"] for row in result["files"].values())
    if total + len(encoded(result)) > LIMIT:
        raise ValueError("small_bootstrap_output_budget_exceeded")
    with (output / "result.json").open("xb") as stream:
        stream.write(encoded(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--staging-input", type=Path)
    args = parser.parse_args()
    staging_inputs = None
    if args.staging_input is not None:
        if args.staging_input.is_symlink() or args.staging_input.stat().st_size > 16384:
            raise ValueError("bounded_explicit_staging_inputs_required")
        staging_inputs = json.loads(args.staging_input.read_bytes())
    result = prepare(args.out, staging_inputs=staging_inputs)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
