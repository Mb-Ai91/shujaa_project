from __future__ import annotations

import json
from pathlib import Path

from core.agents.models import AgentDefinition


class AgentConfigLoader:
    """تحميل تعريفات الوكلاء من ملفات JSON مستقلة."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def load_all(self) -> list[AgentDefinition]:
        if not self.directory.exists():
            return []

        agents: list[AgentDefinition] = []
        seen_ids: set[str] = set()

        for path in sorted(self.directory.glob("*.json")):
            agent = self._load_file(path)

            if agent.agent_id in seen_ids:
                raise ValueError(
                    f"Duplicate agent_id: {agent.agent_id}"
                )

            seen_ids.add(agent.agent_id)
            agents.append(agent)

        return agents

    def _load_file(self, path: Path) -> AgentDefinition:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid agent configuration: {path.name}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                f"Agent configuration must be an object: {path.name}"
            )

        required = (
            "agent_id",
            "name",
            "description",
            "capabilities",
        )

        missing = [
            field
            for field in required
            if field not in data
        ]

        if missing:
            raise ValueError(
                f"Missing agent fields in {path.name}: "
                f"{', '.join(missing)}"
            )

        capabilities = data["capabilities"]

        if not isinstance(capabilities, list):
            raise ValueError(
                f"capabilities must be a list: {path.name}"
            )

        return AgentDefinition(
            agent_id=str(data["agent_id"]).strip(),
            name=str(data["name"]).strip(),
            description=str(data["description"]).strip(),
            capabilities=tuple(
                str(item).strip()
                for item in capabilities
                if str(item).strip()
            ),
            enabled=bool(data.get("enabled", True)),
        )
