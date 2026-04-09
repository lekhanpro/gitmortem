<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="gitmortem hero banner" width="100%" />
</p>

# gitmortem

> Turn a suspicious commit into a production-style postmortem.

[![CI](https://github.com/lekhanpro/gitmortem/actions/workflows/ci.yml/badge.svg)](https://github.com/lekhanpro/gitmortem/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/lekhanpro/gitmortem)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-github%20pages-ff9c54)](https://lekhanpro.github.io/gitmortem/)
[![Python](https://img.shields.io/badge/python-3.10%2B-7ed8c1)](pyproject.toml)
[![Provider](https://img.shields.io/badge/default-groq-ffd5b4)](https://github.com/lekhanpro/gitmortem#provider-support)

`gitmortem` takes a commit hash and generates the kind of report teams actually need after a bad deploy:

- root cause
- blast radius
- timeline
- severity
- immediate actions
- never-again checklist

It is built for the moment after "which commit broke production?" when the real questions become "what changed, who is affected, and what do we fix first?"

## Quick Links

- Landing page: https://lekhanpro.github.io/gitmortem/
- Sample report: [examples/sample-postmortem.md](examples/sample-postmortem.md)
- Install from GitHub: `python -m pip install git+https://github.com/lekhanpro/gitmortem.git`
- Offline mode: `gitmortem HEAD~1 --no-llm`

## Why This Is Useful

Most commit summarizers stop at "what changed."

`gitmortem` is opinionated about the output shape. It tries to produce something much closer to an incident review than a raw code summary:

- a root-cause narrative instead of a generic diff recap
- a blast-radius estimate instead of just changed files
- a timeline built from nearby history
- action items that push toward prevention, not just explanation

## Real Use Cases

- A production deploy went bad and you need a clean first-pass incident summary before writing the real postmortem.
- A rollback fixed the symptom, but the team still needs a root-cause narrative and a prevention checklist.
- A platform or DevOps engineer wants blast-radius context without manually chasing imports and commit history.
- A maintainer wants a structured explanation of a risky commit before sharing it in Slack, an incident doc, or a review meeting.

## What It Looks Like

<p align="center">
  <img src="docs/assets/demo-terminal.svg" alt="gitmortem terminal output preview" width="100%" />
</p>

<p align="center">
  <img src="docs/assets/report-preview.svg" alt="gitmortem report preview" width="100%" />
</p>

Sample report:

- [examples/sample-postmortem.md](examples/sample-postmortem.md)

Live landing page:

- https://lekhanpro.github.io/gitmortem/

## 30-Second Demo

```bash
export GROQ_API_KEY=your_key
gitmortem HEAD~1
```

Offline:

```bash
gitmortem HEAD~1 --no-llm -o reports/incident.md --html
```

Different provider:

```bash
export OPENAI_API_KEY=your_key
gitmortem HEAD~1 --provider openai
```

## Install

### Recommended: Python

Works today directly from GitHub:

```bash
python -m pip install git+https://github.com/lekhanpro/gitmortem.git
```

After the first tagged PyPI release:

```bash
pip install gitmortem
```

### curl | bash

```bash
curl -fsSL https://raw.githubusercontent.com/lekhanpro/gitmortem/main/install.sh | bash
```

### PowerShell

```powershell
irm https://raw.githubusercontent.com/lekhanpro/gitmortem/main/install.ps1 | iex
```

### npm Wrapper

```bash
npm install -g github:lekhanpro/gitmortem
```

The npm package is a wrapper for discovery and convenience. The actual runtime is still the Python CLI.

## Who It Is For

- maintainers debugging a suspicious release
- teams writing incident reviews after a bad deploy
- platform and DevOps engineers triaging blast radius
- developers who want a cleaner first-pass explanation before writing the real postmortem

## Output Shape

Each report aims to include:

- incident summary
- root cause
- trigger
- contributing factors
- blast radius
- affected systems
- timeline reconstruction
- immediate actions
- prevention checklist
- detection improvements

## Provider Support

Groq is the default provider. The provider layer is not locked in.

Why Groq by default:

- fast enough for a CLI that should feel immediate
- inexpensive enough to keep the tool practical
- easy to override when a team already standardizes on OpenAI, Anthropic, OpenRouter, Ollama, or a compatible endpoint

| Provider | Env var | Notes |
|---|---|---|
| `groq` | `GROQ_API_KEY` | Default provider |
| `openai` | `OPENAI_API_KEY` | Native OpenAI API |
| `anthropic` | `ANTHROPIC_API_KEY` | Native Anthropic API |
| `openrouter` | `OPENROUTER_API_KEY` | OpenAI-compatible endpoint |
| `ollama` | none required | Local model path via `http://localhost:11434/v1` |
| `compatible` | provider-specific | Custom OpenAI-compatible base URL |

Examples:

```bash
gitmortem HEAD~1 --provider groq --model llama-3.3-70b-versatile
gitmortem HEAD~1 --provider anthropic --model claude-3-7-sonnet-latest
gitmortem HEAD~1 --provider compatible --base-url https://my-endpoint.example/v1 --api-key sk-...
```

## CLI

```bash
gitmortem COMMIT_HASH [OPTIONS]
```

Important options:

- `--repo`, `-r`: repository path
- `--output`, `-o`: write Markdown report to a file
- `--html`: also emit a standalone HTML report
- `--html-output`: write HTML to a specific path
- `--provider`: `groq`, `openai`, `anthropic`, `openrouter`, `ollama`, `compatible`
- `--model`: override the default model for the chosen provider
- `--api-key`: inline API key override
- `--base-url`: custom base URL for compatible endpoints
- `--window`: surrounding commit window used for timeline reconstruction
- `--no-llm`: skip AI analysis and render a deterministic report

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `GITMORTEM_PROVIDER` | Default provider override |
| `GITMORTEM_MODEL` | Model override |
| `GITMORTEM_BASE_URL` | Base URL for `compatible` or custom routing |
| `GITMORTEM_OUTPUT_DIR` | Default directory for generated reports |

## How It Works

1. Git metadata and diff facts are extracted directly from the repository.
2. The diff is parsed into structured facts that are easier to reason about.
3. A lightweight blast-radius pass looks for likely dependents.
4. Nearby commits are used to reconstruct incident chronology.
5. The configured provider turns those facts into a readable postmortem.

## Why It Can Grow

- Works offline with `--no-llm`
- Provider-flexible by design
- Markdown and HTML outputs are easy to share
- Includes install scripts, Pages docs, CI, and release automation

## FAQ

**Does this send my whole repository to a model?**

No. The tool is built around extracted commit facts, parsed diff summaries, and nearby history rather than shipping an entire repo snapshot by default.

**Can I use it without any API key?**

Yes. `--no-llm` produces a deterministic offline report based on git facts, diff structure, and blast-radius heuristics.

**Am I locked into Groq?**

No. Groq is just the default. OpenAI, Anthropic, OpenRouter, Ollama, and compatible endpoints are supported from the CLI.

## Project Surface

- Docs site: [`docs/`](docs/)
- Sample report: [examples/sample-postmortem.md](examples/sample-postmortem.md)
- Bash installer: [install.sh](install.sh)
- PowerShell installer: [install.ps1](install.ps1)
- npm wrapper: [package.json](package.json)
- CI workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- Pages workflow: [.github/workflows/pages.yml](.github/workflows/pages.yml)
- Release workflow: [.github/workflows/release.yml](.github/workflows/release.yml)
- PyPI publish workflow: [.github/workflows/publish.yml](.github/workflows/publish.yml)

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
python -m gitmortem HEAD~1 --no-llm
```

## Release Notes

For `pip install gitmortem` to work from PyPI, configure PyPI publishing and create a version tag such as:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## License

MIT
