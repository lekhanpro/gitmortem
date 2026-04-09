from pathlib import Path

from gitmortem.blast_radius import blast_radius_summary, find_dependents


def test_find_dependents_for_python_and_typescript(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    package_dir = repo / "pkg"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "service.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    (repo / "worker.py").write_text("from pkg.service import run\n", encoding="utf-8")

    web_dir = repo / "web"
    web_dir.mkdir()
    (web_dir / "api.ts").write_text("export const api = 1;\n", encoding="utf-8")
    (web_dir / "page.ts").write_text("import { api } from './api'\n", encoding="utf-8")

    dependents = find_dependents(str(repo), ["pkg/service.py", "web/api.ts"])
    summary = blast_radius_summary(dependents)

    assert dependents["pkg/service.py"] == ["worker.py"]
    assert dependents["web/api.ts"] == ["web/page.ts"]
    assert "Total files potentially affected: 2" in summary
