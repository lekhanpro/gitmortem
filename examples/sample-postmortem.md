# Postmortem: 9af31c2d - SEV2

> **A refactor removed the null-guard around provider config resolution, causing every Groq-backed invocation to fail during startup when no explicit model override was present.**

## Incident Summary

| Field | Value |
|---|---|
| Commit | `9af31c2d` |
| Author | release-bot |
| Timestamp | 2026-04-09T12:40:00Z |
| Severity | SEV2 |
| Estimated Impact | CLI failed before report generation for all default-provider users |
| Confidence | high |
| Time to Detect | 12 minutes |
| Deploy Pattern | refactor-driven change |

## Root Cause

**A config refactor changed default model lookup from provider-aware fallback logic to a direct env lookup, which returned `None` for the Groq path and broke startup validation.**

**Trigger:** Package release with the default provider set to Groq and no explicit `--model`.

**Contributing Factors**
- No regression test covered the default-provider startup path.
- The release path validated API keys but not derived model defaults.
- The README promoted the default Groq flow, so the broken path was the most common one.

## Blast Radius

**Files Changed:** `gitmortem/config.py`, `gitmortem/cli.py`, `README.md`

**Affected Systems:** CLI startup, provider resolution, installation smoke tests

Total files potentially affected: 4
- gitmortem/config.py -> imported by 3 file(s): gitmortem/cli.py, gitmortem/llm.py, tests/test_cli.py

## Timeline

| Time | Event | Hash |
|---|---|---|
| -3h 24m | Release prep updated provider defaults and docs. | `1f2ab993` |
| -14m | Packaging metadata and release workflow were merged. | `72bf88c1` |
| T+0 (broken commit) | Provider config refactor shipped without startup coverage. | `9af31c2d` |
| +12m | First user report showed startup failure on the default path. | `incident` |

## Immediate Actions

- **[P0]** Restore provider-aware fallback logic in config resolution. *(owner: maintainer)*
- **[P1]** Add a CLI startup smoke test for every supported provider. *(owner: test engineering)*

## Prevention Checklist

- `TEST` Add startup tests that assert the default provider works with env-only configuration.
- `TOOLING` Add release smoke checks that run `gitmortem --version` and `gitmortem HEAD~1 --no-llm`.
- `DOCUMENTATION` Keep install instructions aligned with the actual default provider and release path.

## Detection Improvements

- Run a post-release GitHub Action that executes the README quick-start commands.
- Fail release builds if provider defaults resolve to an empty model string.
