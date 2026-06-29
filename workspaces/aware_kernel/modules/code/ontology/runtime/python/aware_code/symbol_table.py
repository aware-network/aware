from dataclasses import dataclass, field


@dataclass
class CodeSymbolTable:
    bindings: dict[str, str] = field(default_factory=dict)
