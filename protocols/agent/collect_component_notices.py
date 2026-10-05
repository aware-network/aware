"""Retain conservative legal inputs from the exact publisher SBOM, not linkage claims."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import time
import urllib.request
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / "notices/pydantic-core"
    root.mkdir(parents=True, exist_ok=True)
    wheel_bytes = args.wheel.read_bytes()
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as wheel:
        sbom_bytes = wheel.read(next(n for n in wheel.namelist() if n.endswith("cyclonedx.json")))
    (root / "publisher.cyclonedx.json").write_bytes(sbom_bytes)
    sbom = json.loads(sbom_bytes)

    def acquire(component):
        name, version = component["name"], component["version"]
        expected = next(item["content"] for item in component["hashes"] if item["alg"] == "SHA-256")
        url = f"https://static.crates.io/crates/{name}/{name}-{version}.crate"
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Aware-OSS-notice-account/0.1"}), timeout=45) as response:
                    data = response.read()
                break
            except OSError:
                if attempt == 3:
                    raise
                time.sleep(attempt + 1)
        if sha(data) != expected:
            raise ValueError("sbom_acquisition_hash_mismatch:" + name)
        texts = []
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member in archive.getmembers():
                basename = Path(member.name).name.upper()
                if not member.isfile() or not (any(word in basename for word in ("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT", "UNLICENSE")) or (name == "r-efi" and basename == "AUTHORS")):
                    continue
                relative = Path(member.name).relative_to(name + "-" + version)
                if ".." in relative.parts:
                    raise ValueError("unsafe_notice_member")
                content = archive.extractfile(member).read()
                target = root / "crates" / (name + "-" + version) / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                texts.append({"path": target.relative_to(root).as_posix(), "sha256": sha(content), "bytes": len(content)})
        if not texts:
            if name != "wit-bindgen-rt":
                raise ValueError("no_packaged_legal_text:" + name)
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
                vcs = json.loads(archive.extractfile(name + "-" + version + "/.cargo_vcs_info.json").read())
            for filename in ("LICENSE-MIT", "LICENSE-APACHE", "LICENSE-Apache-2.0_WITH_LLVM-exception"):
                source_url = f"https://raw.githubusercontent.com/bytecodealliance/wit-bindgen/{vcs['git']['sha1']}/{filename}"
                with urllib.request.urlopen(source_url, timeout=45) as response:
                    content = response.read()
                target = root / "crates" / (name + "-" + version) / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                texts.append({"path": target.relative_to(root).as_posix(), "sha256": sha(content), "bytes": len(content), "source_url": source_url,
                              "basis": "Root legal text at this crate's packaged VCS revision."})
        return {"name": name, "version": version, "source_url": url, "source_sha256": expected,
                "publisher_licenses": component.get("licenses", []), "legal_files": sorted(texts, key=lambda r: r["path"])}

    with ThreadPoolExecutor(max_workers=12) as executor:
        records = list(executor.map(acquire, sbom["components"]))
    manifest = {"format": "aware.component-notice-input.v1", "wheel_sha256": sha(wheel_bytes),
                "sbom_sha256": sha(sbom_bytes), "components": records,
                "qualification": "Conservative coverage of all publisher SBOM crate candidates. This is not an exact binary-linkage map, toolchain identification or reproducible-build proof. Original expressions and complete packaged legal texts retained; alternatives are not relabeled as Aware Apache."}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"components": len(records), "legal_files": sum(len(r["legal_files"]) for r in records)}))


if __name__ == "__main__":
    main()
