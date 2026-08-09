from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock

from core.tasks.store import TaskRecord


class SQLiteTaskStore:
    """مخزن دائم للمهام باستخدام SQLite."""

    def __init__(
        self,
        database_path: str | Path = ".runtime/tasks.db",
    ) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    work_id TEXT,
                    process_id INTEGER,
                    process_group_id INTEGER,
                    error TEXT,
                    result TEXT
                )
                """
            )

            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(tasks)"
                ).fetchall()
            }

            if "work_id" not in columns:
                connection.execute(
                    "ALTER TABLE tasks ADD COLUMN work_id TEXT"
                )

    def create(self, task: TaskRecord) -> None:
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO tasks (
                        task_id,
                        command,
                        status,
                        work_id,
                        process_id,
                        process_group_id,
                        error,
                        result
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.task_id,
                        task.command,
                        task.status,
                        task.work_id,
                        task.process_id,
                        task.process_group_id,
                        task.error,
                        task.result,
                    ),
                )

    def get(self, task_id: str) -> TaskRecord | None:
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        task_id,
                        command,
                        status,
                        work_id,
                        process_id,
                        process_group_id,
                        error,
                        result
                    FROM tasks
                    WHERE task_id = ?
                    """,
                    (task_id,),
                ).fetchone()

        if row is None:
            return None

        return TaskRecord(
            task_id=row["task_id"],
            command=row["command"],
            status=row["status"],
            work_id=row["work_id"],
            process_id=row["process_id"],
            process_group_id=row["process_group_id"],
            error=row["error"],
            result=row["result"],
        )

    def update(
        self,
        task_id: str,
        *,
        status: str,
        process_id: int | None = None,
        process_group_id: int | None = None,
        error: str | None = None,
        result: str | None = None,
    ) -> None:
        fields = ["status = ?"]
        values: list[object] = [status]

        if process_id is not None:
            fields.append("process_id = ?")
            values.append(process_id)

        if process_group_id is not None:
            fields.append("process_group_id = ?")
            values.append(process_group_id)

        if error is not None:
            fields.append("error = ?")
            values.append(error)

        if result is not None:
            fields.append("result = ?")
            values.append(result)

        values.append(task_id)

        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    f"""
                    UPDATE tasks
                    SET {", ".join(fields)}
                    WHERE task_id = ?
                    """,
                    values,
                )
