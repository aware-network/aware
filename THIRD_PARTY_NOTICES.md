# Third-party notices

Aware-authored source is licensed under Apache-2.0 unless a file or directory
states otherwise. The following vendored or derived components retain their
upstream licenses. Their inclusion does not relicense them under Apache-2.0.

| Component | Repository path | Upstream | License |
| --- | --- | --- | --- |
| xterm.dart | `apps/interface_flutter/aware_terminal_xterm` | <https://github.com/TerminalStudio/xterm.dart> | MIT; copyright 2020 xuty |
| flutter-layer-shell | `apps/os_linux/aware_desktop_shell/flutter_layer_shell` | <https://github.com/khalid151/flutter-layer-shell> | GPL-3.0-only |
| tree-sitter-dart | `workspaces/aware_kernel/languages/dart/grammar/tree_sitter` | Upstream attribution is retained in the vendored license and sources | MIT; copyright 2020-2023 UserNobody14 and others |
| tree-sitter-dart nested source | `workspaces/aware_kernel/languages/dart/grammar/tree_sitter/tree_sitter_dart/tree_sitter` | Upstream attribution is retained in the vendored license and sources | MIT; copyright 2023 Tim Whiting |
| tree-sitter-python | `workspaces/aware_kernel/languages/python/grammar/tree_sitter` | <https://github.com/tree-sitter/tree-sitter-python> | MIT; copyright 2016 Max Brunsfeld |
| tree-sitter-sql | `workspaces/aware_kernel/languages/sql/grammar/tree_sitter` | <https://github.com/DerekStride/tree-sitter-sql> | MIT; copyright 2021 Derek Stride |

The complete license text for each component is retained in its repository
directory. Dependency lockfiles may identify additional dependencies whose
licenses apply when those dependencies are installed; they are not vendored
source merely because they appear in a lockfile.

## Release boundary

The GPL-3.0-only `flutter-layer-shell` component is not eligible for inclusion
in an Apache-only RepositoryRevision or public checkout profile. It must remain
excluded until the owning release explicitly chooses GPL distribution or the
component is replaced. Repository materialization must preserve every selected
component's license and notices.

Tracked binaries, archives, fonts, and generated WebAssembly require a recorded
source, version, license, and reproducible build or acquisition receipt before
they may enter a public release profile. Presence in the development monorepo
is not provenance approval.
