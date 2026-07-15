from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from aware_experience.materialization import projection_resolution


def test_projection_runtime_resolver_uses_meta_projection_support(
    monkeypatch,
) -> None:
    opgi_id = uuid4()
    class_config = SimpleNamespace(
        id=uuid4(),
        name="Room",
        class_fqn="aware_demo.home.Room",
    )
    opg = SimpleNamespace(
        projection_hash="sha256:room-projection",
        object_projection_graph_nodes=(
            SimpleNamespace(class_config=class_config, class_config_id=None),
        ),
    )
    index = SimpleNamespace(
        ocg=SimpleNamespace(object_projection_graphs=(opg,)),
        class_configs_by_id={},
    )

    monkeypatch.setattr(
        projection_resolution,
        "build_meta_graph_opgi_index",
        lambda **_: {"RoomProjection": (opgi_id, {"default"})},
    )
    monkeypatch.setattr(
        projection_resolution,
        "resolve_meta_graph_ocgi_opgi",
        lambda **_: (None, SimpleNamespace(id=opgi_id)),
    )

    resolver = projection_resolution.build_projection_runtime_resolver(index=index)
    resolved = resolver.resolve(
        projection_key="Room",
        experience_name="Demo",
        context="unit",
    )

    assert resolved.projection_key == "RoomProjection"
    assert resolved.opgi_id == opgi_id
    assert resolved.opgi_entry == (opgi_id, frozenset({"default"}))
