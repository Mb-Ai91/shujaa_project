from core.work.queue_contract import WorkQueueProtocol


class FakeWorkQueue:
    def __init__(self) -> None:
        self.items: list[str] = []

    def enqueue(
        self,
        work_id: str,
        *,
        priority: int = 0,
    ) -> None:
        self.items.append(work_id)

    def dequeue(self) -> str | None:
        if not self.items:
            return None
        return self.items.pop(0)

    def peek(self) -> str | None:
        if not self.items:
            return None
        return self.items[0]

    def remove(self, work_id: str) -> bool:
        if work_id not in self.items:
            return False
        self.items.remove(work_id)
        return True

    def contains(self, work_id: str) -> bool:
        return work_id in self.items

    def list(self) -> list[str]:
        return list(self.items)

    def __len__(self) -> int:
        return len(self.items)


def test_work_queue_contract_supports_queue_lifecycle():
    queue: WorkQueueProtocol = FakeWorkQueue()

    queue.enqueue("work-1")
    queue.enqueue("work-2", priority=10)

    assert queue.peek() == "work-1"
    assert queue.contains("work-2")
    assert queue.list() == ["work-1", "work-2"]
    assert len(queue) == 2

    assert queue.dequeue() == "work-1"
    assert queue.remove("work-2") is True
    assert queue.dequeue() is None
