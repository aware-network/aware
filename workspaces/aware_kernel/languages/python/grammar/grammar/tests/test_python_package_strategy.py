from __future__ import annotations

import json
from pathlib import Path

from aware_meta.graph.config.package_strategy import ObjectConfigGraphPackageSpec
from python_grammar.package_strategy import PythonPackageStrategy
import python_grammar.materialization_outputs as materialization_outputs_module
import python_grammar.package_strategy as package_strategy_module


def test_service_protocol_pyproject_deps_follow_bootstrap_import_roots(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    bootstrap_path = render_root / "_aware" / "python.bootstrap.json"
    bootstrap_path.parent.mkdir(parents=True)
    bootstrap_path.write_text(
        json.dumps(
            {
                "dependency_import_roots": ["aware_environment_service_api"],
                "modules": ["aware_environment_service_protocol.protocols"],
                "package_prefix": "aware_environment_service_protocol",
                "version": "v1",
            }
        ),
        encoding="utf-8",
    )
    module_path = render_root / "protocols.py"
    module_path.write_text(
        "class AwareEnvironmentServiceProtocol: ...\n", encoding="utf-8"
    )

    output_root = tmp_path / "package"
    strategy = PythonPackageStrategy(render_root)
    _ = strategy.build_package(
        [bootstrap_path, module_path],
        ObjectConfigGraphPackageSpec(
            name="aware_environment_service_protocol",
            package_name="aware_environment_service_protocol",
            import_root="aware_environment_service_protocol",
            dependencies=[
                "aware_environment_service_api",
                "aware_workflow_ontology",
                "aware-utils",
                "pydantic>=2.8.0,<3.0.0",
            ],
            package_root=output_root,
            metadata={
                "aware_package_kind": "api_service_protocol",
                "prunable_dependency_import_roots": [
                    "aware_environment_service_api",
                    "aware_workflow_ontology",
                ],
            },
        ),
    )

    pyproject = (output_root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"aware_environment_service_api"' in pyproject
    assert '"aware-utils"' in pyproject
    assert '"pydantic>=2.8.0,<3.0.0"' in pyproject
    assert "aware_workflow_ontology" not in pyproject


def test_ontology_dto_pyproject_drops_unreferenced_aware_dependency(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    bootstrap_path = render_root / "_aware" / "python.bootstrap.json"
    bootstrap_path.parent.mkdir(parents=True)
    bootstrap_path.write_text(
        json.dumps(
            {
                "dependency_import_roots": ["aware_content_ontology_dto"],
                "modules": ["aware_environment_ontology_dto.process.process"],
                "package_prefix": "aware_environment_ontology_dto",
                "version": "v1",
            }
        ),
        encoding="utf-8",
    )
    module_path = render_root / "process" / "process.py"
    module_path.parent.mkdir(parents=True)
    module_path.write_text("class Process: ...\n", encoding="utf-8")

    output_root = tmp_path / "package"
    strategy = PythonPackageStrategy(render_root)
    _ = strategy.build_package(
        [bootstrap_path, module_path],
        ObjectConfigGraphPackageSpec(
            name="aware-environment-ontology-dto",
            package_name="aware-environment-ontology-dto",
            import_root="aware_environment_ontology_dto",
            dependencies=[
                "aware-content-ontology-dto",
                "aware-workflow-ontology-dto",
            ],
            package_root=output_root,
            metadata={
                "aware_package_kind": "ontology_dto",
                "prunable_dependency_import_roots": [
                    "aware_content_ontology_dto",
                    "aware_workflow_ontology_dto",
                ],
            },
        ),
    )

    pyproject = (output_root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"aware-content-ontology-dto"' in pyproject
    assert "aware-workflow-ontology-dto" not in pyproject


def test_contract_pyproject_prunes_explicit_semantic_roots_without_aware_name(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    bootstrap_path = render_root / "_aware" / "python.bootstrap.json"
    bootstrap_path.parent.mkdir(parents=True)
    bootstrap_path.write_text(
        json.dumps(
            {
                "dependency_import_roots": ["sensor_contracts"],
                "modules": ["field_gateway_dto.models"],
                "package_prefix": "field_gateway_dto",
                "version": "v1",
            }
        ),
        encoding="utf-8",
    )
    module_path = render_root / "models.py"
    module_path.write_text("class GatewayReading: ...\n", encoding="utf-8")

    output_root = tmp_path / "package"
    strategy = PythonPackageStrategy(render_root)
    _ = strategy.build_package(
        [bootstrap_path, module_path],
        ObjectConfigGraphPackageSpec(
            name="field-gateway-dto",
            package_name="field-gateway-dto",
            import_root="field_gateway_dto",
            dependencies=[
                "sensor-contracts",
                "graph-runtime",
                "pydantic>=2.8.0,<3.0.0",
            ],
            package_root=output_root,
            metadata={
                "aware_package_kind": "api_dto",
                "prunable_dependency_import_roots": [
                    "sensor_contracts",
                    "graph_runtime",
                ],
            },
        ),
    )

    pyproject = (output_root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"sensor-contracts"' in pyproject
    assert "graph-runtime" not in pyproject
    assert '"pydantic>=2.8.0,<3.0.0"' in pyproject


def test_pydantic_model_dependency_roots_follow_type_checking_imports(
    tmp_path: Path,
) -> None:
    import_root_dir = tmp_path / "field_gateway_dto"
    module_path = import_root_dir / "models.py"
    module_path.parent.mkdir(parents=True)
    module_path.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "from typing import TYPE_CHECKING",
                "from unsafe_runtime.enums import RuntimeEnum",
                "if TYPE_CHECKING:",
                "    from sensor_contracts.models import SensorReading",
                "class GatewayReading:",
                "    reading: SensorReading",
                "    runtime_enum: RuntimeEnum",
            ]
        ),
        encoding="utf-8",
    )

    roots = materialization_outputs_module._type_checking_dependency_import_roots(
        candidate_dependency_roots=["sensor_contracts", "unsafe_runtime"],
        package_files=(module_path,),
        import_root_dir=import_root_dir,
        import_root_name="field_gateway_dto",
    )

    assert roots == ["sensor_contracts"]


def test_api_dto_package_prunes_stale_python_modules_after_layout_change(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    semantic_module = render_root / "environment" / "environment.py"
    semantic_module.parent.mkdir(parents=True)
    semantic_module.write_text("class InvokeFunctionRequest: ...\n", encoding="utf-8")

    output_root = tmp_path / "package"
    import_root = output_root / "aware_environment_service_dto"
    stale_default = import_root / "default"
    stale_default.mkdir(parents=True)
    (stale_default / "__init__.py").write_text("# stale\n", encoding="utf-8")
    (stale_default / "invoke_function_request.py").write_text(
        "class InvokeFunctionRequest: ...\n",
        encoding="utf-8",
    )

    strategy = PythonPackageStrategy(render_root)
    _ = strategy.build_package(
        [semantic_module],
        ObjectConfigGraphPackageSpec(
            name="aware-environment-service-dto",
            package_name="aware-environment-service-dto",
            import_root="aware_environment_service_dto",
            package_root=output_root,
            metadata={"aware_package_kind": "api_dto"},
        ),
    )

    assert (import_root / "environment" / "environment.py").is_file()
    assert not (stale_default / "invoke_function_request.py").exists()
    assert not (stale_default / "__init__.py").exists()
    assert (import_root / "__init__.py").is_file()


def test_package_strategy_strips_rendered_import_root_prefix(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    rendered_module = (
        render_root / "aware_storage_ontology_dto" / "blob" / "storage_blob.py"
    )
    rendered_module.parent.mkdir(parents=True)
    rendered_module.write_text("class StorageBlob: ...\n", encoding="utf-8")

    output_root = tmp_path / "package"
    nested_stale = (
        output_root
        / "aware_storage_ontology_dto"
        / "aware_storage_ontology_dto"
        / "stale.py"
    )
    nested_stale.parent.mkdir(parents=True)
    nested_stale.write_text("# stale duplicate\n", encoding="utf-8")

    strategy = PythonPackageStrategy(render_root)
    result = strategy.build_package(
        [rendered_module],
        ObjectConfigGraphPackageSpec(
            name="aware-storage-ontology-dto",
            package_name="aware-storage-ontology-dto",
            import_root="aware_storage_ontology_dto",
            package_root=output_root,
            metadata={"aware_package_kind": "ontology_dto"},
        ),
    )
    files = result.files

    expected_module = (
        output_root / "aware_storage_ontology_dto" / "blob" / "storage_blob.py"
    )
    duplicate_module = (
        output_root
        / "aware_storage_ontology_dto"
        / "aware_storage_ontology_dto"
        / "blob"
        / "storage_blob.py"
    )
    assert expected_module in files
    assert expected_module.is_file()
    assert not duplicate_module.exists()
    assert not nested_stale.exists()


def test_package_strategy_canonicalizes_python_sources_before_changed_detection(
    tmp_path: Path,
) -> None:
    render_root = tmp_path / "render"
    rendered_module = render_root / "models" / "device.py"
    rendered_module.parent.mkdir(parents=True)
    rendered_module.write_text("value={'name':'demo'}\n", encoding="utf-8")

    output_root = tmp_path / "package"
    strategy = PythonPackageStrategy(render_root)
    first = strategy.build_package(
        [rendered_module],
        ObjectConfigGraphPackageSpec(
            name="aware-demo-ontology",
            package_name="aware-demo-ontology",
            import_root="aware_demo_ontology",
            package_root=output_root,
            metadata={"aware_package_kind": "ontology"},
        ),
    )

    packaged_module = output_root / "aware_demo_ontology" / "models" / "device.py"
    assert packaged_module.read_text(encoding="utf-8") == ('value = {"name": "demo"}\n')
    assert packaged_module.resolve() in first.changed_files

    second = strategy.build_package(
        [rendered_module],
        ObjectConfigGraphPackageSpec(
            name="aware-demo-ontology",
            package_name="aware-demo-ontology",
            import_root="aware_demo_ontology",
            package_root=output_root,
            metadata={"aware_package_kind": "ontology"},
        ),
    )

    assert packaged_module in second.files
    assert second.changed_files == []


def test_package_strategy_skips_canonicalizer_when_copy_bytes_match(
    tmp_path: Path,
    monkeypatch,
) -> None:
    render_root = tmp_path / "render"
    rendered_module = render_root / "models" / "device.py"
    rendered_module.parent.mkdir(parents=True)
    rendered_module.write_text('value = {"name": "demo"}\n', encoding="utf-8")

    packaged_module = tmp_path / "package" / "models" / "device.py"
    packaged_module.parent.mkdir(parents=True)
    packaged_module.write_text('value = {"name": "demo"}\n', encoding="utf-8")

    canonicalizer_calls: list[Path] = []

    def _unexpected_canonicalizer(*, path: Path, content: str) -> str:
        _ = content
        canonicalizer_calls.append(path)
        raise AssertionError("byte-identical Python package copy must skip Black")

    monkeypatch.setattr(
        package_strategy_module,
        "_canonicalize_python_package_text",
        _unexpected_canonicalizer,
    )

    strategy = PythonPackageStrategy(render_root)

    assert strategy._copy_if_changed(rendered_module, packaged_module) is False
    assert canonicalizer_calls == []


def test_package_strategy_dependency_pruning_has_no_package_name_hardcodes() -> None:
    source = Path(package_strategy_module.__file__).read_text(encoding="utf-8")

    forbidden_fragments = (
        "_is_generated_aware_contract_dependency",
        'startswith("aware_',
        "startswith('aware_",
        "import_root_path.name.endswith",
        'endswith("_ontology',
        "endswith('_ontology",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source
