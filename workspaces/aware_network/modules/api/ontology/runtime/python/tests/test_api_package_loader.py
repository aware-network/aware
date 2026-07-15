from __future__ import annotations

from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from aware_api_runtime.manifest.loader import (  # noqa: E402
    AwareApiTomlError,
    load_aware_api_toml_spec_from_text,
)
from aware_api_runtime.manifest.spec import (  # noqa: E402
    AwareApiCompilationMode,
)


def test_loader_defaults_compilation_mode_to_raw_xor() -> None:
    spec = load_aware_api_toml_spec_from_text(
        toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"
""",
        toml_path="aware.api.toml",
    )

    assert spec.build.compilation_mode == AwareApiCompilationMode.raw_xor


def test_loader_accepts_api_ontology_compilation_mode() -> None:
    spec = load_aware_api_toml_spec_from_text(
        toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"
compilation_mode = "api_ontology"
""",
        toml_path="aware.api.toml",
    )

    assert spec.build.compilation_mode == AwareApiCompilationMode.api_ontology


def test_loader_defaults_api_dto_semantic_export_code_package_surface() -> None:
    spec = load_aware_api_toml_spec_from_text(
        toml_text="""
aware_api = 1

[api]
package_name = "demo-service-api"
fqn_prefix = "demo_service_api"

[build]
sources_dir = "bindings"
compilation_mode = "api_ontology"

[[semantic_package_exports]]
kind = "api_dto"
package_name = "demo-service-dto"
manifest_path = "dto/aware.toml"
""",
        toml_path="aware.api.toml",
    )

    assert len(spec.semantic_package_exports) == 1
    export = spec.semantic_package_exports[0]
    assert export.code_package_surface == "api"
    assert export.semantic_provider_key == "aware_api"
    assert export.semantic_package_family == "api"
    assert export.semantic_package_kind == "api_dto_package"
    assert export.semantic_contract_provider_key == "aware_api"
    assert export.semantic_contract_module == "aware_api_runtime.semantic_contract"


def test_loader_rejects_unknown_compilation_mode() -> None:
    with pytest.raises(AwareApiTomlError, match="compilation_mode"):
        _ = load_aware_api_toml_spec_from_text(
            toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"
compilation_mode = "future_magic"
""",
            toml_path="aware.api.toml",
        )


def test_loader_accepts_python_language_root_and_product_package_dirs() -> None:
    spec = load_aware_api_toml_spec_from_text(
        toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"

[targets.python]
root_dir = "generated/python"

[targets.python.public_package]
package_dir = "demo_public"

[targets.python.service_protocol]
package_dir = "demo_protocol"
""",
        toml_path="aware.api.toml",
    )

    assert spec.targets.python is not None
    assert spec.targets.python.root_dir == "generated/python"
    assert spec.targets.python.public_package.package_dir == "demo_public"
    assert spec.targets.python.service_protocol.package_dir == "demo_protocol"


def test_loader_accepts_legacy_python_product_root_dirs_for_compatibility() -> None:
    spec = load_aware_api_toml_spec_from_text(
        toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"

[targets.python.public_package]
root_dir = "python/demo_public"
""",
        toml_path="aware.api.toml",
    )

    assert spec.targets.python is not None
    assert spec.targets.python.public_package.root_dir == "python/demo_public"


def test_loader_accepts_dart_language_root_and_public_package_dir() -> None:
    spec = load_aware_api_toml_spec_from_text(
        toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"

[targets.dart]
root_dir = "generated/dart"

[targets.dart.public_package]
package_dir = "demo_public"
""",
        toml_path="aware.api.toml",
    )

    assert spec.targets.dart is not None
    assert spec.targets.dart.root_dir == "generated/dart"
    assert spec.targets.dart.public_package.package_dir == "demo_public"


def test_loader_rejects_dart_public_package_dir_with_parent_escape() -> None:
    with pytest.raises(AwareApiTomlError, match="package_dir"):
        _ = load_aware_api_toml_spec_from_text(
            toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"

[targets.dart.public_package]
package_dir = "../demo_public"
""",
            toml_path="aware.api.toml",
        )


def test_loader_rejects_python_language_root_dir_with_parent_escape() -> None:
    with pytest.raises(AwareApiTomlError, match="root_dir"):
        _ = load_aware_api_toml_spec_from_text(
            toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"

[targets.python]
root_dir = "../python"
""",
            toml_path="aware.api.toml",
        )


def test_loader_rejects_python_product_package_dir_with_parent_escape() -> None:
    with pytest.raises(AwareApiTomlError, match="package_dir"):
        _ = load_aware_api_toml_spec_from_text(
            toml_text="""
aware_api = 1

[api]
package_name = "demo-api"
fqn_prefix = "demo_api"

[build]
sources_dir = "apis"

[targets.python.public_package]
package_dir = "../demo_public"
""",
            toml_path="aware.api.toml",
        )
