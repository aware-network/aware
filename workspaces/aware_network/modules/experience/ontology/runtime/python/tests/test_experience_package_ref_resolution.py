from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest

from aware_experience import package_ref_resolution


def test_package_ref_resolution_sources_are_clean() -> None:
    source = Path(package_ref_resolution.__file__).read_text(encoding="utf-8")

    assert "aware_runtime" not in source
    assert "hydrate_orm_graph_from_oig" not in source


def test_find_projection_hash_by_name_reads_meta_index() -> None:
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=(
                SimpleNamespace(name="Other", projection_hash="hash:other"),
                SimpleNamespace(
                    name="ExperiencePackage",
                    projection_hash="hash:experience-package",
                ),
            )
        )
    )

    assert (
        package_ref_resolution._find_projection_hash_by_name(
            index=cast(Any, index),
            projection_name="ExperiencePackage",
        )
        == "hash:experience-package"
    )


@pytest.mark.asyncio
async def test_hydrate_root_from_commit_uses_meta_oig_root_reifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    branch_id = uuid4()
    commit_id = uuid4()
    root_id = uuid4()
    opg = SimpleNamespace(projection_hash="hash:ExperiencePackage")
    oig = object()
    root = SimpleNamespace(id=root_id)
    captured: dict[str, object] = {}

    class _Materializer:
        def __init__(self, **kwargs: object) -> None:
            captured["materializer_init_kwargs"] = kwargs

        async def get(self, **kwargs: object) -> tuple[object, object]:
            captured["materializer_kwargs"] = kwargs
            return oig, object()

    def _fake_reify_oig_root_model(**kwargs: object) -> object:
        captured["reifier_kwargs"] = kwargs
        return root

    monkeypatch.setattr(package_ref_resolution, "CachedLaneMaterializer", _Materializer)
    monkeypatch.setattr(
        package_ref_resolution,
        "reify_oig_root_model",
        _fake_reify_oig_root_model,
    )

    index = SimpleNamespace(
        ocg=SimpleNamespace(),
        opg_by_hash={opg.projection_hash: opg},
        attribute_configs_by_id={},
        class_configs_by_id={},
    )

    result = await package_ref_resolution._hydrate_root_from_commit(
        index=cast(Any, index),
        branch_id=branch_id,
        projection_hash=opg.projection_hash,
        commit_id=commit_id,
        root_id=root_id,
        root_type=cast(type[Any], SimpleNamespace),
        hydrate_portal_targets=True,
        store=cast(Any, object()),
    )

    assert result is root
    assert cast(dict[str, object], captured["materializer_init_kwargs"])["commits"]
    materializer_kwargs = cast(dict[str, object], captured["materializer_kwargs"])
    assert materializer_kwargs["branch_id"] == branch_id
    assert materializer_kwargs["opg"] is opg
    assert materializer_kwargs["commit_id"] == commit_id
    reifier_kwargs = cast(dict[str, object], captured["reifier_kwargs"])
    assert reifier_kwargs["index"] is index
    assert reifier_kwargs["opg"] is opg
    assert reifier_kwargs["oig"] is oig
    assert reifier_kwargs["root_id"] == root_id
    assert reifier_kwargs["branch_id"] == branch_id
