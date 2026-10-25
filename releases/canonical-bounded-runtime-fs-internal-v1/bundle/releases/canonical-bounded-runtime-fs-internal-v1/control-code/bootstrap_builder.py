"""Deterministic bootstrap packaging of the exact accepted whole-envelope port.

Producer source successor, not a change to the retained 0.1.3 wheel. The
standalone payload imports only its byte-identical relocated stdlib module.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from dataclasses import asdict
from pathlib import Path

from .whole_envelope import WholeEnvelopeArtifact

ACCEPTED_WHEEL_SHA256 = (
    "55b43040847e081c919cfcdb41d19c1debb12949106328f673ac4e80dc1c7323"
)
ACCEPTED_SOURCE_REVISION = "51fd7c480e8d7e8d37e06dba39a6a2525d2c5509"
ACCEPTED_PORT_SHA256 = (
    "043d801def1dbea82fd672915218b8c03674f30deb7f41c174ec0604f2768ce2"
)
SCHEMA = "aware.whole-envelope-bootstrap.v1"
SUPPLIED_SCHEMA = "aware.whole-envelope-bootstrap.supplied.v1"


def build_whole_envelope_bootstrap(
    *, wheel: Path, artifact: WholeEnvelopeArtifact, output: Path
) -> Path:
    """Write a fresh pyz from qualified wheel bytes; never install or activate."""
    if type(artifact) is not WholeEnvelopeArtifact:
        raise TypeError("typed_whole_envelope_artifact_required")
    if not wheel.is_absolute() or not output.is_absolute():
        raise ValueError("absolute_build_paths_required")
    if wheel.is_symlink() or not wheel.is_file():
        raise ValueError("bound_regular_wheel_required")
    body = wheel.read_bytes()
    if hashlib.sha256(body).hexdigest() != ACCEPTED_WHEEL_SHA256:
        raise ValueError("qualified_release_wheel_required")
    with zipfile.ZipFile(io.BytesIO(body)) as source:
        port = source.read("aware_release/install_distribution/whole_envelope.py")
        license_body = source.read("aware_release-0.1.3.dist-info/licenses/LICENSE")
    if hashlib.sha256(port).hexdigest() != ACCEPTED_PORT_SHA256:
        raise ValueError("qualified_port_required")
    main = Path(__file__).with_name("whole_envelope_bootstrap_main.py").read_bytes()
    descriptor = {
        "schema": SCHEMA,
        "artifact": asdict(artifact),
        "release_library": {
            "version": "0.1.3",
            "wheel_sha256": ACCEPTED_WHEEL_SHA256,
            "source_revision": ACCEPTED_SOURCE_REVISION,
            "port_sha256": ACCEPTED_PORT_SHA256,
        },
        "entrypoint_sha256": hashlib.sha256(main).hexdigest(),
        "activation": "not_requested",
    }
    members = {
        "__main__.py": main,
        # Exact bytes, relocated without importing the broad package __init__.
        "whole_envelope.py": port,
        "LICENSE": license_body,
        "release.json": (
            json.dumps(descriptor, sort_keys=True, indent=2) + "\n"
        ).encode(),
    }
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in sorted(members.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, payload)
    return output


def build_supplied_runtime_bootstrap(
    *,
    artifact: WholeEnvelopeArtifact,
    runtime_profile: dict,
    source_revision: str,
    expected_port_sha256: str,
    expected_main_sha256: str,
    expected_license_sha256: str,
    output: Path,
) -> Path:
    """Exact original source-bound successor, not a changed old library wheel.

    Publisher-supplied revision/digests require external qualification. This
    packaging step does not authenticate source provenance or admit execution.
    Runtime root/inode are intentionally absent from the portable descriptor;
    the original port observes them at preview and binds them to its fingerprint.
    """
    if (
        type(artifact) is not WholeEnvelopeArtifact
        or artifact.runtime_mode != "supplied"
    ):
        raise ValueError("explicit_supplied_artifact_required")
    if not output.is_absolute() or output.is_symlink():
        raise ValueError("absolute_fresh_bootstrap_output_required")
    if (
        type(source_revision) is not str
        or re.fullmatch(r"[0-9a-f]{40}", source_revision) is None
    ):
        raise ValueError("exact_source_revision_required")
    if type(runtime_profile) is not dict or set(runtime_profile) != {
        "python_sha256",
        "python_version",
        "bootstrap_sha256",
        "archive_sha256",
        "roster_sha256",
    }:
        raise ValueError("closed_supplied_runtime_profile_required")
    runtime_profile = dict(runtime_profile)
    for key in ("python_sha256", "bootstrap_sha256", "archive_sha256", "roster_sha256"):
        value = runtime_profile[key]
        if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError("exact_supplied_runtime_digest_required")
    version = runtime_profile["python_version"]
    if (
        type(version) not in (tuple, list)
        or len(version) != 3
        or any(type(v) is not int or not 0 <= v <= 255 for v in version)
        or tuple(version[:2]) != (3, 12)
    ):
        raise ValueError("exact_supplied_python_version_required")
    runtime_profile["python_version"] = list(version)
    port_path = Path(__file__).with_name("whole_envelope.py")
    main_path = Path(__file__).with_name("whole_envelope_bootstrap_main.py")
    license_path = Path(__file__).parents[2] / "LICENSE"
    blobs = []
    for path, expected in (
        (port_path, expected_port_sha256),
        (main_path, expected_main_sha256),
        (license_path, expected_license_sha256),
    ):
        if path.is_symlink() or not path.is_file():
            raise ValueError("regular_original_bootstrap_source_required")
        body = path.read_bytes()
        if type(expected) is not str or hashlib.sha256(body).hexdigest() != expected:
            raise ValueError("reviewed_original_bootstrap_source_changed")
        blobs.append(body)
    port, main, license_body = blobs
    descriptor = {
        "schema": SUPPLIED_SCHEMA,
        "artifact": asdict(artifact),
        "supplied_runtime": runtime_profile,
        "release_library": {
            "source_revision": source_revision,
            "port_sha256": expected_port_sha256,
            "qualification": "source_bound_successor_no_installed_package_claim",
        },
        "entrypoint_sha256": expected_main_sha256,
        "license_sha256": expected_license_sha256,
        "activation": "not_requested",
    }
    members = {
        "whole_envelope.py": port,
        "__main__.py": main,
        "LICENSE": license_body,
        "release.json": (
            json.dumps(descriptor, sort_keys=True, indent=2) + "\n"
        ).encode(),
    }
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in sorted(members.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, payload)
    return output
