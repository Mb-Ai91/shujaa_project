import json
from pathlib import Path

import pytest

from tools.owner_constraint_validator import (
    CompletionReceipt,
    ProposedCodespaceAction,
    StateClosureRequest,
    validate_action,
    validate_batch,
    validate_completion_receipt,
    validate_state_closure,
)


@pytest.fixture
def registry_path(tmp_path):
    forbidden_short = "".join(("r", "g"))
    forbidden_long = "".join(("rip", "grep"))

    registry = {
        "schema_version": 1,
        "constraints": [
            {
                "id": "SC-ASSUME-001",
                "status": "active",
                "scope": "codespace-action",
                "deny": ["unknown_evidence"],
                "allowed_alternative": ["hold_and_verify"],
                "authority": "owner",
                "reason": "Unverified assumptions are denied.",
            },
            {
                "id": "SC-OWNER-001",
                "status": "active",
                "scope": "codespace-action",
                "deny": [
                    "instruction_conflict",
                    "scope_expansion",
                ],
                "allowed_alternative": [
                    "request_owner_approval",
                ],
                "authority": "owner",
                "reason": "Owner instructions and scope cannot be overridden.",
            },
            {
                "id": "SC-TOOL-001",
                "status": "active",
                "scope": "codespace-command",
                "deny": [
                    forbidden_short,
                    forbidden_long,
                ],
                "allowed_alternative": [
                    "grep",
                    "find",
                ],
                "authority": "owner",
                "reason": "Only approved search tools may be used.",
            },
            {
                "id": "SC-OUTPUT-001",
                "status": "active",
                "scope": "codespace-output",
                "deny": ["oversized_terminal_output"],
                "allowed_alternative": ["file_with_small_summary"],
                "authority": "owner",
                "reason": "Oversized output must be delivered through a file.",
            },
            {
                "id": "SC-SAVE-001",
                "status": "active",
                "scope": "save-claim",
                "deny": ["unverified_save_claim"],
                "allowed_alternative": ["complete_save_receipt"],
                "authority": "owner",
                "reason": "A save claim requires complete verification.",
            },
            {
                "id": "SC-PROPOSAL-001",
                "status": "active",
                "scope": "proposal-execution",
                "deny": ["unapproved_proposal_execution"],
                "allowed_alternative": ["explicit_owner_approval"],
                "authority": "owner",
                "reason": "A proposal is not execution authority.",
            },
            {
                "id": "SC-COMPLETION-001",
                "status": "active",
                "scope": "completion-claim",
                "deny": ["state_without_required_evidence"],
                "allowed_alternative": ["hold_not_verified"],
                "authority": "owner",
                "reason": "Completion claims require evidence.",
            },
            {
                "id": "SC-STATE-001",
                "status": "active",
                "scope": "state-closure",
                "deny": [
                    "closure_with_active_state_drift",
                    "stale_authoritative_mirror",
                    "unreferenced_required_evidence",
                ],
                "allowed_alternative": [
                    "reconcile_and_verify",
                    "closure_pending",
                ],
                "authority": "owner",
                "reason": "Closure requires synchronized state.",
            },
        ],
    }

    path = tmp_path / "SHUJAA_OWNER_CONSTRAINTS.yaml"
    path.write_text(
        json.dumps(registry),
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize(
    "tool_name",
    [
        "".join(("r", "g")),
        "".join(("rip", "grep")),
    ],
)
def test_forbidden_search_tools_are_held(
    registry_path,
    tool_name,
):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command=f"{tool_name} needle core",
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-TOOL-001" in result.reason_ids


@pytest.mark.parametrize("tool_name", ["grep", "find"])
def test_allowed_search_tools_can_pass(
    registry_path,
    tool_name,
):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command=f"{tool_name} needle core",
        ),
    )

    assert result.gate == "GO"
    assert result.reason_ids == ()


def test_missing_registry_fails_closed(tmp_path):
    result = validate_action(
        tmp_path / "missing.yaml",
        ProposedCodespaceAction(command="grep needle core"),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == ("MISSING_REGISTRY",)


def test_instruction_conflict_is_held(registry_path):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            instruction_conflict=True,
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-OWNER-001" in result.reason_ids


def test_scope_expansion_is_held(registry_path):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            owner_scope="stabilization",
            action_scope="stage5-production-code",
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-OWNER-001" in result.reason_ids


def test_oversized_terminal_output_is_held(
    registry_path,
):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            output_is_oversized=True,
            output_to_file=False,
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-OUTPUT-001" in result.reason_ids


def test_oversized_output_to_file_can_pass(
    registry_path,
):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            output_is_oversized=True,
            output_to_file=True,
        ),
    )

    assert result.gate == "GO"


def test_unverified_save_claim_is_held(registry_path):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            claims_save_complete=True,
            save_receipt_complete=False,
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-SAVE-001" in result.reason_ids


def test_unapproved_proposal_is_not_execution_authority(
    registry_path,
):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            proposal_approved=False,
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-PROPOSAL-001" in result.reason_ids


def test_unknown_evidence_is_held(registry_path):
    result = validate_action(
        registry_path,
        ProposedCodespaceAction(
            command="grep needle core",
            evidence_verified=False,
        ),
    )

    assert result.gate == "HOLD"
    assert "SC-ASSUME-001" in result.reason_ids


def test_batch_isolates_blocked_and_safe_items(
    registry_path,
):
    results = validate_batch(
        registry_path,
        (
            ProposedCodespaceAction(
                command="grep needle core",
                proposal_approved=False,
            ),
            ProposedCodespaceAction(
                command="find core -type f",
            ),
        ),
    )

    assert results[0].gate == "HOLD"
    assert results[1].gate == "GO"


def test_generated_artifact_does_not_imply_codespace_write(
    registry_path,
):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="WRITTEN_TO_CODESPACE",
            path="docs/report.md",
            content_verified=False,
        ),
    )

    assert result.gate == "HOLD"
    assert "INCOMPLETE_SAVE_RECEIPT" in result.reason_ids


def test_tracked_committed_and_pushed_are_distinct(
    registry_path,
):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="PUSHED",
            path="docs/report.md",
            content_verified=True,
            tracked=True,
            commit_hash="abc123",
            pushed=False,
        ),
    )

    assert result.gate == "HOLD"
    assert "UNVERIFIED_PUSHED_STATE" in result.reason_ids
    assert "INCOMPLETE_PUSH_RECEIPT" in result.reason_ids


def test_push_claim_requires_matching_heads(registry_path):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="PUSHED",
            path="docs/report.md",
            content_verified=True,
            tracked=True,
            commit_hash="abc123",
            pushed=True,
            local_head="abc123",
            remote_head="def456",
        ),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == ("LOCAL_REMOTE_MISMATCH",)


def test_test_claim_requires_count_and_exit_code(registry_path):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="GENERATED",
            is_test_claim=True,
            test_count=13,
        ),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == ("INCOMPLETE_TEST_RECEIPT",)


def test_audit_verdict_requires_provenance(registry_path):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="GENERATED",
            is_audit_verdict=True,
            source_artifact="audit.txt",
            evidence_references=("audit.txt:10-20",),
            verdict_persisted=False,
        ),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == (
        "INCOMPLETE_AUDIT_VERDICT_RECEIPT",
    )


def test_large_round_final_go_requires_independent_verification(
    registry_path,
):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="VERIFIED",
            path="docs/report.md",
            content_verified=True,
            tracked=True,
            commit_hash="abc123",
            pushed=True,
            local_head="abc123",
            remote_head="abc123",
            is_large_round=True,
        ),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == (
        "MISSING_INDEPENDENT_VERIFICATION",
    )


def test_multi_item_request_requires_complete_coverage(
    registry_path,
):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="GENERATED",
            requested_items=("one", "two"),
            coverage=("VERIFIED",),
        ),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == ("INCOMPLETE_REQUEST_COVERAGE",)


def test_complete_verified_receipt_can_pass(registry_path):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="VERIFIED",
            path="docs/report.md",
            content_verified=True,
            tracked=True,
            commit_hash="abc123",
            pushed=True,
            local_head="abc123",
            remote_head="abc123",
            is_test_claim=True,
            test_count=20,
            test_exit_code=0,
            is_audit_verdict=True,
            source_artifact="audit.txt",
            evidence_references=("audit.txt:10-20",),
            verdict_persisted=True,
            is_large_round=True,
            independent_codespace_verification=True,
            requested_items=("one", "two"),
            coverage=("VERIFIED", "PARTIAL"),
        ),
    )

    assert result.gate == "GO"
    assert result.reason_ids == ()


def test_verified_test_claim_rejects_nonzero_exit_code(
    registry_path,
):
    result = validate_completion_receipt(
        registry_path,
        CompletionReceipt(
            state="VERIFIED",
            path="tests/report.txt",
            content_verified=True,
            tracked=True,
            commit_hash="abc123",
            pushed=True,
            local_head="abc123",
            remote_head="abc123",
            is_test_claim=True,
            test_count=20,
            test_exit_code=1,
        ),
    )

    assert result.gate == "HOLD"
    assert result.reason_ids == ("FAILED_TEST_RECEIPT",)


def test_project_registry_persists_completion_policy():
    registry = json.loads(
        Path("SHUJAA_OWNER_CONSTRAINTS.yaml").read_text(
            encoding="utf-8"
        )
    )
    completion = next(
        item
        for item in registry["constraints"]
        if item["id"] == "SC-COMPLETION-001"
    )

    assert completion["artifact_states"] == [
        "GENERATED",
        "WRITTEN_TO_CODESPACE",
        "TRACKED",
        "COMMITTED",
        "PUSHED",
        "VERIFIED",
    ]
    assert completion["coverage_states"] == [
        "VERIFIED",
        "PARTIAL",
        "NOT IMPLEMENTED",
        "BLOCKED",
    ]
    assert completion["sandbox_is_not_codespace_evidence"] is True
    assert completion["missing_evidence_result"] == (
        "HOLD — NOT VERIFIED"
    )
    assert completion["documentation_update_cadence"] == [
        "milestone",
        "architecture_decision",
        "stage_state_change",
    ]


def _write_state_sources(
    tmp_path,
    *,
    handoff_status="IMPLEMENTED — CLOSURE PENDING",
    roadmap_status="IMPLEMENTED — CLOSURE PENDING",
    evidence="tests/targeted.txt; tests/full.txt",
    historical="",
):
    handoff = tmp_path / "SHUJAA_HANDOFF.md"
    roadmap = tmp_path / "SHUJAA_ACTIVE_ROADMAP.md"
    handoff.write_text(
        "\n".join(
            (
                "<!-- SHUJAA_CURRENT_STATE_BEGIN -->",
                "| الحقل | القيمة |",
                "|---|---|",
                "| CURRENT_STAGE | Stage 6 |",
                "| CURRENT_SLICE | Slice 6.6 |",
                f"| SLICE_STATUS | {handoff_status} |",
                f"| EVIDENCE_REFERENCES | {evidence} |",
                "<!-- SHUJAA_CURRENT_STATE_END -->",
                historical,
            )
        ),
        encoding="utf-8",
    )
    roadmap.write_text(
        "\n".join(
            (
                "<!-- SHUJAA_CURRENT_STATE_MIRROR_BEGIN -->",
                "| الحقل | القيمة |",
                "|---|---|",
                "| CURRENT_STAGE | Stage 6 |",
                "| CURRENT_SLICE | Slice 6.6 |",
                f"| SLICE_STATUS | {roadmap_status} |",
                "<!-- SHUJAA_CURRENT_STATE_MIRROR_END -->",
                historical,
            )
        ),
        encoding="utf-8",
    )
    return handoff, roadmap


def test_matching_closure_pending_state_can_pass(
    registry_path,
    tmp_path,
):
    handoff, roadmap = _write_state_sources(tmp_path)
    result = validate_state_closure(
        registry_path,
        StateClosureRequest(handoff, roadmap),
    )
    assert result.gate == "GO"
    assert result.reason_ids == ()


def test_state_mismatch_detects_stale_mirror(
    registry_path,
    tmp_path,
):
    handoff, roadmap = _write_state_sources(
        tmp_path,
        roadmap_status="APPROVED CONTRACT — RED NOT STARTED",
    )
    result = validate_state_closure(
        registry_path,
        StateClosureRequest(handoff, roadmap),
    )
    assert result.gate == "HOLD"
    assert result.reason_ids == (
        "CLOSURE_WITH_ACTIVE_STATE_DRIFT",
        "STALE_AUTHORITATIVE_MIRROR",
    )


def test_verified_complete_without_evidence_is_held(
    registry_path,
    tmp_path,
):
    handoff, roadmap = _write_state_sources(
        tmp_path,
        handoff_status="VERIFIED COMPLETE",
        roadmap_status="VERIFIED COMPLETE",
        evidence="NONE",
    )
    result = validate_state_closure(
        registry_path,
        StateClosureRequest(
            handoff,
            roadmap,
            closure_requested=True,
        ),
    )
    assert result.gate == "HOLD"
    assert result.reason_ids == (
        "UNREFERENCED_REQUIRED_EVIDENCE",
    )


def test_verified_complete_conflicting_with_red_is_explicit(
    registry_path,
    tmp_path,
):
    handoff, roadmap = _write_state_sources(
        tmp_path,
        handoff_status="VERIFIED COMPLETE",
        roadmap_status="APPROVED CONTRACT — RED NOT STARTED",
    )
    result = validate_state_closure(
        registry_path,
        StateClosureRequest(handoff, roadmap),
    )
    assert result.gate == "HOLD"
    assert result.reason_ids == (
        "CLOSURE_WITH_ACTIVE_STATE_DRIFT",
        "STALE_AUTHORITATIVE_MIRROR",
        "VERIFIED_COMPLETE_WITH_RED_NOT_STARTED",
    )


def test_historical_state_outside_markers_is_ignored(
    registry_path,
    tmp_path,
):
    handoff, roadmap = _write_state_sources(
        tmp_path,
        historical="Historical: RED NOT STARTED",
    )
    result = validate_state_closure(
        registry_path,
        StateClosureRequest(handoff, roadmap),
    )
    assert result.gate == "GO"


def test_missing_state_markers_fail_closed(
    registry_path,
    tmp_path,
):
    handoff = tmp_path / "SHUJAA_HANDOFF.md"
    roadmap = tmp_path / "SHUJAA_ACTIVE_ROADMAP.md"
    handoff.write_text("CURRENT_SLICE=Slice 6.6", encoding="utf-8")
    roadmap.write_text("CURRENT_SLICE=Slice 6.6", encoding="utf-8")
    result = validate_state_closure(
        registry_path,
        StateClosureRequest(handoff, roadmap),
    )
    assert result.gate == "HOLD"
    assert result.reason_ids == ("INVALID_STATE_SOURCE",)


def test_project_registry_persists_state_policy():
    registry = json.loads(
        Path("SHUJAA_OWNER_CONSTRAINTS.yaml").read_text(
            encoding="utf-8"
        )
    )
    state = next(
        item
        for item in registry["constraints"]
        if item["id"] == "SC-STATE-001"
    )
    assert state["deny"] == [
        "closure_with_active_state_drift",
        "stale_authoritative_mirror",
        "unreferenced_required_evidence",
    ]
    assert state["allowed_alternative"] == [
        "reconcile_and_verify",
        "closure_pending",
    ]


def test_project_state_sources_are_synchronized():
    project_root = Path(__file__).resolve().parents[2]
    result = validate_state_closure(
        project_root
        / "shujaa_crew"
        / "SHUJAA_OWNER_CONSTRAINTS.yaml",
        StateClosureRequest(
            project_root / "docs" / "SHUJAA_HANDOFF.md",
            project_root / "docs" / "SHUJAA_ACTIVE_ROADMAP.md",
        ),
    )

    assert result.gate == "GO"
    assert result.reason_ids == ()
