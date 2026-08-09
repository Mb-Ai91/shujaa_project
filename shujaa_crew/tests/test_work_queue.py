import pytest

from core.work.queue import InMemoryWorkQueue


def test_queue_dequeues_higher_priority_first():
    queue = InMemoryWorkQueue()

    queue.enqueue("work-low", priority=1)
    queue.enqueue("work-high", priority=10)
    queue.enqueue("work-medium", priority=5)

    assert queue.list() == [
        "work-high",
        "work-medium",
        "work-low",
    ]


def test_queue_preserves_fifo_for_equal_priority():
    queue = InMemoryWorkQueue()

    queue.enqueue("work-1", priority=5)
    queue.enqueue("work-2", priority=5)
    queue.enqueue("work-3", priority=5)

    assert queue.dequeue() == "work-1"
    assert queue.dequeue() == "work-2"
    assert queue.dequeue() == "work-3"


def test_queue_rejects_duplicate_work():
    queue = InMemoryWorkQueue()

    queue.enqueue("work-1")

    with pytest.raises(ValueError):
        queue.enqueue("work-1")


def test_queue_supports_peek_remove_and_contains():
    queue = InMemoryWorkQueue()

    queue.enqueue("work-1")
    queue.enqueue("work-2")

    assert queue.peek() == "work-1"
    assert queue.contains("work-2") is True
    assert queue.remove("work-1") is True
    assert queue.peek() == "work-2"
    assert queue.remove("missing") is False


def test_empty_queue_returns_none():
    queue = InMemoryWorkQueue()

    assert queue.peek() is None
    assert queue.dequeue() is None
    assert len(queue) == 0
