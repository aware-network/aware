"""Fresh descriptive preparation copying; no authority or retained value cache."""

from __future__ import annotations

import dataclasses
import types
from typing import Any

from aware_file_system.confined_mutation import (
    ConfinedTreeEntryPin,
    ConfinedTreePreparationObservation,
    ConfinedTreeScratchEffect,
)


def _bind_preparation_copy():
    namespace = vars(dataclasses)
    native_getattr, native_type = getattr, type
    original_asdict = dataclasses.asdict
    original_inner = namespace["_asdict_inner"]
    original_fields = dataclasses.fields
    atomic = namespace["_ATOMIC_TYPES"]
    deepcopy_namespace = vars(namespace["copy"])
    original_deepcopy = deepcopy_namespace["deepcopy"]
    known = (
        ConfinedTreePreparationObservation,
        ConfinedTreeEntryPin,
        ConfinedTreeScratchEffect,
    )
    pins = tuple(
        (name, namespace[name])
        for name in (
            "asdict",
            "_asdict_inner",
            "fields",
            "_ATOMIC_TYPES",
            "_is_dataclass_instance",
            "_FIELDS",
            "_FIELD",
            "copy",
        )
    )
    functions = tuple(
        (
            function,
            function.__code__,
            function.__defaults__,
            function.__kwdefaults__,
            None
            if function.__kwdefaults__ is None
            else tuple(function.__kwdefaults__.items()),
        )
        for _, function in (*pins, ("deepcopy", original_deepcopy))
        if type(function) is types.FunctionType
    )
    converters = []
    for cls in known:
        count = len(original_fields(cls))
        lines = [
            "def convert(value, current, walk, atomic, get_attribute, value_type):",
            "    result = {}",
            "    key = member = None",
            "    try:",
        ]
        for index in range(count):
            # Match dict-comprehension ordering: key is read before member and
            # recursive copying. Field names remain fresh even after callbacks.
            lines.extend(
                (
                    f"        key = current[{index}].name",
                    f"        member = get_attribute(value, current[{index}].name)",
                    "        result[key] = member if value_type(member) in atomic else walk(member)",
                )
            )
        lines.extend(
            (
                "        return result",
                "    finally:",
                "        del value, current, walk, atomic, get_attribute, value_type, result, key, member",
            )
        )
        compiled: dict[str, Any] = {}
        exec(  # noqa: S102 -- fixed authored field counts and literal indices only
            compile("\n".join(lines), "<workspace-preparation-copy>", "exec"),
            {},
            compiled,
        )
        function = compiled["convert"]
        converters.append((cls, count, function, function.__code__))
    converters = tuple(converters)

    def check():
        if (
            deepcopy_namespace.get("deepcopy") is not original_deepcopy
            or any(namespace.get(name) is not original for name, original in pins)
        ) or any(
            function.__code__ is not code
            or function.__defaults__ is not defaults
            or function.__kwdefaults__ is not kwdefaults
            or (
                items is not None
                and (
                    type(kwdefaults) is not dict
                    or len(kwdefaults) != len(items)
                    or any(type(key) is not str for key in kwdefaults)
                    or any(kwdefaults.get(key) is not item for key, item in items)
                )
            )
            for function, code, defaults, kwdefaults, items in functions
        ):
            raise TypeError("original preparation copy helpers required")
        if (
            walk.__code__ is not walk_code
            or walk.__defaults__ is not None
            or walk.__kwdefaults__ is not None
        ):
            raise TypeError("original preparation copy dispatcher required")

    check_code = check.__code__

    def copy_unknown(value):
        result = None
        try:
            # Unknown values retain original stdlib container/deepcopy behavior.
            if check.__code__ is not check_code:
                raise TypeError("original preparation copy guard required")
            check()
            result = original_inner(value, dict)
            if check.__code__ is not check_code:
                raise TypeError("original preparation copy guard required")
            check()
            return result
        finally:
            del value, result

    unknown_code = copy_unknown.__code__

    def walk(value):
        current = result = item = None
        try:
            kind = type(value)
            if kind in atomic:
                return value
            if kind is tuple:
                result = []
                for item in value:
                    result.append(walk(item))
                return tuple(result)
            for cls, count, convert, code in converters:
                if kind is cls:
                    current = original_fields(value)
                    if len(current) == count:
                        if (
                            type(convert) is not types.FunctionType
                            or convert.__code__ is not code
                            or convert.__defaults__ is not None
                            or convert.__kwdefaults__ is not None
                        ):
                            raise TypeError("original preparation converter required")
                        return convert(
                            value, current, walk, atomic, native_getattr, native_type
                        )
                    # Metadata may add/remove/reorder fields. Reuse this exact
                    # fields() snapshot rather than repeating prefix effects.
                    return {
                        field.name: walk(getattr(value, field.name))
                        for field in current
                    }
            # Unknown values retain the original post-classification delegate.
            if (
                copy_unknown.__code__ is not unknown_code
                or copy_unknown.__defaults__ is not None
                or copy_unknown.__kwdefaults__ is not None
            ):
                raise TypeError("original preparation copy dispatcher required")
            return copy_unknown(value)
        finally:
            del value, current, result, item

    walk_code = walk.__code__

    native_handoff = None
    try:
        from aware_workspace_sdk._tree_native_binding import prepare_preparation_copy
    except ImportError:
        pass
    else:
        native_handoff = prepare_preparation_copy(
            known,
            tuple(count for _, count, _, _ in converters),
            atomic,
            original_fields,
            walk,
            converters,
            copy_unknown,
        )

    def copy_preparation_observation(value):
        result = None
        try:
            # Guard dispatch itself is definition-time bound and checked before
            # execution; a mutable module helper cannot become a validation rail.
            if check.__code__ is not check_code or walk.__code__ is not walk_code:
                raise TypeError("original preparation copy dispatcher required")
            check()
            if type(value) not in known:
                return original_asdict(value)
            if native_handoff is None:
                result = walk(value)
            else:
                native_context, native_copy = native_handoff
                result = native_copy(native_context, value)
            if check.__code__ is not check_code:
                raise TypeError("original preparation copy guard required")
            check()
            return result
        finally:
            del value, result

    return copy_preparation_observation


copy_preparation_observation = _bind_preparation_copy()
