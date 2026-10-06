import argparse
import json
import os
from pathlib import Path

from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_runtime import (
    decode_specification_snapshot,
    encode_specification_snapshot,
    resolve_iteration_identity,
)
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObserveRequest,
    SpecificationOperationError,
    SpecificationSdkClient,
)


def _observation(value) -> dict[str, object]:
    return {
        "snapshot": json.loads(encode_specification_snapshot(value.snapshot)),
        "source_digest": value.source_digest,
        "source_context_digest": value.source_context_digest,
        "provider_ref": value.provider_ref,
        "authority_mode": value.authority_mode,
        "observation_grade": value.observation_grade,
        "iterations": [
            {
                "iteration_ref": i.iteration_ref,
                "plan_revision": i.plan.plan_revision,
                "plan_digest": i.plan_digest,
            }
            for i in value.iterations
        ],
        "work_authority": False,
        "phase_acceptance": False,
    }


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
    """Read-only consumer composition over fresh, original Protocol issuance."""
    parser = argparse.ArgumentParser(prog="aware-spec")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("observe", "iteration-identity"):
        command = commands.add_parser(name)
        command.add_argument("--repository-root", required=True)
        command.add_argument("--protocol-manifest", default="aware.protocol.toml")
        command.add_argument("--spec-manifest", action="append", required=True)
        command.add_argument("--expected-manifest-sha256")
        command.add_argument("--expected-source-digest")
        if name == "iteration-identity":
            command.add_argument("--iteration-ref", required=True)
    args = parser.parse_args(argv)
    provider = None
    selection = None
    release = None
    output: dict[str, object] = {}
    exit_code = 2
    try:
        try:
            from aware_protocol_fs_adapter import (
                admit_specification_selection,
                release_specification_selection,
                require_specification_selection,
            )
        except ImportError as error:
            raise SpecificationOperationError(
                "protocol_integration_unavailable"
            ) from error
        release = release_specification_selection
        repository = Path(args.repository_root)
        manifest = Path(args.protocol_manifest)
        # Protocol resolves relative manifests beneath the repository once.
        admission = admit_specification_selection(
            repository_root=repository,
            manifest_path=manifest,
            selected_manifest_paths=tuple(args.spec_manifest),
            expected_manifest_sha256=args.expected_manifest_sha256,
        )
        selection = admission.selection
        if selection is None:
            output = {
                "error": "protocol_selection_admission_refused",
                "diagnostics": list(admission.admission.diagnostics),
                "effect": "none",
            }
        else:
            provider = SpecificationFsSdkProvider.from_protocol_selection(selection)
            observation = SpecificationSdkClient(provider).observe(
                SpecificationObserveRequest(args.expected_source_digest)
            )
            output = _observation(observation)
            output["retained_capability_exported"] = False
            if args.command == "iteration-identity":
                identity = resolve_iteration_identity(
                    observation.snapshot, args.iteration_ref
                )
                output["selected_iteration_ref"] = identity.iteration_ref
            require_specification_selection(selection)
            exit_code = 0
    except (ValueError, OSError) as error:
        output = {
            "error": getattr(error, "code", "request_or_source_invalid"),
            "effect": getattr(error, "effect", "none"),
        }
    finally:
        cleanup: list[str] = []
        try:
            if provider is not None:
                provider.close()
        except (ValueError, OSError) as error:
            cleanup.append(f"source_provider_cleanup_failed:{type(error).__name__}")
        finally:
            try:
                if selection is not None and release is not None:
                    release(selection)
            except (ValueError, OSError) as error:
                cleanup.append(
                    f"protocol_selection_cleanup_failed:{type(error).__name__}"
                )
        if cleanup:
            if exit_code == 0:
                output = {"error": "source_cleanup_failed", "effect": "none"}
                exit_code = 2
            output["cleanup_diagnostics"] = cleanup
    print(json.dumps(output, sort_keys=True))
    return exit_code
