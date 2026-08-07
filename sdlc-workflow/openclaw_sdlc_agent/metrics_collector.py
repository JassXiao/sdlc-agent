import time
import subprocess
import os
from typing import Dict, Any, Optional

class MetricsCollector:
    """Metrics Collector for the SDLC Workflow.
    Tracks execution duration, Git diff line changes, and retry counts,
    and generates a Markdown summary report.
    """

    def __init__(self, session_id: str, model_used: str):
        self.session_id = session_id
        self.model_used = model_used
        self.start_time = time.time()
        self.end_time: Optional[float] = None

    def stop(self) -> float:
        self.end_time = time.time()
        return self.end_time - self.start_time

    def get_duration(self) -> float:
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    def get_git_diff_stats(self) -> Dict[str, Any]:
        """Gets Git diff statistics relative to HEAD."""
        try:
            # Run git diff HEAD --numstat
            result = subprocess.run(
                ["git", "diff", "HEAD", "--numstat"],
                capture_output=True,
                text=True,
                check=True
            )
            stats = []
            total_insertions = 0
            total_deletions = 0

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    ins_str, del_str, file_path = parts
                    ins = int(ins_str) if ins_str != "-" else 0
                    dels = int(del_str) if del_str != "-" else 0
                    stats.append({
                        "file": file_path,
                        "insertions": ins,
                        "deletions": dels
                    })
                    total_insertions += ins
                    total_deletions += dels

            return {
                "success": True,
                "files": stats,
                "total_files_changed": len(stats),
                "total_insertions": total_insertions,
                "total_deletions": total_deletions,
                "total_line_changes": total_insertions + total_deletions
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files": [],
                "total_files_changed": 0,
                "total_insertions": 0,
                "total_deletions": 0,
                "total_line_changes": 0
            }

    def generate_report(self, status: str, retries: int) -> str:
        duration = self.get_duration()
        diff_stats = self.get_git_diff_stats()

        md = []
        md.append("# SDLC Workflow Execution Report (summary.md)")
        md.append("")
        md.append("## Basic Information")
        md.append(f"- **Session ID:** `{self.session_id}`")
        md.append(f"- **Model Used:** `{self.model_used}`")
        md.append(f"- **Execution Duration:** `{duration:.2f} seconds`")
        md.append(f"- **Consistency Retries:** `{retries}`")
        md.append(f"- **Status:** `{status}`")
        md.append("")

        md.append("## Git Diff Statistics")
        if diff_stats.get("success"):
            md.append(f"- **Total Files Changed:** {diff_stats['total_files_changed']}")
            md.append(f"- **Total Line Changes:** {diff_stats['total_line_changes']} ({diff_stats['total_insertions']} additions, {diff_stats['total_deletions']} deletions)")
            md.append("")

            if diff_stats["files"]:
                md.append("### Detailed Git Diff (by file)")
                md.append("| File | Insertions (+) | Deletions (-) |")
                md.append("|:---|:---|:---|")
                for f in diff_stats["files"]:
                    md.append(f"| `{f['file']}` | {f['insertions']} | {f['deletions']} |")
            else:
                md.append("*No files changed in Git working directory.*")
        else:
            md.append(f"*Failed to retrieve Git diff statistics:* {diff_stats.get('error')}")

        md_text = "\n".join(md) + "\n"

        # Write to summary.md in the workspace root
        try:
            with open("summary.md", "w", encoding="utf-8") as f:
                f.write(md_text)
        except Exception as e:
            print(f"Error writing summary.md: {e}")

        return md_text
