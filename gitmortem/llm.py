from __future__ import annotations

import json
import re
from dataclasses import dataclass

from gitmortem.config import LLMSettings
from gitmortem.git_analyzer import CommitFact
from gitmortem.timeline import build_history_context

ROOT_CAUSE_SYSTEM = """
You are a senior site reliability engineer conducting a production incident postmortem.
You will be given a structured summary of a git commit diff and the commit metadata.
Your job is to identify the root cause of the incident with engineering precision.

Rules:
- Be specific. Name exact files, functions, and variables where possible.
- Use the 5 Whys technique implicitly and go beyond the surface code change.
- Do not speculate beyond the provided evidence. If something is unknowable from the diff, say so.
- Output only valid JSON.
- Keep each field concise.
""".strip()

ROOT_CAUSE_USER = """
COMMIT: {short_hash} by {author} at {timestamp}
MESSAGE: {commit_message}

FILES CHANGED:
{files_changed}

DIFF SUMMARY:
{diff_summary}

BLAST RADIUS:
{blast_radius}

Return only this JSON:
{{
  "root_cause": "One sentence describing what actually caused the incident.",
  "trigger": "Immediate trigger for the failure.",
  "contributing_factors": ["factor 1", "factor 2"],
  "unknowns": ["unknown 1"],
  "confidence": "high | medium | low",
  "affected_systems": ["component 1", "component 2"]
}}
""".strip()

TIMELINE_SYSTEM = """
You are reconstructing the timeline of an engineering incident from git history.
Given a list of commits surrounding the broken commit, produce a chronological narrative.
Output only valid JSON.
""".strip()

TIMELINE_USER = """
BROKEN COMMIT: {short_hash}

SURROUNDING COMMITS:
{commit_history}

Return only this JSON:
{{
  "timeline": [
    {{
      "time": "relative label such as -2d, -3h, T+0 (broken commit), +1h",
      "event": "plain-English description of what happened",
      "hash": "short commit hash"
    }}
  ],
  "time_to_detect": "estimated time from deploy to detection if inferable, otherwise unknown",
  "deploy_pattern": "what pattern likely led here"
}}
""".strip()

CHECKLIST_SYSTEM = """
You are writing the never-again section of a postmortem.
Given root cause analysis and the affected files, generate concrete prevention items.
Be incident-specific and actionable. Output only valid JSON.
""".strip()

CHECKLIST_USER = """
ROOT CAUSE: {root_cause}
TRIGGER: {trigger}
CONTRIBUTING FACTORS: {contributing_factors}
AFFECTED FILES: {affected_files}

Return only this JSON:
{{
  "immediate_actions": [
    {{"action": "what to do right now", "owner": "responsible role", "priority": "P0|P1|P2"}}
  ],
  "prevention_items": [
    {{"item": "specific preventive measure", "type": "test|process|tooling|monitoring|docs"}}
  ],
  "detection_improvements": ["concrete alerting or observability improvement"],
  "severity": "SEV1|SEV2|SEV3",
  "estimated_impact": "plain-English user or system impact estimate"
}}
""".strip()


class LLMOrchestrationError(RuntimeError):
    """Raised when an LLM request or JSON parse fails."""


@dataclass
class StructuredLLMClient:
    settings: LLMSettings

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        if self.settings.provider == "anthropic":
            response_text = self._anthropic_complete(system_prompt, user_prompt)
        else:
            response_text = self._openai_compatible_complete(system_prompt, user_prompt)
        return _parse_json_payload(response_text)

    def _openai_compatible_complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMOrchestrationError(
                "The 'openai' package is required for Groq, OpenAI, OpenRouter, "
                "Ollama, and compatible providers."
            ) from exc

        client_kwargs: dict[str, object] = {"api_key": self.settings.api_key}
        if self.settings.base_url:
            client_kwargs["base_url"] = self.settings.base_url
        if self.settings.provider == "openrouter":
            client_kwargs["default_headers"] = {
                "HTTP-Referer": "https://github.com/lekhanpro/gitmortem",
                "X-Title": "gitmortem",
            }

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=self.settings.model,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMOrchestrationError("Model returned an empty response.")
        return content

    def _anthropic_complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise LLMOrchestrationError(
                "The 'anthropic' package is required for Anthropic provider."
            ) from exc

        client = Anthropic(api_key=self.settings.api_key)
        response = client.messages.create(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            temperature=self.settings.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        chunks = [
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ]
        payload = "".join(chunks).strip()
        if not payload:
            raise LLMOrchestrationError("Model returned an empty response.")
        return payload


def run_root_cause(
    settings: LLMSettings,
    commit_fact: CommitFact,
    diff_summary: str,
    blast_radius_text: str,
) -> dict:
    files_changed = ", ".join(commit_fact.files_changed[:12]) or "none"
    prompt = ROOT_CAUSE_USER.format(
        short_hash=commit_fact.short_hash,
        author=commit_fact.author,
        timestamp=commit_fact.timestamp,
        commit_message=commit_fact.message,
        files_changed=files_changed,
        diff_summary=diff_summary,
        blast_radius=blast_radius_text,
    )
    return StructuredLLMClient(settings).complete_json(ROOT_CAUSE_SYSTEM, prompt)


def run_timeline(
    settings: LLMSettings,
    commit_fact: CommitFact,
    surrounding_commits: list[CommitFact],
) -> dict:
    prompt = TIMELINE_USER.format(
        short_hash=commit_fact.short_hash,
        commit_history=build_history_context(surrounding_commits),
    )
    return StructuredLLMClient(settings).complete_json(TIMELINE_SYSTEM, prompt)


def run_checklist(settings: LLMSettings, root_cause_data: dict, commit_fact: CommitFact) -> dict:
    prompt = CHECKLIST_USER.format(
        root_cause=root_cause_data["root_cause"],
        trigger=root_cause_data["trigger"],
        contributing_factors=", ".join(root_cause_data.get("contributing_factors", [])),
        affected_files=", ".join(commit_fact.files_changed[:12]),
    )
    return StructuredLLMClient(settings).complete_json(CHECKLIST_SYSTEM, prompt)


def _parse_json_payload(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise LLMOrchestrationError("Model response did not contain valid JSON.")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise LLMOrchestrationError("Model response JSON could not be parsed.") from exc
