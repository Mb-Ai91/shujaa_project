from concurrent.futures import ThreadPoolExecutor

from core.runtime.process_registry import ProcessRegistry


def test_process_registry_supports_concurrent_writes(tmp_path):
    registry_path = tmp_path / "processes.json"

    def register_task(index: int) -> None:
        registry = ProcessRegistry(registry_path)
        registry.register(
            task_id=f"task-{index}",
            pid=1000 + index,
            pgid=2000 + index,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(register_task, range(20)))

    registry = ProcessRegistry(registry_path)
    data = registry.all()

    assert len(data) == 20

    for index in range(20):
        assert data[f"task-{index}"] == {
            "pid": 1000 + index,
            "pgid": 2000 + index,
        }
