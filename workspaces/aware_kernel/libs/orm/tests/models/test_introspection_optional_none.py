from __future__ import annotations

from dataclasses import dataclass

from aware_meta_ontology.domain.domain import Domain


@dataclass(frozen=True, slots=True)
class _AttrCfg:
    name: str
    is_virtual: bool = False
    is_required: bool = False
    default_value: str | None = None


def test_try_attribute_value_treats_optional_explicit_none_as_missing() -> None:
    dom_unset = Domain(name="default")
    dom_explicit_none = Domain(name="default", description=None)

    cfg = _AttrCfg(name="description", is_required=False)
    assert dom_unset.try_attribute_value(cfg) == (False, None)
    assert dom_explicit_none.try_attribute_value(cfg) == (False, None)


def test_try_attribute_value_keeps_required_none_present() -> None:
    dom = Domain(name="default", description=None)

    cfg = _AttrCfg(name="description", is_required=True)
    assert dom.try_attribute_value(cfg) == (True, None)
