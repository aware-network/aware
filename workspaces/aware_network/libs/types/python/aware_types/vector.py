from __future__ import annotations

from typing import SupportsFloat, cast, final, override

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema as _cs


class Vector(list[float]):
    """Lightweight vector type used for annotations."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: object,
        handler: GetCoreSchemaHandler,
    ) -> _cs.CoreSchema:
        _ = source_type
        _ = handler
        list_float_schema = _cs.list_schema(_cs.float_schema())

        def _coerce(v: object) -> "Vector":
            if isinstance(v, cls):
                return v
            if isinstance(v, list):
                list_values = cast(list[object], v)
                coerced_values: list[float] = []
                try:
                    for value in list_values:
                        if isinstance(value, SupportsFloat):
                            coerced_values.append(float(value))
                            continue
                        if isinstance(value, (str, bytes, bytearray)):
                            coerced_values.append(float(value))
                            continue
                        raise TypeError(f"Unsupported vector element type: {type(value).__name__}")
                    return cls(coerced_values)
                except (TypeError, ValueError) as exc:
                    raise TypeError(f"Vector elements must be floats: {exc}")
            raise TypeError("Vector must be a list of floats")

        def _ser(v: "Vector") -> list[float]:
            return list(v)

        return _cs.no_info_after_validator_function(
            _coerce,
            list_float_schema,
            serialization=_cs.plain_serializer_function_ser_schema(_ser, return_schema=list_float_schema),
        )


@final
class VectorDim:
    """Annotation helper to carry dimensions for Vector."""

    dimension: int

    def __init__(self, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError("VectorDim requires a positive integer dimension")
        self.dimension = dimension

    @override
    def __repr__(self) -> str:
        return f"VectorDim({self.dimension})"
