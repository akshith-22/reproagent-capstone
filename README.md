# ReproAgent: Local LLM Baseline

ReproAgent is a tool-using AI agent that audits whether another person can reproduce an AI/ML project. A local Qwen3 model—not a fixed Python workflow—chooses which repository files to inspect, observes tool results, records nine evidence-based judgments, and finishes with JSON and Markdown reports.

The baseline runs locally through Ollama. It requires no API key, paid account, or Python packages.

## Agent architecture

The agent follows a bounded plan-act-observe loop:

1. The Qwen3 model receives the audit goal and available tool schemas.
2. It selects `list_files` and `read_file` actions to gather evidence.
3. Python validates each path, executes the read-only action, and returns the observation.
4. The model calls `record_check` once per reproducibility criterion.
5. The host rejects an early `finish_audit` and reports missing judgments.
6. After all nine judgments exist, the model finishes; Python computes the weighted score and writes reports.

Safety controls restrict reads to the selected project, reject path traversal, limit files to 1 MB/12,000 characters, cap the loop at 24 model steps, treat repository text as untrusted data, and never execute audited code.

## What it checks

- README quality
- Dependency declarations
- Exact setup/install command
- Exact run command
- API-key/environment-variable guidance
- Input and output locations
- Concrete test case and expected behavior
- Executable entry point
- Example input

## Requirements

- macOS, Windows, or Linux capable of running Ollama
- Python 3.10 or newer
- Ollama
- Approximately 1.4 GB free for `qwen3:1.7b`
- Internet access for the one-time Ollama/model download
- No API key or environment variable

## Setup

1. Clone the public repository and enter it:

   ```bash
   git clone https://github.com/akshith-22/reproagent-capstone.git
   cd reproagent-capstone
   ```

2. Install Ollama from <https://ollama.com/download>. On macOS with Homebrew:

   ```bash
   brew install --cask ollama
   ```

3. Start Ollama (open the application or run `ollama serve`) and download the model once:

   ```bash
   ollama pull qwen3:1.7b
   ```

4. Confirm the model is installed with `ollama list`.

No `pip install` is needed because the Python code uses only the standard library. Optional provider/model settings are documented in `.env.example`.

## Exact baseline command

From the repository root, with Ollama running:

```bash
python3 run_baseline.py \
  --project examples/sample_project \
  --output outputs/baseline_report.json \
  --markdown-output outputs/baseline_report.md
```

Input is `examples/sample_project/`. Output appears in the terminal, `outputs/baseline_report.json`, and `outputs/baseline_report.md`. A run typically takes under two minutes on an Apple Silicon laptop, but timing depends on hardware.

## Concrete test case and actual result

The sample project includes a README, `requirements.txt`, executable `main.py`, example input, and saved prediction. Its README intentionally omits an installation command and API-key/environment guidance. Expected behavior is to pass dependencies and fail setup and environment guidance.

The actual Qwen3 run completed 14 agent actions, autonomously selected `README.md` and `requirements.txt`, recorded all nine judgments, and produced **75/100**. It correctly found most items but incorrectly failed dependencies, incorrectly passed setup, and marked environment guidance uncertain. These are useful baseline errors for later improvement. The actual reports are under `outputs/`, and `evidence/baseline_run.png` shows the run.

## Tests

Run five deterministic tests without invoking a model:

```bash
python3 -m unittest discover -s tests -v
```

They verify scoring, mocked model-directed tool use, missing-project handling, small-model output normalization, and path-traversal blocking.

## Repository layout

```text
.
├── README.md
├── .env.example                    # optional provider/model overrides
├── run_baseline.py                 # CLI entry point
├── repro_agent/
│   ├── llm_agent.py                # LLM loop, tools, safety, reports
│   └── auditor.py                  # deterministic comparison
├── examples/sample_project/        # concrete test input
├── outputs/                         # actual local-LLM output
├── tests/                           # five deterministic tests
├── evidence/baseline_run.png        # execution screenshot
└── proposal/                         # proposal artifacts
```

## Known limitations

The 1.7B model can misinterpret explicit evidence, as the concrete result demonstrates. It sometimes emits tagged completion text instead of a native tool call, so the host accepts that form only after all nine judgments exist. The baseline reads text but does not execute documented commands, deeply inspect notebooks, or guarantee that instructions are correct. Model download and inference speed vary by computer.
