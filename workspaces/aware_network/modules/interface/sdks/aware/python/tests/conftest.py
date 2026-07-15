import json
import sys
import types
from pathlib import Path

try:  # pragma: no cover - optional dependency bridge for tests
    import yaml  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - provide stub
    yaml_stub = types.ModuleType("yaml")

    def safe_dump(value, *_, **__):
        return json.dumps(value)

    def safe_load(*_, **__):
        return {}

    yaml_stub.safe_dump = safe_dump
    yaml_stub.safe_load = safe_load
    sys.modules["yaml"] = yaml_stub

ROOT = Path(__file__).resolve().parents[8]
TOOLS_CLI = ROOT / "tools" / "cli"
if str(TOOLS_CLI) not in sys.path:
    sys.path.append(str(TOOLS_CLI))
