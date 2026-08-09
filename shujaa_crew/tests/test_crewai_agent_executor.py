import pytest

from adapters.agents.crewai_executor import CrewAIAgentExecutor
from core.agents.models import AgentDefinition


def build_agent(
    executor_config=None,
) -> AgentDefinition:
    return AgentDefinition(
        agent_id="research-agent",
        name="Research Agent",
        description="Research agent.",
        capabilities=("research",),
        executor="crewai",
        executor_config=executor_config,
    )


def test_crewai_executor_reads_existing_agent_binding(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "senior_data_researcher.jsonc"
    ).write_text(
        "{}",
        encoding="utf-8",
    )

    executor = CrewAIAgentExecutor(
        agents_dir=agents_dir,
    )

    agent_name = executor.get_crewai_agent_name(
        build_agent(
            {
                "crewai_agent": "senior_data_researcher",
            }
        )
    )

    assert agent_name == "senior_data_researcher"


def test_crewai_executor_rejects_missing_config(tmp_path):
    executor = CrewAIAgentExecutor(
        agents_dir=tmp_path,
    )

    with pytest.raises(ValueError):
        executor.get_crewai_agent_name(
            build_agent()
        )


def test_crewai_executor_rejects_missing_agent_binding(tmp_path):
    executor = CrewAIAgentExecutor(
        agents_dir=tmp_path,
    )

    with pytest.raises(ValueError):
        executor.get_crewai_agent_name(
            build_agent({})
        )


def test_crewai_executor_rejects_unknown_definition(tmp_path):
    executor = CrewAIAgentExecutor(
        agents_dir=tmp_path,
    )

    with pytest.raises(ValueError):
        executor.get_crewai_agent_name(
            build_agent(
                {
                    "crewai_agent": "missing_agent",
                }
            )
        )
