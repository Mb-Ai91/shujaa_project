from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TextIO


class MockRunner:
    """مشغّل محلي للاختبارات لا يستخدم أي نموذج ذكاء اصطناعي."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path(__file__).resolve().parents[2]
        self.log_path = (
            self.project_dir
            / ".runtime"
            / "mock_runner.log"
        )

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def get_result(
        self,
        process: subprocess.Popen[str],
    ) -> str:
        return "Mock task completed"

    def start(self, topic: str) -> subprocess.Popen[str]:
        log_file: TextIO = self.log_path.open(
            "a",
            encoding="utf-8",
        )

        normalized_topic = topic.strip().lower()

        if "mock:failed" in normalized_topic:
            code = (
                "import sys; "
                "print('Mock task failed', flush=True); "
                "sys.exit(1)"
            )

        elif "mock:timeout" in normalized_topic:
            code = (
                "import time; "
                "print('Mock task waiting for timeout', flush=True); "
                "time.sleep(300)"
            )

        else:
            code = (
                "import time; "
                "print('Mock task started', flush=True); "
                "time.sleep(4); "
                "print('Mock task completed', flush=True)"
            )

        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    code,
                ],
                cwd=self.project_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        finally:
            log_file.close()

        return process
