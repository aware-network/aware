"""Build the separately admitted CPython preparation scanner from exact inputs.

The hook does not install a compiler, headers, packages, or a runtime backend.
Its binary and receipt live in a temporary build directory, and wheel mapping
is explicit. The authored lock is required before any compiler execution.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shlex
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path
from typing import Any

_BUILD_REFUSAL_01 = "preparation scan build lock schema mismatch"
_BUILD_REFUSAL_02 = "preparation scan requires the exact admitted runtime ABI"
_BUILD_REFUSAL_03 = "preparation scan source digest differs from build lock"
_BUILD_REFUSAL_04 = "preparation scan compiler is not selected"
_BUILD_REFUSAL_05 = "preparation scan compiler command differs from build lock"
_BUILD_REFUSAL_06 = "preparation scan admitted compiler is unavailable"
_BUILD_REFUSAL_07 = "preparation scan compiler digest differs from build lock"
_BUILD_REFUSAL_08 = "preparation scan Python header digest differs from lock"
_BUILD_REFUSAL_09 = "preparation scan system header digest differs from lock"
_BUILD_REFUSAL_10 = "preparation scan compiler dependency format is ambiguous"
_BUILD_REFUSAL_11 = "preparation scan compiled dependency differs from build lock"
_BUILD_REFUSAL_12 = "preparation scan build input changed during compilation"
_BUILD_REFUSAL_13 = "preparation scan compiler changed during compilation"
_BUILD_REFUSAL_14 = "preparation scan build lock changed during compilation"
_BUILD_REFUSAL_15 = "usage: hatch_build.py SOURCE LOCK EXISTING_OUTPUT_DIRECTORY"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_native(
    source: Path, lock_path: Path, output_directory: Path
) -> dict[str, Any]:
    """Compile the pinned authored source and return exact input/output evidence."""
    source = source.resolve(strict=True)
    lock_path = lock_path.resolve(strict=True)
    output_directory = output_directory.resolve(strict=True)
    lock_bytes = lock_path.read_bytes()
    lock_sha256 = hashlib.sha256(lock_bytes).hexdigest()
    lock = json.loads(lock_bytes)
    if lock["schema"] != "aware.ontology.preparation-scan-build-lock.v0":
        raise RuntimeError(_BUILD_REFUSAL_01)
    runtime = lock["runtime"]
    observed_runtime = {
        "implementation": sys.implementation.name,
        "version": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "pointer_bytes": __import__("struct").calcsize("P"),
        "byteorder": sys.byteorder,
        "extension_suffix": sysconfig.get_config_var("EXT_SUFFIX"),
        "soabi": sysconfig.get_config_var("SOABI"),
        "gil_disabled": bool(sysconfig.get_config_var("Py_GIL_DISABLED")),
        "trace_refs": bool(sysconfig.get_config_var("Py_TRACE_REFS")),
    }
    if observed_runtime != runtime:
        raise RuntimeError(_BUILD_REFUSAL_02)
    if _digest(source) != lock["source_sha256"]:
        raise RuntimeError(_BUILD_REFUSAL_03)
    compiler_command = shlex.split(str(sysconfig.get_config_var("CC")))
    if not compiler_command:
        raise RuntimeError(_BUILD_REFUSAL_04)
    if compiler_command != shlex.split(lock["compiler"]["selected_name"]):
        raise RuntimeError(_BUILD_REFUSAL_05)
    compiler = shutil.which(compiler_command[0])
    if compiler is None:
        raise RuntimeError(_BUILD_REFUSAL_06)
    compiler_path = Path(compiler).resolve(strict=True)
    if _digest(compiler_path) != lock["compiler"]["binary_sha256"]:
        raise RuntimeError(_BUILD_REFUSAL_07)
    include = Path(sysconfig.get_paths()["include"]).resolve(strict=True)
    for relative, digest in lock["python_headers_sha256"].items():
        header = (include / relative).resolve(strict=True)
        if not header.is_relative_to(include) or _digest(header) != digest:
            raise RuntimeError(_BUILD_REFUSAL_08)
    for absolute, digest in lock["system_headers_sha256"].items():
        header = Path(absolute).resolve(strict=True)
        if _digest(header) != digest:
            raise RuntimeError(_BUILD_REFUSAL_09)
    suffix = runtime["extension_suffix"]
    output = output_directory / ("_preparation_scan" + suffix)
    dependencies = output_directory / "preparation-scan.d"
    command = [
        str(compiler_path),
        *compiler_command[1:],
        *lock["compile_flags"],
        "-I",
        str(include),
        "-MD",
        "-MF",
        str(dependencies),
        str(source),
        "-o",
        str(output),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError("preparation scan compiler refused: " + completed.stderr)
    # Compiler dependency output uses standard Make escaping. These selected
    # paths contain no spaces; reject ambiguous escaped paths rather than guess.
    dependency_text = dependencies.read_text().replace("\\\n", " ")
    _, separator, body = dependency_text.partition(":")
    if not separator or "\\" in body:
        raise RuntimeError(_BUILD_REFUSAL_10)
    dependency_paths = [Path(value).resolve(strict=True) for value in body.split()]
    observed_dependencies = {str(path): _digest(path) for path in dependency_paths}
    expected_dependencies = {str(source): lock["source_sha256"]}
    expected_dependencies.update(lock["system_headers_sha256"])
    expected_dependencies.update(
        {
            str((include / relative).resolve()): digest
            for relative, digest in lock["python_headers_sha256"].items()
        }
    )
    if any(
        expected_dependencies.get(path) != digest
        for path, digest in observed_dependencies.items()
    ):
        raise RuntimeError(_BUILD_REFUSAL_11)
    for path, digest in expected_dependencies.items():
        if _digest(Path(path)) != digest:
            raise RuntimeError(_BUILD_REFUSAL_12)
    if _digest(compiler_path) != lock["compiler"]["binary_sha256"]:
        raise RuntimeError(_BUILD_REFUSAL_13)
    if _digest(lock_path) != lock_sha256:
        raise RuntimeError(_BUILD_REFUSAL_14)
    receipt = {
        "schema": "aware.ontology.preparation-scan-build-receipt.v0",
        "source": str(source),
        "source_sha256": _digest(source),
        "lock": str(lock_path),
        "lock_sha256": lock_sha256,
        "compiler": str(compiler_path),
        "compiler_sha256": _digest(compiler_path),
        "runtime": observed_runtime,
        "command": command,
        "dependencies_sha256": observed_dependencies,
        "all_observed_dependencies_locked": True,
        "declared_inputs_unchanged_before_and_after": True,
        "output": str(output),
        "output_sha256": _digest(output),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "runtime_backend_installation": False,
    }
    receipt_path = output_directory / "preparation-scan-build-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(_BUILD_REFUSAL_15)
    result = build_native(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    print(
        json.dumps(
            {"output": result["output"], "output_sha256": result["output_sha256"]}
        )
    )
    raise SystemExit(0)


def get_build_hook() -> type[Any]:
    """Resolve the declared build dependency only for Hatchling's hook loader."""
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface

    # The standalone pinned compiler CLI exits before loading its wheel dependency.

    class CustomBuildHook(BuildHookInterface):
        """Map the one authored source's admitted ABI binary into the wheel."""

        def initialize(self, version: str, build_data: dict[str, Any]) -> None:
            if self.target_name != "wheel":
                return
            root = Path(self.root).resolve(strict=True)
            self._scan_build_directory = tempfile.TemporaryDirectory(
                prefix="aware-preparation-scan-wheel-"
            )
            receipt = build_native(
                root / "aware_ontology_object_facade_client" / "_preparation_scan.c",
                root.parent / "native" / "preparation_scan_build_lock_v0.json",
                Path(self._scan_build_directory.name),
            )
            output = Path(receipt["output"])
            build_data.setdefault("force_include", {})[str(output)] = (
                "aware_ontology_object_facade_client/" + output.name
            )
            build_data["pure_python"] = False
            build_data["infer_tag"] = True

        def finalize(
            self, version: str, build_data: dict[str, Any], artifact_path: str
        ) -> None:
            if self.target_name == "wheel":
                self._scan_build_directory.cleanup()

    return CustomBuildHook
