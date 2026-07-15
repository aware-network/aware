from __future__ import annotations

# Standard
from enum import Enum


class CodeLanguage(Enum):
    aware = "aware"
    dart = "dart"
    python = "python"
    sql = "sql"


class CodeTestRunStatus(Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    unsupported = "unsupported"
