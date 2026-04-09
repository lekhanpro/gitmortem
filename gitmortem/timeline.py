from __future__ import annotations

from datetime import datetime

from gitmortem.git_analyzer import CommitFact


def build_history_context(surrounding_commits: list[CommitFact]) -> str:
    if not surrounding_commits:
        return "No surrounding commits found."
    return "\n".join(
        f"[{commit.short_hash}] {commit.timestamp[:19]} | {commit.author} | "
        f"{commit.message.splitlines()[0][:100]}"
        for commit in surrounding_commits
    )


def fallback_timeline(commit_fact: CommitFact, surrounding_commits: list[CommitFact]) -> dict:
    target_time = _parse_time(commit_fact.timestamp)
    entries = []

    for item in surrounding_commits:
        time_label = _relative_label(
            _parse_time(item.timestamp), target_time, item.hash == commit_fact.hash
        )
        entries.append(
            {
                "time": time_label,
                "event": _describe_commit(item),
                "hash": item.short_hash,
            }
        )

    return {
        "timeline": entries
        or [
            {
                "time": "T+0 (broken commit)",
                "event": _describe_commit(commit_fact),
                "hash": commit_fact.short_hash,
            }
        ],
        "time_to_detect": "unknown from git history alone",
        "deploy_pattern": _classify_deploy_pattern(commit_fact.message),
    }


def _describe_commit(commit_fact: CommitFact) -> str:
    summary = commit_fact.message.splitlines()[0]
    file_count = len(commit_fact.files_changed)
    return f"{commit_fact.author} committed '{summary}' touching {file_count} file(s)."


def _relative_label(commit_time: datetime, target_time: datetime, is_target: bool) -> str:
    if is_target:
        return "T+0 (broken commit)"

    delta = commit_time - target_time
    seconds = int(delta.total_seconds())
    sign = "+" if seconds >= 0 else "-"
    seconds = abs(seconds)

    days, remainder = divmod(seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, _ = divmod(remainder, 60)

    if days:
        return f"{sign}{days}d {hours}h"
    if hours:
        return f"{sign}{hours}h {minutes}m"
    return f"{sign}{max(minutes, 1)}m"


def _classify_deploy_pattern(message: str) -> str:
    lowered = message.lower()
    if "refactor" in lowered:
        return "refactor-driven change"
    if "bump" in lowered or "upgrade" in lowered or "dependency" in lowered:
        return "dependency update"
    if "merge" in lowered:
        return "merge-based deploy"
    if "hotfix" in lowered or "fix" in lowered:
        return "fix-forward deploy"
    return "single commit code change"


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
