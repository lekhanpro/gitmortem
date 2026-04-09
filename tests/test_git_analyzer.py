from __future__ import annotations

import subprocess
from pathlib import Path

from gitmortem.git_analyzer import extract_commit, get_raw_diff, get_surrounding_commits


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def test_extract_commit_and_surrounding_history(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")

    first_file = repo / "service.py"
    first_file.write_text("print('ok')\n", encoding="utf-8")
    _git(repo, "add", "service.py")
    _git(repo, "commit", "-m", "initial commit")

    first_commit = _git(repo, "rev-parse", "HEAD")

    first_file.write_text("print('broken')\nprint('boom')\n", encoding="utf-8")
    _git(repo, "add", "service.py")
    _git(repo, "commit", "-m", "break production")

    second_commit = _git(repo, "rev-parse", "HEAD")

    fact = extract_commit(str(repo), second_commit)
    history = get_surrounding_commits(str(repo), second_commit, window=1)
    raw_diff = get_raw_diff(str(repo), second_commit)

    assert fact.short_hash == second_commit[:8]
    assert fact.insertions >= 1
    assert fact.deletions >= 1
    assert fact.files_changed == ["service.py"]
    assert first_commit[:8] in {item.short_hash for item in history}
    assert "print('boom')" in raw_diff
