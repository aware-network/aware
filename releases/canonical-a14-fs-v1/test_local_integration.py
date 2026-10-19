"""A14 accounting over original frozen tests; retained reads, no installation."""

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from types import FunctionType

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "releases/canonical-a14-fs-v1"
BASELINE = "23d5b8ea89d5d62efcd47e3c69b29779148d6da3"
LAYOUT_SHA = "55d18f86bed814658e2e6994eb0d726595f05851483fec95a0a023e67f9ba919"
ENVELOPE_SHA = "050ed63545dd1d63c795285609e15dbdaa054c28788c9e5993e8a1871f356ea6"
PAYLOAD_SHA = "4d1bf3b5ab43e904d463ba307840cf681889339d7197b089083add866d692c58"
ISSUE = "docs/issues/2026/10/19/fb-2026-10-19-canonical-a14-public-integration-v0.md"
EXTRAS = {
    ISSUE,
    *[
        str(RELEASE.relative_to(ROOT)) + "/" + n
        for n in (
            "LAYOUT-REVIEW.json",
            "LOCAL-INTEGRATION.md",
            "test_local_integration.py",
        )
    ],
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


def load(path, digest, name):
    if path.is_symlink() or sha(path.read_bytes()) != digest:
        raise ValueError("original_integration_test_required")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bind(function, replacements):
    code = function.__code__
    if not all(
        any(type(c) is type(k) and c == k for c in code.co_consts) for k in replacements
    ):
        raise ValueError("original_test_constant_required")
    return FunctionType(
        code.replace(
            co_consts=tuple(
                next(
                    (
                        v
                        for k, v in replacements.items()
                        if type(c) is type(k) and c == k
                    ),
                    c,
                )
                for c in code.co_consts
            )
        ),
        function.__globals__,
        function.__name__,
        function.__defaults__,
        function.__closure__,
    )


owner = load(
    ROOT / "releases/canonical-reference-fs-v1/test_local_integration.py",
    "e43c4a7d786930d2e88888a554d81028e6e1f4560f7220225661356e0820a7ee",
    "a14_original_integration_test",
)
for name in (
    "ROOT",
    "RELEASE",
    "BASELINE",
    "LAYOUT_SHA",
    "ENVELOPE_SHA",
    "PAYLOAD_SHA",
    "ISSUE",
    "EXTRAS",
):
    setattr(owner, name, globals()[name])


class Integration(owner.Integration):
    test_exact_postimages_and_modes = bind(
        owner.Integration.test_exact_postimages_and_modes, {1745: 1818}
    )
    test_baseline_and_exact_scope = bind(
        owner.Integration.test_baseline_and_exact_scope, {37: 97, 41: 101}
    )
    test_whole_envelope_and_raw_findings = bind(
        owner.Integration.test_whole_envelope_and_raw_findings,
        {
            1801: 1835,
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-a14-source-notice-review-v1.tar.gz",
        },
    )
    test_installer_four_coordinates_only = bind(
        owner.Integration.test_installer_four_coordinates_only,
        {
            "73f5038b365dcc7f193b7ebd71b77145d12fe2386311be75dcffd9afadd25df9": "afca86cad0fe96c40250819a37b3ab7284236b30d12db919e6596c2aae6a9d30",
            "d133ae36d78648b0f1c77652b7ab56ded7b2180620e0c023eccf9da4c2cc88e0": "8c804765c0aae2ee8ffe72768158867eab29dae93c669ec6c259421103eaf0e8",
            "canonical-reference-source-notice-review-v1.tar.gz": "canonical-a14-source-notice-review-v1.tar.gz",
            "canonical-init-summary-source-notice-review-v1.tar.gz": "canonical-reference-source-notice-review-v1.tar.gz",
            "canonical-reference-fs-v1": "canonical-a14-fs-v1",
            "canonical-init-summary-fs-v1": "canonical-reference-fs-v1",
        },
    )

    def test_complete_source_map(self):
        bind(owner.Integration.test_complete_source_map, {1342: 1372})(self)
        index = json.loads((RELEASE / "SOURCE-INDEX.json").read_bytes())
        mapping = json.loads((RELEASE / "SOURCE-MAP.json").read_bytes())
        rows = [r for r in index["files"] if "metadata_overlay" in r]
        self.assertEqual(len(rows), 3)
        for row in rows:
            binding = row["metadata_overlay"]
            self.assertEqual(mapping[row["path"]]["metadata_overlay"], binding)
            self.assertEqual(
                sha((RELEASE / binding["original_attached_path"]).read_bytes()),
                binding["original_sha256"],
            )
            self.assertEqual(
                sha((ROOT / mapping[row["path"]]["path"]).read_bytes()),
                binding["effective_sha256"],
            )

    def test_original_retained_installation_reads(self):
        original = load(
            ROOT / "releases/canonical-init-summary-fs-v1/test_local_integration.py",
            "ad3e35eab434e9062afbb3294d478646c2debe37fbd4ff2368a35ee8489f9a68",
            "a14_original_retained_reads",
        )
        original.PAYLOAD_SHA = PAYLOAD_SHA
        bound = bind(original.retained_installation_reads, {153: 155})
        self.assertEqual(
            bound.__code__.co_code,
            original.retained_installation_reads.__code__.co_code,
        )
        bound(self)


if __name__ == "__main__":
    unittest.main()
