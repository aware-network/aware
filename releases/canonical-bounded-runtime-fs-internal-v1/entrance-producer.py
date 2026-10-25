"""Bind one actual successor pair to the unchanged original bootstrap producer.

Data-coordinate adapter only. No copied installer, extractor, activation,
runtime/environment creation or consumer evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
ENVELOPE = Path("/tmp/aware-bounded-envelope._wsj_guc")
ARCHIVE = "aware-canonical-bounded-runtime-source-notice-v1.tar.gz"
ENVELOPE_SHA = "35973999e92199958921ea9e45419361e8d2a2bf31fda57a25884d08128e92cc"
PAYLOAD_SHA = "af84f17ea5572b76dc262834e6e844fde068921ab6afbbe8a2e3ad21ffc52828"
PLAN_SHA = "3b6f94ae507df06cec34de223cdbdf6c7fba9a24759d58735202cdfec5cc1a23"
CAPSULE = Path("/tmp/aware-release017-artifacts.ZFxx2X/capsule/sources")
RELEASE_ID = "canonical-bounded-runtime-fs-internal-v1"
SPECIFICATION_EXAMPLE_MEMBER = "examples/prepare_draft_input.py"
SPECIFICATION_EXAMPLE_SOURCE = (
    "workspaces/aware_kernel/modules/specification/sdks/specification/python/cli/"
    + SPECIFICATION_EXAMPLE_MEMBER
)
SPECIFICATION_EXAMPLE_REVISION = "d09a66d78c9a537cca7ab31730fb5f9aef415add"
SPECIFICATION_EXAMPLE_SHA256 = (
    "21e1bea900ae75e47be2ff889e87d514cba08ba9f325681dcc0ee3f1df68bcb5"
)
SPECIFICATION_EXAMPLE_SIZE = 2081


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular_bound_input_required")
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for body in iter(lambda: stream.read(65536), b""):
            result.update(body)
    return result.hexdigest()


def prepare(root, *, selection=None):
    if (
        root.parent != Path("/tmp")
        or not root.name.startswith("aware-bounded-bootstrap.")
        or root.is_symlink()
        or (root.exists() and (not root.is_dir() or any(root.iterdir())))
    ):
        raise ValueError("fresh_explicit_small_output_required")
    envelope, archive, envelope_sha, payload_sha, plan_sha, capsule = (
        ENVELOPE,
        ARCHIVE,
        ENVELOPE_SHA,
        PAYLOAD_SHA,
        PLAN_SHA,
        CAPSULE,
    )
    release_id, product_revision = (
        RELEASE_ID,
        "d868aeda46ccc5c442c6314f96c89df3689a5564",
    )
    source_manifest = None
    borrowed = False
    if selection is not None:
        if type(selection) is not dict or set(selection) not in (
            {
                "envelope_root",
                "archive_name",
                "envelope_sha256",
                "payload_sha256",
                "plan_sha256",
                "source_root",
                "source_revision",
                "release_id",
                "product_revision",
            },
            {
                "envelope_root",
                "archive_name",
                "envelope_sha256",
                "payload_sha256",
                "plan_sha256",
                "source_root",
                "source_revision",
                "release_id",
                "product_revision",
                "control_profile",
                "source_manifest",
            },
        ):
            raise ValueError("complete_explicit_control_selection_required")
        borrowed = "control_profile" in selection
        if borrowed and selection["control_profile"] not in (
            "aware.release.original-bootstrap-borrowed-directory-staging.v1",
            "aware.release.original-bootstrap-retired-member-staging.v1",
            "aware.release.original-bootstrap-observation-receipts.v1",
        ):
            raise ValueError("explicit_qualified_control_profile_required")
        envelope, capsule = (
            Path(selection["envelope_root"]),
            Path(selection["source_root"]),
        )
        archive, envelope_sha, payload_sha, plan_sha = (
            selection[k]
            for k in (
                "archive_name",
                "envelope_sha256",
                "payload_sha256",
                "plan_sha256",
            )
        )
        if (
            not envelope.is_absolute()
            or not capsule.is_absolute()
            or Path(archive).name != archive
        ):
            raise ValueError("absolute_source_roots_and_simple_archive_name_required")
        release_id, product_revision = (
            selection["release_id"],
            selection["product_revision"],
        )
        revision = selection["source_revision"]
        if (
            type(revision) is not str
            or len(revision) != 40
            or any(c not in "0123456789abcdef" for c in revision)
        ):
            raise ValueError("exact_control_source_revision_required")
        baseline = Path("/tmp/aware-release017-artifacts.ZFxx2X/capsule/capsule.json")
        if (
            digest(baseline)
            != "282f8961698037f76d4867b5e770c315d5c8e41401a1200a07c5a59b71a6074d"
        ):
            raise ValueError("qualified_original_capsule_manifest_changed")
        source_manifest = json.loads(baseline.read_bytes())["members"]
        overrides = {
            "filesystem._staging_guard_history",
            "filesystem.staging_root",
            "filesystem.staging_member",
            "filesystem.staging_complete",
            "filesystem.confined_entry",
            "release.product_staging",
        }
        source_manifest["filesystem._staging_guard_history"] = {
            "source_path": "workspaces/aware_kernel/modules/filesystem/libs/file_system/python/aware_file_system/_staging_guard_history.py"
        }
        source_manifest = {
            name: {
                "source_path": row["source_path"],
                "source_revision": revision
                if name in overrides
                else row["source_revision"],
                "sha256": digest(capsule / (name.replace(".", "/") + ".py")),
                "bytes": (capsule / (name.replace(".", "/") + ".py")).stat().st_size,
            }
            for name, row in source_manifest.items()
        }
    if borrowed:
        source_manifest = selection["source_manifest"]
        expected_members = (
            38
            if selection["control_profile"]
            == "aware.release.original-bootstrap-observation-receipts.v1"
            else 37
        )
        if (
            type(source_manifest) is not dict
            or len(source_manifest) != expected_members
        ):
            raise ValueError("complete_control_member_provenance_required")
    if digest(envelope / archive) != envelope_sha:
        raise ValueError("exact_envelope_changed")
    if digest(envelope / "staging-plan.json") != plan_sha:
        raise ValueError("exact_staging_plan_changed")
    path = (
        REPO
        / "docs/specs/aware-portable-protocol/release/prepare_supplied_runtime_bootstrap_v1.py"
    )
    if digest(path) != (
        "c33c49b8212786a0cc32c3276b85734ceb7e31a8238099aeb15920da8b41b845"
        if borrowed
        and selection["control_profile"]
        == "aware.release.original-bootstrap-observation-receipts.v1"
        else "aab5a9038c96e86dd6e5446bd0ce2cbdc528c70c408eb752451d9f63db809fe0"
        if borrowed
        else "3e1ab5f6f1efaf37de28d7e89d3c499e9efbec27ccd1123190243bc615ef038d"
        if selection is not None
        else "16d0f58c456356d282cb679face73a3c01e76e48dc84b20b11946f54df267bf9"
    ):
        raise ValueError("original_preparer_changed")
    spec = importlib.util.spec_from_file_location(
        "bounded_original_bootstrap_preparer", path
    )
    if spec is None or spec.loader is None:
        raise ValueError("original_bootstrap_preparer_unavailable")
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    coordinates = {
        "COHORT": root,
        "ENVELOPE": envelope,
        "ARCHIVE": archive,
        "ENVELOPE_SHA": envelope_sha,
        "PAYLOAD_SHA": payload_sha,
        "PAYLOAD_MEMBER": "payload/aware-canonical-bounded-install-fs-internal-v1.tar.gz",
        "RELEASE_ID": release_id,
        # Producer integration checkpoint, not a claim of public availability
        # or single-revision source for this explicitly composite candidate.
        "PRODUCT_REVISION": product_revision,
    }
    for key, value in coordinates.items():
        setattr(original, key, value)
    root.mkdir(mode=0o700, exist_ok=True)
    staging = {
        "profile": selection["control_profile"]
        if borrowed
        else "aware.release.original-bootstrap-sealed-staging.v1"
        if selection is not None
        else "aware.release.original-bootstrap-bounded-staging.v1",
        "source_root": str(capsule),
        "plan_path": str(envelope / "staging-plan.json"),
        "plan_sha256": plan_sha,
        "maximum_outer_decoded_bytes": 512 * 1024**2,
        "maximum_inner_decoded_bytes": 64 * 1024**2,
    }
    if source_manifest is not None:
        staging.update(
            control_source_revision=selection["source_revision"],
            source_manifest=source_manifest,
        )
    result = original.prepare(root / "prepared", staging_inputs=staging)
    return {
        "schema": "aware.actual-bounded-bootstrap.preparation.v1",
        "adapter_sha256": digest(Path(__file__)),
        "original_preparer_sha256": digest(path),
        "coordinate_bindings": {key: str(value) for key, value in coordinates.items()},
        "staging_inputs": staging,
        "original_result": result,
        "memory_fit": "unproved",
        "installed_readiness": "unproved",
        "new_environments": 0,
        "new_runtime_copies": 0,
    }


def _cold_native_current_inputs(selection):
    legacy_keys = {
        "prepared_root",
        "prepared_result_sha256",
        "envelope_path",
        "runtime_archive_path",
        "native_helper_path",
    }
    if type(selection) is not dict or set(selection) not in (
        legacy_keys,
        legacy_keys | {"native_current_inputs"},
        legacy_keys | {"native_current_inputs", "specification_example"},
    ):
        raise ValueError("exact_cold_entrance_selection_required")
    if "native_current_inputs" not in selection:
        return {}
    pins = selection["native_current_inputs"]
    names = {
        "configure_native_current_v1.py",
        "native-current-descriptor.json",
        "native-current-resource-record.json",
    }
    if type(pins) is not dict or pins.keys() != names:
        raise ValueError("exact_optional_native_current_pins_required")
    for pin in pins.values():
        if (
            type(pin) is not dict
            or pin.keys() != {"path", "sha256", "size_bytes"}
            or type(pin["path"]) is not str
            or not Path(pin["path"]).is_absolute()
            or str(Path(pin["path"])) != pin["path"]
            or ".." in Path(pin["path"]).parts
            or type(pin["sha256"]) is not str
            or len(pin["sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in pin["sha256"])
            or type(pin["size_bytes"]) is not int
            or pin["size_bytes"] <= 0
        ):
            raise ValueError("exact_optional_native_current_file_pin_required")
    return pins


def _cold_specification_example(selection):
    """Select only the exact original typed example, never arbitrary Python."""
    if "specification_example" not in selection:
        return None
    pin = selection["specification_example"]
    if (
        "native_current_inputs" not in selection
        or type(pin) is not dict
        or pin.keys() != {"path", "sha256", "size_bytes"}
        or type(pin["path"]) is not str
        or not Path(pin["path"]).is_absolute()
        or str(Path(pin["path"])) != pin["path"]
        or ".." in Path(pin["path"]).parts
        or type(pin["sha256"]) is not str
        or pin["sha256"] != SPECIFICATION_EXAMPLE_SHA256
        or type(pin["size_bytes"]) is not int
        or pin["size_bytes"] != SPECIFICATION_EXAMPLE_SIZE
    ):
        raise ValueError("exact_original_specification_example_pin_required")
    source = Path(pin["path"])
    if (
        source.stat().st_size != SPECIFICATION_EXAMPLE_SIZE
        or digest(source) != SPECIFICATION_EXAMPLE_SHA256
    ):
        raise ValueError("original_specification_example_changed")
    return pin


def _cold_configure_script(script, native_current_inputs):
    """Add explicit configure/run commands; preserve default shell bytes."""
    if not native_current_inputs:
        return script
    changes = (
        (
            "install-apply INSTALL_ROOT RUNTIME_ROOT EXPECTED_PLAN_SHA256'",
            (
                "install-apply INSTALL_ROOT RUNTIME_ROOT EXPECTED_PLAN_SHA256 | "
                "configure INSTALL_ROOT RUNTIME_ROOT EXPECTED_PLAN_SHA256 ORIGINAL_APPLY_LOG "
                "(creates two native-current datafiles once) | run INSTALL_ROOT [AWARE_ARGS...]'"
            ),
        ),
        (
            '    install-apply) test "$#" -eq 4 || { usage >&2; exit 2; } ;;',
            (
                '    install-apply) test "$#" -eq 4 || { usage >&2; exit 2; } ;;\n'
                '    configure) test "$#" -eq 5 || { usage >&2; exit 2; } ;;\n'
                '    run) test "$#" -ge 2 || { usage >&2; exit 2; } ;;'
            ),
        ),
        (
            '        exec "$@"\n        ;;\nesac\n',
            (
                '        exec "$@"\n        ;;\n'
                "    configure)\n"
                "        case \"$runtime_root\" in /*) ;; *) printf '%s\\n' "
                "'An explicit absolute runtime root is required.' >&2; exit 2 ;; esac\n"
                '        exec "$target/env/bin/python" -I -B -X utf8 '
                '"$base/configure_native_current_v1.py" configure "$target" "$runtime_root" '
                '"$reviewed_plan" "$5" --descriptor "$base/native-current-descriptor.json" '
                '--cold-root "$base"\n'
                "        ;;\n"
                "    run)\n"
                "        shift 2\n"
                '        exec "$target/env/bin/python" -I -B "$target/env/bin/aware" "$@"\n'
                "        ;;\nesac\n"
            ),
        ),
    )
    for before, after in changes:
        if script.count(before) != 1:
            raise ValueError("original_cold_configure_callsite_changed")
        script = script.replace(before, after)
    return script


def _cold_install_guide():
    """Frozen instructions for the optional configure/run delivery view."""
    return """# Private supplied-runtime installation

This delivery is for private qualification on the reference Linux x86_64 host
(Ubuntu 24.04/glibc 2.39). It is not public release or legal/disclosure clearance.
No host Python is needed. /bin/sh, dirname, sha256sum, the exact qualified native
tar/gzip tools and ELF libraries, and CPython's platform libraries are still
required; see ENTRANCE.json. Git is separately required for repository operations.

Use absolute paths below. The installation root must already be private and
owned by the consumer; the separate runtime root must satisfy the original
runtime helper's fresh-root requirements. Keep the complete delivery together,
including its descriptor/resource data and source/notice carriage.

```sh
set -eu
entrance=/absolute/path/to/cold-entrance
runtime=/absolute/path/to/fresh-runtime
target=/absolute/path/to/private-install-root
apply_log=/absolute/path/to/retained-original-apply.stdout

"$entrance/install-aware" runtime-preview "$runtime"
"$entrance/install-aware" runtime-apply "$runtime"
"$entrance/install-aware" install-preview "$target" "$runtime"
```

Review the original installation plan. Set reviewed_fp to its exact fingerprint;
do not reuse a fingerprint from another target, runtime selection or packet.
Retain complete original stdout without filtering, selecting or reencoding JSON:

```sh
reviewed_fp=REPLACE_WITH_EXACT_REVIEWED_PLAN_SHA256
"$entrance/install-aware" install-apply "$target" "$runtime" "$reviewed_fp" >"$apply_log"
"$entrance/install-aware" configure "$target" "$runtime" "$reviewed_fp" "$apply_log"
"$entrance/install-aware" run "$target" --help
```

Continue only after each preceding command succeeds. Retain failed/unknown
results and state; do not retry configure or clean up unknown state automatically.
Configure explicitly creates bootstrap-receipt.json and env/aware-native-current.json
once through the original retained initializer. This DATA setup is not Issue
admission, native authority or permission for an SDK operation.

For useful work, replace --help with the original SDK command and its arguments:
install-aware run INSTALL_ROOT [AWARE_ARGS...]. Quote each argument normally; run
forwards them unchanged to the installed original SDK console entry using its
installed interpreter with -I -B. Use this entrance for subsequent CLI launches
to prevent bytecode-cache writes to the supplied runtime. Original SDK commands,
review/admission requirements and errors remain in effect; no commands or policy
are supplied by this guide. No native operation is proved by installation/setup.
"""


def _cold_specification_guide():
    """Explain the original example without replacing its types or codec."""
    return """# Original specification DATA example

The carried examples/prepare_draft_input.py is the unchanged original authored
public-type example referenced by aware-specification-cli 0.4.4. ENTRANCE.json
records its original authored path, source revision and byte pin; SHA256SUMS
covers the hardlinked example and this guide. These bindings are provenance,
not authority or a new software selector. The complete source is also retained
inside the product source archive.

Its illustrative meaning is a non-mutating JSON checker. The customer must
approve that exact meaning before using its output. Carriage does not approve
customer intent; do not treat the example as a generic specification author.

After installation/configuration, run the original example separately with the
supplied installed Python and capture its canonical DATA bytes unchanged:

```sh
set -eu
entrance=/absolute/path/to/cold-entrance
target=/absolute/path/to/private-install-root
draft_data=/absolute/path/to/new-specification-draft.data
"$target/env/bin/python" -I -B "$entrance/examples/prepare_draft_input.py" >"$draft_data"
```

This uses no host Python. The original typed factories and original wire codec
produce canonical bytes on stdout. Preserve those exact bytes: do not JSON
reencode, pretty-print, add a newline, or substitute shell text. Do not use
partial output after a failed preparation. No CLI command runs this Python
on behalf of a draft request, and no new writer, wire codec or command is added.

The result is DATA only, not Issue admission, native authority or permission to
apply anything. Use install-aware run INSTALL_ROOT --help and the installed
original SDK's help for subsequent commands. Follow its original reviews,
admission, preview and apply workflow with the approved DATA; original guards
and errors remain in effect. Retain unknown results rather than retrying or
rewriting them. This is private qualification, not public/legal clearance.
"""


def prepare_cold_entrance_view(root, selection):
    """Compose an exact ordinary-profile delivery view; never execute it.

    No extraction or installation implementation is copied here. Runtime
    creation remains the native owner's operation; Python preview/apply remain
    the original whole-envelope port. All inputs are retained hardlink aliases.
    """
    native_current_inputs = _cold_native_current_inputs(selection)
    specification_example = _cold_specification_example(selection)
    if (
        root.parent != Path("/tmp")
        or not root.name.startswith("aware-cold-entrance.")
        or root.exists()
        or root.is_symlink()
    ):
        raise ValueError("fresh_cold_entrance_view_required")
    prepared = Path(selection["prepared_root"])
    if prepared.is_symlink() or not prepared.is_dir():
        raise ValueError("original_prepared_directory_required")
    if digest(prepared / "result.json") != selection["prepared_result_sha256"]:
        raise ValueError("original_preparation_record_changed")
    record = json.loads((prepared / "result.json").read_bytes())
    if (
        record.get("schema") != "aware.supplied-runtime.bootstrap-preparation.v1"
        or record.get("repeat_small_builds_equal") is not True
        or record.get("descriptor", {}).get("activation") != "not_requested"
    ):
        raise ValueError("qualified_supplied_preparation_required")
    runtime, artifact = record["supplied_runtime"], record["artifact"]
    if artifact["platform"] != "linux_x86_64" or artifact["runtime_mode"] != "supplied":
        raise ValueError("explicit_linux_supplied_profile_required")
    paths = {}
    for name, row in record["files"].items():
        relative = Path(name)
        if relative.is_absolute() or any(
            part in ("", ".", "..") for part in name.split("/")
        ):
            raise ValueError("canonical_prepared_relative_path_required")
        original = prepared / relative
        if digest(original) != row["sha256"] or original.stat().st_size != row["bytes"]:
            raise ValueError("original_prepared_member_changed:" + name)
        if name.startswith("bundle/"):
            paths[name] = original
    slot = "bundle/releases/" + artifact["release_id"] + "/" + artifact["envelope_name"]
    if slot not in paths or record["files"][slot]["bytes"] != 0:
        raise ValueError("original_readonly_archive_slot_required")
    archive, runtime_archive, helper = (
        Path(selection[key])
        for key in ("envelope_path", "runtime_archive_path", "native_helper_path")
    )
    for original, expected in (
        (archive, artifact["envelope_sha256"]),
        (runtime_archive, runtime["archive_sha256"]),
        (helper, runtime["bootstrap_sha256"]),
        (prepared / "runtime-postimage.json", runtime["roster_sha256"]),
    ):
        if digest(original) != expected:
            raise ValueError("cold_entrance_original_input_changed")
    if archive.stat().st_size != artifact["envelope_size"] or not os.access(
        helper, os.X_OK
    ):
        raise ValueError("exact_envelope_and_executable_helper_required")
    paths[slot] = archive
    paths.update(
        {
            "bootstrap.pyz": prepared / "bootstrap-a.pyz",
            "runtime-bootstrap": helper,
            "runtime.tar.gz": runtime_archive,
            "runtime-postimage.json": prepared / "runtime-postimage.json",
        }
    )
    for name, pin in native_current_inputs.items():
        source = Path(pin["path"])
        if (
            source.stat().st_size != pin["size_bytes"]
            or digest(source) != pin["sha256"]
        ):
            raise ValueError("original_native_current_carriage_changed:" + name)
        paths[name] = source
    if specification_example:
        paths[SPECIFICATION_EXAMPLE_MEMBER] = Path(specification_example["path"])
    root.mkdir(mode=0o700)
    for name, original in paths.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(original, target)
    # Fixed filenames and quoted argv only. No shell parsing of JSON, selected
    # commands, guard reconstruction, runtime fallback or automatic retry.
    script = r"""#!/bin/sh
set -eu
umask 077
usage() {
    printf '%s\n' 'Usage: install-aware runtime-preview RUNTIME_ROOT | runtime-apply RUNTIME_ROOT | install-preview INSTALL_ROOT RUNTIME_ROOT | install-apply INSTALL_ROOT RUNTIME_ROOT EXPECTED_PLAN_SHA256'
}
case "${1-}" in
    --help) usage; exit 0 ;;
    runtime-preview|runtime-apply) test "$#" -eq 2 || { usage >&2; exit 2; } ;;
    install-preview) test "$#" -eq 3 || { usage >&2; exit 2; } ;;
    install-apply) test "$#" -eq 4 || { usage >&2; exit 2; } ;;
    *) usage >&2; exit 2 ;;
esac
action=$1
target=$2
runtime_root=${3-}
case "$target" in /*) ;; *) printf '%s\n' 'An explicit absolute final root is required.' >&2; exit 2 ;; esac
base=$(CDPATH= cd -P -- "$(/usr/bin/dirname -- "$0")" && pwd -P)
cd "$base"
/usr/bin/sha256sum --check --strict SHA256SUMS
case "$action" in
    runtime-preview|runtime-apply)
        phase=--preview
        if test "$action" = runtime-apply; then phase=--apply; fi
        exec "$base/runtime-bootstrap" --profile runtime-stripped128-v1 --archive "$base/runtime.tar.gz" --root "$target" "$phase"
        ;;
    install-preview|install-apply)
        case "$runtime_root" in /*) ;; *) printf '%s\n' 'An explicit absolute runtime root is required.' >&2; exit 2 ;; esac
        runtime_python="$runtime_root/python/bin/python3.12"
        observed_python=$(/usr/bin/sha256sum -- "$runtime_python") || exit 2
        case "$observed_python" in "@RUNTIME_PYTHON_SHA256@  "*) ;; *) printf '%s\n' 'Supplied runtime executable digest refused.' >&2; exit 2 ;; esac
        set -- "$runtime_root/python/bin/python3.12" -I -S -B -X utf8 "$base/bootstrap.pyz" --bundle-root "$base/bundle" --installation-root "$target" --python-executable "$runtime_root/python/bin/python3.12" --supplied-runtime-root "$runtime_root" --timeout-seconds 1800
        if test "$action" = install-apply; then
            set -- "$@" --apply --expected-plan-sha256 "$reviewed_plan"
        fi
        exec "$@"
        ;;
esac
"""
    # Capture the explicit caller value before replacing positional arguments.
    script = script.replace(
        "action=$1\ntarget=$2\n", "action=$1\ntarget=$2\nreviewed_plan=${4-}\n"
    )
    script = script.replace("@RUNTIME_PYTHON_SHA256@", runtime["python_sha256"])
    script = _cold_configure_script(script, native_current_inputs)
    (root / "entrance-producer.py").write_bytes(Path(__file__).read_bytes())
    (root / "install-aware").write_text(script)
    (root / "install-aware").chmod(0o755)
    if native_current_inputs:
        guide = _cold_install_guide()
        if specification_example:
            guide += "\nFor the original typed specification DATA example, see [SPECIFICATION.md](SPECIFICATION.md).\n"
        (root / "INSTALL.md").write_text(guide)
    if specification_example:
        (root / "SPECIFICATION.md").write_text(_cold_specification_guide())
    descriptor = {
        "schema": "aware.ordinary-cold-entrance.local-candidate.v1",
        "artifact": artifact,
        "supplied_runtime": runtime,
        "source_revision": record["source_revision"],
        "prepared_result_sha256": selection["prepared_result_sha256"],
        "profile": "runtime-stripped128-v1",
        "platform": "Ubuntu24.04/glibc2.39/linux_x86_64 reference-host only",
        "prerequisites": [
            "/bin/sh",
            "/usr/bin/dirname",
            "/usr/bin/sha256sum",
            "exact helper-pinned /usr/bin/tar and /usr/bin/gzip and qualified ELF dependencies",
            "qualified CPython ELF dependencies",
            "Git separately for repository operations",
        ],
        "trusted_acquisition_origin": None,
        "public_revision": None,
        "runtime_preview": "Original roster validation only; not source/root observation or admission.",
        "review_boundary": "After runtime-apply succeeds, install-preview returns original plan. Only install-apply with its exact reviewed fingerprint dispatches original installation.",
        "installation_root_prerequisite": "Existing private owned installation root; runtime root is separate and original-port validated. No wrapper directory creation or runtime movement.",
        "installed_command": "ROOT/env/bin/aware",
        "activation": "not_requested",
        "source_notice_disposition": "Private internal qualification only;20legal gaps and all findings/provenance limitations retained. Full envelope and both carriage maps required.",
        "resource_acceptance": False,
        "supplier_two_root_acceptance": False,
        "cold_execution_acceptance": False,
        "unassisted_acceptance": False,
    }
    if specification_example:
        descriptor["specification_example"] = {
            "member": SPECIFICATION_EXAMPLE_MEMBER,
            "authored_path": SPECIFICATION_EXAMPLE_SOURCE,
            "source_revision": SPECIFICATION_EXAMPLE_REVISION,
            "source_path": specification_example["path"],
            "sha256": SPECIFICATION_EXAMPLE_SHA256,
            "size_bytes": SPECIFICATION_EXAMPLE_SIZE,
            "authorizes_operation": False,
        }
    (root / "ENTRANCE.json").write_text(
        json.dumps(descriptor, indent=2, sort_keys=True) + "\n"
    )
    accounts = {
        str(path.relative_to(root)): {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
        }
        for path in root.rglob("*")
        if path.is_file()
    }
    (root / "SHA256SUMS").write_text(
        "".join(f"{row['sha256']}  {name}\n" for name, row in sorted(accounts.items()))
    )
    return {
        "schema": "aware.cold-entrance.preparation.v1",
        "root": str(root),
        "files": accounts,
        "checksum_sha256": digest(root / "SHA256SUMS"),
        "artifact": artifact,
        "new_environments": 0,
        "new_runtime_trees": 0,
        "new_archive_copies": 0,
        "execution": "not_invoked",
        "public_authority": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--sha256")
    args = parser.parse_args()
    selection = None
    if args.selection is not None:
        if (
            args.selection.stat().st_size > 16384
            or digest(args.selection) != args.sha256
        ):
            raise ValueError("exact_bounded_control_selection_required")
        selection = json.loads(args.selection.read_bytes())
    result = prepare(args.root, selection=selection)
    (args.root / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))
