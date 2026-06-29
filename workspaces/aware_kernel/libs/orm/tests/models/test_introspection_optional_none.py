from __future__ import annotations

from dataclasses import dataclass

from aware_meta_ontology.class_.class_config import ClassConfig


@dataclass(frozen=True, slots=True)
class _AttrCfg:
    name: str
    is_virtual: bool = False
    is_required: bool = False
    default_value: str | None = None


def test_try_attribute_value_treats_optional_explicit_none_as_missing() -> None:
    cls_unset = ClassConfig(class_fqn="pkg.ns.Foo", name="Foo")
    cls_explicit_none = ClassConfig(
        class_fqn="pkg.ns.Foo",
        name="Foo",
        description=None,
    )

    cfg = _AttrCfg(name="description", is_required=False)
    assert cls_unset.try_attribute_value(cfg) == (False, None)
    assert cls_explicit_none.try_attribute_value(cfg) == (False, None)


def test_try_attribute_value_keeps_required_none_present() -> None:
    cls = ClassConfig(class_fqn="pkg.ns.Foo", name="Foo", description=None)

    cfg = _AttrCfg(name="description", is_required=True)
    assert cls.try_attribute_value(cfg) == (True, None)
