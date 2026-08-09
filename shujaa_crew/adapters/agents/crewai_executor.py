from __future__ import annotations

from pathlib import Path

from core.agents.models import AgentDefinition


class CrewAIAgentExecutor:
    """منفّذ وكلاء CrewAI داخل شجاع."""

    def __init__(
        self,
        agents_dir: str | Path = "agents",
    ) -> None:
        self.agents_dir = Path(agents_dir)

    def get_crewai_agent_name(
        self,
        agent: AgentDefinition,
    ) -> str:
        config = agent.executor_config

        if not isinstance(config, dict):
            raise ValueError(
                f"Missing executor_config for agent: {agent.agent_id}"
            )

        crewai_agent = config.get("crewai_agent")

        if not isinstance(crewai_agent, str):
            raise ValueError(
                f"Missing crewai_agent for agent: {agent.agent_id}"
            )

        crewai_agent = crewai_agent.strip()

        if not crewai_agent:
            raise ValueError(
                f"Missing crewai_agent for agent: {agent.agent_id}"
            )

        definition_path = (
            self.agents_dir / f"{crewai_agent}.jsonc"
        )

        if not definition_path.is_file():
            raise ValueError(
                f"CrewAI agent definition not found: {crewai_agent}"
            )

        return crewai_agent

    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        self.get_crewai_agent_name(agent)

        raise NotImplementedError(
            "CrewAI agent execution is not wired yet."
        )
