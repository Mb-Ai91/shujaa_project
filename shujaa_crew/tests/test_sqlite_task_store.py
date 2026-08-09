import sqlite3

from adapters.storage.sqlite_task_store import SQLiteTaskStore
from core.tasks.store import TaskRecord


def test_sqlite_task_store_persists_task_between_instances(tmp_path):
    database_path = tmp_path / "tasks.db"

    first_store = SQLiteTaskStore(database_path)

    first_store.create(
        TaskRecord(
            task_id="persistent-task",
            command="test persistence",
            status="completed",
            work_id="work-123",
            result="saved result",
        )
    )

    second_store = SQLiteTaskStore(database_path)
    task = second_store.get("persistent-task")

    assert task is not None
    assert task.task_id == "persistent-task"
    assert task.command == "test persistence"
    assert task.status == "completed"
    assert task.work_id == "work-123"
    assert task.result == "saved result"


def test_sqlite_task_store_updates_task(tmp_path):
    database_path = tmp_path / "tasks.db"
    store = SQLiteTaskStore(database_path)

    store.create(
        TaskRecord(
            task_id="update-task",
            command="test update",
            status="queued",
        )
    )

    store.update(
        "update-task",
        status="completed",
        process_id=123,
        process_group_id=123,
        result="final result",
    )

    task = store.get("update-task")

    assert task is not None
    assert task.status == "completed"
    assert task.process_id == 123
    assert task.process_group_id == 123
    assert task.result == "final result"


def test_sqlite_task_store_migrates_legacy_database(tmp_path):
    database_path = tmp_path / "legacy.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE tasks (
                task_id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                status TEXT NOT NULL,
                process_id INTEGER,
                process_group_id INTEGER,
                error TEXT,
                result TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO tasks (
                task_id,
                command,
                status
            )
            VALUES (?, ?, ?)
            """,
            (
                "legacy-task",
                "legacy command",
                "completed",
            ),
        )

    store = SQLiteTaskStore(database_path)

    task = store.get("legacy-task")

    assert task is not None
    assert task.task_id == "legacy-task"
    assert task.work_id is None

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(tasks)"
            ).fetchall()
        }

    assert "work_id" in columns
