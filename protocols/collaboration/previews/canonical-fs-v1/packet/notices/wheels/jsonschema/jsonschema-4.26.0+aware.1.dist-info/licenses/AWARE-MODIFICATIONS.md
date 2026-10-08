# Aware packaging modification

This wheel is derived from the jsonschema 4.26.0 source archive, SHA-256
0c26707e2efad8aa1bfc5b7ce170f3fccc2e4918ff85989ba9ffa9facb2be326. Aware changed the wheel build configuration to omit the
`jsonschema/benchmarks/` subtree and assigned the distinct local version
`4.26.0+aware.1`. The upstream runtime Python modules are unchanged.
The original jsonschema MIT COPYING remains included. This document describes
the packaging delta; it does not assert rights over separately sourced content.
