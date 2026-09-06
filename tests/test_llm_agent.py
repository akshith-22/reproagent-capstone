import json
from pathlib import Path
import unittest

from repro_agent.llm_agent import RepositoryAuditAgent


ROOT = Path(__file__).resolve().parents[1]


class FakeResponsesClient:
    def __init__(self):
        self.calls = 0

    def create(self, payload):
        self.calls += 1
        if self.calls == 1:
            return {
                "id": "resp_1",
                "output": [
                    {
                        "type": "function_call",
                        "name": "list_files",
                        "call_id": "call_1",
                        "arguments": "{}",
                    }
                ],
            }
        if self.calls == 2:
            return {
                "id": "resp_2",
                "output": [
                    {
                        "type": "function_call",
                        "name": "read_file",
                        "call_id": "call_2",
                        "arguments": json.dumps({"path": "README.md"}),
                    }
                ],
            }
        output = []
        for check_id in (
            "readme",
            "dependencies",
            "setup",
            "run_command",
            "environment",
            "io_locations",
            "test_case",
            "entrypoint",
            "example_input",
        ):
            status = "FAIL" if check_id in {"setup", "environment"} else "PASS"
            output.append(
                {
                    "type": "function_call",
                    "name": "record_check",
                    "call_id": f"call_{check_id}",
                    "arguments": json.dumps(
                        {
                            "id": check_id,
                            "status": status,
                            "evidence": "README.md or file inventory",
                            "recommendation": (
                                "None" if status == "PASS" else "Document this item."
                            ),
                        }
                    ),
                }
            )
        output.append(
            {
                "type": "function_call",
                "name": "finish_audit",
                "call_id": "call_finish",
                "arguments": json.dumps(
                    {
                        "summary": "Two documentation gaps found.",
                        "limitations": ["Commands were not executed."],
                    }
                ),
            }
        )
        return {"id": "resp_3", "output": output}


class RepositoryAuditAgentTests(unittest.TestCase):
    def test_model_controls_tool_loop_and_report_is_scored(self):
        client = FakeResponsesClient()
        report = RepositoryAuditAgent(
            ROOT / "examples/sample_project", "fake-model", client
        ).run()
        self.assertEqual(client.calls, 3)
        self.assertEqual(report.tool_trace[0]["tool"], "list_files")
        self.assertEqual(report.tool_trace[1]["tool"], "read_file")
        self.assertEqual(
            [event["tool"] for event in report.tool_trace].count("record_check"), 9
        )
        self.assertEqual(report.tool_trace[-1]["tool"], "finish_audit")
        self.assertEqual(report.score, 75)

    def test_read_tool_blocks_parent_directory_escape(self):
        agent = RepositoryAuditAgent(
            ROOT / "examples/sample_project", "fake-model", FakeResponsesClient()
        )
        result = agent._execute_tool("read_file", {"path": "../../README.md"})
        self.assertIn("error", result)

    def test_report_accepts_small_model_stringified_check_objects(self):
        agent = RepositoryAuditAgent(
            ROOT / "examples/sample_project", "fake-model", FakeResponsesClient()
        )
        report = agent._build_report(
            {
                "summary": "Done",
                "checks": [
                    json.dumps(
                        {
                            "id": "readme",
                            "status": "PASS",
                            "evidence": "README.md",
                            "recommendation": "None",
                        }
                    )
                ],
                "limitations": "Commands were not executed.",
            }
        )
        self.assertEqual(report.checks[0].status, "PASS")
        self.assertEqual(report.checks[1].status, "UNCERTAIN")
        self.assertEqual(report.limitations, ["Commands were not executed."])


if __name__ == "__main__":
    unittest.main()
