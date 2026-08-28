"""Validate proposed Codespace actions against owner constraints."""

from __future__ import annotations

import argparse
import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


_REQUIRED_CONSTRAINT_IDS = frozenset(
    {
        "SC-ASSUME-001",
        "SC-OWNER-001",
        "SC-TOOL-001",
        "SC-OUTPUT-001",
        "SC-SAVE-001",
        "SC-PROPOSAL-001",
        "SC-COMPLETION-001",
        "SC-STATE-001",
    }
)

_ARTIFACT_STATES = (
    "GENERATED",
    "WRITTEN_TO_CODESPACE",
    "TRACKED",
    "COMMITTED",
    "PUSHED",
    "VERIFIED",
)

_COVERAGE_STATES = frozenset(
    {
        "VERIFIED",
        "PARTIAL",
        "NOT IMPLEMENTED",
        "BLOCKED",
    }
)

_REQUIRED_CONSTRAINT_FIELDS = frozenset(
    {
        "id",
        "status",
        "scope",
        "deny",
        "allowed_alternative",
        "authority",
        "reason",
    }
)

_COMMAND_SEPARATOR = re.compile(r"(?:&&|\|\||[;|\n])")
_STATE_ROW = re.compile(
    r"^\|\s*([A-Z][A-Z0-9_]*)\s*\|\s*(.*?)\s*\|\s*$"
)
_HANDOFF_STATE_BEGIN = "<!-- SHUJAA_CURRENT_STATE_BEGIN -->"
_HANDOFF_STATE_END = "<!-- SHUJAA_CURRENT_STATE_END -->"
_ROADMAP_STATE_BEGIN = (
    "<!-- SHUJAA_CURRENT_STATE_MIRROR_BEGIN -->"
)
_ROADMAP_STATE_END = (
    "<!-- SHUJAA_CURRENT_STATE_MIRROR_END -->"
)
_MIRRORED_STATE_FIELDS = (
    "CURRENT_STAGE",
    "CURRENT_SLICE",
    "SLICE_STATUS",
)


@dataclass(frozen=True)
class ProposedCodespaceAction:
    command: str
    owner_scope: str = "stabilization"
    action_scope: str = "stabilization"
    instruction_conflict: bool = False
    output_is_oversized: bool = False
    output_to_file: bool = False
    claims_save_complete: bool = False
    save_receipt_complete: bool = False
    proposal_approved: bool = True
    evidence_verified: bool = True
    search_read_only: bool = False
    search_within_workspace: bool = False
    search_within_task_scope: bool = False
    search_targets_sensitive: bool = True


@dataclass(frozen=True)
class ValidationResult:
    gate: str
    reason_ids: tuple[str, ...]


@dataclass(frozen=True)
class CompletionReceipt:
    state: str
    path: str | None = None
    content_verified: bool = False
    git_required: bool = True
    tracked: bool = False
    commit_hash: str | None = None
    pushed: bool = False
    local_head: str | None = None
    remote_head: str | None = None
    is_test_claim: bool = False
    test_count: int | None = None
    test_exit_code: int | None = None
    is_audit_verdict: bool = False
    source_artifact: str | None = None
    evidence_references: tuple[str, ...] = ()
    verdict_persisted: bool = False
    is_large_round: bool = False
    independent_codespace_verification: bool = False
    requested_items: tuple[str, ...] = ()
    coverage: tuple[str, ...] = ()


@dataclass(frozen=True)
class StateClosureRequest:
    handoff_path: Path
    roadmap_path: Path
    closure_requested: bool = False


def _load_registry(
    registry_path: Path,
) -> Mapping[str, Mapping[str, object]]:
    content = registry_path.read_text(encoding="utf-8")
    data = json.loads(content)

    if data.get("schema_version") != 1:
        raise ValueError("unsupported schema version")

    constraints = data.get("constraints")
    if not isinstance(constraints, list):
        raise ValueError("constraints must be a list")

    indexed: dict[str, Mapping[str, object]] = {}

    for constraint in constraints:
        if not isinstance(constraint, dict):
            raise ValueError("constraint must be an object")

        if not _REQUIRED_CONSTRAINT_FIELDS.issubset(constraint):
            raise ValueError("constraint fields are incomplete")

        constraint_id = constraint["id"]
        if not isinstance(constraint_id, str):
            raise ValueError("constraint id must be a string")

        if constraint_id in indexed:
            raise ValueError("duplicate constraint id")

        if not isinstance(constraint["deny"], list):
            raise ValueError("deny must be a list")

        if not isinstance(
            constraint["allowed_alternative"],
            list,
        ):
            raise ValueError(
                "allowed_alternative must be a list"
            )

        indexed[constraint_id] = constraint

    if set(indexed) != _REQUIRED_CONSTRAINT_IDS:
        raise ValueError("constraint set mismatch")

    return indexed


def _is_active(
    constraints: Mapping[str, Mapping[str, object]],
    constraint_id: str,
) -> bool:
    return (
        constraints[constraint_id].get("status")
        == "active"
    )


def _marker_block(
    content: str,
    begin_marker: str,
    end_marker: str,
) -> str:
    if (
        content.count(begin_marker) != 1
        or content.count(end_marker) != 1
    ):
        raise ValueError("state markers must be unique")

    before, block_and_after = content.split(begin_marker, 1)
    del before
    block, after = block_and_after.split(end_marker, 1)
    del after
    return block


def _normalize_state_value(value: str) -> str:
    normalized = value.strip()
    if (
        len(normalized) >= 2
        and normalized[0] == "`"
        and normalized[-1] == "`"
    ):
        return normalized[1:-1].strip()
    return normalized


def _read_state_fields(
    path: Path,
    begin_marker: str,
    end_marker: str,
    required_fields: Sequence[str],
) -> Mapping[str, str]:
    content = path.read_text(encoding="utf-8")
    block = _marker_block(content, begin_marker, end_marker)
    fields: dict[str, str] = {}

    for line in block.splitlines():
        match = _STATE_ROW.match(line)
        if match is None:
            continue
        key, raw_value = match.groups()
        if key in fields:
            raise ValueError("duplicate state field")
        fields[key] = _normalize_state_value(raw_value)

    if any(not fields.get(key) for key in required_fields):
        raise ValueError("required state field missing")
    return fields


def _invoked_commands(command: str) -> tuple[str, ...]:
    invoked: list[str] = []

    for segment in _COMMAND_SEPARATOR.split(command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            continue

        while tokens and "=" in tokens[0]:
            name, _, _ = tokens[0].partition("=")
            if not name.isidentifier():
                break
            tokens.pop(0)

        if not tokens:
            continue

        invoked.append(Path(tokens[0]).name)

    return tuple(invoked)


def _forbidden_tool_invoked(
    command: str,
    denied_tools: Iterable[object],
) -> bool:
    denied = {
        item
        for item in denied_tools
        if isinstance(item, str)
    }
    return bool(
        denied.intersection(_invoked_commands(command))
    )


def _conditional_tool_policy_violated(
    command: str,
    conditional_rules: object,
    action: ProposedCodespaceAction,
) -> bool:
    if not isinstance(conditional_rules, list):
        return True

    evidence = {
        "search_read_only": action.search_read_only,
        "search_within_workspace": (
            action.search_within_workspace
        ),
        "search_within_task_scope": (
            action.search_within_task_scope
        ),
        "no_sensitive_targets": (
            not action.search_targets_sensitive
        ),
    }

    for segment in _COMMAND_SEPARATOR.split(command):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            return True

        while tokens and "=" in tokens[0]:
            name, _, _ = tokens[0].partition("=")
            if not name.isidentifier():
                break
            tokens.pop(0)

        if not tokens:
            continue

        invoked = Path(tokens[0]).name

        for rule in conditional_rules:
            if not isinstance(rule, Mapping):
                return True

            commands = rule.get("commands")
            required = rule.get("required_evidence")
            denied_options = rule.get("deny_options")

            if not all(
                isinstance(items, list)
                for items in (
                    commands,
                    required,
                    denied_options,
                )
            ):
                return True

            if invoked not in commands:
                continue

            if any(
                token == option
                or token.startswith(f"{option}=")
                for token in tokens[1:]
                for option in denied_options
            ):
                return True

            if any(
                not evidence.get(requirement, False)
                for requirement in required
            ):
                return True

    return False


def validate_action(
    registry_path: Path,
    action: ProposedCodespaceAction,
) -> ValidationResult:
    try:
        constraints = _load_registry(registry_path)
    except FileNotFoundError:
        return ValidationResult(
            gate="HOLD",
            reason_ids=("MISSING_REGISTRY",),
        )
    except (OSError, json.JSONDecodeError, ValueError):
        return ValidationResult(
            gate="HOLD",
            reason_ids=("INVALID_REGISTRY",),
        )

    reasons: list[str] = []

    tool_constraint = constraints["SC-TOOL-001"]

    if (
        _is_active(constraints, "SC-TOOL-001")
        and (
            _forbidden_tool_invoked(
                action.command,
                tool_constraint["deny"],
            )
            or (
                "conditional_allow" in tool_constraint
                and _conditional_tool_policy_violated(
                    action.command,
                    tool_constraint["conditional_allow"],
                    action,
                )
            )
        )
    ):
        reasons.append("SC-TOOL-001")

    if _is_active(constraints, "SC-OWNER-001"):
        if action.instruction_conflict:
            reasons.append("SC-OWNER-001")
        elif action.action_scope != action.owner_scope:
            reasons.append("SC-OWNER-001")

    if (
        _is_active(constraints, "SC-OUTPUT-001")
        and action.output_is_oversized
        and not action.output_to_file
    ):
        reasons.append("SC-OUTPUT-001")

    if (
        _is_active(constraints, "SC-SAVE-001")
        and action.claims_save_complete
        and not action.save_receipt_complete
    ):
        reasons.append("SC-SAVE-001")

    if (
        _is_active(constraints, "SC-PROPOSAL-001")
        and not action.proposal_approved
    ):
        reasons.append("SC-PROPOSAL-001")

    if (
        _is_active(constraints, "SC-ASSUME-001")
        and not action.evidence_verified
    ):
        reasons.append("SC-ASSUME-001")

    unique_reasons = tuple(dict.fromkeys(reasons))

    return ValidationResult(
        gate="HOLD" if unique_reasons else "GO",
        reason_ids=unique_reasons,
    )


def validate_batch(
    registry_path: Path,
    actions: Sequence[ProposedCodespaceAction],
) -> tuple[ValidationResult, ...]:
    return tuple(
        validate_action(registry_path, action)
        for action in actions
    )


def validate_completion_receipt(
    registry_path: Path,
    receipt: CompletionReceipt,
) -> ValidationResult:
    try:
        constraints = _load_registry(registry_path)
    except FileNotFoundError:
        return ValidationResult(
            gate="HOLD",
            reason_ids=("MISSING_REGISTRY",),
        )
    except (OSError, json.JSONDecodeError, ValueError):
        return ValidationResult(
            gate="HOLD",
            reason_ids=("INVALID_REGISTRY",),
        )

    if not _is_active(constraints, "SC-COMPLETION-001"):
        return ValidationResult(
            gate="HOLD",
            reason_ids=("SC-COMPLETION-001",),
        )

    reasons: list[str] = []

    if receipt.state not in _ARTIFACT_STATES:
        reasons.append("INVALID_ARTIFACT_STATE")
        state_index = -1
    else:
        state_index = _ARTIFACT_STATES.index(receipt.state)

    if state_index >= 1:
        if not receipt.path or not receipt.content_verified:
            reasons.append("INCOMPLETE_SAVE_RECEIPT")

    if state_index >= 2 and receipt.git_required:
        if not receipt.tracked:
            reasons.append("UNVERIFIED_TRACKED_STATE")

    if state_index >= 3 and not receipt.commit_hash:
        reasons.append("UNVERIFIED_COMMITTED_STATE")

    if state_index >= 4:
        if not receipt.pushed:
            reasons.append("UNVERIFIED_PUSHED_STATE")
        if not receipt.local_head or not receipt.remote_head:
            reasons.append("INCOMPLETE_PUSH_RECEIPT")
        elif receipt.local_head != receipt.remote_head:
            reasons.append("LOCAL_REMOTE_MISMATCH")

    if receipt.is_test_claim:
        if receipt.test_count is None or receipt.test_exit_code is None:
            reasons.append("INCOMPLETE_TEST_RECEIPT")
        elif state_index == 5 and receipt.test_exit_code != 0:
            reasons.append("FAILED_TEST_RECEIPT")

    if receipt.is_audit_verdict:
        if (
            not receipt.source_artifact
            or not receipt.evidence_references
            or not receipt.verdict_persisted
        ):
            reasons.append("INCOMPLETE_AUDIT_VERDICT_RECEIPT")

    if (
        receipt.is_large_round
        and state_index == 5
        and not receipt.independent_codespace_verification
    ):
        reasons.append("MISSING_INDEPENDENT_VERIFICATION")

    if receipt.requested_items or receipt.coverage:
        if len(receipt.requested_items) != len(receipt.coverage):
            reasons.append("INCOMPLETE_REQUEST_COVERAGE")
        elif any(
            status not in _COVERAGE_STATES
            for status in receipt.coverage
        ):
            reasons.append("INVALID_COVERAGE_STATE")

    unique_reasons = tuple(dict.fromkeys(reasons))
    return ValidationResult(
        gate="HOLD" if unique_reasons else "GO",
        reason_ids=unique_reasons,
    )


def validate_state_closure(
    registry_path: Path,
    request: StateClosureRequest,
) -> ValidationResult:
    try:
        constraints = _load_registry(registry_path)
    except FileNotFoundError:
        return ValidationResult(
            gate="HOLD",
            reason_ids=("MISSING_REGISTRY",),
        )
    except (OSError, json.JSONDecodeError, ValueError):
        return ValidationResult(
            gate="HOLD",
            reason_ids=("INVALID_REGISTRY",),
        )

    try:
        handoff = _read_state_fields(
            request.handoff_path,
            _HANDOFF_STATE_BEGIN,
            _HANDOFF_STATE_END,
            (*_MIRRORED_STATE_FIELDS, "EVIDENCE_REFERENCES"),
        )
        roadmap = _read_state_fields(
            request.roadmap_path,
            _ROADMAP_STATE_BEGIN,
            _ROADMAP_STATE_END,
            _MIRRORED_STATE_FIELDS,
        )
    except FileNotFoundError:
        return ValidationResult(
            gate="HOLD",
            reason_ids=("MISSING_STATE_SOURCE",),
        )
    except (OSError, ValueError):
        return ValidationResult(
            gate="HOLD",
            reason_ids=("INVALID_STATE_SOURCE",),
        )

    if not _is_active(constraints, "SC-STATE-001"):
        return ValidationResult(
            gate="HOLD",
            reason_ids=("SC-STATE-001",),
        )

    reasons: list[str] = []
    mismatched = tuple(
        field
        for field in _MIRRORED_STATE_FIELDS
        if handoff[field] != roadmap[field]
    )
    if mismatched:
        reasons.extend(
            (
                "CLOSURE_WITH_ACTIVE_STATE_DRIFT",
                "STALE_AUTHORITATIVE_MIRROR",
            )
        )

    handoff_status = handoff["SLICE_STATUS"]
    roadmap_status = roadmap["SLICE_STATUS"]
    statuses = (handoff_status, roadmap_status)
    if (
        any("VERIFIED COMPLETE" in value for value in statuses)
        and any("RED NOT STARTED" in value for value in statuses)
    ):
        reasons.append("VERIFIED_COMPLETE_WITH_RED_NOT_STARTED")

    evidence = handoff["EVIDENCE_REFERENCES"].strip().upper()
    closure_claimed = request.closure_requested or (
        "VERIFIED COMPLETE" in handoff_status
    )
    if closure_claimed and evidence in {"", "NONE", "NOT FOUND"}:
        reasons.append("UNREFERENCED_REQUIRED_EVIDENCE")

    unique_reasons = tuple(dict.fromkeys(reasons))
    return ValidationResult(
        gate="HOLD" if unique_reasons else "GO",
        reason_ids=unique_reasons,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one proposed Codespace action."
        )
    )
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument(
        "--owner-scope",
        default="stabilization",
    )
    parser.add_argument("--action-scope")
    parser.add_argument(
        "--instruction-conflict",
        action="store_true",
    )
    parser.add_argument(
        "--output-is-oversized",
        action="store_true",
    )
    parser.add_argument(
        "--output-to-file",
        action="store_true",
    )
    parser.add_argument(
        "--claims-save-complete",
        action="store_true",
    )
    parser.add_argument(
        "--save-receipt-complete",
        action="store_true",
    )
    parser.add_argument(
        "--unapproved-proposal",
        action="store_true",
    )
    parser.add_argument(
        "--unknown-evidence",
        action="store_true",
    )
    parser.add_argument(
        "--search-read-only",
        action="store_true",
    )
    parser.add_argument(
        "--search-within-workspace",
        action="store_true",
    )
    parser.add_argument(
        "--search-within-task-scope",
        action="store_true",
    )
    parser.add_argument(
        "--no-sensitive-search-targets",
        action="store_true",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    action_scope = (
        args.action_scope
        if args.action_scope is not None
        else args.owner_scope
    )

    result = validate_action(
        args.registry,
        ProposedCodespaceAction(
            command=args.command,
            owner_scope=args.owner_scope,
            action_scope=action_scope,
            instruction_conflict=(
                args.instruction_conflict
            ),
            output_is_oversized=(
                args.output_is_oversized
            ),
            output_to_file=args.output_to_file,
            claims_save_complete=(
                args.claims_save_complete
            ),
            save_receipt_complete=(
                args.save_receipt_complete
            ),
            proposal_approved=(
                not args.unapproved_proposal
            ),
            evidence_verified=(
                not args.unknown_evidence
            ),
            search_read_only=args.search_read_only,
            search_within_workspace=(
                args.search_within_workspace
            ),
            search_within_task_scope=(
                args.search_within_task_scope
            ),
            search_targets_sensitive=(
                not args.no_sensitive_search_targets
            ),
        ),
    )

    print(f"OWNER_CONSTRAINT_GATE={result.gate}")
    print(
        "OWNER_CONSTRAINT_REASONS="
        + (
            ",".join(result.reason_ids)
            if result.reason_ids
            else "NONE"
        )
    )
    return 0 if result.gate == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
