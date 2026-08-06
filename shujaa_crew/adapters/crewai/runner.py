from __future__ import annotations

import os
import subprocess
from pathlib import Path


class CrewAIRunner:
    """محوّل مسؤول عن تشغيل CrewAI بأمان."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path(__file__).resolve().parents[2]
        self.log_path = self.project_dir / "n8n_output.log"

    def start(self, topic: str) -> int:
        env = os.environ.copy()
        env["TERM"] = "dumb"

        log_file = self.log_path.open("a", encoding="utf-8")

        try:
            process = subprocess.Popen(
                ["uv", "run", "crewai", "run"],
                cwd=self.project_dir,
                stdin=subprocess.PIPE,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                start_new_session=True,
            )

            if process.stdin is None:
                process.terminate()
                raise RuntimeError("تعذر فتح قناة الإدخال إلى CrewAI.")

            process.stdin.write(f"{topic}\n")
            process.stdin.flush()
            process.stdin.close()

            return process.pid

        except Exception:
            log_file.close()
            raise
