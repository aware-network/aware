"""Explicit consumer native-current DATA setup through original retained creation.

No installer, copied writer, disposal implementation, native operation or guard
refresh. The publisher descriptor/resource sit beside the outer archive. Only
an explicit configure command delegates the two guarded CREATEs to the exact
hash-bound retained original initialize_native_current_v1.py.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

CONFIGURE_DESCRIPTOR_SCHEMA = "aware.native-current.configure-descriptor.v1"


def _read_bounded(path, maximum):
    """Bound the read request before allocating, including a growth sentinel."""
    if type(maximum) is not int or maximum < 1:
        raise ValueError("positive_input_read_bound_required")
    with Path(path).open("rb") as stream:
        body = stream.read(maximum + 1)
    if not 0 < len(body) <= maximum:
        raise ValueError("bounded_configure_input_required:" + str(path))
    return body


@dataclass(frozen=True, slots=True)
class CurrentInputsPreparation:
    original_request: object
    original_receipt_body: bytes
    receipt_lineage: dict
    authorizes_native_profile: Literal[False] = False


def _descriptor_member(value):
    from pathlib import PurePosixPath

    if (
        type(value) is not str
        or not value
        or value.startswith("/")
        or "\\" in value
        or str(PurePosixPath(value)) != value
        or any(part in (".", "..") for part in value.split("/"))
    ):
        raise ValueError("explicit_canonical_descriptor_member_required")
    return value


def validate_configure_descriptor(descriptor):
    if (
        type(descriptor) is not dict
        or descriptor.keys()
        != {
            "schema",
            "layout",
            "locations",
            "supplied_runtime_profile",
            "mount_template",
            "initializer",
        }
        or descriptor["schema"] != CONFIGURE_DESCRIPTOR_SCHEMA
    ):
        raise ValueError("explicit_native_current_descriptor_required")
    initializer = descriptor["initializer"]
    if (
        type(initializer) is not dict
        or initializer.keys() != {"member", "sha256", "size_bytes"}
        or type(initializer["sha256"]) is not str
        or len(initializer["sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in initializer["sha256"])
        or type(initializer["size_bytes"]) is not int
        or not 0 < initializer["size_bytes"] <= 1048576
    ):
        raise ValueError("exact_original_initializer_pin_required")
    _descriptor_member(initializer["member"])
    layout = descriptor["layout"]
    if type(layout) is not dict or layout.keys() != {
        "outer_root_name",
        "inner_root_name",
        "site_member",
    }:
        raise ValueError("explicit_producer_root_names_required")
    for name, value in layout.items():
        _descriptor_member(value)
        if name != "site_member" and "/" in value:
            raise ValueError("single_explicit_producer_root_name_required")
    locations = descriptor["locations"]
    if type(locations) is not dict or locations.keys() != {
        "runtime_archive",
        "runtime_inventory",
        "runtime_probe",
        "verifier",
        "outer_archive",
        "resource_record",
    }:
        raise ValueError("complete_static_descriptor_locations_required")
    for selected in locations.values():
        if (
            type(selected) is not dict
            or selected.keys() != {"anchor", "member"}
            or selected["anchor"]
            not in {
                "cold_root",
                "runtime_root",
                "installed_site",
                "retained_outer",
                "retained_inner",
            }
        ):
            raise ValueError("explicit_descriptor_location_required")
        _descriptor_member(selected["member"])
    if locations["resource_record"] != {
        "anchor": "cold_root",
        "member": "native-current-resource-record.json",
    }:
        raise ValueError("adjacent_cold_resource_record_required_no_outer_hash_cycle")
    return descriptor


def generate_configure_descriptor(
    config, *, outer_root_name, inner_root_name, locations, initializer_member
):
    """Pure publisher projection of qualified DATA, not current observations.

    Source hashes, runtime/build/member pins and resource claims are carried
    verbatim. Caller supplies exact original producer root names and locators.
    No installed tree, receipt, runtime or archive is discovered or hashed.
    """
    import copy

    template = {
        "schema": "aware.workspace.native-consumer-inputs.v1",
        "profile": "ordinary-supplied-runtime-linux-x86_64-catalog-v1",
        "artifact": copy.deepcopy(config["artifact"]),
        "supplied_runtime": None,
        "receipt": {
            "receipt_path": None,
            "receipt_sha256": None,
            "receipt_size_bytes": None,
            "installation_root": None,
            "retained_source_and_notices": None,
            "expected_plan_sha256": None,
        },
        "runtime": copy.deepcopy(config["runtime_context"]),
        "native_artifact": copy.deepcopy(config["native_artifact_pin"]),
        "coordinates": {
            "retained_envelope_root": None,
            "environment_prefix": None,
            "wheel_member": config["wheel_member"],
            "build_manifest_member": config["build_manifest_member"],
        },
        "native_envelope": copy.deepcopy(config["native_envelope"]),
        "wheel": copy.deepcopy(config["wheel"]),
        "runtime_tree": copy.deepcopy(config["runtime_tree"]),
        "product": copy.deepcopy(config["product"]),
    }
    for name in (
        "runtime_root",
        "stdlib_root",
        "environment_prefix",
        "launch_executable",
    ):
        template["runtime"][name] = None
    for name in ("envelope_root", "installed_native_path"):
        template["native_envelope"][name] = None
    for name in ("wheel_path", "installed_site"):
        template["wheel"][name] = None
    for name in (
        "archive_path",
        "inventory_path",
        "extracted_root",
        "runtime_root",
        "probe_path",
    ):
        template["runtime_tree"]["runtime"][name] = None
    template["product"]["retained_inner_root"] = None
    template["product"]["retained_tree"]["private_root"] = None
    for name in ("verifier", "outer_archive"):
        template["product"][name]["path"] = None
    template["product"]["resource"]["record"]["path"] = None
    descriptor = {
        "schema": CONFIGURE_DESCRIPTOR_SCHEMA,
        "initializer": {
            "member": initializer_member,
            "sha256": config["initializer"]["sha256"],
            "size_bytes": config["initializer"]["size_bytes"],
        },
        "layout": {
            "outer_root_name": outer_root_name,
            "inner_root_name": inner_root_name,
            "site_member": "lib/python3.12/site-packages",
        },
        "locations": copy.deepcopy(locations),
        "supplied_runtime_profile": copy.deepcopy(config["supplied_runtime_profile"]),
        "mount_template": template,
    }
    return validate_configure_descriptor(descriptor)


def select_original_bootstrap_line(raw):
    """Select exact outer stdout line bytes; never decode a nested receipt."""
    if type(raw) is not bytes or not 0 < len(raw) <= 8 * 1024**2:
        raise ValueError("bounded_original_bootstrap_log_bytes_required")
    chosen, offset = None, 0
    for number, line in enumerate(raw.splitlines(keepends=True), 1):
        if line.strip():
            chosen = (offset, number, line)
        offset += len(line)
    if chosen is None:
        raise ValueError("original_bootstrap_output_line_required")
    start, number, body = chosen
    return body, {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_size_bytes": len(raw),
        "line_number_1based": number,
        "start_offset_bytes": start,
        "end_offset_bytes_exclusive": start + len(body),
        "line_size_bytes": len(body),
        "line_sha256": hashlib.sha256(body).hexdigest(),
        "reencoded": False,
    }


def project_current_mount_data(
    descriptor,
    receipt,
    original_receipt_body,
    *,
    installation_root,
    runtime_root,
    cold_root,
    expected_plan_sha256,
    supplied_runtime_projection,
):
    """Pure coordinate projection; original decoder owns all type/codec policy."""
    import copy

    validate_configure_descriptor(descriptor)
    roots = tuple(Path(value) for value in (installation_root, runtime_root, cold_root))
    if any(
        not path.is_absolute() or ".." in path.parts or str(path).startswith("//")
        for path in roots
    ):
        raise ValueError("explicit_absolute_configure_roots_required")
    install, runtime, cold = roots
    env = install / "env"
    declaration = copy.deepcopy(descriptor["mount_template"])
    # These are cross-input bindings only. Historical installer claims, nested
    # streams, current source guards and cleanup remain with original observers.
    if (
        type(receipt) is not dict
        or receipt.get("artifact") != declaration["artifact"]
        or receipt.get("status") != "installed"
        or type(receipt.get("returncode")) is not int
        or receipt["returncode"] != 0
        or receipt.get("environment") != str(env)
        or receipt.get("fingerprint") != expected_plan_sha256
        or receipt.get("reviewed_installation_plan_sha256") != expected_plan_sha256
        or receipt.get("supplied_runtime") != supplied_runtime_projection
    ):
        raise ValueError(
            "original_receipt_descriptor_root_or_reviewed_fingerprint_mismatch"
        )
    outer_value = receipt.get("retained_source_and_notices")
    if type(outer_value) is not str:
        raise ValueError("original_retained_outer_coordinate_required")
    outer = Path(outer_value)
    layout = descriptor["layout"]
    if (
        str(outer) != outer_value
        or ".." in outer.parts
        or not outer.is_relative_to(install)
        or outer == install
        or outer.name != layout["outer_root_name"]
        or outer.parent.name != "outer"
    ):
        raise ValueError("original_retained_outer_explicit_layout_mismatch")
    private = outer.parent.parent
    inner = private / "inner" / layout["inner_root_name"]
    site = env / layout["site_member"]
    anchors = {
        "cold_root": cold,
        "runtime_root": runtime,
        "installed_site": site,
        "retained_outer": outer,
        "retained_inner": inner,
    }

    def location(name):
        selected = descriptor["locations"][name]
        return str(anchors[selected["anchor"]] / selected["member"])

    declaration["supplied_runtime"] = copy.deepcopy(supplied_runtime_projection)
    declaration["receipt"].update(
        receipt_path=str(install / "bootstrap-receipt.json"),
        receipt_sha256=hashlib.sha256(original_receipt_body).hexdigest(),
        receipt_size_bytes=len(original_receipt_body),
        installation_root=str(install),
        retained_source_and_notices=str(outer),
        expected_plan_sha256=expected_plan_sha256,
    )
    declaration["runtime"].update(
        runtime_root=str(runtime / "python"),
        stdlib_root=str(runtime / "python/lib/python3.12"),
        environment_prefix=str(env),
        launch_executable=str(env / "bin/python"),
    )
    declaration["coordinates"].update(
        retained_envelope_root=str(outer), environment_prefix=str(env)
    )
    declaration["native_envelope"].update(
        envelope_root=str(outer),
        installed_native_path=str(site / declaration["wheel"]["member"]),
    )
    declaration["wheel"].update(
        installed_site=str(site),
        wheel_path=str(inner / declaration["coordinates"]["wheel_member"]),
    )
    declaration["runtime_tree"]["runtime"].update(
        extracted_root=str(runtime),
        runtime_root=str(runtime / "python"),
        archive_path=location("runtime_archive"),
        inventory_path=location("runtime_inventory"),
        probe_path=location("runtime_probe"),
    )
    declaration["product"]["retained_inner_root"] = str(inner)
    declaration["product"]["retained_tree"]["private_root"] = str(private)
    declaration["product"]["verifier"]["path"] = location("verifier")
    declaration["product"]["outer_archive"]["path"] = location("outer_archive")
    declaration["product"]["resource"]["record"]["path"] = location("resource_record")
    return declaration


def prepare_current_request(
    descriptor,
    raw_bootstrap_output,
    *,
    installation_root,
    runtime_root,
    cold_root,
    expected_plan_sha256,
):
    """Original selection observation + original codec, never native admission."""
    import json

    from aware_release.install_distribution import whole_envelope as original
    from aware_workspace_fs_adapter import _native_checker_mount as mount

    validate_configure_descriptor(descriptor)
    body, lineage = select_original_bootstrap_line(raw_bootstrap_output)
    receipt = original._decode(body)  # preserve original outer historical parser
    profile = dict(descriptor["supplied_runtime_profile"])
    profile["python_version"] = tuple(profile["python_version"])
    supplied = original.observe_supplied_runtime_selection(
        root=Path(runtime_root), **profile
    )
    declaration = project_current_mount_data(
        descriptor,
        receipt,
        body,
        installation_root=installation_root,
        runtime_root=runtime_root,
        cold_root=cold_root,
        expected_plan_sha256=expected_plan_sha256,
        supplied_runtime_projection=original.supplied_runtime_projection(supplied),
    )
    # Reuse the original closed decoder/type builders instead of reconstructing
    # their policy or importing a sidecar harness into the consumer product.
    encoded = json.dumps(
        declaration,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    decoded = mount._decode_mount_body(encoded, str(Path(installation_root) / "env"))
    return CurrentInputsPreparation(decoded.request, body, lineage)


def load_retained_original_initializer(descriptor, retained_outer):
    """Hash-bound runpy of the genuine retained original, never a copied port.

    Both reads use the same publisher pin. A changed input refuses; no digest
    refresh or source repair is attempted. Ordinary bookends do not claim
    authenticated/continuous source custody.
    """
    import runpy

    validate_configure_descriptor(descriptor)
    selected = descriptor["initializer"]
    path = Path(retained_outer) / selected["member"]

    def verify():
        body = _read_bounded(path, selected["size_bytes"])
        if (
            len(body) != selected["size_bytes"]
            or hashlib.sha256(body).hexdigest() != selected["sha256"]
        ):
            raise ValueError("pinned_retained_original_initializer_changed")

    verify()
    original = runpy.run_path(str(path), run_name="native_current_original_initializer")
    verify()
    create = original["create_current_inputs"]
    kind = original["CurrentInputsCreationError"]
    if (
        not callable(create)
        or create.__code__.co_filename != str(path)
        or not isinstance(kind, type)
        or not issubclass(kind, RuntimeError)
    ):
        raise ValueError("original_retained_creation_entries_required")
    return original


def configure_main(argv=None):
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        description="Explicitly create two absent native-current DATA files once; no install, activation or native admission."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser(
        "configure",
        help="Create bootstrap-receipt.json and env/aware-native-current.json once.",
    )
    command.add_argument("installation_root", type=Path)
    command.add_argument("runtime_root", type=Path)
    command.add_argument("expected_plan_sha256")
    command.add_argument("original_apply_log", type=Path)
    command.add_argument("--descriptor", type=Path, required=True)
    command.add_argument("--cold-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if (
        sys.version_info[:2] != (3, 12)
        or not sys.flags.isolated
        or not sys.flags.dont_write_bytecode
        or sys.flags.no_site
        or sys.prefix != str(args.installation_root / "env")
        or sys.base_prefix != str(args.runtime_root / "python")
    ):
        raise ValueError("selected_installed_python_I_B_without_S_required")
    from aware_release.install_distribution import whole_envelope as original

    descriptor_body = _read_bounded(args.descriptor, 65536)
    descriptor = original._decode(descriptor_body)
    prepared = prepare_current_request(
        descriptor,
        _read_bounded(args.original_apply_log, 8 * 1024**2),
        installation_root=args.installation_root,
        runtime_root=args.runtime_root,
        cold_root=args.cold_root,
        expected_plan_sha256=args.expected_plan_sha256,
    )
    original = load_retained_original_initializer(
        descriptor, prepared.original_request.coordinates.retained_envelope_root
    )
    original_create = original["create_current_inputs"]
    original_error_kind = original["CurrentInputsCreationError"]
    try:
        result = original_create(
            prepared.original_request, prepared.original_receipt_body
        )
    except original_error_kind as error:
        # Report the original uncertainty once, then preserve the full original
        # exception/cause chain. Do not dispose again, retry, chmod or refresh.
        print(
            json.dumps(
                {
                    "status": "configure_failed",
                    "phase": error.phase,
                    "original_cleanup": repr(error.original_cleanup),
                    "original_cleanup_error": repr(error.original_cleanup_error),
                    "original_umask_restore_error": repr(
                        error.original_umask_restore_error
                    ),
                    "receipt_lineage": prepared.receipt_lineage,
                    "authorizes_retry": False,
                    "authorizes_native_profile": False,
                }
            ),
            file=sys.stderr,
        )
        raise
    print(
        json.dumps(
            {
                "status": "native_current_inputs_created",
                "paths": result.paths,
                "original_apply_log": str(args.original_apply_log),
                "receipt_lineage": prepared.receipt_lineage,
                "original_cleanup": repr(result.original_cleanup),
                "authorizes_native_profile": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(configure_main())
