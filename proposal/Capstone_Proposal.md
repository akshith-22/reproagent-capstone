# CSE 598 Capstone Project Proposal

| Field | Response |
|---|---|
| Student name | **Venkata Sai Akshith Reddy Ganta** |
| Project title | **ReproAgent: A Local LLM Agent for Auditing AI Project Reproducibility** |
| Repository / notebook link | **https://github.com/akshith-22/reproagent-capstone** |
| Configuration location | `.env.example` (optional; no key is required) |

## 1. Problem Definition

AI/ML repositories often omit details needed to rerun their results. ReproAgent inspects a project and produces a scored, evidence-based report of missing reproducibility information. The intended user is a student, reviewer, or developer preparing a project for independent execution. Input is a local repository folder containing source code and documentation. Output is a JSON and Markdown audit with per-criterion status, file evidence, recommendations, a tool trace, and a 0–100 score. Success means correctly classifying nine requirements: README quality, dependencies, setup, run command, environment variables, input/output locations, test case, entry point, and example input. False passes, false failures, unsafe reads, or failure to terminate count as errors.

## 2. Motivation and Project Scope

Reproducibility is essential for grading, collaboration, and trustworthy AI development, but manual review is repetitive and inconsistent. Agentic AI is appropriate because the task is sequential and evidence-driven: a model must decide which tools and files are relevant, observe results, revise its next action, make individual judgments, and determine when the audit is complete. A fixed checklist cannot reliably interpret varied repository structures or natural-language instructions. The semester scope includes local Python-oriented repositories, autonomous read-only inspection, grounded findings, safe sandboxed command verification, and failure diagnosis. Remote authentication, automatic code repair, arbitrary operating systems, GPU-heavy projects, and guarantees of scientific correctness are out of scope. A 1.7B local model and bounded tools keep the project feasible and free to reproduce.

## 3. Runnable Baseline

The baseline uses Qwen3 1.7B through Ollama and Python's standard library. No API key is required. The model receives the audit goal plus four tools: `list_files`, `read_file`, `record_check`, and `finish_audit`. It autonomously selects files, incorporates each tool observation, records nine judgments, and completes the report. The host restricts paths to the target directory, limits file/loop size, rejects premature completion, and computes a deterministic weighted score. This is a meaningful agent baseline because decisions about evidence gathering and classifications come from an LLM, while transparent guardrails bound its actions. Implementation is in `run_baseline.py` and `repro_agent/llm_agent.py`; tests are under `tests/`.

## 4. Test Case and Baseline Output

Input is `examples/sample_project/`. It contains a README, dependency file, executable, example input, and saved output, while its README intentionally omits an installation command and environment/API-key guidance. Expected behavior is to pass dependencies and fail setup and environment guidance. The actual local-model run made 14 agent actions, selected `README.md` and `requirements.txt`, recorded all nine judgments, rejected one premature finish, and completed with **75/100**. It correctly classified six criteria, but incorrectly failed dependencies, incorrectly passed setup, and marked environment guidance uncertain. Thus the model/tool loop worked and exposed concrete reasoning errors to improve. The screenshot is `evidence/baseline_run.png`; full reports are under `outputs/`.

## 5. Reproducibility and Run Instructions

Requirements are Python 3.10+, Ollama, about 1.4 GB for the model, and internet only for the one-time download. No API key is needed. Install Ollama from `https://ollama.com/download`, start it, and run `ollama pull qwen3:1.7b`. From the repository root execute:

```bash
python3 run_baseline.py --project examples/sample_project --output outputs/baseline_report.json --markdown-output outputs/baseline_report.md
```

Input is `examples/sample_project/`; outputs appear in the terminal and `outputs/`. Run five offline tests with `python3 -m unittest discover -s tests -v`. Inference is hardware-dependent but normally completes within two minutes on Apple Silicon.

## 6. Initial Evaluation Plan

I will create a labeled set of at least 30 small public or instructor-approved repositories. Two reviewers will label each criterion and resolve disagreements. The heuristic comparison, local-LLM baseline, and improved agent will be evaluated using per-check precision, recall, macro-F1, score error, clean-environment execution success, grounded-evidence rate, latency, invalid-tool rate, and termination rate. Improvement means higher macro-F1 and execution success without unsafe commands or unacceptable latency.

## 7. Limitations and Next Steps

The small model already demonstrates false positive and false negative judgments. It may choose too few files, repeat actions, emit non-native completion syntax, and cannot yet verify whether documented commands work. Next steps are evidence-aware prompting, a planner/evaluator separation, safe subprocess execution in temporary environments, retry and failure diagnosis, notebook/package-manager adapters, exact line citations, and comparison with a stronger model when available. Risks include unsafe repository instructions, slow downloads, hardware variation, and annotation disagreement; path confinement, allowlists, timeouts, action budgets, and a labeling guide will mitigate them.
