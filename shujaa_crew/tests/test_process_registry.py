from concurrent.futures import ThreadPoolExecutor

from core.runtime.process_registry import ProcessRegistry
from core.runtime.process_registry_contract import (
    ProcessOwnership,
    RegistrationDisposition,
)


def test_process_registry_supports_concurrent_writes(tmp_path):
    registry_path = tmp_path / "processes.json"

    def register_task(index: int):
        registry = ProcessRegistry(registry_path)
        return registry.register(
            ProcessOwnership(
                task_id=f"task-{index}",
                execution_id=f"exec-{index}",
                pid=1000 + index,
                pgid=2000 + index,
                process_start_time_ticks=3000 + index,
            )
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(
            executor.map(register_task, range(20))
        )

    assert all(
        result.disposition
        == RegistrationDisposition.REGISTERED
        for result in results
    )

    registry = ProcessRegistry(registry_path)
    data = registry.all()

    assert len(data) == 20

    for index in range(20):
        assert data[f"task-{index}"] == ProcessOwnership(
            task_id=f"task-{index}",
            execution_id=f"exec-{index}",
            pid=1000 + index,
            pgid=2000 + index,
            process_start_time_ticks=3000 + index,
        )
