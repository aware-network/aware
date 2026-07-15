from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import import_module
from typing import cast

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class MetaOntologyFunctionRef:
    ref: str
    class_fqn: str
    function_name: str
    is_constructor: bool
    input_model: type[BaseModel]
    output_model: type[BaseModel]

    def __str__(self) -> str:
        return self.ref


def meta_ontology_function_ref(method: Callable[..., object]) -> MetaOntologyFunctionRef:
    owner_cls, function_name = _resolve_generated_method_owner(method)
    functions = _load_generated_functions(owner_cls=owner_cls)
    function_entry = _load_function_entry(
        functions=functions,
        owner_cls=owner_cls,
        function_name=function_name,
    )
    canonical = function_entry.get("canonical")
    if not isinstance(canonical, Mapping):
        raise ValueError(
            "Generated FUNCTIONS entry is missing canonical metadata: "
            f"class={owner_cls.__module__}.{owner_cls.__name__} "
            f"function={function_name}"
        )
    is_constructor = canonical.get("is_constructor")
    if not isinstance(is_constructor, bool):
        raise ValueError(
            "Generated FUNCTIONS canonical metadata is missing is_constructor: "
            f"class={owner_cls.__module__}.{owner_cls.__name__} "
            f"function={function_name}"
        )
    class_fqn = f"{owner_cls.__module__}.{owner_cls.__name__}"
    return MetaOntologyFunctionRef(
        ref=f"{class_fqn}.{function_name}",
        class_fqn=class_fqn,
        function_name=function_name,
        is_constructor=is_constructor,
        input_model=_load_model_type(
            function_entry=function_entry,
            key="input",
            owner_cls=owner_cls,
            function_name=function_name,
        ),
        output_model=_load_model_type(
            function_entry=function_entry,
            key="output",
            owner_cls=owner_cls,
            function_name=function_name,
        ),
    )


def _resolve_generated_method_owner(
    method: Callable[..., object],
) -> tuple[type[object], str]:
    raw_method = getattr(method, "__func__", method)
    if not inspect.isfunction(raw_method):
        raise TypeError(
            "meta_ontology_function_ref expects a generated ontology method symbol, "
            f"got {type(method).__name__}"
        )
    module_name = str(getattr(raw_method, "__module__", "") or "")
    qualname = str(getattr(raw_method, "__qualname__", "") or "")
    function_name = str(getattr(raw_method, "__name__", "") or "")
    if not module_name or not qualname or not function_name:
        raise ValueError(
            "Generated ontology method is missing module/qualname metadata."
        )
    if "<locals>" in qualname:
        raise ValueError(
            "meta_ontology_function_ref only supports generated class methods, "
            f"got local function {module_name}.{qualname}"
        )
    qualname_parts = qualname.split(".")
    if len(qualname_parts) != 2:
        raise ValueError(
            "meta_ontology_function_ref only supports top-level generated ontology classes, "
            f"got {module_name}.{qualname}"
        )
    class_name, declared_function_name = qualname_parts
    if declared_function_name != function_name:
        raise ValueError(
            "Generated ontology method qualname/function mismatch: "
            f"qualname={qualname} function_name={function_name}"
        )
    module = import_module(module_name)
    owner = getattr(module, class_name, None)
    if not inspect.isclass(owner):
        raise ValueError(
            "Generated ontology method owner class could not be resolved: "
            f"{module_name}.{class_name}"
        )
    resolved_attr = getattr(owner, function_name, None)
    resolved_raw = getattr(resolved_attr, "__func__", resolved_attr)
    if resolved_raw is not raw_method:
        raise ValueError(
            "Generated ontology method symbol does not match owner class attribute: "
            f"{module_name}.{class_name}.{function_name}"
        )
    return cast(type[object], owner), function_name


def _load_generated_functions(
    *,
    owner_cls: type[object],
) -> Mapping[str, object]:
    module = import_module(owner_cls.__module__)
    functions = getattr(module, "FUNCTIONS", None)
    if not isinstance(functions, Mapping):
        raise ValueError(
            "Generated ontology module is missing FUNCTIONS metadata: "
            f"module={owner_cls.__module__}"
        )
    return cast(Mapping[str, object], functions)


def _load_function_entry(
    *,
    functions: Mapping[str, object],
    owner_cls: type[object],
    function_name: str,
) -> Mapping[str, object]:
    class_functions = functions.get(owner_cls.__name__)
    if not isinstance(class_functions, Mapping):
        raise ValueError(
            "Generated FUNCTIONS metadata is missing owner class: "
            f"class={owner_cls.__module__}.{owner_cls.__name__}"
        )
    function_entry = class_functions.get(function_name)
    if not isinstance(function_entry, Mapping):
        raise ValueError(
            "Generated FUNCTIONS metadata is missing function: "
            f"class={owner_cls.__module__}.{owner_cls.__name__} "
            f"function={function_name}"
        )
    return cast(Mapping[str, object], function_entry)


def _load_model_type(
    *,
    function_entry: Mapping[str, object],
    key: str,
    owner_cls: type[object],
    function_name: str,
) -> type[BaseModel]:
    value = function_entry.get(key)
    if not inspect.isclass(value) or not issubclass(value, BaseModel):
        raise TypeError(
            "Generated FUNCTIONS metadata has invalid model binding: "
            f"class={owner_cls.__module__}.{owner_cls.__name__} "
            f"function={function_name} key={key}"
        )
    return cast(type[BaseModel], value)


__all__ = [
    "MetaOntologyFunctionRef",
    "meta_ontology_function_ref",
]
