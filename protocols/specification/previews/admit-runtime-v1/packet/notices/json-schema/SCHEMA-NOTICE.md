# JSON Schema specification resources — scoped notice

This notice identifies the JSON Schema specification-support resources carried in the selected `jsonschema-specifications` 2025.9.1 wheel (SHA-256 `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe`). It does not describe or clear other packages or components.

The package's MIT license is carried verbatim in `COPYING.jsonschema-specifications`, matching its in-wheel `COPYING`. For specification-origin material, this notice attributes the JSON Schema Specification Authors and selects the BSD-3-Clause alternative described by the [pinned upstream README](https://github.com/json-schema-org/json-schema-spec/blob/51326f80900357fe3069beb4f5f575db24c1b9a7/README.md). `LICENSE.json-schema-spec` carries the **complete** pinned upstream license file, including both BSD-3-Clause and AFL-3.0 texts. Carrying that whole file does not elect AFL-3.0.

The following paths are relative to `jsonschema_specifications/schemas/` inside that exact wheel. Hashes identify the carried bytes, not universal upstream equivalence.

| Carried resource | SHA-256 | Origin observation |
| --- | --- | --- |
| `draft201909/metaschema.json` | `7b761b3e121f0a0ca1ea2a0b8e2cc856bcf801604b8268d71bacaa202bc0c13b` | Snapshot byte match |
| `draft201909/vocabularies/applicator` | `6895100e99726fbb107058512bbec3ecfd4b24e8fd2facee3e505ee72b0d4c31` | C-SA adaptation |
| `draft201909/vocabularies/content` | `9b7d4f55a4e2fdb02c430068fdffabc732addce238da3f1df2690249c3353274` | Snapshot byte match |
| `draft201909/vocabularies/core` | `b5a2c4957f6495d0a5081f0409ebe8a14e4139acb203fc748471f8ede2af5b2c` | C-SC adaptation |
| `draft201909/vocabularies/format` | `50ebbfe790611a849b8cc400a09c1d0e0fb6ab5c0d43a0f22201fd3625056bf4` | Snapshot byte match |
| `draft201909/vocabularies/meta-data` | `d47e2445dd6a82271a298d83cc6c6cb8d4ae1e15e0dc56becd37a163ecf01286` | Snapshot byte match |
| `draft201909/vocabularies/validation` | `1e526c1d335a734805fc82cf5798c12b960ad7da2517c66cda5a1b09359c3c1c` | Snapshot byte match |
| `draft202012/metaschema.json` | `41da76f5afb7ce062d248f762463a92f7ca47e4e0f905b224ba6afeef91ded0f` | Snapshot byte match |
| `draft202012/vocabularies/applicator` | `c4a6e4147b91fef7fea6dc058cb1bf93402f7414b76578a8b16aaf1dad6aacef` | Snapshot byte match |
| `draft202012/vocabularies/content` | `08343747764e4a5814262793cf4d652057a7913863c5950d43297e8e1fdac5b6` | Snapshot byte match |
| `draft202012/vocabularies/core` | `c2d12a8e4dd11d336dfc83a3f663aa4c69f0b49b3beb094ffeb25b5316f4803d` | Snapshot byte match |
| `draft202012/vocabularies/format-annotation` | `abc775adfefd89d22358170d9bf93f4ebd2349563bbbedd60f02bef7c812bcc0` | Snapshot byte match |
| `draft202012/vocabularies/format-assertion` | `c52242b9a1bb786b26c3e82c7add428c31f9c96e575dce99e56ea5feaa6da20c` | Snapshot byte match |
| `draft202012/vocabularies/meta-data` | `8f76d6e14f41b9b92ef933b708cdc5144c8b5268651ad11918485fb1754f1c76` | Snapshot byte match |
| `draft202012/vocabularies/unevaluated` | `2dbfbcb73994b670b0976492adee1fffb46c21682784d2f5a4ca561f9e2d0cb4` | Snapshot byte match |
| `draft202012/vocabularies/validation` | `7010a31e541f32d2be721e2de348df75c9b36876a3ed304877fc0abda1d37a58` | Snapshot byte match |
| `draft3/metaschema.json` | `2cf75f64436fb5be374a2eaa27ab8b7e1fd651c9b46daea6c67b02fd64e2458b` | C-S3 adaptation |
| `draft4/metaschema.json` | `e1489d0b4755f02793302591d3fcb8f07b6893a82a94f24895f8e4edf11b82e2` | Observed publication byte match; original snapshot not matched |
| `draft6/metaschema.json` | `c29dfce9f54835c3a06c03b3c5d5ec0eda77706568f9c4df7cfbc7566a51006d` | C-S6 adaptation |
| `draft7/metaschema.json` | `3d5392088261606c559b603f385329c9f1ab45b5d667eb990687453b055d405e` | C-S7 adaptation |

Five carried resources differ from the observed specification publications: `draft3/metaschema.json` removes URI-format checks on `$ref` and `id`; `draft6/metaschema.json` removes `enum` minimum-length and uniqueness constraints; `draft7/metaschema.json` removes those `enum` constraints and the `writeOnly` declaration; `draft201909/vocabularies/applicator` and `draft201909/vocabularies/core` each add a `$vocabulary` declaration. These differences predate this Aware bundle; their identification is not a claim that Aware authored them. `draft4/metaschema.json` is an observed publication byte match, not proof of a matched original snapshot.

The notice and attached legal files are scoped to this wheel and these resources. Benchmark fixtures, the rpds compiled extension, other third-party packages, and whole-bundle disclosure require separate coverage. This notice alone does not authorize delivery or release.
