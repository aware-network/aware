from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias, TypedDict


DiagnosticDataObject: TypeAlias = Mapping[str, "DiagnosticDataValue"]
DiagnosticDataValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | Sequence["DiagnosticDataValue"]
    | DiagnosticDataObject
)


class Utf16PositionDict(TypedDict):
    line: int
    character: int


class DiagnosticRangeDict(TypedDict):
    start: Utf16PositionDict
    end: Utf16PositionDict


class AwareDiagnostic(TypedDict, total=False):
    message: str
    severity: int
    source: str
    code: str
    range: DiagnosticRangeDict
    data: Mapping[str, DiagnosticDataValue]
