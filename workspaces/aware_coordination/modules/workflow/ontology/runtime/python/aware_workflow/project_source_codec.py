"""Project TOML representation codec only; no file or Protocol admission.

Callers supply bounded bytes. A decoded record is data, not an issued source
reading, Object, branch, caller permit or View observation.
"""

import json
import tomllib

from .project_read_contract import MAX_RECORD_BYTES, ProjectContextRecordV1


def decode_project_context_toml(body: bytes) -> ProjectContextRecordV1:
    if type(body) is not bytes or len(body) > MAX_RECORD_BYTES:
        raise ValueError("Project source requires bounded UTF-8 bytes")
    try:
        value = tomllib.loads(body.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError("invalid Project source TOML") from error
    return ProjectContextRecordV1.from_wire(value)


def encode_project_context_toml(record: ProjectContextRecordV1) -> bytes:
    if type(record) is not ProjectContextRecordV1:
        raise ValueError("exact Project source record required")
    wire = record.to_wire()  # Revalidate nested content; never repair an instance.
    # JSON quoted strings are a TOML basic-string subset for these validated
    # scalar values. Preserve order/case and escape quotes/backslashes exactly.
    def quote(value: object) -> str:
        return json.dumps(value, ensure_ascii=False)
    fields = ("schema_id", "project_key", "title", "priority_level", "status")
    lines = [f"{key} = {quote(wire[key])}" for key in fields]
    lines.append("goal_tags = [" + ", ".join(quote(tag) for tag in record.goal_tags) + "]")
    body = ("\n".join(lines) + "\n").encode("utf-8")
    if len(body) > MAX_RECORD_BYTES:
        raise ValueError("encoded Project record exceeds byte budget")
    return body
