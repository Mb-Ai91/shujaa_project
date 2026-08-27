from pathlib import Path

import pytest

from tools.owner_constraint_validator import (
    ProposedCodespaceAction,
    validate_action,
)


REGISTRY = (
    Path(__file__).resolve().parents[1]
    / "SHUJAA_OWNER_CONSTRAINTS.yaml"
)
RG = "".join(("r", "g"))
RIPGREP = "".join(("rip", "grep"))
SCOPED = {
    "search_read_only": True,
    "search_within_workspace": True,
    "search_within_task_scope": True,
    "search_targets_sensitive": False,
}


@pytest.mark.parametrize(
    ("command", "evidence", "expected_gate"),
    [
        (f"{RG} needle core", {}, "HOLD"),
        (f"{RG} needle core", SCOPED, "GO"),
        (f"{RIPGREP} needle core", SCOPED, "GO"),
        (f"/usr/bin/{RG} needle core", SCOPED, "GO"),
        (
            f"{RG} needle core",
            {**SCOPED, "search_read_only": False},
            "HOLD",
        ),
        (
            f"{RG} needle core",
            {**SCOPED, "search_within_workspace": False},
            "HOLD",
        ),
        (
            f"{RG} needle core",
            {**SCOPED, "search_within_task_scope": False},
            "HOLD",
        ),
        (
            f"{RG} needle core",
            {**SCOPED, "search_targets_sensitive": True},
            "HOLD",
        ),
        (f"{RG} --pre python needle core", SCOPED, "HOLD"),
        (f"{RG} --pre=python needle core", SCOPED, "HOLD"),
    ],
)
def test_rg_requires_scoped_read_only_evidence(
    command,
    evidence,
    expected_gate,
):
    result = validate_action(
        REGISTRY,
        ProposedCodespaceAction(
            command=command,
            **evidence,
        ),
    )

    assert result.gate == expected_gate
    if expected_gate == "HOLD":
        assert result.reason_ids == ("SC-TOOL-001",)
    else:
        assert result.reason_ids == ()
