from __future__ import annotations

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    ("runner_name", "expected_class"),
    [
        ("mock", "MockRunner"),
        ("crewai", "CrewAIRunner"),
    ],
)
def test_runner_selection(runner_name: str, expected_class: str):
    env = os.environ.copy()
    env["SHUJAA_RUNNER"] = runner_name

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from apps.api.app import runner; "
                "print(type(runner).__name__)"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == expected_class


def test_invalid_runner_is_rejected():
    env = os.environ.copy()
    env["SHUJAA_RUNNER"] = "invalid"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import apps.api.app",
        ],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Unsupported SHUJAA_RUNNER" in result.stderr
