#!/usr/bin/env node

const { spawnSync } = require("node:child_process");

const SOURCE =
  process.env.GITMORTEM_PIP_SOURCE ||
  "git+https://github.com/lekhanpro/gitmortem.git";

const PYTHON_CANDIDATES = [
  { command: "py", args: ["-3"] },
  { command: "python3", args: [] },
  { command: "python", args: [] }
];

function findPython() {
  for (const candidate of PYTHON_CANDIDATES) {
    const result = spawnSync(
      candidate.command,
      [...candidate.args, "--version"],
      { stdio: "ignore" }
    );
    if (result.status === 0) {
      return candidate;
    }
  }
  return null;
}

function runPython(python, extraArgs, options = {}) {
  return spawnSync(
    python.command,
    [...python.args, ...extraArgs],
    {
      stdio: "inherit",
      ...options
    }
  );
}

function ensureInstalled(python) {
  const check = spawnSync(
    python.command,
    [...python.args, "-m", "gitmortem", "--version"],
    { stdio: "ignore" }
  );
  if (check.status === 0) {
    return;
  }

  const install = runPython(python, [
    "-m",
    "pip",
    "install",
    "--user",
    "--upgrade",
    SOURCE
  ]);
  if (install.status !== 0) {
    process.exit(install.status ?? 1);
  }
}

function main() {
  const python = findPython();
  if (!python) {
    console.error("gitmortem requires Python 3.10+.");
    process.exit(1);
  }

  ensureInstalled(python);
  const result = runPython(python, ["-m", "gitmortem", ...process.argv.slice(2)]);
  process.exit(result.status ?? 1);
}

main();

