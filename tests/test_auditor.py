from pathlib import Path
import unittest

from repro_agent.auditor import ReproducibilityAuditor


ROOT = Path(__file__).resolve().parents[1]


class ReproducibilityAuditorTests(unittest.TestCase):
    def test_sample_project_finds_two_documentation_gaps(self) -> None:
        report = ReproducibilityAuditor(ROOT / "examples/sample_project").run()
        failed = {check.id for check in report.checks if check.status == "FAIL"}
        self.assertEqual(failed, {"setup", "environment"})
        self.assertEqual(report.score, 75)
        self.assertEqual(report.max_score, 100)

    def test_missing_project_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not exist"):
            ReproducibilityAuditor(ROOT / "examples/missing").run()


if __name__ == "__main__":
    unittest.main()

