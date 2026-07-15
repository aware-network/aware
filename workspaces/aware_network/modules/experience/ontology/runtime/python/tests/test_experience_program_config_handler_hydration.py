from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import UUID, uuid4

import pytest

from aware_experience.handlers.impl.program import program_config_graph_program_config
from aware_experience_ontology.program.program_config import ProgramConfig
from aware_experience_ontology.program.program_config_graph_program_config import (
    ProgramConfigGraphProgramConfig,
)


def test_program_config_graph_program_config_handler_source_is_clean() -> None:
    source = Path(program_config_graph_program_config.__file__).read_text(
        encoding="utf-8"
    )

    assert "aware_" + "runtime" not in source
    assert "hydrate_orm_graph_" + "from_oig" not in source


@pytest.mark.asyncio
async def test_build_via_program_config_graph_uses_meta_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    program_config_graph_id = uuid4()
    program_config_id = uuid4()
    commit_id = uuid4()
    oig_id = uuid4()
    projection_hash = "hash:ProgramConfig"
    opg = SimpleNamespace(name="ProgramConfig", projection_hash=projection_hash)
    oig = object()
    hydrated_program = ProgramConfig.model_construct(id=program_config_id)
    captured: dict[str, object] = {}

    class _Session:
        def __init__(self) -> None:
            self._objects: dict[tuple[type[object], UUID], object] = {}

        def imap_get(self, model_type: type[object], object_id: UUID) -> object | None:
            return self._objects.get((model_type, object_id))

        def merge(self, obj: object) -> None:
            self._objects[(type(obj), cast(UUID, getattr(obj, "id")))] = obj

    class _Store:
        async def head(
            self, *, branch_id: UUID, projection_hash: str
        ) -> dict[str, str]:
            captured["head"] = {
                "branch_id": branch_id,
                "projection_hash": projection_hash,
            }
            return {
                "commit_id": str(commit_id),
                "object_instance_graph_id": str(oig_id),
            }

    class _Materializer:
        async def get(self, **kwargs: object) -> tuple[object, object]:
            captured["materializer_kwargs"] = kwargs
            return oig, object()

    class _ScratchSession:
        def imap_get(self, model_type: type[object], object_id: UUID) -> object | None:
            if model_type is ProgramConfig and object_id == program_config_id:
                return hydrated_program
            return None

    def _fake_reify_oig_session(**kwargs: object) -> _ScratchSession:
        captured["reifier_kwargs"] = kwargs
        return _ScratchSession()

    session = _Session()
    index = SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={projection_hash: opg},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )
    monkeypatch.setattr(
        program_config_graph_program_config,
        "current_handler_session",
        lambda: session,
    )
    monkeypatch.setattr(
        program_config_graph_program_config,
        "current_handler_context",
        lambda: SimpleNamespace(branch_id=branch_id),
    )
    monkeypatch.setattr(
        program_config_graph_program_config,
        "current_handler_index",
        lambda: index,
    )
    monkeypatch.setattr(program_config_graph_program_config, "FSCommitStore", _Store)
    monkeypatch.setattr(
        program_config_graph_program_config,
        "CachedLaneMaterializer",
        _Materializer,
    )
    monkeypatch.setattr(
        program_config_graph_program_config,
        "reify_oig_session",
        _fake_reify_oig_session,
    )

    result = await program_config_graph_program_config.build_via_program_config_graph(
        program_config_graph_id=program_config_graph_id,
        program_config_id=program_config_id,
        key="primary",
    )

    assert isinstance(result, ProgramConfigGraphProgramConfig)
    assert result.program_config is hydrated_program
    assert session.imap_get(ProgramConfig, program_config_id) is hydrated_program
    assert captured["head"] == {
        "branch_id": branch_id,
        "projection_hash": projection_hash,
    }
    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["opg"] is opg
    assert materializer_kwargs["commit_id"] == commit_id
    assert materializer_kwargs["oig_id"] == oig_id
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is index
    assert reifier_kwargs["opg"] is opg
    assert reifier_kwargs["oig"] is oig
    assert reifier_kwargs["branch_id"] == branch_id
