#!/usr/bin/env python3
"""Command-line entry point for the OpenAI-powered ReproAgent baseline."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from repro_agent.llm_agent import (
    OllamaResponsesClient,
    OpenAIResponsesClient,
    RepositoryAuditAgent,
    load_dotenv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a local project for reproducibility documentation."
    )
    parser.add_argument("--project", required=True, type=Path, help="Project directory")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    parser.add_argument(
        "--markdown-output", type=Path, help="Optional Markdown report path"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(Path(__file__).resolve().parent / ".env")
    provider = os.environ.get("AGENT_PROVIDER", "ollama").lower()
    if provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "qwen3:1.7b")
        client = OllamaResponsesClient()
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY is required when AGENT_PROVIDER=openai")
        model = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
        client = OpenAIResponsesClient(api_key)
    else:
        raise SystemExit("AGENT_PROVIDER must be 'ollama' or 'openai'")
    auditor = RepositoryAuditAgent(
        args.project,
        model=model,
        client=client,
    )
    report = auditor.run()

    if args.output:
        auditor.write_json(report, args.output)
    if args.markdown_output:
        auditor.write_markdown(report, args.markdown_output)

    print(auditor.format_console(report))
    if args.output:
        print(f"JSON report: {args.output}")
    if args.markdown_output:
        print(f"Markdown report: {args.markdown_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
