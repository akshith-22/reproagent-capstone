"""Deterministic plan-inspect-evaluate-report reproducibility agent."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class AuditCheck:
    id: str
    label: str
    status: str
    evidence: str
    recommendation: str
    weight: int


@dataclass(frozen=True)
class AuditReport:
    project: str
    workflow: list[str]
    files_inspected: list[str]
    score: int
    max_score: int
    checks: list[AuditCheck]

    def to_dict(self) -> dict:
        return asdict(self)


class ReproducibilityAuditor:
    """Audits one local project with an explicit agent-style workflow."""

    README_NAMES = ("README.md", "README.rst", "README.txt", "README")
    DEPENDENCY_FILES = (
        "requirements.txt",
        "pyproject.toml",
        "environment.yml",
        "Pipfile",
        "package.json",
    )
    ENTRYPOINTS = ("main.py", "app.py", "run.py", "run_baseline.py")

    def __init__(self, project: Path):
        self.project = project.resolve()

    def run(self) -> AuditReport:
        if not self.project.is_dir():
            raise ValueError(f"Project directory does not exist: {self.project}")

        workflow = [
            "PLAN: select reproducibility criteria",
            "INSPECT: inventory project files and read documentation",
            "EVALUATE: apply deterministic evidence rules",
            "REPORT: score findings and recommend fixes",
        ]
        files = sorted(
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )
        readme_path = next(
            (self.project / name for name in self.README_NAMES if (self.project / name).is_file()),
            None,
        )
        readme = readme_path.read_text(encoding="utf-8") if readme_path else ""
        lower = readme.lower()

        checks = [
            self._check(
                "readme",
                "README exists",
                bool(readme_path),
                readme_path.name if readme_path else "No README found",
                "Add a README at the project root.",
                15,
            ),
            self._check(
                "dependencies",
                "Dependencies are declared",
                any((self.project / name).is_file() for name in self.DEPENDENCY_FILES)
                or "dependencies" in lower,
                "Dependency file or README dependency section found",
                "Declare dependencies in a standard file and explain installation.",
                15,
            ),
            self._check(
                "setup",
                "Setup command is documented",
                self._matches(readme, r"(?:pip|conda|npm|poetry|uv)\s+(?:install|sync|create)"),
                "Install/setup command found" if self._matches(readme, r"(?:pip|conda|npm|poetry|uv)\s+(?:install|sync|create)") else "No install/setup command found",
                "Add the exact command needed to install dependencies.",
                15,
            ),
            self._check(
                "run_command",
                "Exact run command is documented",
                self._matches(readme, r"(?:python3?|node|npm\s+run|jupyter)\s+[\w./-]+"),
                "Executable command found",
                "Add one copy-pasteable command from the repository root.",
                15,
            ),
            self._check(
                "environment",
                "Environment variables are explained",
                any(term in lower for term in ("environment variable", "api key", ".env", "no api")),
                "Environment/API-key guidance found" if any(term in lower for term in ("environment variable", "api key", ".env", "no api")) else "No environment or API-key guidance found",
                "List required variables or explicitly state that none are required.",
                10,
            ),
            self._check(
                "io_locations",
                "Input and output locations are documented",
                "input" in lower and "output" in lower,
                "Both input and output are mentioned",
                "Name the input path and where generated output appears.",
                10,
            ),
            self._check(
                "test_case",
                "Concrete test case is documented",
                "test case" in lower and ("expected" in lower or "should" in lower),
                "Test case and expected behavior found",
                "Add a small input plus its expected behavior or output.",
                10,
            ),
            self._check(
                "entrypoint",
                "Executable entry point exists",
                any((self.project / name).is_file() for name in self.ENTRYPOINTS),
                "Recognized entry point found",
                "Add a conventional executable entry point such as main.py.",
                5,
            ),
            self._check(
                "example_input",
                "Example input exists",
                any("input" in Path(name).name.lower() for name in files),
                "Input-named example file found",
                "Commit a small example input file.",
                5,
            ),
        ]
        score = sum(check.weight for check in checks if check.status == "PASS")
        return AuditReport(
            project=self.project.name,
            workflow=workflow,
            files_inspected=files,
            score=score,
            max_score=sum(check.weight for check in checks),
            checks=checks,
        )

    @staticmethod
    def _matches(text: str, pattern: str) -> bool:
        return bool(re.search(pattern, text, flags=re.IGNORECASE))

    @staticmethod
    def _check(
        check_id: str,
        label: str,
        passed: bool,
        evidence: str,
        recommendation: str,
        weight: int,
    ) -> AuditCheck:
        return AuditCheck(
            id=check_id,
            label=label,
            status="PASS" if passed else "FAIL",
            evidence=evidence,
            recommendation="None" if passed else recommendation,
            weight=weight,
        )

    @staticmethod
    def write_json(report: AuditReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def write_markdown(report: AuditReport, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            "# ReproAgent Audit Report",
            "",
            f"**Project:** `{report.project}`  ",
            f"**Score:** {report.score}/{report.max_score}",
            "",
            "| Status | Check | Evidence | Recommendation |",
            "|---|---|---|---|",
        ]
        for check in report.checks:
            rows.append(
                f"| {check.status} | {check.label} | {check.evidence} | {check.recommendation} |"
            )
        rows.extend(["", "## Agent workflow", ""])
        rows.extend(f"- {step}" for step in report.workflow)
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    @staticmethod
    def format_console(report: AuditReport) -> str:
        lines = [
            "ReproAgent baseline completed",
            f"Project: {report.project}",
            f"Score: {report.score}/{report.max_score}",
            "Findings:",
        ]
        lines.extend(f"  [{item.status}] {item.label}" for item in report.checks)
        failed = [item for item in report.checks if item.status == "FAIL"]
        lines.append(f"Action items: {len(failed)}")
        lines.extend(f"  - {item.recommendation}" for item in failed)
        return "\n".join(lines)

