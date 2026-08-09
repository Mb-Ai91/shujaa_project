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


def test_crewai_executor_loads_definition(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "sample_agent.jsonc"
    ).write_text(
        '''
        {
          "role": "Sample Agent",
          "goal": "Test goal",
          "backstory": "Test backstory"
        }
        ''',
        encoding="utf-8",
    )

    executor = CrewAIAgentExecutor(
        agents_dir=agents_dir,
    )

    definition = executor.load_crewai_definition(
        build_agent(
            {
                "crewai_agent": "sample_agent",
            }
        )
    )

    assert definition["role"] == "Sample Agent"
    assert definition["goal"] == "Test goal"
    assert definition["backstory"] == "Test backstory"


def test_crewai_executor_builds_agent_without_external_call(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "sample_agent.jsonc"
    ).write_text(
        '''
        {
          "role": "Sample Agent",
          "goal": "Test goal",
          "backstory": "Test backstory",
          "llm": "test-provider/test-model",
          "settings": {
            "verbose": false,
            "max_iter": 4
          }
        }
        ''',
        encoding="utf-8",
    )

    captured = {}

    def fake_agent_factory(**kwargs):
        captured.update(kwargs)
        return kwargs

    executor = CrewAIAgentExecutor(
        agents_dir=agents_dir,
        agent_factory=fake_agent_factory,
    )

    result = executor.build_crewai_agent(
        build_agent(
            {
                "crewai_agent": "sample_agent",
            }
        )
    )

    assert result["role"] == "Sample Agent"
    assert result["goal"] == "Test goal"
    assert result["backstory"] == "Test backstory"
    assert result["llm"] == "test-provider/test-model"
    assert result["verbose"] is False
    assert result["max_iter"] == 4


def test_crewai_executor_rejects_incomplete_definition(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "broken_agent.jsonc"
    ).write_text(
        '''
        {
          "role": "Broken Agent"
        }
        ''',
        encoding="utf-8",
    )

    executor = CrewAIAgentExecutor(
        agents_dir=agents_dir,
        agent_factory=lambda **kwargs: kwargs,
    )

    with pytest.raises(ValueError):
        executor.build_crewai_agent(
            build_agent(
                {
                    "crewai_agent": "broken_agent",
                }
            )
        )


def test_crewai_executor_builds_task_and_crew(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "sample_agent.jsonc"
    ).write_text(
        '''
        {
          "role": "Sample Agent",
          "goal": "Test goal",
          "backstory": "Test backstory"
        }
        ''',
        encoding="utf-8",
    )

    created = {}

    def fake_agent_factory(**kwargs):
        created["agent"] = kwargs
        return "agent-object"

    def fake_task_factory(**kwargs):
        created["task"] = kwargs
        return "task-object"

    def fake_crew_factory(**kwargs):
        created["crew"] = kwargs
        return "crew-object"

    executor = CrewAIAgentExecutor(
        agents_dir=agents_dir,
        agent_factory=fake_agent_factory,
        task_factory=fake_task_factory,
        crew_factory=fake_crew_factory,
    )

    agent = build_agent(
        {
            "crewai_agent": "sample_agent",
        }
    )

    crewai_agent = executor.build_crewai_agent(agent)
    crewai_task = executor.build_task(
        crewai_agent,
        "perform test",
    )
    crew = executor.build_crew(
        crewai_agent,
        crewai_task,
    )

    assert crewai_agent == "agent-object"
    assert crewai_task == "task-object"
    assert crew == "crew-object"

    assert created["task"]["description"] == "perform test"
    assert created["task"]["agent"] == "agent-object"

    assert created["crew"]["agents"] == ["agent-object"]
    assert created["crew"]["tasks"] == ["task-object"]


def test_crewai_executor_executes_without_real_llm(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "sample_agent.jsonc"
    ).write_text(
        '''
        {
          "role": "Sample Agent",
          "goal": "Test goal",
          "backstory": "Test backstory"
        }
        ''',
        encoding="utf-8",
    )

    class FakeCrew:
        def kickoff(self):
            return "fake crew result"

    executor = CrewAIAgentExecutor(
        agents_dir=agents_dir,
        agent_factory=lambda **kwargs: "agent-object",
        task_factory=lambda **kwargs: "task-object",
        crew_factory=lambda **kwargs: FakeCrew(),
    )

    result = executor.execute(
        build_agent(
            {
                "crewai_agent": "sample_agent",
            }
        ),
        "perform test",
    )

    assert result == "fake crew result"
