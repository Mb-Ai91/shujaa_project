from adapters.agents.crewai_definition_loader import (
    CrewAIDefinitionLoader,
)


def test_crewai_definition_loader_reads_jsonc(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    (
        agents_dir / "sample_agent.jsonc"
    ).write_text(
        '''
        {
          // test comment
          "role": "Sample Agent",
          "goal": "Test goal",
          "backstory": "Test backstory",
          "llm": "mock/model"
        }
        ''',
        encoding="utf-8",
    )

    loader = CrewAIDefinitionLoader(
        agents_dir=agents_dir,
    )

    data = loader.load("sample_agent")

    assert data["role"] == "Sample Agent"
    assert data["goal"] == "Test goal"
    assert data["backstory"] == "Test backstory"
    assert data["llm"] == "mock/model"
