from __future__ import annotations

from pathlib import Path
from types import ModuleType
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_code.semantic_materialization import (
    SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY,
)
from aware_experience.materialization import lane_state
from aware_experience.materialization import service as materialization_service
from aware_experience.materialization import static_projection_targets
from aware_experience.materialization.source_module_ontology import (
    dto_stable_ids_import_roots_by_module_id_from_context,
    source_module_ontology_dto_stable_ids_import_targets,
)


def test_experience_materialization_service_runtime_import_boundary() -> None:
    source = Path(materialization_service.__file__).read_text(encoding="utf-8")

    assert "from aware_meta.runtime.graph_lane import" in source
    assert "_bind_meta_graph_runtime_lane(" in source
    assert "aware_" + "runtime" not in source
    assert "from aware_" + "runtime.environment.operation.support" not in source
    assert "from aware_" + "runtime.function_call.executor" not in source
    assert "from aware_" + "runtime.function_call.invoker" not in source
    assert "from aware_" + "runtime.graph.identity_chain" not in source
    assert "from aware_" + "runtime.harness.branching" not in source
    assert "from aware_" + "runtime.harness.runtime_harness" not in source
    assert "from aware_" + "runtime.index" not in source
    assert "from aware_" + "runtime.materialization" not in source
    assert "hydrate_orm_graph_" + "from_oig" not in source
    assert "importlib.util" not in source
    assert "spec_from_file_location" not in source
    assert "sys.modules" not in source
    assert "AWARE_ROOT" not in source
    assert ".glob(pattern)" not in source


def test_static_projection_stable_ids_use_declared_dto_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class_config_id = uuid4()
    stable_ids_module = ModuleType("aware_identity_ontology_dto.stable_ids")

    def _stable_demo_id(*, key: str) -> UUID:
        return uuid4()

    setattr(
        stable_ids_module,
        "CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID",
        {
            str(class_config_id): ("stable_demo_id", ("key",)),
        },
    )
    setattr(stable_ids_module, "stable_demo_id", _stable_demo_id)
    imported_modules: list[str] = []

    def _import_module(name: str) -> ModuleType:
        imported_modules.append(name)
        if name == "aware_identity_ontology_dto.stable_ids":
            return stable_ids_module
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr(static_projection_targets.importlib, "import_module", _import_module)
    roots_by_module_id = dto_stable_ids_import_roots_by_module_id_from_context(
        context={
            SEMANTIC_LANGUAGE_MATERIALIZATION_TARGETS_CONTEXT_KEY: [
                {
                    "target_language_plugin_id": "python",
                    "materialization_source": "ontology",
                    "stable_ids_import_root": "aware_identity_ontology",
                },
                {
                    "target_language_plugin_id": "python",
                    "materialization_source": "ontology_orm_models",
                    "stable_ids_import_root": ("aware_identity_ontology_orm_models"),
                },
                {
                    "target_language_plugin_id": "python",
                    "materialization_source": "ontology_dto",
                    "stable_ids_import_root": "aware_identity_ontology_dto",
                },
            ],
        },
    )

    assert roots_by_module_id == {"identity": ("aware_identity_ontology_dto",)}
    stable_fn, arg_names = materialization_service._stable_source_id_binding_for_node(
        node_name="aware_identity.RoleConfig",
        class_config_id=class_config_id,
        dto_stable_ids_import_roots_by_module_id=roots_by_module_id,
    )

    assert stable_fn is _stable_demo_id
    assert arg_names == ("key",)
    assert imported_modules == ["aware_identity_ontology_dto.stable_ids"]


def test_static_projection_stable_ids_include_source_module_ontology_dto_target(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "modules" / "home"
    experience_manifest_path = (
        module_root / "experiences" / "home_story" / "aware.experience.toml"
    )
    ontology_package_manifest_path = module_root / "ontology" / "aware.ontology.toml"
    ontology_source_manifest_path = module_root / "ontology" / "structure" / "aware.toml"
    experience_manifest_path.parent.mkdir(parents=True)
    ontology_package_manifest_path.parent.mkdir(parents=True)
    ontology_source_manifest_path.parent.mkdir(parents=True)
    (module_root / "aware.module.toml").write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "ontology/aware.ontology.toml"',
                "",
                "[[packages]]",
                'id = "home_story_experience"',
                'kind = "experience"',
                'manifest = "experiences/home_story/aware.experience.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ontology_package_manifest_path.write_text(
        "\n".join(
            [
                "aware_ontology = 1",
                "",
                "[ontology]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
                'source_manifest = "structure/aware.toml"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ontology_source_manifest_path.write_text(
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "home-ontology"',
                'fqn_prefix = "aware_home"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    experience_manifest_path.write_text("aware_experience = 1\n", encoding="utf-8")

    targets = source_module_ontology_dto_stable_ids_import_targets(
        context=None,
        source_experience_toml_path=experience_manifest_path,
    )

    assert targets.roots_by_module_id == {"home": ("aware_home_ontology_dto",)}
    assert targets.import_paths == (
        ontology_source_manifest_path.parent / "python" / "dto",
    )


def test_projection_node_module_id_keeps_multiword_aware_prefix() -> None:
    assert (
        materialization_service._module_id_from_projection_node_name(
            node_name="aware_home_devices.Device"
        )
        == "home_devices"
    )


def test_static_projection_stable_ids_fail_closed_without_dto_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported_modules: list[str] = []

    def _import_module(name: str) -> ModuleType:
        imported_modules.append(name)
        raise ModuleNotFoundError(name=name)

    monkeypatch.setattr(static_projection_targets.importlib, "import_module", _import_module)

    with pytest.raises(materialization_service._StaticProjectionTargetNotDerivable):
        materialization_service._stable_source_id_binding_for_node(
            node_name="aware_identity.RoleConfig",
            class_config_id=uuid4(),
            dto_stable_ids_import_roots_by_module_id={},
        )

    assert imported_modules == []


@pytest.mark.asyncio
async def test_hydrate_lane_session_uses_meta_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    projection_hash = "hash:ExperiencePackage"
    opg = SimpleNamespace(name="ExperiencePackage", projection_hash=projection_hash)
    oig = object()
    scratch_session = object()
    captured: dict[str, object] = {}

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            captured["head"] = {
                "branch_id": branch_id,
                "projection_hash": projection_hash,
            }
            return {"commit_id": str(commit_id)}

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            captured["materializer_kwargs"] = kwargs
            return oig, object()

    def _fake_reify_oig_session(**kwargs: object) -> object:
        captured["reifier_kwargs"] = kwargs
        return scratch_session

    monkeypatch.setattr(lane_state, "FSCommitStore", _Store)
    monkeypatch.setattr(lane_state, "OIGMaterializer", _Materializer)
    monkeypatch.setattr(
        lane_state,
        "reify_oig_session",
        _fake_reify_oig_session,
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={projection_hash: opg},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )

    result = await lane_state.hydrate_lane_session(
        index=cast(Any, index),
        branch_id=branch_id,
        projection_hash=projection_hash,
        error_context="test",
    )

    assert result is scratch_session
    assert captured["head"] == {
        "branch_id": branch_id,
        "projection_hash": projection_hash,
    }
    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["opg"] is opg
    assert materializer_kwargs["commit_id"] is None
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is index
    assert reifier_kwargs["opg"] is opg
    assert reifier_kwargs["oig"] is oig
    assert reifier_kwargs["branch_id"] == branch_id


@pytest.mark.asyncio
async def test_hydrate_lane_root_from_head_uses_meta_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    root_id = uuid4()
    projection_hash = "hash:ExperiencePackage"
    opg = SimpleNamespace(name="ExperiencePackage", projection_hash=projection_hash)
    oig = object()
    root = SimpleNamespace(id=root_id)
    captured: dict[str, object] = {}

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            captured["head"] = {
                "branch_id": branch_id,
                "projection_hash": projection_hash,
            }
            return {"commit_id": str(commit_id)}

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            captured["materializer_kwargs"] = kwargs
            return oig, object()

    class _ScratchSession:
        def imap_get(self, model_type: type[object], object_id: UUID) -> object | None:
            if object_id == root_id:
                return root
            return None

    def _fake_reify_oig_session(**kwargs: object) -> _ScratchSession:
        captured["reifier_kwargs"] = kwargs
        return _ScratchSession()

    monkeypatch.setattr(lane_state, "FSCommitStore", _Store)
    monkeypatch.setattr(lane_state, "OIGMaterializer", _Materializer)
    monkeypatch.setattr(
        lane_state,
        "reify_oig_session",
        _fake_reify_oig_session,
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={projection_hash: opg},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )

    result = await lane_state.hydrate_lane_root_from_head(
        index=cast(Any, index),
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_id=root_id,
        root_type=cast(type[Any], cast(object, SimpleNamespace)),
    )

    assert result is root
    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["opg"] is opg
    assert materializer_kwargs["commit_id"] is None
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is index
    assert reifier_kwargs["opg"] is opg
    assert reifier_kwargs["oig"] is oig
    assert reifier_kwargs["branch_id"] == branch_id
