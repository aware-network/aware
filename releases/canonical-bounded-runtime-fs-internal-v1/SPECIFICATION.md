# Original specification DATA example

The carried examples/prepare_draft_input.py is the unchanged original authored
public-type example referenced by aware-specification-cli 0.4.4. ENTRANCE.json
records its original authored path, source revision and byte pin; SHA256SUMS
covers the hardlinked example and this guide. These bindings are provenance,
not authority or a new software selector. The complete source is also retained
inside the product source archive.

Its illustrative meaning is a non-mutating JSON checker. The customer must
approve that exact meaning before using its output. Carriage does not approve
customer intent; do not treat the example as a generic specification author.

After installation/configuration, run the original example separately with the
supplied installed Python and capture its canonical DATA bytes unchanged:

```sh
set -eu
entrance=/absolute/path/to/cold-entrance
target=/absolute/path/to/private-install-root
draft_data=/absolute/path/to/new-specification-draft.data
"$target/env/bin/python" -I -B "$entrance/examples/prepare_draft_input.py" >"$draft_data"
```

This uses no host Python. The original typed factories and original wire codec
produce canonical bytes on stdout. Preserve those exact bytes: do not JSON
reencode, pretty-print, add a newline, or substitute shell text. Do not use
partial output after a failed preparation. No CLI command runs this Python
on behalf of a draft request, and no new writer, wire codec or command is added.

The result is DATA only, not Issue admission, native authority or permission to
apply anything. Use install-aware run INSTALL_ROOT --help and the installed
original SDK's help for subsequent commands. Follow its original reviews,
admission, preview and apply workflow with the approved DATA; original guards
and errors remain in effect. Retain unknown results rather than retrying or
rewriting them. This is private qualification, not public/legal clearance.
