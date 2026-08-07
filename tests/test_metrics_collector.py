import os
import unittest
from unittest.mock import patch, MagicMock
from openclaw_sdlc_agent.metrics_collector import MetricsCollector

class TestMetricsCollector(unittest.TestCase):
    def setUp(self):
        self.session_id = "test-session-123"
        self.model_used = "openai/gpt-5.6-terra"
        self.collector = MetricsCollector(session_id=self.session_id, model_used=self.model_used)

    def tearDown(self):
        if os.path.exists("summary.md"):
            try:
                os.remove("summary.md")
            except OSError:
                pass

    def test_timing(self):
        # Stop immediately and verify duration is recorded
        duration = self.collector.stop()
        self.assertGreaterEqual(duration, 0.0)
        self.assertEqual(duration, self.collector.get_duration())

    @patch("subprocess.run")
    def test_get_git_diff_stats_empty(self, mock_run):
        # Mock git diff HEAD --numstat returning empty output
        mock_response = MagicMock()
        mock_response.stdout = ""
        mock_run.return_value = mock_response

        stats = self.collector.get_git_diff_stats()
        self.assertTrue(stats["success"])
        self.assertEqual(stats["total_files_changed"], 0)
        self.assertEqual(stats["total_insertions"], 0)
        self.assertEqual(stats["total_deletions"], 0)

    @patch("subprocess.run")
    def test_get_git_diff_stats_with_changes(self, mock_run):
        # Mock git diff HEAD --numstat with some changes
        mock_response = MagicMock()
        mock_response.stdout = (
            "12\t5\tfile1.py\n"
            "0\t3\tfile2.py\n"
            "-\t-\tbinary_file.bin\n"
        )
        mock_run.return_value = mock_response

        stats = self.collector.get_git_diff_stats()
        self.assertTrue(stats["success"])
        self.assertEqual(stats["total_files_changed"], 3)
        self.assertEqual(stats["total_insertions"], 12)
        self.assertEqual(stats["total_deletions"], 8)
        self.assertEqual(stats["total_line_changes"], 20)
        self.assertEqual(len(stats["files"]), 3)
        self.assertEqual(stats["files"][0]["file"], "file1.py")
        self.assertEqual(stats["files"][0]["insertions"], 12)
        self.assertEqual(stats["files"][0]["deletions"], 5)

    @patch("subprocess.run")
    def test_generate_report(self, mock_run):
        mock_response = MagicMock()
        mock_response.stdout = "4\t2\topenclaw_sdlc_agent/agent.py\n"
        mock_run.return_value = mock_response

        self.collector.stop()
        report = self.collector.generate_report(status="success", retries=1)

        # Check report content
        self.assertIn("# SDLC Workflow Execution Report (summary.md)", report)
        self.assertIn(self.session_id, report)
        self.assertIn(self.model_used, report)
        self.assertIn("Consistency Retries:** `1`", report)
        self.assertIn("Status:** `success`", report)
        self.assertIn("openclaw_sdlc_agent/agent.py", report)

        # Check if file summary.md was written
        self.assertTrue(os.path.exists("summary.md"))
        with open("summary.md", "r", encoding="utf-8") as f:
            file_content = f.read()
        self.assertEqual(report, file_content)

if __name__ == "__main__":
    unittest.main()
