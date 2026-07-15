from __future__ import annotations

from pathlib import Path
import sys


TESTS_ROOT = Path(__file__).resolve().parent
SDK_ROOT = TESTS_ROOT.parent
MEMORY_MODULE_ROOT = TESTS_ROOT.parents[3]


for _path in (
    SDK_ROOT,
    MEMORY_MODULE_ROOT / "apis/memory/python/aware_memory_service_api",
    MEMORY_MODULE_ROOT / "apis/memory/python/aware_memory_service_dto",
):
    text = str(_path)
    if text not in sys.path:
        sys.path.insert(0, text)
