"""Public owner-codec source tests using small genuine FileSystem carriers."""

import json
import os
import tempfile
import unittest
from contextlib import ExitStack
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from unittest.mock import patch

from aware_file_system import confined_mutation as read
from aware_file_system import private_directory as owner
from aware_file_system import retained_file_sequence as sequence
from aware_file_system import terminal_codec as codec


class TerminalCodecTests(unittest.TestCase):
    fixture_parent = None

    def setUp(self):
        self.root = Path(
            tempfile.mkdtemp(prefix=self._testMethodName + "-", dir=self.fixture_parent)
        )
        (self.root / "nested").mkdir(mode=0o700)
        handle = sequence.retain_confined_file_sequence(
            root=self.root,
            requests=(
                read.ConfinedFileMutationRequest(
                    read.ConfinedMutationKind.CREATE,
                    "nested/record",
                    False,
                    None,
                    b"original\x00\xffbytes",
                ),
            ),
            limits=sequence.ConfinedSequenceLimits(**sequence._LIMIT_CAPS),
            confinement_profile=read.ConfinedMutationProfile.DESCRIPTOR_WALK_V1,
        )
        self.values = {}

        def collect(value):
            if is_dataclass(value):
                self.values.setdefault(type(value), value)
                for row in fields(value):
                    collect(getattr(value, row.name))
            elif type(value) is tuple:
                for child in value:
                    collect(child)

        try:
            before = sequence.observe_confined_file_sequence(handle)
            collect(before)
            for step in before.binding.ordered_steps:
                result = sequence.execute_next_confined_file_step(
                    handle, expected_ordinal=step.ordinal
                )
                collect(result)
            collect(sequence.observe_confined_file_sequence(handle))
            try:
                sequence.execute_next_confined_file_step(handle, expected_ordinal=0)
            except sequence.ConfinedSequenceRefusal as error:
                self.sequence_error = error
                collect(error.evidence)
        finally:
            collect(sequence.release_confined_file_sequence(handle))
        collect(
            read.observe_confined_file_with_cleanup(
                root=self.root, path="nested/record"
            )
        )
        try:
            with patch.object(
                read.os, "read", side_effect=OSError("controlled original read failure")
            ):
                read.observe_confined_file_with_cleanup(
                    root=self.root, path="nested/record"
                )
        except read.ConfinedFileObservationError as error:
            self.read_error = error
        try:
            owner.retain_private_directory(
                root=self.root, privacy_profile="unsupported"
            )
        except owner.PrivateDirectoryRefusal as error:
            self.private_error = error

    def test_all_eighteen_roots_have_genuine_fixture_members(self):
        self.assertEqual(len(codec._VALUE_TYPES), 18)
        self.assertTrue(set(codec._VALUE_TYPES) <= set(self.values))

    def test_existing_sequence_payloads_remain_exact(self):
        for cls in sequence._VALUE_TYPES:
            with self.subTest(cls=cls):
                value = self.values[cls]
                self.assertEqual(
                    codec.terminal_value_to_payload(value),
                    sequence.confined_sequence_value_to_payload(value),
                )

    def test_unknown_cleanup_remains_unknown(self):
        unknown = read.ConfinedFileReadCleanup(
            "unknown", 2, 2, None, ("original uncertainty",)
        )
        payload = codec.terminal_value_to_payload(unknown)
        decoded = codec.terminal_value_from_payload(type(unknown), payload)
        self.assertEqual(decoded, unknown)
        self.assertIsNone(decoded.closed_count)
        cleanup = replace(
            self.values[sequence.ConfinedSequenceCleanup],
            ledger_complete=False,
            release="unknown",
        )
        self.assertEqual(
            codec.terminal_value_from_payload(
                type(cleanup), codec.terminal_value_to_payload(cleanup)
            ),
            cleanup,
        )

    def test_live_foreign_and_private_roots_refuse(self):
        for cls in (
            dict,
            object,
            sequence.RetainedConfinedFileSequence,
            owner.RetainedPrivateDirectory,
            owner.PrivateDirectoryBinding,
        ):
            with (
                self.subTest(cls=cls),
                self.assertRaises(owner.PrivateDirectoryRefusal),
            ):
                codec.terminal_value_from_payload(cls, {})
        for value in (None, {}, object(), self.sequence_error):
            with (
                self.subTest(value=type(value)),
                self.assertRaises(owner.PrivateDirectoryRefusal),
            ):
                codec.terminal_value_to_payload(value)

    def test_malformed_unknown_or_wrong_contract_refuse(self):
        cls = read.ConfinedFileReadCleanup
        good = codec.terminal_value_to_payload(self.values[cls])
        for payload in (
            {},
            dict(good, extra=True),
            dict(good, contract="foreign"),
            dict(good, value={}),
        ):
            with (
                self.subTest(payload=payload),
                self.assertRaises(owner.PrivateDirectoryRefusal),
            ):
                codec.terminal_value_from_payload(cls, payload)

    def test_boolean_counts_and_byte_corruption_refuse(self):
        cls = read.ConfinedFileReadCleanup
        payload = codec.terminal_value_to_payload(self.values[cls])
        payload["value"]["closed_count"] = True
        with self.assertRaises(owner.PrivateDirectoryRefusal):
            codec.terminal_value_from_payload(cls, payload)
        cls = read.ConfinedFileObservation
        payload = codec.terminal_value_to_payload(self.values[cls])
        payload["value"]["content"]["value"]["data"] = "corrupted"
        with self.assertRaises(owner.PrivateDirectoryRefusal):
            codec.terminal_value_from_payload(cls, payload)

    def test_all_original_error_families_roundtrip_detached(self):
        for error in (self.sequence_error, self.private_error, self.read_error):
            with self.subTest(error=type(error)):
                value = codec.capture_terminal_error(error)
                payload = codec.terminal_error_to_payload(error)
                decoded = codec.terminal_error_from_payload(
                    json.loads(json.dumps(payload, allow_nan=False))
                )
                self.assertEqual(decoded, value)
                self.assertIsNot(decoded, value)
                self.assertFalse(isinstance(decoded, BaseException))
                self.assertEqual(codec.terminal_error_to_payload(decoded), payload)
                self.assertEqual(decoded.code, error.code)

    def test_read_failure_retains_observation_and_unknown_cleanup(self):
        observed = self.values[read.ConfinedFileObservation]
        cleanup = read.ConfinedFileReadCleanup(
            "unknown", 2, 2, None, ("original interruption",)
        )
        error = read.ConfinedFileObservationError(
            "filesystem_read_cleanup_unverified",
            stage="cleanup",
            cause_kind="interrupted",
            root_locator=str(self.root),
            path=observed.path,
            observation=observed,
            cleanup=cleanup,
        )
        original_cause = KeyboardInterrupt(
            "original cause; not part of provider scalar payload"
        )
        error.__cause__ = original_cause
        decoded = codec.terminal_error_from_payload(
            codec.terminal_error_to_payload(error)
        )
        self.assertEqual(decoded.observation.content, b"original\x00\xffbytes")
        self.assertEqual(decoded.cleanup, cleanup)
        self.assertIs(error.__cause__, original_cause)
        self.assertEqual(decoded.cleanup.outcome, "unknown")

    def test_error_early_sequence_absence_is_not_filled(self):
        error = sequence.ConfinedSequenceRefusal("sequence_early_refusal")
        value = codec.terminal_error_from_payload(
            codec.terminal_error_to_payload(error)
        )
        self.assertIsNone(value.provider_evidence)

    def test_error_rejects_unknown_public_attributes_and_arguments(self):
        error = sequence.ConfinedSequenceRefusal("code")
        error.extra = "must not disappear"
        with self.assertRaises(codec.TerminalCodecError) as raised:
            codec.capture_terminal_error(error)
        self.assertIs(raised.exception.original_input, error)
        error = sequence.ConfinedSequenceRefusal("code")
        error.args = ("code", "extra argument")
        with self.assertRaises(codec.TerminalCodecError):
            codec.terminal_error_to_payload(error)

    def test_error_cross_code_path_and_family_mismatches_refuse(self):
        payload = codec.terminal_error_to_payload(self.sequence_error)
        payload["code"] = "foreign_code"
        with self.assertRaises(codec.TerminalCodecError):
            codec.terminal_error_from_payload(payload)
        payload = codec.terminal_error_to_payload(self.read_error)
        payload["provider_evidence"] = {}
        with self.assertRaises(codec.TerminalCodecError):
            codec.terminal_error_from_payload(payload)
        payload = codec.terminal_error_to_payload(self.private_error)
        payload["provider_evidence"] = None
        with self.assertRaises(codec.TerminalCodecError):
            codec.terminal_error_from_payload(payload)

    def test_error_unknown_schema_keys_and_types_refuse(self):
        good = codec.terminal_error_to_payload(self.read_error)
        for payload in (
            {},
            dict(good, extra=1),
            dict(good, schema="foreign"),
            dict(good, code=True),
            dict(good, family="future"),
        ):
            with (
                self.subTest(payload=payload),
                self.assertRaises(codec.TerminalCodecError) as raised,
            ):
                codec.terminal_error_from_payload(payload)
            self.assertIs(raised.exception.original_input, payload)

    def test_error_uses_one_original_budget_for_all_nested_values(self):
        original = owner._Budget
        instances = []

        def budget():
            value = original()
            instances.append(value)
            return value

        with patch.object(owner, "_Budget", side_effect=budget):
            payload = codec.terminal_error_to_payload(self.read_error)
        self.assertEqual(len(instances), 1)
        instances.clear()
        with patch.object(owner, "_Budget", side_effect=budget):
            codec.terminal_error_from_payload(payload)
        self.assertEqual(len(instances), 1)

    def test_capacity_refusal_uses_original_owner_limits(self):
        with (
            patch.object(owner, "_MAX_WIRE", 64),
            self.assertRaises(owner.PrivateDirectoryRefusal) as raised,
        ):
            codec.terminal_value_to_payload(
                self.values[sequence.ConfinedSequenceBinding]
            )
        self.assertEqual(raised.exception.code, "private_codec_capacity_exceeded")
        with (
            patch.object(owner, "_MAX_PRIVATE", 64),
            self.assertRaises(codec.TerminalCodecError),
        ):
            codec.terminal_error_to_payload(self.read_error)

    def test_codec_has_no_io_enrollment_or_cleanup(self):
        original_payloads = [
            (cls, codec.terminal_value_to_payload(self.values[cls]))
            for cls in codec._VALUE_TYPES
        ]
        errors = [
            codec.terminal_error_to_payload(value)
            for value in (self.sequence_error, self.private_error, self.read_error)
        ]
        before = (
            dict(sequence._HANDLES),
            dict(owner._DIRECTORIES),
            dict(owner._PRIVATE_SEQUENCES),
        )

        def forbidden(*args, **kwargs):
            raise AssertionError("codec must not perform IO")

        with ExitStack() as stack:
            for name in (
                "open",
                "read",
                "write",
                "close",
                "stat",
                "lstat",
                "fstat",
                "chmod",
                "unlink",
            ):
                stack.enter_context(patch.object(os, name, forbidden))
            for cls, payload in original_payloads:
                self.assertEqual(
                    codec.terminal_value_to_payload(
                        codec.terminal_value_from_payload(cls, payload)
                    ),
                    payload,
                )
            for payload in errors:
                self.assertEqual(
                    codec.terminal_error_to_payload(
                        codec.terminal_error_from_payload(payload)
                    ),
                    payload,
                )
        self.assertEqual(
            (
                dict(sequence._HANDLES),
                dict(owner._DIRECTORIES),
                dict(owner._PRIVATE_SEQUENCES),
            ),
            before,
        )

    def test_original_constructor_substitution_refuses_before_call(self):
        value = self.values[read.ConfinedFileReadCleanup]
        payload = codec.terminal_value_to_payload(value)
        calls = []

        def foreign(*args, **kwargs):
            calls.append(True)

        with patch.object(read.ConfinedFileReadCleanup, "__post_init__", foreign):
            with self.assertRaises(owner.PrivateDirectoryRefusal):
                codec.terminal_value_to_payload(value)
            with self.assertRaises(owner.PrivateDirectoryRefusal):
                codec.terminal_value_from_payload(type(value), payload)
        self.assertEqual(calls, [])

    def test_invalid_read_error_path_retains_rejected_carrier(self):
        error = read.ConfinedFileObservationError(
            "filesystem_read_failed",
            stage="read",
            cause_kind="failed",
            root_locator=str(self.root),
            path="foreign",
            observation=self.values[read.ConfinedFileObservation],
            cleanup=self.values[read.ConfinedFileReadCleanup],
        )
        with self.assertRaises(codec.TerminalCodecError) as raised:
            codec.capture_terminal_error(error)
        self.assertIs(raised.exception.original_input, error)
        self.assertFalse(raised.exception.authorizes_retry)

    def test_new_evidence_constructor_substitution_refuses_before_call(self):
        payload = codec.terminal_error_to_payload(self.read_error)
        calls = []

        def foreign(*args, **kwargs):
            calls.append(True)

        with patch.object(codec.TerminalErrorEvidence, "__init__", foreign):
            with self.assertRaises(codec.TerminalCodecError):
                codec.capture_terminal_error(self.read_error)
            with self.assertRaises(codec.TerminalCodecError):
                codec.terminal_error_from_payload(payload)
        self.assertEqual(calls, [])

    def test_foreign_provider_error_export_cannot_become_original(self):
        class Foreign(RuntimeError):
            def __init__(self):
                self.code = "foreign_code"
                self.evidence = None
                super().__init__(self.code)

        error = Foreign()
        with (
            patch.object(sequence, "ConfinedSequenceRefusal", Foreign),
            self.assertRaises(codec.TerminalCodecError) as raised,
        ):
            codec.capture_terminal_error(error)
        self.assertIs(raised.exception.original_input, error)


def _roundtrip(value_type):
    def test(self):
        value = self.values[value_type]
        payload = codec.terminal_value_to_payload(value)
        decoded = codec.terminal_value_from_payload(
            value_type, json.loads(json.dumps(payload, allow_nan=False))
        )
        self.assertEqual(decoded, value)
        self.assertIs(type(decoded), value_type)
        self.assertIsNot(decoded, value)
        self.assertEqual(codec.terminal_value_to_payload(decoded), payload)
        payload["value"].clear()
        self.assertEqual(decoded, value)

    return test


for _type in codec._VALUE_TYPES:
    setattr(TerminalCodecTests, "test_roundtrip_" + _type.__name__, _roundtrip(_type))
