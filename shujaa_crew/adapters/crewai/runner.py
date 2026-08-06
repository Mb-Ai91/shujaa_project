from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TextIO


class CrewAIRunner:
    """محوّل مسؤول عن تشغيل CrewAI دون shell=True."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path(__file__).resolve().parents[2]
        self.log_path = self.project_dir / "n8n_output.log"

    def start(self, topic: str) -> subprocess.Popen[str]:
        env = os.environ.copy()
        env["TERM"] = "dumb"

        log_file: TextIO = self.log_path.open("a", encoding="utf-8")

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
        finally:
            log_file.close()

        if process.stdin is None:
            process.terminate()
            raise RuntimeError("Unable to open CrewAI input stream.")

        try:
            process.stdin.write(f"{topic}\n")
            process.stdin.flush()
        except BrokenPipeError as error:
            process.terminate()
            raise RuntimeError("Unable to send task to CrewAI.") from error
        finally:
            process.stdin.close()

        return process
