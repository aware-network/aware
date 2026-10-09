# New canonical dependency notice inputs

Internal review input, not a customer envelope or public clearance. Bound to the
unchanged archive recorded in manifest.json. Keep source archives, original legal
texts, this explanation and the manifest/checksums together.

msgpack 1.2.3: preserve its original COPYING plus complete Apache-2.0 terms.
Six source headers retain their full copyright/Apache notices as component inputs.
The pinned source's generated-C header declares Cython 3.3.0. The attached Cython
COPYING contains an output-license exception; its Apache LICENSE is also retained.
This does not attest the wheel publisher's actual compiler or exact component map.

pathspec 1.1.1: retain its complete MPL-2.0 LICENSE and original corresponding
source archive. The original publisher source URL and hash are in manifest.json.
No Aware modification or replacement license is asserted. The source is supplied
alongside this input, not hidden behind an internal repository coordinate.

PyYAML 6.0.3: retain its original MIT LICENSE and source. Its pinned CI defaults to
LibYAML 0.2.5 and builds a static library; retain that version's complete MIT text.
The default is configurable. These are conservative source/build inputs, not an
attestation that this exact wheel used that ref or generator. Cython's pinned
3.3.0 exception is correlated to msgpack's source only, not silently assigned as
PyYAML's toolchain identity. PyYAML's exact build-generator version is unproved.

The two new extensions' original byte hashes remain in manifest.json. Native
inspection and a CI recipe do not prove static linkage or reproducible builds.
Inherited rpds/pydantic-core/schema notice inputs and the other in-wheel legal
files are NOT attached by this small cut; the later whole envelope must include
and bind them. FileSystem README/metadata findings remain unresolved in the
unchanged payload. This cut changes no wheel, runtime, authority or selection.
