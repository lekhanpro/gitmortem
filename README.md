# gitmortem

> `gitmortem abc1234` turns a suspicious commit into a production-style incident report.

`gitmortem` generates a postmortem from a commit hash: root cause, blast radius, timeline, severity, and the "never again" checklist. It works offline in `--no-llm` mode, and when you want AI analysis it defaults to Groq while still supporting OpenAI, Anthropic, OpenRouter, Ollama, and custom OpenAI-compatible endpoints.

## Features

- Groq-first by default with multi-provider LLM support
- Offline `--no-llm` mode for pure git and static analysis
- Structured diff parsing with rename/new/delete detection
- Lightweight blast radius analysis across Python, JavaScript, TypeScript, Java, and Go
- Timeline reconstruction from nearby git history
- Markdown report output with optional standalone HTML export

## Install

```bash
pip install gitmortem
```

For local development:

```bash
git clone https://github.com/lekhanpro/gitmortem
cd gitmortem
pip install -e ".[dev]"
```

## Quick Start

Analyze the previous commit with Groq as the default provider:

```bash
export GROQ_API_KEY=your_key
gitmortem HEAD~1
```

Use a different provider:

```bash
export OPENAI_API_KEY=your_key
gitmortem HEAD~1 --provider openai
```

Run fully offline:

```bash
gitmortem HEAD~1 --no-llm
```

Write reports to disk:

```bash
gitmortem abc1234 -o reports/abc1234.md --html
```

## Provider Support

`gitmortem` defaults to Groq because it gives fast inference and a simple setup. Users can override the provider with `--provider` or the `GITMORTEM_PROVIDER` environment variable.

| Provider | Env var | Notes |
|---|---|---|
| `groq` | `GROQ_API_KEY` | Default provider |
| `openai` | `OPENAI_API_KEY` | Native OpenAI API |
| `anthropic` | `ANTHROPIC_API_KEY` | Native Anthropic API |
| `openrouter` | `OPENROUTER_API_KEY` | OpenAI-compatible endpoint |
| `ollama` | none required | Defaults to `http://localhost:11434/v1` |
| `compatible` | provider-specific | Bring your own OpenAI-compatible base URL |

Examples:

```bash
gitmortem HEAD~1 --provider groq --model llama-3.3-70b-versatile
gitmortem HEAD~1 --provider anthropic --model claude-3-7-sonnet-latest
gitmortem HEAD~1 --provider compatible --base-url https://my-endpoint.example/v1 --api-key sk-...
```

## CLI Reference

```bash
gitmortem COMMIT_HASH [OPTIONS]
```

Important options:

- `--repo`, `-r`: repository path
- `--output`, `-o`: write markdown report to a file
- `--html`: also emit a standalone HTML report
- `--html-output`: write HTML to a specific path
- `--provider`: `groq`, `openai`, `anthropic`, `openrouter`, `ollama`, `compatible`
- `--model`: override the default model for the chosen provider
- `--api-key`: inline API key override
- `--base-url`: custom base URL for `compatible` or overrides
- `--window`: surrounding commit window used for timeline reconstruction
- `--no-llm`: skip AI analysis and render a deterministic report

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | for default LLM mode | Groq API key |
| `OPENAI_API_KEY` | for OpenAI | OpenAI API key |
| `ANTHROPIC_API_KEY` | for Anthropic | Anthropic API key |
| `OPENROUTER_API_KEY` | for OpenRouter | OpenRouter API key |
| `GITMORTEM_PROVIDER` | no | Default provider override |
| `GITMORTEM_MODEL` | no | Model override |
| `GITMORTEM_BASE_URL` | no | Base URL for `compatible` or custom routing |
| `GITMORTEM_OUTPUT_DIR` | no | Default directory for generated reports |

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Packaging

- `ci.yml` runs tests and linting on push and pull request
- `publish.yml` builds and publishes to PyPI on a version tag

## License

MIT
