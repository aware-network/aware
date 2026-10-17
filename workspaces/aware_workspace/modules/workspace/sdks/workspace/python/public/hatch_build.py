"""Compile the optional private formatter using the selected Python toolchain.

The same function serves Hatch and disposable source qualification. It installs
nothing, changes no source and returns compilation evidence, never authority.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types
from pathlib import Path
from typing import Any

_JSON_CODE_FIELDS = (
    "co_argcount",
    "co_posonlyargcount",
    "co_kwonlyargcount",
    "co_nlocals",
    "co_stacksize",
    "co_flags",
    "co_code",
    "co_consts",
    "co_names",
    "co_varnames",
    "co_filename",
    "co_name",
    "co_qualname",
    "co_firstlineno",
    "co_linetable",
    "co_exceptiontable",
    "co_freevars",
    "co_cellvars",
)


def _json_profile_model(value: object) -> object:
    if type(value) is types.CodeType:
        return [
            "code",
            *(_json_profile_model(getattr(value, name)) for name in _JSON_CODE_FIELDS),
        ]
    if type(value) is bytes:
        return ["bytes", value.hex()]
    if type(value) is tuple:
        return ["tuple", *(_json_profile_model(item) for item in value)]
    if type(value) is dict:
        return [
            "dict",
            *[
                [_json_profile_model(key), _json_profile_model(item)]
                for key, item in value.items()
            ],
        ]
    if value is None or type(value) in (bool, int, str):
        return value
    raise TypeError("Unsupported original JSON declaration")


def _json_profile_key(value: object) -> bytes:
    if value is None:
        return b"\x00"
    if type(value) is bool:
        return b"\x01" + bytes([int(value)])
    if type(value) is int:
        if value < -(2**63) or value > 2**64:
            raise TypeError("Original JSON declaration integer exceeds profile")
        if value == 2**64:
            return b"\x02\x02" + bytes(8)
        return (
            b"\x02"
            + bytes([int(value < 0)])
            + (value & ((1 << 64) - 1)).to_bytes(8, "little")
        )
    if type(value) is str:
        text = value.encode("utf-8", "surrogatepass")
        return b"\x03" + len(text).to_bytes(8, "little") + text
    if type(value) is list:
        return (
            b"\x04"
            + len(value).to_bytes(8, "little")
            + b"".join(_json_profile_key(item) for item in value)
        )
    raise TypeError("Unsupported original JSON profile")


def _json_profile_header() -> tuple[str, list[dict[str, str | int]]]:
    functions = [
        json.dumps,
        *(
            getattr(json.JSONEncoder, name)
            for name in ("__init__", "encode", "iterencode", "default")
        ),
        dataclasses.fields,
    ]
    header = [
        "#include <stddef.h>",
        f"#define WORKSPACE_JSON_PROFILE_COUNT {len(functions)}",
        "#define WORKSPACE_JSON_PROFILE_FIELD_COUNT 18",
        "static const char *index_json_profile_fields[] = {"
        + ",".join(json.dumps(name) for name in _JSON_CODE_FIELDS)
        + "};",
    ]
    pins = []
    for ordinal, function in enumerate(functions):
        model = [
            _json_profile_model(function.__code__),
            _json_profile_model(function.__defaults__),
            _json_profile_model(function.__kwdefaults__),
        ]
        key = _json_profile_key(model)
        if len(key) > 262144:
            raise ValueError("Original JSON declaration exceeds build quota")
        header.append(
            "static const unsigned char index_json_profile_"
            + str(ordinal)
            + "[] = {"
            + ",".join(map(str, key))
            + "};"
        )
        pins.append(
            {
                "function": function.__qualname__,
                "size": len(key),
                "sha256": hashlib.sha256(key).hexdigest(),
            }
        )
    header.append(
        "static const unsigned char *index_json_profiles[] = {"
        + ",".join("index_json_profile_" + str(i) for i in range(len(functions)))
        + "};"
    )
    header.append(
        "static const size_t index_json_profile_sizes[] = {"
        + ",".join(str(pin["size"]) for pin in pins)
        + "};"
    )
    return "\n".join(header) + "\n", pins


def compile_native(
    root: Path, output_directory: Path, *, diagnostic_counters: bool = False
) -> dict[str, Any]:
    if type(diagnostic_counters) is not bool:
        raise TypeError("exact diagnostic build selection required")
    root = root.resolve(strict=True)
    output_directory = output_directory.resolve(strict=True)
    if not output_directory.is_dir():
        raise ValueError("an existing output directory is required")
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        return {"status": "portable", "reason": "unsupported_python"}
    if sys.platform != "linux":
        return {"status": "portable", "reason": "unsupported_platform"}
    linker = shlex.split(sysconfig.get_config_var("LDSHARED") or "")
    if not linker or (executable := shutil.which(linker[0])) is None:
        return {"status": "portable", "reason": "compiler_unavailable"}
    source = root / "aware_workspace_sdk" / "_tree_native.c"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if type(suffix) is not str or not suffix.startswith(".") or "/" in suffix:
        raise RuntimeError("exact native extension suffix is unavailable")
    target = output_directory / ("_tree_native" + suffix)
    includes = list(
        dict.fromkeys(
            str(Path(path).resolve(strict=True))
            for path in (
                sysconfig.get_path("include"),
                sysconfig.get_path("platinclude"),
            )
        )
    )
    with tempfile.TemporaryDirectory(
        prefix="workspace-tree-build-", dir=output_directory
    ) as temporary:
        pending = Path(temporary) / target.name
        profile, profile_pins = _json_profile_header()
        profile_path = Path(temporary) / "workspace-json-profile.h"
        profile_path.write_text(profile, encoding="utf-8")
        profile_hash = hashlib.sha256(profile.encode()).hexdigest()
        command = [
            executable,
            *linker[1:],
            "-O3",
            "-g0",
            "-fPIC",
            "-fno-strict-aliasing",
            *(["-DWORKSPACE_FORMATTER_COSTS=1"] if diagnostic_counters else []),
            "-ffile-prefix-map=" + str(root) + "=.",
            *["-I" + path for path in includes],
            "-include",
            str(profile_path),
            str(source),
            "-o",
            str(pending),
        ]
        result = subprocess.run(
            command, cwd=root, capture_output=True, text=True, timeout=120, check=False
        )
        if result.returncode:
            raise RuntimeError("native metadata compilation failed: " + result.stderr)
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
            raise RuntimeError("native metadata source changed during compilation")
        binary_hash = hashlib.sha256(pending.read_bytes()).hexdigest()
        os.replace(pending, target)
    return {
        "status": "compiled",
        "diagnostic_counters": diagnostic_counters,
        "source": str(source),
        "source_sha256": source_hash,
        "artifact": str(target),
        "artifact_sha256": binary_hash,
        "compiler": executable,
        "compiler_sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
        "command": command,
        "python": platform.python_version(),
        "soabi": sysconfig.get_config_var("SOABI"),
        "stderr": result.stderr,
        "json_profile_header_sha256": profile_hash,
        "json_profile_pins": profile_pins,
        "json_profile_header": profile,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--diagnostic-counters", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            compile_native(
                Path(__file__).parent,
                args.output_directory,
                diagnostic_counters=args.diagnostic_counters,
            ),
            indent=2,
        )
    )
else:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface

    class CustomBuildHook(BuildHookInterface):
        """No runtime compilation or optional build dependency installation."""

        PLUGIN_NAME = "custom"

        def initialize(self, version: str, build_data: dict[str, Any]) -> None:
            if self.target_name != "wheel":
                return
            self._native_directory = tempfile.TemporaryDirectory(
                prefix="workspace-tree-wheel-"
            )
            try:
                evidence = compile_native(
                    Path(self.root), Path(self._native_directory.name)
                )
                if evidence["status"] == "compiled":
                    build_data["force_include"][evidence["artifact"]] = (
                        "aware_workspace_sdk/" + Path(evidence["artifact"]).name
                    )
                    build_data["pure_python"] = False
                    interpreter = f"cp{sys.version_info.major}{sys.version_info.minor}"
                    local_platform = (
                        sysconfig.get_platform().replace("-", "_").replace(".", "_")
                    )
                    build_data["tag"] = (
                        f"{interpreter}-{interpreter}{sys.abiflags}-{local_platform}"
                    )
            except BaseException:
                self._native_directory.cleanup()
                raise

        def finalize(
            self, version: str, build_data: dict[str, Any], artifact_path: str
        ) -> None:
            directory = getattr(self, "_native_directory", None)
            if directory is not None:
                directory.cleanup()
