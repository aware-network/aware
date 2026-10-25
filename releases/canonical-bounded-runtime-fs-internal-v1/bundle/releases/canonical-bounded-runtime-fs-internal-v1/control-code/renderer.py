"""Producer rendering of the original driver with explicit bounded staging.

The original offline installer remains the only installation rail. Source seeds
are embedded exact accepted bodies; the shared loader captures the remaining
original source closure. This is not an archive parser or installation fallback.
"""

from __future__ import annotations

import ast
import hashlib
import json

PROFILE = "aware.release.original-bootstrap-bounded-staging.v1"
COMPACT_PROFILE = "aware.release.original-bootstrap-compact-staging.v1"
RECORDED_PROFILE = "aware.release.original-bootstrap-recorded-staging.v1"
SEALED_PROFILE = "aware.release.original-bootstrap-sealed-staging.v1"
PACKED_PROFILE = "aware.release.original-bootstrap-packed-staging.v1"
COMPRESSED_PROFILE = "aware.release.original-bootstrap-compressed-staging.v1"
BORROWED_PROFILE = "aware.release.original-bootstrap-borrowed-directory-staging.v1"
RECEIPT_PROFILE = "aware.release.original-bootstrap-observation-receipts.v1"
RETIRED_PROFILE = "aware.release.original-bootstrap-retired-member-staging.v1"
ORIGINAL_SHA256 = "2841e7017b6bd83d986d3ed06c3190bf1312bce830862bbd7035ce873e055c9e"
SEEDS = {
    "loader": "dc007af3a116b5693b9ae7bc2fb55fddb53d53702e12d98fd5dc00ced6a14567",
    "observer": "c5d8d499c18c5fd49110a1247b7f29a2021101bbd7f0b55cfb86e0bbc0ff29da",
    "driver": "73b476e2ea469e40d03e035a1fdbfb43468b70fc9d523753b587e6a87954eaba",
}
COMPACT_SEEDS = {
    **SEEDS,
    "loader": "72797706e96aceaeddb35ce9e7842531e939924ac55b3073ef1bdb736a42ddcf",
    "driver": "e523625759612affbff939e34c6b93ab3fc81c28920a052e1e9aa452aa11f8d8",
}
RECORDED_SEEDS = {
    **SEEDS,
    "loader": "7329a5ba683f68c2f21e35afef4578dada9011cbc9d0a7102f9a55263cdaef1d",
    "driver": "2860fda1df1c6d0167d9de07fa350f56cb6790fab99617674524f1b80891e3ae",
}
SEALED_SEEDS = {
    **RECORDED_SEEDS,
    "loader": "918a29e6b1721e3d945b29e8228de9f16c214d5559e31523b7ea45b81920e449",
}
PACKED_SEEDS = {
    **RECORDED_SEEDS,
    "loader": "3a0f2ccc70b2893c8e0cd72edee2028a7a34baa23274c133ca4b952a17d38825",
}
COMPRESSED_SEEDS = {
    **SEEDS,
    "loader": "13283d05193402c6166c998f84dffc1cc89e6e078a5814ecb6c3da0b87f4a39b",
    "driver": "d901bd065246db67dbc87843ebb944888c012eaf431e1c2e6836485b27e3f8c9",
}

BORROWED_SEEDS = {
    **SEEDS,
    "loader": "f5696e3b6f98783a73533d22c221dfa0fec6593122b352d069bd5c38fc7cd65c",
    "driver": "738c33605123b5036b9214ba5c2b6035ce9c7f7dcf6ec5ce0ddbd06027525d49",
}

RETIRED_SEEDS = {
    **SEEDS,
    "loader": "feffff023b57546ad1edd2d2a9fe77c7cc232c8969c45f9033535fb02d00abb9",
    "driver": "4365780f9eb8994fd27e0499d35de5800beee2f13504b5b76108a7c8a499cd09",
}


RECEIPT_SEEDS = {
    **SEEDS,
    "loader": "6b1494a3ac4c31c8d24d7748c1a36034a3e935beefe3b132b5d56af77107b7dd",
    "driver": "04ae81df16752c14ae66a9aff1e8cc4ba57908f48dc4efa1e65e458e8664ef8b",
}

# Executed in the original install.py namespace. No producer imports or checkout
# paths survive. Source bodies and plan bytes are bound by that driver's digest.
_RUNTIME = """
_BOOTSTRAP_ATTEMPT = {}


def _seed(name, body):
    name = "_aware_original_bootstrap_" + name
    if name in sys.modules:
        raise ValueError("bootstrap_seed_namespace_present")
    module = types.ModuleType(name)
    module.__file__ = str(Path(__file__).absolute()) + ":" + name
    sys.modules[name] = module
    _BOOTSTRAP_ATTEMPT.setdefault("seed_modules", []).append(module)
    exec(compile(body, module.__file__, "exec"), module.__dict__)
    return module


def _stage_original(root, archive):
    state = _BOOTSTRAP_ATTEMPT
    if state.get("started"):
        raise ValueError("bootstrap_staging_attempt_spent")
    state["started"] = True
    loader = state["loader"] = _seed("loader", _SEED_BODIES["loader"])
    observer = state["observer"] = _seed("observer", _SEED_BODIES["observer"])
    driver = state["driver"] = _seed("driver", _SEED_BODIES["driver"])
    selection = loader.SourceSelection(
        root.parent / "releases" / _STAGING["release_id"] / "driver-sources",
        loader.STAGING_BOUND_PROFILE,
    )
    handle = state["source_handle"] = loader.bind_original_sources(
        selection, original_owner=observer
    )
    stage = state["stage"] = loader.bound_module(handle, "release.product_staging")
    owner = loader.bound_module(handle, "release.whole_envelope")
    groups = []
    for namespace, partitions in _STAGING["plan"]:
        groups.append(stage.metadata.StagingPlanGroup(namespace, tuple(
            stage.metadata._captured_plan((tuple(limits), tuple(tuple(row) for row in rows)))
            for limits, rows in partitions
        )))
    plan = stage.metadata.PartitionedStagingPlan(tuple(groups))
    state["plan"] = plan
    retained = Path(tempfile.mkdtemp(prefix="aware-specification-install-"))
    state["retained"] = retained
    request = driver.DriverStagingRequest(
        loader, handle,
        owner.ArchiveBodyRequest(archive, PACKET_SHA, _STAGING["envelope_size"]),
        plan, retained, _STAGING["payload_member"], PAYLOAD_SHA,
        _STAGING["maximum_outer_decoded_bytes"],
        _STAGING["maximum_inner_decoded_bytes"],
        "original-bootstrap-staging",
    )
    state["request"] = request
    result = state["result"] = driver.stage_for_original_driver(
        request, profile=driver.PROFILE, explicit_staging_intent=True
    )
    # The original role has checked the intended roots, source flow and both
    # owner-sealed completions. This return alone does not invoke installation.
    return retained, result.inner_directory, result.retained_source_and_notices


def _release_original_staging():
    state = _BOOTSTRAP_ATTEMPT
    result, stage = state["result"], state["stage"]
    # Explicit caller settlement after the original installer/pip check. Never
    # retried, and never used to erase partial effects on any failed attempt.
    if state.get("release_started"):
        raise ValueError("bootstrap_release_spent")
    state["release_started"] = True
    state["cleanup"] = []
    for group in (result.original_inner, result.original_outer):
        returned = stage.root.release_stage(group.stage_handle)
        state["cleanup"].append(returned)
        if returned.cleanup != "confirmed" or returned.capture_complete is not True:
            raise ValueError("bootstrap_staging_release_incomplete")
    state["loader"].retire_source_binding(state["source_handle"])
    state["source_retired"] = True
"""


def render_original_driver(original, *, seeds, source_bodies, staging, profile):
    """Return an executable driver, preserving the original delegation AST.

    No IO, imports of consumer code, package install or archive scan. The
    producer must carry source_bodies next to this driver in driver-sources.
    """
    if (
        profile
        not in (
            PROFILE,
            COMPACT_PROFILE,
            RECORDED_PROFILE,
            SEALED_PROFILE,
            PACKED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
            RECEIPT_PROFILE,
        )
        or hashlib.sha256(original).hexdigest() != ORIGINAL_SHA256
    ):
        raise ValueError("explicit_original_driver_profile_required")
    selected_seeds = (
        RECEIPT_SEEDS
        if profile == RECEIPT_PROFILE
        else RETIRED_SEEDS
        if profile == RETIRED_PROFILE
        else BORROWED_SEEDS
        if profile == BORROWED_PROFILE
        else COMPRESSED_SEEDS
        if profile == COMPRESSED_PROFILE
        else PACKED_SEEDS
        if profile == PACKED_PROFILE
        else SEALED_SEEDS
        if profile == SEALED_PROFILE
        else RECORDED_SEEDS
        if profile == RECORDED_PROFILE
        else COMPACT_SEEDS
        if profile == COMPACT_PROFILE
        else SEEDS
    )
    if set(seeds) != set(selected_seeds):
        raise ValueError("exact_original_seed_set_required")
    for name, digest in selected_seeds.items():
        if (
            type(seeds[name]) is not bytes
            or hashlib.sha256(seeds[name]).hexdigest() != digest
        ):
            raise ValueError("original_seed_changed:" + name)
    # Read the literal accepted pin table without executing a producer source.
    tree = ast.parse(seeds["loader"])
    pins = None
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "STAGING_PINS"
                for target in node.targets
            )
            and isinstance(node.value, ast.Call)
        ):
            pins = ast.literal_eval(node.value.args[0])
    if pins is None:
        raise ValueError("original_source_pins_required")
    pins["filesystem.staging_root"] = (
        "e3b74fbaa8cf05b9398db319a6acd25a66189521893a81138df0e7689bed5edc",
        18310,
    )
    if profile in (
        COMPACT_PROFILE,
        RECORDED_PROFILE,
        SEALED_PROFILE,
        PACKED_PROFILE,
        COMPRESSED_PROFILE,
        BORROWED_PROFILE,
        RETIRED_PROFILE,
        RECEIPT_PROFILE,
    ):
        tables = ("COMPACT_STAGING_PINS",)
        if profile in (
            RECORDED_PROFILE,
            SEALED_PROFILE,
            PACKED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
            RECEIPT_PROFILE,
        ):
            tables += ("RECORDED_STAGING_PINS",)
        if profile in (
            SEALED_PROFILE,
            PACKED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
            RECEIPT_PROFILE,
        ):
            tables += ("SEALED_STAGING_PINS",)
        if profile in (
            PACKED_PROFILE,
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
            RECEIPT_PROFILE,
        ):
            tables += ("PACKED_STAGING_PINS",)
        if profile in (
            COMPRESSED_PROFILE,
            BORROWED_PROFILE,
            RETIRED_PROFILE,
            RECEIPT_PROFILE,
        ):
            tables += ("COMPRESSED_STAGING_PINS",)
        if profile in (BORROWED_PROFILE, RETIRED_PROFILE, RECEIPT_PROFILE):
            tables += ("BORROWED_STAGING_PINS",)
        if profile in (RETIRED_PROFILE, RECEIPT_PROFILE):
            tables += ("RETIRED_STAGING_PINS",)
        if profile == RECEIPT_PROFILE:
            tables += ("RECEIPT_STAGING_PINS",)
        for table in tables:
            _apply_literal_overrides(tree, table, pins)
    if set(source_bodies) != set(pins):
        raise ValueError("complete_original_source_closure_required")
    for name, (digest, size) in pins.items():
        body = source_bodies[name]
        if (
            type(body) is not bytes
            or len(body) != size
            or hashlib.sha256(body).hexdigest() != digest
        ):
            raise ValueError("original_source_changed:" + name)
    required = {
        "release_id",
        "archive",
        "envelope_sha256",
        "payload_sha256",
        "payload_member",
        "envelope_size",
        "maximum_outer_decoded_bytes",
        "maximum_inner_decoded_bytes",
        "plan",
    }
    if type(staging) is not dict or set(staging) != required:
        raise ValueError("exact_staging_configuration_required")
    for key in ("release_id", "archive"):
        value = staging[key]
        if (
            type(value) is not str
            or not value
            or value in (".", "..")
            or "/" in value
            or "\\" in value
        ):
            raise ValueError("single_release_coordinate_required")
    for key in ("envelope_sha256", "payload_sha256"):
        value = staging[key]
        if (
            type(value) is not str
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
        ):
            raise ValueError("sha256_required")
    for key in (
        "envelope_size",
        "maximum_outer_decoded_bytes",
        "maximum_inner_decoded_bytes",
    ):
        if type(staging[key]) is not int or not 0 < staging[key] <= 4 * 1024**3:
            raise ValueError("bounded_archive_coordinate_required")
    if (
        type(staging["payload_member"]) is not str
        or not staging["payload_member"]
        or any(part in ("", ".", "..") for part in staging["payload_member"].split("/"))
    ):
        raise ValueError("relative_payload_member_required")
    config = json.dumps(staging, sort_keys=True, separators=(",", ":"))
    if len(config.encode()) > 4 * 1024**2:
        raise ValueError("bounded_staging_plan_required")
    text = original.decode()
    original_tree = ast.parse(text)
    main = next(
        node
        for node in original_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    )
    start = next(
        node
        for node in main.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "verifier" for t in node.targets)
    )
    stop = next(
        node
        for node in main.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "environment" for t in node.targets)
    )
    lines = text.splitlines(keepends=True)
    # Replace only original staging. Interpreter/platform/target/environment,
    # install.sh, pip check, error reporting and the receipt stay in main.
    lines[start.lineno - 1 : stop.lineno - 1] = [
        '    archive = root.parent / "releases" / _STAGING["release_id"] / ARCHIVE\n',
        "    retained, inner_directory, retained_source = _stage_original(root, archive)\n",
    ]
    text = "".join(lines).replace("str(retained / packet_root)", "str(retained_source)")
    text = text.replace(
        '    print(\n        json.dumps(\n            {\n                "status": "installed",',
        '    _release_original_staging()\n    print(\n        json.dumps(\n            {\n                "status": "installed",',
    )
    # Constants are revision-bound producer coordinates, never ambient inputs.
    for name, value in (
        ("PACKET_SHA", staging["envelope_sha256"]),
        ("PAYLOAD_SHA", staging["payload_sha256"]),
        ("ARCHIVE", staging["archive"]),
    ):
        node = next(
            node
            for node in original_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
        )
        segment = ast.get_source_segment(original.decode(), node)
        if segment is None:
            raise ValueError("original_driver_constant_missing")
        text = text.replace(segment, f"{name} = {value!r}", 1)
    marker = '\nif __name__ == "__main__":'
    if text.count(marker) != 1 or text.count("    _release_original_staging()\n") != 1:
        raise ValueError("original_driver_shape_changed")
    declarations = (
        "\n_STAGING = json.loads("
        + repr(config)
        + ")\n_SEED_BODIES = "
        + repr(seeds)
        + "\n"
    )
    runtime = _RUNTIME
    if profile in (
        COMPACT_PROFILE,
        RECORDED_PROFILE,
        SEALED_PROFILE,
        PACKED_PROFILE,
        COMPRESSED_PROFILE,
        BORROWED_PROFILE,
        RETIRED_PROFILE,
        RECEIPT_PROFILE,
    ):
        selected = (
            "RECEIPT"
            if profile == RECEIPT_PROFILE
            else "RETIRED"
            if profile == RETIRED_PROFILE
            else "BORROWED"
            if profile == BORROWED_PROFILE
            else "COMPRESSED"
            if profile == COMPRESSED_PROFILE
            else "PACKED"
            if profile == PACKED_PROFILE
            else "SEALED"
            if profile == SEALED_PROFILE
            else "RECORDED"
            if profile == RECORDED_PROFILE
            else "COMPACT"
        )
        runtime = runtime.replace(
            "loader.STAGING_BOUND_PROFILE", "loader." + selected + "_STAGING_PROFILE"
        )
        if selected == "RECEIPT":
            runtime = runtime.replace(
                "        loader.RECEIPT_STAGING_PROFILE,\n",
                "        loader.RECEIPT_STAGING_PROFILE,\n"
                "        initial_modules=loader.RECEIPT_INITIAL_MODULES,\n",
                1,
            )
        runtime = runtime.replace(
            "profile=driver.PROFILE",
            "profile=driver."
            + ("RECORDED" if selected in ("SEALED", "PACKED") else selected)
            + "_PROFILE",
        )
    rendered = text.replace(marker, declarations + runtime + marker)
    ast.parse(rendered)
    return rendered.encode()


def _apply_literal_overrides(tree, table, pins):
    declarations = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == table
            for target in node.targets
        )
    ]
    if len(declarations) != 1 or not isinstance(declarations[0].value, ast.Call):
        raise ValueError("exact_compact_source_pin_table_required")
    overrides = declarations[0].value.args[0]
    if not isinstance(overrides, ast.Dict):
        raise TypeError("literal_compact_source_overrides_required")
    for key, value in zip(overrides.keys, overrides.values, strict=True):
        if key is not None:
            pins[ast.literal_eval(key)] = ast.literal_eval(value)
