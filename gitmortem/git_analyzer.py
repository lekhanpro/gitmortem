from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import git

EMPTY_TREE_HASH = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class GitAnalyzerError(RuntimeError):
    """Raised when git analysis fails."""


@dataclass(frozen=True)
class CommitFact:
    hash: str
    short_hash: str
    author: str
    timestamp: str
    message: str
    files_changed: list[str]
    insertions: int
    deletions: int
    parent_hashes: list[str]
    repo_root: str


def _open_repo(repo_path: str) -> git.Repo:
    try:
        return git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError as exc:
        raise GitAnalyzerError(f"'{repo_path}' is not a git repository.") from exc
    except git.NoSuchPathError as exc:
        raise GitAnalyzerError(f"Repository path '{repo_path}' does not exist.") from exc


def extract_commit(repo_path: str, commit_hash: str) -> CommitFact:
    repo = _open_repo(repo_path)
    try:
        commit = repo.commit(commit_hash)
    except (git.BadName, ValueError) as exc:
        raise GitAnalyzerError(f"Commit '{commit_hash}' could not be resolved.") from exc

    stats_total = commit.stats.total
    repo_root = str(Path(repo.working_tree_dir or repo.common_dir).resolve())

    return CommitFact(
        hash=commit.hexsha,
        short_hash=commit.hexsha[:8],
        author=str(commit.author),
        timestamp=commit.committed_datetime.isoformat(),
        message=commit.message.strip(),
        files_changed=sorted(commit.stats.files.keys()),
        insertions=stats_total.get("insertions", 0),
        deletions=stats_total.get("deletions", 0),
        parent_hashes=[parent.hexsha[:8] for parent in commit.parents],
        repo_root=repo_root,
    )


def get_surrounding_commits(repo_path: str, commit_hash: str, window: int = 10) -> list[CommitFact]:
    repo = _open_repo(repo_path)
    target = extract_commit(repo_path, commit_hash)

    try:
        ordered_hashes = repo.git.rev_list("--all", "--date-order").splitlines()
    except git.GitCommandError as exc:
        raise GitAnalyzerError("Unable to enumerate git history.") from exc

    try:
        idx = ordered_hashes.index(target.hash)
    except ValueError:
        return [target]

    start = max(0, idx - window)
    end = min(len(ordered_hashes), idx + window + 1)
    selected = list(reversed(ordered_hashes[start:end]))
    return [extract_commit(repo_path, commit_id) for commit_id in selected]


def get_raw_diff(repo_path: str, commit_hash: str) -> str:
    repo = _open_repo(repo_path)
    commit = repo.commit(commit_hash)
    base = commit.parents[0].hexsha if commit.parents else EMPTY_TREE_HASH
    try:
        return repo.git.diff(
            base,
            commit.hexsha,
            "--find-renames",
            "--find-copies",
            "--binary",
        )
    except git.GitCommandError as exc:
        raise GitAnalyzerError(f"Failed to build diff for '{commit_hash}'.") from exc
