# GitHub PR/CI — read-only part of #17

[Русский](GITHUB_STATUS.md)

`PublicGitHubStatus` explicitly reads public repository PR/CI metadata using up to
four fixed GitHub REST GETs, without token/config/credential discovery, ambient
proxies, redirects, retries, polling or writes. No HTTP/UI/taskflow wiring or
Issue/branch/commit/draft PR creation. Full #17 stays open pending #15/#16 and
trusted independent review.

Owner configuration supplies an explicit owner/repository, expected check names
and trusted check App ID. The reader queries PR metadata, check runs and combined
legacy statuses for the exact head SHA, then rereads PR metadata. Head/state/
draft/merged/base-ref changes are stale, not successful evidence.

All expected names must come from the trusted App; all reported runs must be
completed success, with no foreign Apps or failed/pending legacy statuses.
Missing jobs, skipped/neutral, stale commits, pagination/incomplete totals,
malformed/duplicate JSON, wrong types, oversized bodies and network/HTTP failures
never produce green. A previous failed rerun returned by filter=all conservatively
blocks green even when a newer rerun succeeded.

Each response is capped at 1 MiB; default socket timeout is 10 seconds (owner
configurable up to 30), not a hard overall deadline. Pagination is reported
incomplete, never followed to arbitrary URLs. PR/diff links derive from trusted
configuration and validated numeric IDs, not response URLs.

**ready_for_merge is always False.** A green CI snapshot does not establish
rulesets/required checks, independent approvals, mergeability, current local code
or owner permission. PR metadata can change after the final GET. Private repos,
Enterprise and authenticated access are outside this reader. Untrusted check
names must be rendered as text by any future UI.

49 offline injected-HTTP tests and explicit public GitHub observations are recorded
in [QA evidence](qa-issue-17-status.json). See the Russian guide for the API example,
limits and official REST links. No new dependency or upstream source copying.
