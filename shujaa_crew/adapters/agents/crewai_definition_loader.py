from __future__ import annotations

import json
import re
from pathlib import Path


class CrewAIDefinitionLoader:
    """تحميل تعريف وكيل CrewAI من ملف JSONC بشكل محلي."""

    def __init__(
        self,
        agents_dir: str | Path = "agents",
    ) -> None:
        self.agents_dir = Path(agents_dir)

    def load(self, agent_name: str) -> dict[str, object]:
        path = self.agents_dir / f"{agent_name}.jsonc"

        if not path.is_file():
            raise ValueError(
                f"CrewAI agent definition not found: {agent_name}"
            )

        text = path.read_text(encoding="utf-8")

        # إزالة تعليقات // مع الحفاظ على النصوص بين علامات الاقتباس.
        text = re.sub(
            r'(^|[^:])//.*$',
            r'\1',
            text,
            flags=re.MULTILINE,
        )

        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid CrewAI agent definition: {agent_name}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                f"CrewAI agent definition must be an object: {agent_name}"
            )

        return data
