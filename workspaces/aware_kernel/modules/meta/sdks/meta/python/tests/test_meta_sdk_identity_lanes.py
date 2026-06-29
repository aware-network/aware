from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest

import aware_meta_sdk
from aware_meta_sdk.identity_lanes import validate_compiler_identity_lanes_seeded


def test_meta_sdk_identity_lane_helper_is_public_and_runtime_free() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "aware_meta_sdk"
        / "identity_lanes.py"
    ).read_text(encoding="utf-8")

    assert "from aware_runtime" not in source
    assert "import aware_runtime" not in source
    assert "aware_runtime." not in source
    assert "validate_compiler_identity_lanes_seeded" in aware_meta_sdk.__all__
    assert aware_meta_sdk.validate_compiler_identity_lanes_seeded is (
        validate_compiler_identity_lanes_seeded
    )


@pytest.mark.asyncio
async def test_validate_compiler_identity_lanes_seeded_requires_commit_heads() -> None:
    index, identities = _build_index()
    store = _HeadStore()
    ocgi = index.ocg.object_config_graph_identity
    ocgi_seed_opg, opgi_seed_opg, _domain_opg = index.ocg.object_projection_graphs

    store.put(
        branch_id=ocgi.id,
        projection_hash=ocgi_seed_opg.projection_hash,
        object_instance_graph_id=str(ocgi.id),
    )
    for opgi in identities:
        store.put(
            branch_id=opgi.id,
            projection_hash=opgi_seed_opg.projection_hash,
            object_instance_graph_id=opgi.id,
        )

    await validate_compiler_identity_lanes_seeded(index=index, store=store)

    expected_requests = [(ocgi.id, ocgi_seed_opg.projection_hash)]
    expected_requests.extend(
        (opgi.id, opgi_seed_opg.projection_hash) for opgi in identities
    )
    assert store.requests == expected_requests


@pytest.mark.asyncio
async def test_validate_compiler_identity_lanes_seeded_fails_without_attached_opgi() -> (
    None
):
    index, identities = _build_index()
    index.ocg.object_config_graph_identity.object_projection_graph_identities = (
        identities[:-1]
    )
    store = _HeadStore()
    ocgi = index.ocg.object_config_graph_identity
    ocgi_seed_opg, opgi_seed_opg, _domain_opg = index.ocg.object_projection_graphs
    store.put(
        branch_id=ocgi.id,
        projection_hash=ocgi_seed_opg.projection_hash,
        object_instance_graph_id=ocgi.id,
    )
    for opgi in identities[:-1]:
        store.put(
            branch_id=opgi.id,
            projection_hash=opgi_seed_opg.projection_hash,
            object_instance_graph_id=opgi.id,
        )

    with pytest.raises(RuntimeError, match="Missing required OPGI"):
        await validate_compiler_identity_lanes_seeded(index=index, store=store)


@pytest.mark.asyncio
async def test_validate_compiler_identity_lanes_seeded_fails_on_mismatched_head_oig() -> (
    None
):
    index, identities = _build_index()
    store = _HeadStore()
    ocgi = index.ocg.object_config_graph_identity
    ocgi_seed_opg, _opgi_seed_opg, _domain_opg = index.ocg.object_projection_graphs

    store.put(
        branch_id=ocgi.id,
        projection_hash=ocgi_seed_opg.projection_hash,
        object_instance_graph_id=uuid4(),
    )

    with pytest.raises(RuntimeError, match="mismatched object_instance_graph_id"):
        await validate_compiler_identity_lanes_seeded(index=index, store=store)


def _build_index() -> tuple[SimpleNamespace, tuple[SimpleNamespace, ...]]:
    ocgi_id = uuid4()
    ocgi_seed_opg = _opg("ObjectConfigGraphIdentity")
    opgi_seed_opg = _opg("ObjectProjectionGraphIdentity")
    domain_opg = _opg("Environment")
    identities = tuple(
        SimpleNamespace(
            id=uuid4(),
            object_config_graph_identity_id=ocgi_id,
            object_projection_graph_id=opg.id,
        )
        for opg in (ocgi_seed_opg, opgi_seed_opg, domain_opg)
    )
    ocgi = SimpleNamespace(
        id=ocgi_id,
        object_projection_graph_identities=list(identities),
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_config_graph_identity=ocgi,
            object_projection_graphs=(ocgi_seed_opg, opgi_seed_opg, domain_opg),
        )
    )
    return index, identities


def _opg(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        projection_hash=f"projection:{name}",
    )


class _HeadStore:
    def __init__(self) -> None:
        self._heads: dict[tuple[UUID, str], dict[str, Any]] = {}
        self.requests: list[tuple[UUID, str]] = []

    def put(
        self,
        *,
        branch_id: UUID,
        projection_hash: str,
        object_instance_graph_id: object,
    ) -> None:
        self._heads[(branch_id, projection_hash)] = {
            "commit_id": str(uuid4()),
            "object_instance_graph_id": object_instance_graph_id,
        }

    async def head(self, *, branch_id: UUID, projection_hash: str) -> object | None:
        self.requests.append((branch_id, projection_hash))
        return self._heads.get((branch_id, projection_hash))
