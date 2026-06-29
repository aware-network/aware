from __future__ import annotations

import argparse
import json
from pathlib import Path

from aware_file_system.native_apply_benchmark import (
    NativeApplyBenchmarkConfig,
    run_native_apply_benchmark,
)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Emit Python-vs-Rust native apply benchmark evidence.",
    )
    parser.add_argument("--fixture-root", required=True)
    parser.add_argument("--target-dir", default=None)
    parser.add_argument("--cargo-path", default=None)
    parser.add_argument("--cargo-home", default=None)
    parser.add_argument("--manifest-path", default=None)
    parser.add_argument("--prepared-binary-path", default=None)
    parser.add_argument("--prepared-service-binary-path", default=None)
    parser.add_argument("--prepared-library-path", default=None)
    parser.add_argument("--files-per-operation", type=int, default=16)
    parser.add_argument("--create-file-count", type=int, default=None)
    parser.add_argument("--update-file-count", type=int, default=None)
    parser.add_argument("--delete-file-count", type=int, default=None)
    parser.add_argument("--payload-bytes", type=int, default=1024)
    parser.add_argument(
        "--payload-content-kind",
        choices=("text", "bytes"),
        default="text",
    )
    parser.add_argument("--fixture-profile", default="balanced")
    parser.add_argument("--no-digest-verification", action="store_true")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--build-timeout-s", type=float, default=240.0)
    parser.add_argument("--rust-library-backend", action="store_true")
    parser.add_argument("--rust-service-backend", action="store_true")
    parser.add_argument("--rust-service-streaming-payload", action="store_true")
    parser.add_argument("--rust-service-direct-streaming-payload", action="store_true")
    parser.add_argument("--rust-service-stream-chunk-bytes", type=int, default=262_144)
    parser.add_argument("--rust-service-compact-response", action="store_true")
    parser.add_argument("--rust-service-server-timings", action="store_true")
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--receipt-dir", default=None)
    parser.add_argument("--compact", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    receipt = run_native_apply_benchmark(
        NativeApplyBenchmarkConfig(
            files_per_operation=args.files_per_operation,
            payload_bytes=args.payload_bytes,
            payload_content_kind=args.payload_content_kind,
            iterations=args.iterations,
            fixture_profile=args.fixture_profile,
            create_file_count=args.create_file_count,
            update_file_count=args.update_file_count,
            delete_file_count=args.delete_file_count,
            verify_digests=not args.no_digest_verification,
            fixture_root=Path(args.fixture_root),
            target_dir=Path(args.target_dir) if args.target_dir else None,
            cargo_path=Path(args.cargo_path) if args.cargo_path else None,
            cargo_home=Path(args.cargo_home) if args.cargo_home else None,
            manifest_path=Path(args.manifest_path) if args.manifest_path else None,
            prepared_binary_path=(
                Path(args.prepared_binary_path) if args.prepared_binary_path else None
            ),
            prepared_service_binary_path=(
                Path(args.prepared_service_binary_path)
                if args.prepared_service_binary_path
                else None
            ),
            prepared_library_path=(
                Path(args.prepared_library_path) if args.prepared_library_path else None
            ),
            rust_library_backend=args.rust_library_backend,
            rust_service_backend=args.rust_service_backend,
            rust_service_streaming_payload=args.rust_service_streaming_payload,
            rust_service_direct_streaming_payload=(
                args.rust_service_direct_streaming_payload
            ),
            rust_service_stream_chunk_bytes=args.rust_service_stream_chunk_bytes,
            rust_service_compact_response=args.rust_service_compact_response,
            rust_service_server_timings=args.rust_service_server_timings,
            release=args.release,
            build_timeout_s=args.build_timeout_s,
            write_receipt=args.write_receipt,
            receipt_dir=Path(args.receipt_dir) if args.receipt_dir else None,
        )
    )
    indent = None if args.compact else 2
    print(json.dumps(receipt, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
