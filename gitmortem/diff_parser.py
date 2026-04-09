from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileDiff:
    filename: str
    extension: str
    additions: list[str]
    deletions: list[str]
    hunks: int
    is_new_file: bool
    is_deleted_file: bool
    is_renamed: bool
    previous_filename: str | None = None
    is_binary: bool = False


def parse_diff(raw_diff: str) -> list[FileDiff]:
    file_diffs: list[FileDiff] = []
    current: dict[str, object] | None = None

    for line in raw_diff.splitlines():
        if line.startswith("diff --git "):
            if current is not None:
                file_diffs.append(_build_file_diff(current))
            current = _new_file_state(line)
            continue

        if current is None:
            continue

        if line.startswith("new file mode"):
            current["is_new_file"] = True
        elif line.startswith("deleted file mode"):
            current["is_deleted_file"] = True
        elif line.startswith("rename from "):
            current["is_renamed"] = True
            current["previous_filename"] = line.removeprefix("rename from ").strip()
        elif line.startswith("rename to "):
            current["is_renamed"] = True
            current["filename"] = line.removeprefix("rename to ").strip()
        elif line.startswith("Binary files "):
            current["is_binary"] = True
        elif line.startswith("@@"):
            current["hunks"] = int(current["hunks"]) + 1
        elif line.startswith("+") and not line.startswith("+++"):
            _append_line(current["additions"], line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            _append_line(current["deletions"], line[1:])

    if current is not None:
        file_diffs.append(_build_file_diff(current))

    return file_diffs


def summarize_diff_for_llm(file_diffs: list[FileDiff]) -> str:
    if not file_diffs:
        return "No textual diff content found."

    lines: list[str] = []
    for file_diff in file_diffs:
        status = _status_label(file_diff)
        lines.append(f"FILE: {file_diff.filename} ({file_diff.extension or 'no extension'})")
        lines.append(
            f"  status={status}, hunks={file_diff.hunks}, "
            f"+{len(file_diff.additions)} lines, -{len(file_diff.deletions)} lines"
        )
        if file_diff.previous_filename:
            lines.append(f"  PREVIOUS: {file_diff.previous_filename}")
        if file_diff.is_binary:
            lines.append("  NOTE: binary content changed")
        if file_diff.additions:
            lines.append(f"  ADDED: {'; '.join(file_diff.additions[:5])}")
        if file_diff.deletions:
            lines.append(f"  REMOVED: {'; '.join(file_diff.deletions[:5])}")
        lines.append("")
    return "\n".join(lines).strip()


def _new_file_state(line: str) -> dict[str, object]:
    match = re.match(r"diff --git a/(.+?) b/(.+)$", line)
    left = match.group(1) if match else "unknown"
    right = match.group(2) if match else left
    return {
        "filename": right,
        "fallback_filename": left,
        "additions": [],
        "deletions": [],
        "hunks": 0,
        "is_new_file": False,
        "is_deleted_file": False,
        "is_renamed": False,
        "previous_filename": None,
        "is_binary": False,
    }


def _append_line(bucket: object, raw_line: str) -> None:
    if not isinstance(bucket, list):
        return

    cleaned = raw_line.rstrip()
    cleaned = cleaned if cleaned else "<blank line>"
    if len(bucket) < 50:
        bucket.append(cleaned)


def _build_file_diff(state: dict[str, object]) -> FileDiff:
    filename = str(state["filename"])
    if bool(state["is_deleted_file"]):
        filename = str(state.get("previous_filename") or state.get("fallback_filename") or filename)

    extension = Path(filename).suffix.lstrip(".")

    return FileDiff(
        filename=filename,
        extension=extension,
        additions=list(state["additions"]),
        deletions=list(state["deletions"]),
        hunks=int(state["hunks"]),
        is_new_file=bool(state["is_new_file"]),
        is_deleted_file=bool(state["is_deleted_file"]),
        is_renamed=bool(state["is_renamed"]),
        previous_filename=str(state["previous_filename"]) if state["previous_filename"] else None,
        is_binary=bool(state["is_binary"]),
    )


def _status_label(file_diff: FileDiff) -> str:
    if file_diff.is_renamed:
        return "renamed"
    if file_diff.is_new_file:
        return "new"
    if file_diff.is_deleted_file:
        return "deleted"
    return "modified"
