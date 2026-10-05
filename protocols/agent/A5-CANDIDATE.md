# a5 Issue-usability candidate preparation

Status: source preparation in progress, not consumer acceptance or publication.
The selected public `release.json` and a4 archive remain unchanged.

Input: independently accepted Issue owner source
`c112eeb065f414f810e3d4d221e20bcb9df38487`, with content/closeout acceptance
at `5d005d4a1dd702226cadc32548a796fa5521132c`. Owner-source closeout is
`c8c193f7f16e39fb66cc7970183b3a0447ffdab8` in the producer repository.
The consumer includes the neutral owner bytes; it does not depend on access to
that repository or the private evaluation archive.

The `prepare_issue_a5.py` generator adopts exactly five committed source files
and four pinned test files. Runtime content, lifecycle and publication decisions
stay with existing owners. The CLI summary is reused directly, not duplicated.
The thin open composition requires explicit initial problem/objective/acceptance
and retains partial receipts on a later request-construction failure.

Proposed versions: `aware-agent-cli 0.1.0a5`, `aware-issue-sdk 0.7.0a3`,
`aware-issue-fs-adapter 0.6.0a3`, `aware-issue-cli 0.6.0a3` and customer contract
`aware.agent.fs.v1 1.2.0`. No dependencies or authority profiles are added.
SDK omitted-content compatibility and full JSON remain supported. The existing
repository owner and other payload dependencies are not redesigned.

Build only from a committed public source revision in disposable scratch with
the existing builder. Keep its candidate release record separate from live
selection. Retain archive/manifest/source/notice hashes and prove fresh offline
installation, absent checkout imports/editables, exact owner bytes, dependency
reachability, real Issue/repository refusals, closeout, partial receipts and
foreign-work preservation. Independent candidate review precedes any promotion.

See [the candidate workflow](quickstart-a5-candidate.md). External evaluation,
consumer promotion and public Git publication remain separate. No push.
