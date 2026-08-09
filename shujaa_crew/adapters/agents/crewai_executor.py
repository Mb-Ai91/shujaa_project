from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Task

from adapters.agents.crewai_definition_loader import CrewAIDefinitionLoader
from core.agents.models import AgentDefinition


class CrewAIAgentExecutor:
    """منفّذ وكلاء CrewAI داخل شجاع."""

    AGENT_SETTING_FIELDS = (
        "verbose",
        "allow_delegation",
        "max_iter",
        "max_rpm",
        "max_tokens",
        "memory",
        "respect_context_window",
        "max_retry_limit",
        "planning",
        "reasoning",
        "max_reasoning_attempts",
        "allow_code_execution",
        "code_execution_mode",
        "multimodal",
        "inject_date",
        "date_format",
        "use_system_prompt",
        "max_execution_time",
    )

    def __init__(
        self,
        agents_dir: str | Path = "agents",
        agent_factory: Callable[..., Any] = Agent,
        task_factory: Callable[..., Any] = Task,
        crew_factory: Callable[..., Any] = Crew,
    ) -> None:
        self.loader = CrewAIDefinitionLoader(
            agents_dir=agents_dir,
        )
        self.agent_factory = agent_factory
        self.task_factory = task_factory
        self.crew_factory = crew_factory

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

        self.loader.load(crewai_agent)

        return crewai_agent

    def load_crewai_definition(
        self,
        agent: AgentDefinition,
    ) -> dict[str, object]:
        crewai_agent = self.get_crewai_agent_name(agent)
        return self.loader.load(crewai_agent)

    def build_crewai_agent(
        self,
        agent: AgentDefinition,
    ) -> Any:
        definition = self.load_crewai_definition(agent)

        for field in ("role", "goal", "backstory"):
            value = definition.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Missing CrewAI agent field: {field}"
                )

        kwargs: dict[str, object] = {
            "role": definition["role"],
            "goal": definition["goal"],
            "backstory": definition["backstory"],
        }

        llm = definition.get("llm")

        if isinstance(llm, (str, dict)):
            kwargs["llm"] = llm

        settings = definition.get("settings")

        if not isinstance(settings, dict):
            settings = {}

        for field in self.AGENT_SETTING_FIELDS:
            if field in settings:
                kwargs[field] = settings[field]
            elif field in definition:
                kwargs[field] = definition[field]

        return self.agent_factory(**kwargs)

    def build_task(
        self,
        crewai_agent: Any,
        task: str,
    ) -> Any:
        normalized_task = task.strip()

        if not normalized_task:
            raise ValueError("Task is required.")

        return self.task_factory(
            description=normalized_task,
            expected_output=(
                "A complete and accurate result for the requested task."
            ),
            agent=crewai_agent,
        )

    def build_crew(
        self,
        crewai_agent: Any,
        crewai_task: Any,
    ) -> Any:
        return self.crew_factory(
            agents=[crewai_agent],
            tasks=[crewai_task],
            verbose=False,
            memory=False,
        )

    def execute(
        self,
        agent: AgentDefinition,
        task: str,
    ) -> str:
        crewai_agent = self.build_crewai_agent(agent)
        crewai_task = self.build_task(crewai_agent, task)
        crew = self.build_crew(
            crewai_agent,
            crewai_task,
        )

        result = crew.kickoff()

        return str(result)
