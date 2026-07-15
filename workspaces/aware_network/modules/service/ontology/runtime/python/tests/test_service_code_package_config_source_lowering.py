from __future__ import annotations

import json
from pathlib import Path

from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
)
from aware_service_ontology.service.service_enums import (
    ServiceConfigCodePackageConfigCardinality,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_code_package_config_id,
    stable_service_config_id,
)
from aware_service_runtime.builder import (
    build_service_compile_plan,
    emit_service_compile_plan_artifact,
)
from aware_service_runtime.materialization.service import (
    resolve_service_definition_materialization_specs,
)
from aware_service_runtime.materialization.snapshot_commit import (
    ServiceDefinitionCodePackageConfigSnapshot,
    _build_service_config_definition_snapshot_objects,
)
from aware_service_runtime.workspace import ServiceWorkspace


def test_service_code_package_config_source_lowers_to_compile_plan(
    tmp_path: Path,
) -> None:
    toml_path = _write_service_toml(tmp_path)
    _write_service_source(tmp_path)

    snapshot = ServiceWorkspace.from_toml(
        toml_path=toml_path, repo_root=tmp_path
    ).build_snapshot()
    plan = build_service_compile_plan(snapshot=snapshot)

    config_key = code_package_source_config_key(
        manifest_kind="aware_experience_toml",
        surface="experience",
    )
    expected_code_package_config_id = stable_code_package_config_id(
        config_key=config_key
    )

    ownership_slot = plan.service_ownership[0].code_package_configs[0]
    assert ownership_slot.slot_key == "experience"
    assert ownership_slot.manifest_kind == "aware_experience_toml"
    assert ownership_slot.surface == "experience"
    assert ownership_slot.cardinality == "many"
    assert ownership_slot.required is True

    config_slot = plan.service_configs[0].code_package_configs[0]
    assert config_slot.slot_key == "experience"
    assert config_slot.manifest_kind == "aware_experience_toml"
    assert config_slot.surface == "experience"
    assert config_slot.code_package_config_key == config_key
    assert config_slot.code_package_config_id == expected_code_package_config_id
    assert config_slot.cardinality == "many"
    assert config_slot.required is True

    artifact = emit_service_compile_plan_artifact(
        plan=plan,
        runtime_package_dir=tmp_path / "runtime",
        repo_root=tmp_path,
    )
    payload = json.loads(artifact.path.read_text(encoding="utf-8"))
    serialized_slot = payload["service_configs"][0]["code_package_configs"][0]
    assert serialized_slot == {
        "cardinality": "many",
        "code_package_config_id": str(expected_code_package_config_id),
        "code_package_config_key": config_key,
        "manifest_kind": "aware_experience_toml",
        "required": True,
        "slot_key": "experience",
        "source_path": "services/bindings/experience.services.aware",
        "surface": "experience",
    }
    decoded_specs = resolve_service_definition_materialization_specs(
        compile_plan_payloads=(payload,)
    )
    decoded_slot = decoded_specs[0].service_config.code_package_configs[0]
    assert decoded_slot == config_slot


def test_service_config_definition_snapshot_includes_code_package_config_bridge() -> (
    None
):
    service_config_id = stable_service_config_id(name="aware_experience")
    config_key = code_package_source_config_key(
        manifest_kind="aware_experience_toml",
        surface="experience",
    )
    code_package_config_id = stable_code_package_config_id(config_key=config_key)
    expected_bridge_id = stable_service_config_code_package_config_id(
        service_config_id=service_config_id,
        code_package_config_id=code_package_config_id,
        slot_key="experience",
    )

    service_config, objects_by_id = _build_service_config_definition_snapshot_objects(
        name="aware_experience",
        apis=(),
        experiences=(),
        code_package_configs=(
            ServiceDefinitionCodePackageConfigSnapshot(
                slot_key="experience",
                code_package_config_id=code_package_config_id,
                cardinality="many",
                required=True,
            ),
        ),
        operations=(),
        contract_configs=(),
    )

    assert service_config.id == service_config_id
    assert len(service_config.code_package_configs) == 1
    bridge = service_config.code_package_configs[0]
    assert bridge.id == expected_bridge_id
    assert bridge.slot_key == "experience"
    assert bridge.code_package_config_id == code_package_config_id
    assert bridge.cardinality is ServiceConfigCodePackageConfigCardinality.many
    assert bridge.required is True
    assert objects_by_id[expected_bridge_id] is bridge


def _write_service_toml(root: Path) -> Path:
    toml_path = root / "aware.service.toml"
    toml_path.write_text(
        "\n".join(
            [
                "aware_service = 1",
                "",
                "[service]",
                'package_name = "aware-experience-service"',
                'fqn_prefix = "aware_experience_service"',
                "",
                "[build]",
                'sources_dir = "services/bindings"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "service_ontology"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return toml_path


def _write_service_source(root: Path) -> Path:
    path = root / "services" / "bindings" / "experience.services.aware"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """\
service aware_experience {
    api experience;

    package experience {
        manifest aware_experience_toml;
        surface experience;
        cardinality many;
        required true;
    }

    operation resolve_experience_package_projection_ownership {
        endpoint experience.package_materialization.resolve_experience_package_projection_ownership;
    }
}
""",
        encoding="utf-8",
    )
    return path
