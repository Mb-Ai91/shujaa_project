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


@dataclass(frozen=True)
class ValidationResult:
    gate: str
    reason_ids: tuple[str, ...]


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

    if (
        _is_active(constraints, "SC-TOOL-001")
        and _forbidden_tool_invoked(
            action.command,
            constraints["SC-TOOL-001"]["deny"],
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
