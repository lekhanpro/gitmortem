from __future__ import annotations

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from gitmortem.cli import app

runner = CliRunner()


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def test_cli_runs_in_offline_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    _git(repo, "init")
    _git(repo, "config", "user.name", "CLI Tester")
    _git(repo, "config", "user.email", "cli@example.com")

    target = repo / "app.py"
    target.write_text("print('safe')\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "safe commit")

    target.write_text("print('unsafe')\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "break it")

    commit_hash = _git(repo, "rev-parse", "HEAD")

    result = runner.invoke(app, [commit_hash, "--repo", str(repo), "--no-llm"])

    assert result.exit_code == 0
    assert "Commit Report" in result.stdout
    assert "offline" in result.stdout
