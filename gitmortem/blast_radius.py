from __future__ import annotations

import os
import re
from pathlib import Path

IMPORT_PATTERNS = {
    "py": [
        re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE),
        re.compile(r"^\s*from\s+([\w.]+)\s+import", re.MULTILINE),
    ],
    "js": [
        re.compile(r"""from\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "jsx": [
        re.compile(r"""from\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "ts": [
        re.compile(r"""from\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "tsx": [
        re.compile(r"""from\s+['"]([^'"]+)['"]"""),
        re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)"""),
    ],
    "java": [
        re.compile(r"^\s*import\s+([\w.]+);", re.MULTILINE),
    ],
    "go": [
        re.compile(r'"([\w./-]+)"'),
    ],
}


def find_dependents(repo_path: str, changed_files: list[str]) -> dict[str, list[str]]:
    repo_root = Path(repo_path).resolve()
    source_files = _all_source_files(repo_root)
    dependents: dict[str, list[str]] = {changed: [] for changed in changed_files}

    for source_file in source_files:
        ext = source_file.suffix.lstrip(".")
        if ext not in IMPORT_PATTERNS:
            continue

        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        imports = _extract_imports(content, ext)
        if not imports:
            continue

        relative_source = source_file.relative_to(repo_root).as_posix()

        for changed in changed_files:
            if relative_source == changed.replace("\\", "/"):
                continue

            changed_path = (repo_root / changed).resolve()
            aliases = _candidate_aliases(repo_root, source_file, changed_path)
            if any(_matches_import(import_target, aliases) for import_target in imports):
                dependents[changed].append(relative_source)

    return {key: sorted(set(value)) for key, value in dependents.items()}


def blast_radius_summary(dependents: dict[str, list[str]]) -> str:
    total = sum(len(items) for items in dependents.values())
    if total == 0:
        return "No cross-file dependencies detected."

    lines = [f"Total files potentially affected: {total}"]
    for changed_file, imported_by in dependents.items():
        if not imported_by:
            continue
        preview = ", ".join(imported_by[:5])
        suffix = "..." if len(imported_by) > 5 else ""
        lines.append(
            f"- {changed_file} -> imported by {len(imported_by)} file(s): {preview}{suffix}"
        )
    return "\n".join(lines)


def _all_source_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for extension in IMPORT_PATTERNS:
        files.extend(repo_root.rglob(f"*.{extension}"))
    return files


def _extract_imports(content: str, extension: str) -> set[str]:
    imports: set[str] = set()
    for pattern in IMPORT_PATTERNS.get(extension, []):
        imports.update(match.group(1).strip() for match in pattern.finditer(content))
    return {_normalize_import(value) for value in imports if value}


def _candidate_aliases(repo_root: Path, source_file: Path, changed_file: Path) -> set[str]:
    aliases: set[str] = set()
    source_ext = source_file.suffix.lstrip(".")
    relative_without_ext = changed_file.relative_to(repo_root).with_suffix("")
    posix_target = relative_without_ext.as_posix()

    aliases.add(_normalize_import(changed_file.stem))
    aliases.add(_normalize_import(posix_target))

    if source_ext == "py":
        dotted = ".".join(relative_without_ext.parts)
        if changed_file.name == "__init__.py":
            dotted = ".".join(changed_file.relative_to(repo_root).parent.parts)
        aliases.add(_normalize_import(dotted))

    if source_ext in {"js", "jsx", "ts", "tsx"}:
        rel = os.path.relpath(relative_without_ext, source_file.parent.relative_to(repo_root))
        rel = Path(rel).as_posix()
        if not rel.startswith("."):
            rel = f"./{rel}"
        aliases.add(_normalize_import(rel))
        if rel.endswith("/index"):
            aliases.add(_normalize_import(rel[: -len("/index")]))

    if source_ext == "java":
        aliases.add(_normalize_import(".".join(relative_without_ext.parts)))

    if source_ext == "go":
        aliases.add(_normalize_import(posix_target))

    return {alias for alias in aliases if alias}


def _normalize_import(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    normalized = normalized.removesuffix(".py")
    normalized = normalized.removesuffix(".js")
    normalized = normalized.removesuffix(".jsx")
    normalized = normalized.removesuffix(".ts")
    normalized = normalized.removesuffix(".tsx")
    normalized = normalized.removesuffix("/index")
    if normalized.startswith("./"):
        return normalized
    return normalized.strip("/")


def _matches_import(import_target: str, aliases: set[str]) -> bool:
    normalized_target = _normalize_import(import_target)
    if normalized_target in aliases:
        return True
    return any(
        normalized_target.endswith(f".{alias}") or normalized_target.endswith(f"/{alias}")
        for alias in aliases
        if alias and not alias.startswith(".")
    )
