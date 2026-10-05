"""Optional Linux evaluator helpers; not an Aware operation or submission validator."""

import argparse
import fcntl
import gzip
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "aware.evaluation.private-capture.v1"
SYMBOLS = ("selected-command", "task-python", "aware-python")
RECEIPT_FIELDS = (
    "outcome", "publication_receipt_ref", "closeout_publication_receipt_ref",
    "operator_ref", "transaction_mode", "reference_update",
    "shared_index_projection", "index_reconciliation_pending",
)


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n").encode()


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)


def now():
    return datetime.now(timezone.utc).isoformat()


def execution(env):
    found = [(provider, env.get(key)) for provider, key in (
        ("codex", "CODEX_THREAD_ID"), ("claude_code", "CLAUDE_CODE_SESSION_ID")
    ) if env.get(key, "").strip()]
    if len(found) != 1:
        raise ValueError("harness_identity_missing_or_ambiguous")
    provider, session = found[0]
    if not re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", session):
        raise ValueError("harness_session_format_unsupported")
    return provider + "-" + session


def private_root(root, *, create=True):
    root = Path(root).absolute()
    if create and not root.exists() and not root.is_symlink():
        root.mkdir(mode=0o700)  # Parents must already exist. Never chmod an existing root.
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077:
        raise ValueError("private_root_requires_real_directory_mode_0700")
    if info.st_uid != os.getuid():
        raise ValueError("private_root_owner_mismatch")
    return root.resolve(strict=True)


def new_file(path, data):
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def regular_bytes(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("evidence_non_regular_file")
        return stream.read()


@contextmanager
def journal_lock(root, *, create=True):
    flags = os.O_RDWR | os.O_NOFOLLOW | (os.O_CREAT if create else 0)
    fd = os.open(root / ".capture.lock", flags, 0o600)
    with os.fdopen(fd, "rb+") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("capture_lock_non_regular")
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def events(root):
    journal = root / "commands.jsonl"
    if not journal.exists() and not journal.is_symlink():
        return []
    data = regular_bytes(journal)
    if data and not data.endswith(b"\n"):
        raise ValueError("journal_incomplete_record_inspect_do_not_replay")
    records = [decode(line) for line in data.splitlines()]
    starts = {}
    finished = set()
    for number, record in enumerate(records, 1):
        if not isinstance(record, dict) or record.get("sequence") != number or record.get("schema") != FORMAT:
            raise ValueError("journal_shape_or_sequence_invalid")
        capture_id = record.get("capture_id")
        if not isinstance(capture_id, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", capture_id):
            raise ValueError("capture_id_invalid")
        if record.get("event") == "started":
            if capture_id in starts:
                raise ValueError("journal_duplicate_start")
            starts[capture_id] = record
        elif record.get("event") == "finished":
            if capture_id not in starts or capture_id in finished:
                raise ValueError("journal_unpaired_finish")
            finished.add(capture_id)
        else:
            raise ValueError("journal_event_invalid")
    return records


def append_event(root, records, event):
    event = {**event, "sequence": len(records) + 1, "schema": FORMAT}
    fd = os.open(root / "commands.jsonl", os.O_CREAT | os.O_APPEND | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "ab") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("capture_journal_non_regular")
        stream.write(encoded(event))
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    records.append(event)


INTERPRETER_PROBE = (
    "import json,sys; print(json.dumps({'executable':sys.executable,"
    "'version':list(sys.version_info[:3]),'full_version':sys.version,"
    "'implementation':sys.implementation.name}))"
)


def capture(root, capture_id, pass_name, argv, executable_ref, *, interpreter=False):
    actor = execution(os.environ)  # Before creating evidence or running anything.
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", capture_id):
        raise ValueError("capture_id_invalid")
    if pass_name not in ("I", "U", "V", "R") or executable_ref not in SYMBOLS:
        raise ValueError("capture_metadata_invalid")
    if not argv or not Path(argv[0]).is_absolute() or any(not isinstance(a, str) for a in argv):
        raise ValueError("command_requires_absolute_executable_and_exact_argv")
    if interpreter:
        if len(argv) != 1:
            raise ValueError("interpreter_requires_only_executable")
        argv = [argv[0], "-I", "-c", INTERPRETER_PROBE]
    root = private_root(root)
    with journal_lock(root):
        records = events(root)
        if any(r["capture_id"] == capture_id for r in records):
            raise ValueError("capture_id_already_used_inspect_do_not_replay")
        run = root / capture_id
        run.mkdir(mode=0o700)  # Exclusive reservation; partial directories are not retried.
        start = {"event": "started", "capture_id": capture_id, "pass": pass_name,
                 "execution_ref": actor, "observed_at_utc": now(), "argv": argv,
                 "cwd": os.getcwd(), "executable_ref": executable_ref,
                 "kind": "interpreter" if interpreter else "command"}
        append_event(root, records, start)  # Durable before subprocess start.
        exit_code = None
        process_error = None
        with (run / "stdout").open("xb") as stdout, (run / "stderr").open("xb") as stderr:
            os.chmod(run / "stdout", 0o600)
            os.chmod(run / "stderr", 0o600)
            try:
                exit_code = subprocess.run(argv, stdout=stdout, stderr=stderr, check=False).returncode
            except OSError as error:
                process_error = type(error).__name__  # No path-bearing exception message.
            finally:
                stdout.flush()
                stderr.flush()
                os.fsync(stdout.fileno())
                os.fsync(stderr.fileno())
        streams = {name: regular_bytes(run / name) for name in ("stdout", "stderr")}
        end = {"event": "finished", "capture_id": capture_id, "observed_at_utc": now(),
               "exit_code": exit_code, "process_error": process_error,
               "streams": {name: {"sha256": digest(data), "bytes": len(data)} for name, data in streams.items()}}
        if interpreter and exit_code == 0:
            try:
                value = decode(streams["stdout"])
                version = value["version"]
                if (not isinstance(version, list) or len(version) != 3
                        or any(type(n) is not int or n < 0 for n in version)
                        or value["implementation"] not in ("cpython", "pypy")):
                    raise ValueError("interpreter_metadata_invalid")
                end["interpreter"] = {"version": version, "implementation": value["implementation"]}
            except (ValueError, KeyError, TypeError, UnicodeError):
                end["interpreter_metadata_invalid"] = True
        append_event(root, records, end)  # No JSON receipt parsing can interrupt capture.
    return exit_code if exit_code is not None else 2


def receipt_metadata(value):
    """Private presentation only. Unknown stays null; never inherit another receipt."""
    source = value if isinstance(value, dict) else {}
    result = {name: source.get(name) for name in RECEIPT_FIELDS}
    projection = source.get("projection")
    result["source_digest"] = None
    if isinstance(projection, dict) and isinstance(projection.get("source"), dict):
        result["source_digest"] = projection["source"].get("digest")
    children = source.get("receipts")
    result["receipts"] = [receipt_metadata(child) for child in children] if isinstance(children, list) else []
    return result


def tree_bytes(root):
    if root.is_symlink() or not root.is_dir():
        raise ValueError("snapshot_requires_real_directory")
    result = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ValueError("snapshot_symlink_or_special_file_refused")
        relative = path.relative_to(root).as_posix()
        result[relative] = regular_bytes(path)
    return result


def freeze(source, destination):
    """Separate deterministic copy. Never modify U or include our own inventory in itself."""
    source = Path(source).absolute()
    destination = Path(destination).absolute()
    if source.is_symlink():
        raise ValueError("snapshot_source_symlink_refused")
    resolved_source = source.resolve(strict=True)
    resolved_destination = destination.resolve(strict=False)
    if (resolved_destination.is_relative_to(resolved_source)
            or resolved_source.is_relative_to(resolved_destination)):
        raise ValueError("snapshot_destination_must_be_separate")
    if destination.exists() or destination.is_symlink():
        raise ValueError("snapshot_destination_exists")
    # Captured commands serialize with this snapshot. Other tools must be quiescent.
    if (source / "commands.jsonl").exists():
        with journal_lock(private_root(source, create=False), create=False):
            records = events(source)
            if {r["capture_id"] for r in records if r["event"] == "started"} != {
                    r["capture_id"] for r in records if r["event"] == "finished"}:
                raise ValueError("snapshot_incomplete_command_inspect_do_not_replay")
            return freeze_tree(source, destination)
    return freeze_tree(source, destination)


def freeze_tree(source, destination):
    contents = tree_bytes(source)
    inventory = encoded({"schema": "aware.evaluation.freeze.v1", "files": {
        name: {"sha256": digest(data), "bytes": len(data)} for name, data in contents.items()},
        "non_claims": ["digest-bound snapshot, not WORM or an atomic customer-repository snapshot"]})
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w", format=tarfile.PAX_FORMAT) as stream:
        for name, data in contents.items():
            member = tarfile.TarInfo("snapshot/" + name)
            member.size = len(data)
            member.mode = 0o600
            member.mtime = 0
            stream.addfile(member, io.BytesIO(data))
    compressed = gzip.compress(archive.getvalue(), mtime=0)
    if tree_bytes(source) != contents:
        raise ValueError("snapshot_source_changed")
    destination.mkdir(mode=0o700)
    new_file(destination / "snapshot.tar.gz", compressed)
    new_file(destination / "inventory.json", inventory)
    sums = b"".join((digest(data)[7:] + "  " + name + "\n").encode() for name, data in sorted({
        "inventory.json": inventory, "snapshot.tar.gz": compressed}.items()))
    new_file(destination / "SHA256SUMS", sums)  # Excluded from its own inventory.
    return {"outcome": "frozen", "snapshot_sha256": digest(compressed), "files": len(contents)}


def export_metadata(root, destination):
    """No copying or substring redaction. Only constructed metadata leaves private storage."""
    root = private_root(root, create=False)
    destination = Path(destination).absolute()
    if destination.resolve(strict=False).is_relative_to(root):
        raise ValueError("export_destination_must_be_separate")
    with journal_lock(root, create=False):
        records = events(root)
        starts = [r for r in records if r["event"] == "started"]
        ends = {r["capture_id"]: r for r in records if r["event"] == "finished"}
        captures = []
        interpreter_captures = {}
        for number, start in enumerate(starts, 1):
            # Revalidate scalars before inclusion. Raw argv, cwd, IDs and streams never leave.
            actor = start.get("execution_ref", "")
            if not isinstance(actor, str) or not re.fullmatch(
                    r"(?:codex|claude_code)-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", actor):
                raise ValueError("export_execution_invalid")
            if start.get("pass") not in ("I", "U", "V", "R") or start.get("executable_ref") not in SYMBOLS:
                raise ValueError("export_metadata_invalid")
            if start.get("kind") not in ("command", "interpreter"):
                raise ValueError("export_kind_invalid")
            argv = start.get("argv")
            if not isinstance(argv, list) or not argv or any(not isinstance(a, str) for a in argv):
                raise ValueError("export_argv_invalid")
            interpreter_key = (actor, start["pass"], start["executable_ref"], argv[0])
            end = ends.get(start["capture_id"])
            item = {"capture": number, "execution_ref": actor, "pass": start["pass"],
                    "executable_ref": start["executable_ref"], "kind": start["kind"],
                    "argv_sha256": digest(encoded(start["argv"])),
                    "started_at_utc": public_time(start["observed_at_utc"]),
                    "ended_at_utc": None, "exit_code": None,
                    "result": "incomplete_effect_unknown" if end is None else "captured",
                    "streams": {}, "interpreter": None,
                    "interpreter_capture": interpreter_captures.get(interpreter_key)}
            if end is not None:
                if end["exit_code"] is not None and type(end["exit_code"]) is not int:
                    raise ValueError("export_exit_code_invalid")
                item["ended_at_utc"] = public_time(end["observed_at_utc"])
                item["exit_code"] = end["exit_code"]
                if end["exit_code"] is None:
                    item["result"] = "process_start_failed_or_unavailable"
                for name in ("stdout", "stderr"):
                    data = regular_bytes(root / start["capture_id"] / name)
                    observed = {"sha256": digest(data), "bytes": len(data)}
                    if observed != end["streams"][name]:
                        raise ValueError("export_stream_digest_mismatch")
                    item["streams"][name] = observed
                if start["kind"] == "interpreter" and "interpreter" in end:
                    # Recompute from original stream, not a caller-supplied public DTO.
                    probe = decode(regular_bytes(root / start["capture_id"] / "stdout"))
                    version = probe.get("version")
                    implementation = probe.get("implementation")
                    if (not isinstance(version, list) or len(version) != 3
                            or any(type(n) is not int or n < 0 for n in version)
                            or implementation not in ("cpython", "pypy")
                            or start["argv"][1:] != ["-I", "-c", INTERPRETER_PROBE]):
                        raise ValueError("export_interpreter_invalid")
                    item["interpreter"] = {"version": version, "implementation": implementation}
                    interpreter_captures[interpreter_key] = number
            captures.append(item)
        result = {"schema": "aware.evaluation.metadata-export.v1", "authority": "external-client-evidence-only",
                  "journal_sha256": digest(regular_bytes(root / "commands.jsonl")), "captures": captures,
                  "omissions": ["raw argv and inline payloads", "cwd and private paths", "raw streams and SDK receipts",
                                "arbitrary attachments and customer source"],
                  "non_claims": ["not a complete v2 submission or exhaustive sanitization audit",
                                 "no claim of product success, enforcement, authenticated identity or input isolation"]}
    new_file(destination, encoded(result))
    return {"outcome": "exported", "captures": len(captures)}


def public_time(value):
    if not isinstance(value, str):
        raise TypeError("timestamp_invalid")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("timestamp_requires_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("capture", "interpreter"):
        command = commands.add_parser(name)
        command.add_argument("--private-root", type=Path, required=True)
        command.add_argument("--capture-id", required=True)
        command.add_argument("--pass", dest="pass_name", choices=("I", "U", "V", "R"), required=True)
        command.add_argument("--executable-ref", choices=SYMBOLS, required=True)
        command.add_argument("argv", nargs=argparse.REMAINDER)
    command = commands.add_parser("freeze")
    command.add_argument("source", type=Path)
    command.add_argument("destination", type=Path)
    command = commands.add_parser("export")
    command.add_argument("--private-root", type=Path, required=True)
    command.add_argument("destination", type=Path)
    command = commands.add_parser("receipt")
    command.add_argument("private_json", type=Path)
    args = parser.parse_args()
    try:
        if args.operation in ("capture", "interpreter"):
            argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            return capture(args.private_root, args.capture_id, args.pass_name, argv,
                           args.executable_ref, interpreter=args.operation == "interpreter")
        if args.operation == "freeze":
            result = freeze(args.source, args.destination)
        elif args.operation == "export":
            result = export_metadata(args.private_root, args.destination)
        else:
            result = receipt_metadata(decode(regular_bytes(args.private_json)))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as error:
        # Do not print potentially private filenames, raw JSON or exception text.
        diagnostic = str(error) if type(error) is ValueError and re.fullmatch(r"[a-z_]+", str(error)) else type(error).__name__
        print(json.dumps({"outcome": "evidence_failure", "diagnostic": diagnostic,
                          "instruction": "inspect retained evidence; do not automatically rerun a product operation"}), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
