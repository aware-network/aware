import argparse
import json
import os
from pathlib import Path

from aware_command_runtime import AwareCommandRegistry, run_cli
from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_runtime import (
    decode_specification_snapshot,
    resolve_iteration_identity,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)

from .read_commands import _observation, register_read_commands


def compatibility_main(argv=None) -> int:
    """Historical raw-root diagnostics; not the installed consumer entrance."""
    parser = argparse.ArgumentParser(prog="aware-spec")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("observe", "iteration-identity", "create-draft"):
        command = commands.add_parser(name)
        command.add_argument("--source-base", required=True)
        command.add_argument("--root", action="append", required=True)
        if name != "create-draft":
            command.add_argument("--expected-source-digest")
        if name == "iteration-identity":
            command.add_argument("--iteration-ref", required=True)
        if name == "create-draft":
            command.add_argument("--snapshot-json", required=True)
            command.add_argument("--author-ref", required=True)
            command.add_argument("--intent-ref", required=True)
    args = parser.parse_args(argv)
    provider = None
    try:
        fd = os.open(args.source_base, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            provider = SpecificationFsSdkProvider(fd, tuple(args.root))
        finally:
            os.close(fd)
        client = SpecificationSdkClient(provider)
        if args.command == "create-draft":
            snapshot = decode_specification_snapshot(
                Path(args.snapshot_json).read_bytes()
            )
            if len(snapshot.definitions) != 1:
                raise SpecificationOperationError("draft_requires_one_definition")
            result = client.create_draft(
                SpecificationDraftRequest(
                    snapshot.definitions[0], args.author_ref, args.intent_ref
                )
            )
            output = _observation(result.observation)
            output.update(
                created_paths=result.created_paths,
                authoring_intent_ref=result.authoring_intent_ref,
                effect="published",
            )
        elif args.command == "iteration-identity":
            observation = client.observe(
                SpecificationObserveRequest(args.expected_source_digest)
            )
            identity = resolve_iteration_identity(
                observation.snapshot, args.iteration_ref
            )
            output = _observation(observation)
            output["selected_iteration_ref"] = identity.iteration_ref
            output["retained_capability_exported"] = False
        else:
            output = _observation(
                client.observe(SpecificationObserveRequest(args.expected_source_digest))
            )
        print(json.dumps(output, sort_keys=True))
        return 0
    except (ValueError, OSError, SpecificationOperationError) as error:
        print(
            json.dumps(
                {
                    "error": getattr(error, "code", "request_or_source_invalid"),
                    "effect": getattr(error, "effect", "none"),
                },
                sort_keys=True,
            )
        )
        return 2
    finally:
        if provider is not None:
            provider.close()


def main(argv=None) -> int:
    """Standalone read projection; authority remains with Protocol and SPEC."""
    registry = AwareCommandRegistry()
    register_read_commands(registry)
    return run_cli(registry, argv=argv, prog="aware-spec")
