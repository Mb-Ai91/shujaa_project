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
