"""Synthetic evaluator fixtures; no private client evidence or customer source."""

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("evaluation_evidence", Path(__file__).with_name("evidence.py"))
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)
SESSION = "01234567-89ab-4cde-8fab-0123456789ab"


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="aware-evaluator-tooling-")
        self.base = Path(self.temporary.name)
        self.root = self.base / "private"
        self.environment = patch.dict(os.environ, {"CODEX_THREAD_ID": SESSION}, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def command(self, code="print('fixture')", capture_id="first", pass_name="U"):
        return evidence.capture(self.root, capture_id, pass_name, [sys.executable, "-c", code], "task-python")

    def journal(self):
        return evidence.events(self.root)

    def export(self):
        destination = self.base / "public.json"
        evidence.export_metadata(self.root, destination)
        return json.loads(destination.read_bytes())

    def test_discover_codex_identity_without_borrowing(self):
        self.assertEqual(evidence.execution(os.environ), "codex-" + SESSION)

    def test_claude_identity_is_separate(self):
        self.assertEqual(evidence.execution({"CLAUDE_CODE_SESSION_ID": SESSION}), "claude_code-" + SESSION)

    def test_missing_ambiguous_or_unsupported_identity(self):
        for env in ({}, {"CODEX_THREAD_ID": SESSION, "CLAUDE_CODE_SESSION_ID": SESSION}, {"CODEX_THREAD_ID": "borrowed"}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                evidence.execution(env)

    def test_missing_identity_refuses_before_evidence_or_command(self):
        marker = self.base / "effect"
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            self.command(f"from pathlib import Path; Path({str(marker)!r}).touch()")
        self.assertFalse(marker.exists())
        self.assertFalse(self.root.exists())

    def test_first_identity_command_has_start_before_execution(self):
        code = ("import json,os; from pathlib import Path; "
                f"rows=Path({str(self.root / 'commands.jsonl')!r}).read_text().splitlines(); "
                "assert len(rows)==1 and json.loads(rows[0])['event']=='started'; "
                "print(os.environ['CODEX_THREAD_ID'])")
        self.assertEqual(self.command(code), 0)
        self.assertEqual((self.root / "first" / "stdout").read_text().strip(), SESSION)
        self.assertEqual([r["event"] for r in self.journal()], ["started", "finished"])
        self.assertEqual(self.journal()[0]["argv"], [sys.executable, "-c", code])

    def test_child_refusal_with_null_projection_does_not_break_capture(self):
        self.assertEqual(self.command("import sys; print('{\"projection\":null}'); sys.exit(2)"), 2)
        self.assertEqual(self.journal()[1]["exit_code"], 2)
        summary = evidence.receipt_metadata(json.loads((self.root / "first" / "stdout").read_bytes()))
        self.assertIsNone(summary["source_digest"])

    def test_unknown_receipts_are_null(self):
        for value in (None, [], "not an envelope", {"projection": None}, {"projection": {"source": None}}):
            with self.subTest(value=value):
                summary = evidence.receipt_metadata(value)
                self.assertIsNone(summary["reference_update"])
                self.assertIsNone(summary["source_digest"])

    def test_receipt_preserves_publication_fields_and_false_without_inheriting(self):
        summary = evidence.receipt_metadata({"reference_update": "cas_failed", "operator_ref": "owner",
                                             "transaction_mode": "compare_and_swap", "index_reconciliation_pending": False,
                                             "receipts": [{"projection": None}, None]})
        self.assertEqual(summary["reference_update"], "cas_failed")
        self.assertEqual(summary["operator_ref"], "owner")
        self.assertEqual(summary["transaction_mode"], "compare_and_swap")
        self.assertIs(summary["index_reconciliation_pending"], False)
        self.assertIsNone(summary["receipts"][0]["reference_update"])
        self.assertIsNone(summary["receipts"][1]["operator_ref"])

    def test_duplicate_id_does_not_execute_again(self):
        marker = self.base / "effect"
        code = f"from pathlib import Path; p=Path({str(marker)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x')"
        self.command(code)
        with self.assertRaisesRegex(ValueError, "already_used"):
            self.command(code)
        self.assertEqual(marker.read_text(), "x")

    def test_completion_logging_failure_retains_start_and_does_not_replay(self):
        marker = self.base / "effect"
        original = evidence.append_event

        def fail_finish(root, records, event):
            if event["event"] == "finished":
                raise OSError("synthetic full disk")
            return original(root, records, event)

        with patch.object(evidence, "append_event", side_effect=fail_finish), self.assertRaises(OSError):
            self.command(f"from pathlib import Path; Path({str(marker)!r}).write_text('once')")
        self.assertEqual(marker.read_text(), "once")
        self.assertEqual(len(self.journal()), 1)
        with self.assertRaisesRegex(ValueError, "already_used"):
            self.command()
        self.assertEqual(self.export()["captures"][0]["result"], "incomplete_effect_unknown")
        with self.assertRaisesRegex(ValueError, "incomplete_command"):
            evidence.freeze(self.root, self.base / "freeze")

    def test_start_logging_failure_prevents_execution(self):
        marker = self.base / "effect"
        with patch.object(evidence, "append_event", side_effect=OSError("synthetic")), self.assertRaises(OSError):
            self.command(f"from pathlib import Path; Path({str(marker)!r}).touch()")
        self.assertFalse(marker.exists())
        # The reservation itself prevents accidental reuse even without a journal entry.
        with self.assertRaises(FileExistsError):
            self.command()

    def test_missing_executable_retains_typed_observation(self):
        self.assertEqual(evidence.capture(self.root, "missing", "I", [str(self.base / "absent")], "selected-command"), 2)
        self.assertIsNone(self.journal()[1]["exit_code"])
        self.assertEqual(self.journal()[1]["process_error"], "FileNotFoundError")

    def test_exact_argv_not_shell_expansion(self):
        marker = self.base / "must-not-exist"
        argument = "$(touch " + str(marker) + ")"
        evidence.capture(self.root, "args", "U", [sys.executable, "-c", "import sys; print(sys.argv[1])", argument], "task-python")
        self.assertEqual((self.root / "args" / "stdout").read_text().strip(), argument)
        self.assertFalse(marker.exists())

    def test_relative_executable_refused(self):
        with self.assertRaisesRegex(ValueError, "absolute_executable"):
            evidence.capture(self.root, "first", "U", ["python3"], "task-python")

    def test_open_private_root_is_not_silently_chmodded(self):
        self.root.mkdir(mode=0o755)
        with self.assertRaisesRegex(ValueError, "0700"):
            self.command()
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o755)

    def test_private_root_mode_and_stream_mode_preserved(self):
        self.command()
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o700)
        for name in ("stdout", "stderr"):
            self.assertEqual((self.root / "first" / name).stat().st_mode & 0o777, 0o600)

    def test_symlink_root_refused(self):
        target = self.base / "target"
        target.mkdir(mode=0o700)
        self.root.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "0700"):
            self.command()
        self.assertEqual(list(target.iterdir()), [])

    def test_symlink_journal_refused_before_command(self):
        self.root.mkdir(mode=0o700)
        target = self.base / "target"
        target.write_bytes(b"")
        (self.root / "commands.jsonl").symlink_to(target)
        with self.assertRaises(OSError):
            self.command()
        self.assertEqual(target.read_bytes(), b"")

    def test_partial_journal_refuses_new_command(self):
        self.command()
        with (self.root / "commands.jsonl").open("ab") as stream:
            stream.write(b'{"incomplete":')
        with self.assertRaisesRegex(ValueError, "incomplete_record"):
            self.command(capture_id="second")
        self.assertFalse((self.root / "second").exists())

    def test_contiguous_journal_sequences(self):
        self.command()
        self.command(capture_id="second", pass_name="V")
        self.assertEqual([r["sequence"] for r in self.journal()], [1, 2, 3, 4])

    def test_concurrent_processes_serialize_the_journal(self):
        self.root.mkdir(mode=0o700)
        processes = []
        for name in ("one", "two"):
            argv = [sys.executable, "-I", "-B", evidence.__file__, "capture",
                    "--private-root", str(self.root), "--capture-id", name, "--pass", "V",
                    "--executable-ref", "task-python", "--", sys.executable, "-c", "print('fixture')"]
            processes.append(subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        for process in processes:
            _, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
        rows = self.journal()
        self.assertEqual([r["sequence"] for r in rows], [1, 2, 3, 4])
        self.assertEqual([r["event"] for r in rows], ["started", "finished", "started", "finished"])

    def test_fifo_journal_refuses_without_blocking_or_effect(self):
        self.root.mkdir(mode=0o700)
        os.mkfifo(self.root / "commands.jsonl")
        with self.assertRaisesRegex(ValueError, "non_regular_file"):
            self.command()
        self.assertFalse((self.root / "first").exists())

    def test_interpreter_capture_and_export_keep_actual_numeric_version(self):
        self.assertEqual(evidence.capture(self.root, "python", "U", [sys.executable], "task-python", interpreter=True), 0)
        exported = self.export()["captures"][0]
        self.assertEqual(exported["interpreter"]["version"], list(sys.version_info[:3]))
        self.assertEqual(exported["executable_ref"], "task-python")
        self.assertNotIn(sys.executable, json.dumps(exported))

    def test_interpreter_does_not_accept_arbitrary_probe(self):
        with self.assertRaisesRegex(ValueError, "only_executable"):
            evidence.capture(self.root, "python", "U", [sys.executable, "-c", "print('secret')"], "task-python", interpreter=True)

    def test_test_command_links_only_same_prior_execution_pass_symbol_and_executable(self):
        evidence.capture(self.root, "python", "U", [sys.executable], "task-python", interpreter=True)
        self.command(capture_id="tests")
        self.command(capture_id="other-pass", pass_name="V")
        evidence.capture(self.root, "other-symbol", "U", [sys.executable, "-c", "print('fixture')"], "aware-python")
        rows = self.export()["captures"]
        self.assertEqual(rows[1]["interpreter_capture"], 1)
        self.assertIsNone(rows[2]["interpreter_capture"])
        self.assertIsNone(rows[3]["interpreter_capture"])

    def test_other_execution_cannot_borrow_interpreter_provenance(self):
        evidence.capture(self.root, "python", "U", [sys.executable], "task-python", interpreter=True)
        with patch.dict(os.environ, {"CODEX_THREAD_ID": "11111111-2222-4333-8444-555555555555"}, clear=True):
            self.command(capture_id="other-actor")
        self.assertIsNone(self.export()["captures"][1]["interpreter_capture"])

    def test_other_executable_cannot_borrow_interpreter_provenance(self):
        evidence.capture(self.root, "python", "U", [sys.executable], "task-python", interpreter=True)
        evidence.capture(self.root, "other-path", "U", ["/bin/true"], "task-python")
        self.assertIsNone(self.export()["captures"][1]["interpreter_capture"])

    def test_export_default_omits_code_patches_raw_streams_paths_and_arbitrary_metadata(self):
        secret = "PRIVATE_PAYLOAD_MARKER"
        self.command(f"print({secret!r}) # *** Begin Patch /home/private/client.py")
        journal = self.root / "commands.jsonl"
        records = self.journal()
        records[0]["arbitrary_attachment"] = "SECRET_ATTACHMENT"
        records[1]["arbitrary_diagnostic"] = "SECRET_DIAGNOSTIC"
        journal.write_bytes(b"".join(evidence.encoded(r) for r in records))
        value = self.export()
        public = json.dumps(value)
        for omitted in (secret, "*** Begin Patch", "SECRET_ATTACHMENT", "SECRET_DIAGNOSTIC", str(self.base), "/home/private", sys.executable):
            self.assertNotIn(omitted, public)
        row = value["captures"][0]
        self.assertEqual(row["argv_sha256"], evidence.digest(evidence.encoded(records[0]["argv"])))
        self.assertEqual(row["streams"]["stdout"]["sha256"], evidence.digest((self.root / "first" / "stdout").read_bytes()))
        self.assertEqual(value["authority"], "external-client-evidence-only")

    def test_export_retains_null_exit_code_without_inventing_success(self):
        evidence.capture(self.root, "absent", "I", [str(self.base / "absent")], "selected-command")
        self.assertIsNone(self.export()["captures"][0]["exit_code"])

    def test_export_stream_substitution_refused(self):
        self.command()
        (self.root / "first" / "stdout").write_text("changed")
        with self.assertRaisesRegex(ValueError, "digest_mismatch"):
            self.export()
        self.assertFalse((self.base / "public.json").exists())

    def test_export_refuses_inside_private_root_and_overwrite(self):
        self.command()
        with self.assertRaisesRegex(ValueError, "separate"):
            evidence.export_metadata(self.root, self.root / "public.json")
        self.export()
        with self.assertRaises(FileExistsError):
            self.export()

    def test_export_invalid_scalar_refused_not_redacted_into_success(self):
        self.command()
        rows = self.journal()
        rows[0]["executable_ref"] = "/private/path"
        (self.root / "commands.jsonl").write_bytes(b"".join(evidence.encoded(r) for r in rows))
        with self.assertRaisesRegex(ValueError, "metadata_invalid"):
            self.export()

    def test_freeze_is_deterministic_self_excluding_and_does_not_change_input(self):
        self.command()
        before = evidence.tree_bytes(self.root)
        modes = {p: p.stat().st_mode for p in self.root.rglob("*")}
        a, b = self.base / "freeze-a", self.base / "freeze-b"
        self.assertEqual(evidence.freeze(self.root, a), evidence.freeze(self.root, b))
        self.assertEqual(evidence.tree_bytes(a), evidence.tree_bytes(b))
        self.assertEqual(evidence.tree_bytes(self.root), before)
        self.assertEqual({p: p.stat().st_mode for p in self.root.rglob("*")}, modes)
        checksums = (a / "SHA256SUMS").read_text().splitlines()
        self.assertEqual(len(checksums), 2)
        for row in checksums:
            sha, name = row.split("  ", 1)
            self.assertNotEqual(name, "SHA256SUMS")
            self.assertEqual(sha, hashlib.sha256((a / name).read_bytes()).hexdigest())
        with tarfile.open(fileobj=io.BytesIO((a / "snapshot.tar.gz").read_bytes()), mode="r:gz") as archive:
            self.assertEqual(set(archive.getnames()), {"snapshot/" + name for name in before})

    def test_freeze_separate_outputs_existing_input_checksum_is_carried_not_rewritten(self):
        self.root.mkdir(mode=0o700)
        (self.root / "SHA256SUMS").write_text("original customer evidence inventory\n")
        evidence.freeze(self.root, self.base / "freeze")
        inventory = json.loads((self.base / "freeze" / "inventory.json").read_bytes())
        self.assertIn("SHA256SUMS", inventory["files"])
        self.assertEqual((self.root / "SHA256SUMS").read_text(), "original customer evidence inventory\n")

    def test_freeze_destination_inside_source_or_ancestor_refused(self):
        self.root.mkdir(mode=0o700)
        for destination in (self.root / "frozen", self.base):
            with self.subTest(destination=destination), self.assertRaisesRegex(ValueError, "separate"):
                evidence.freeze(self.root, destination)

    def test_freeze_no_overwrite(self):
        self.root.mkdir(mode=0o700)
        destination = self.base / "frozen"
        evidence.freeze(self.root, destination)
        with self.assertRaisesRegex(ValueError, "exists"):
            evidence.freeze(self.root, destination)

    def test_freeze_symlink_and_fifo_refused(self):
        self.root.mkdir(mode=0o700)
        (self.root / "link").symlink_to(self.base / "missing")
        with self.assertRaisesRegex(ValueError, "special_file"):
            evidence.freeze(self.root, self.base / "frozen")
        (self.root / "link").unlink()
        os.mkfifo(self.root / "fifo")
        with self.assertRaisesRegex(ValueError, "special_file"):
            evidence.freeze(self.root, self.base / "frozen")

    def test_freeze_detects_observed_source_change(self):
        self.root.mkdir(mode=0o700)
        original = evidence.tree_bytes
        calls = []

        def changes(root):
            calls.append(root)
            if len(calls) == 2:
                (root / "new").write_bytes(b"later")
            return original(root)

        with patch.object(evidence, "tree_bytes", side_effect=changes), self.assertRaisesRegex(ValueError, "source_changed"):
            evidence.freeze(self.root, self.base / "frozen")
        self.assertFalse((self.base / "frozen").exists())

    def test_freeze_does_not_create_missing_capture_lock_in_input(self):
        self.root.mkdir(mode=0o700)
        (self.root / "commands.jsonl").write_bytes(b"")
        with self.assertRaises(FileNotFoundError):
            evidence.freeze(self.root, self.base / "frozen")
        self.assertFalse((self.root / ".capture.lock").exists())

    def test_duplicate_json_key_refused(self):
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            evidence.decode('{"a":1,"a":2}')

    def test_cli_runs_exact_command_and_preserves_exit_code(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(Path(evidence.__file__)), "capture",
                                 "--private-root", str(self.root), "--capture-id", "cli", "--pass", "I",
                                 "--executable-ref", "selected-command", "--", sys.executable, "-c", "import sys; sys.exit(7)"],
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(self.journal()[1]["exit_code"], 7)

    def test_cli_formatter_error_does_not_echo_private_path(self):
        missing = self.base / "private-secret.json"
        result = subprocess.run([sys.executable, "-I", "-B", str(Path(evidence.__file__)), "receipt", str(missing)],
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 3)
        self.assertNotIn(str(missing).encode(), result.stderr)
        self.assertIn(b"do not automatically rerun", result.stderr)


if __name__ == "__main__":
    unittest.main()
