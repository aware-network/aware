# Generated-output policy

This policy separates user authorship from Aware's reusable implementation.

## User sources and original output

Users keep whatever rights they hold in `.aware` sources, configuration,
content, data, and other original inputs they provide. Users also keep whatever
rights they acquire in output that is original to those inputs. Aware does not
claim ownership merely because Aware tooling parsed, compiled, materialized, or
rendered it.

This statement does not grant rights in third-party material supplied by a
user, and it is not a promise that every generated result is copyrightable.

## Aware-authored fragments

Aware runtime code, SDK support code, templates, schemas, and other reusable
Aware-authored fragments embedded in generated output remain Apache-2.0. Their
presence does not change the license of separable user-authored material.

Upstream-owned fragments retain their upstream licenses and notices.

## Materialization receipts

A materialization receipt intended for distribution should identify the source
revision, generator revision, generated artifact hashes, SPDX expressions, and
required notices. A generated artifact without that evidence is not eligible
for a public RepositoryRevision release profile.
