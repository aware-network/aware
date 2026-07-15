from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from aware_meta.runtime import projection_support


def test_build_meta_graph_opgi_index_prefers_observable_keys(
    monkeypatch,
) -> None:
    projection_hash = "sha256:projection"
    opgi_id = uuid4()
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=(
                SimpleNamespace(projection_hash=projection_hash),
            ),
        ),
    )
    opgi = SimpleNamespace(
        id=opgi_id,
        projection_name="ProjectionExperience",
        object_projection_graph_observables=(
            SimpleNamespace(observable_key="summary", key="legacy-summary"),
            SimpleNamespace(observable_key="", key="ignored"),
        ),
    )

    def _fake_resolve_meta_graph_ocgi_opgi(**kwargs: object) -> tuple[None, object]:
        assert kwargs["index"] is index
        assert kwargs["projection_hash"] == projection_hash
        return None, opgi

    monkeypatch.setattr(
        projection_support,
        "resolve_meta_graph_ocgi_opgi",
        _fake_resolve_meta_graph_ocgi_opgi,
    )

    assert projection_support.build_meta_graph_opgi_index(index=index) == {
        "ProjectionExperience": (opgi_id, {"summary"}),
    }


def test_build_meta_graph_opgi_index_falls_back_to_legacy_observable_keys(
    monkeypatch,
) -> None:
    projection_hash = "sha256:projection"
    opgi_id = uuid4()
    index = SimpleNamespace(
        ocg=SimpleNamespace(
            object_projection_graphs=(
                SimpleNamespace(projection_hash=projection_hash),
            ),
        ),
    )
    opgi = SimpleNamespace(
        id=opgi_id,
        projection_name="ProjectionExperience",
        object_projection_graph_observables=(
            SimpleNamespace(observable_key="", key="default"),
        ),
    )

    monkeypatch.setattr(
        projection_support,
        "resolve_meta_graph_ocgi_opgi",
        lambda **_: (None, opgi),
    )

    assert projection_support.build_meta_graph_opgi_index(index=index) == {
        "ProjectionExperience": (opgi_id, {"default"}),
    }
