from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import TextIO


class CrewAIRunner:
    """محوّل مسؤول عن تشغيل CrewAI."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path(__file__).resolve().parents[2]
        self.log_path = self.project_dir / "n8n_output.log"

    def start(self, topic: str) -> subprocess.Popen[str]:
        env = os.environ.copy()
        env["TERM"] = "dumb"

        inputs = json.dumps(
            {"topic": topic},
            ensure_ascii=False,
        )

        log_file: TextIO = self.log_path.open("a", encoding="utf-8")

        try:
            process = subprocess.Popen(
                ["uv", "run", "crewai", "run", "--inputs", inputs],
                cwd=self.project_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                start_new_session=True,
            )
        finally:
            log_file.close()

        return process

    def get_error(self, return_code: int) -> str:
        error_message = f"Exit code: {return_code}"

        try:
            log_text = self.log_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            return error_message

        recent_log = log_text[-12000:]

        if "RESOURCE_EXHAUSTED" in recent_log or "429" in recent_log:
            return "LLM quota exhausted: RESOURCE_EXHAUSTED (429)."

        meaningful_lines = [
            line.strip()
            for line in recent_log.splitlines()
            if line.strip()
            and any(
                keyword in line.lower()
                for keyword in (
                    "error",
                    "failed",
                    "exception",
                    "missing required input",
                    "connection reset",
                    "socket hang up",
                )
            )
        ]

        if meaningful_lines:
            return meaningful_lines[-1][:500]

        return error_message
