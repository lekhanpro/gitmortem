#!/usr/bin/env bash
set -euo pipefail

SOURCE="${GITMORTEM_PIP_SOURCE:-git+https://github.com/lekhanpro/gitmortem.git}"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi
  return 1
}

main() {
  if ! PYTHON_BIN="$(find_python)"; then
    echo "gitmortem install failed: Python 3.10+ is required." >&2
    exit 1
  fi

  if command -v pipx >/dev/null 2>&1; then
    pipx install --force "$SOURCE"
    echo "gitmortem installed with pipx."
  else
    "$PYTHON_BIN" -m pip install --user --upgrade "$SOURCE"
    echo "gitmortem installed with pip to the user site."
  fi

  cat <<'EOF'

Next steps:
  gitmortem HEAD~1
  gitmortem HEAD~1 --no-llm

If your shell cannot find `gitmortem`, add your Python user bin directory to PATH
or run:
  python -m gitmortem HEAD~1
EOF
}

main "$@"

