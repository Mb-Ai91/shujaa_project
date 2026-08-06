from __future__ import annotations

from adapters.crewai.runner import CrewAIRunner


class ShujaaManager:
    """الطبقة المركزية لاستقبال المهام وتوجيهها."""

    MAX_COMMAND_LENGTH = 4000

    def __init__(self, crew_runner: CrewAIRunner | None = None) -> None:
        self.crew_runner = crew_runner or CrewAIRunner()

    def submit(self, command: object) -> dict[str, object]:
        if not isinstance(command, str):
            raise ValueError("يجب أن يكون الأمر نصاً.")

        command = command.strip()

        if not command:
            raise ValueError("الأمر فارغ.")

        if len(command) > self.MAX_COMMAND_LENGTH:
            raise ValueError("الأمر أطول من الحد المسموح.")

        process_id = self.crew_runner.start(command)

        return {
            "status": "accepted",
            "process_id": process_id,
            "message": "استلم المدير شجاع المهمة ووجّهها للتنفيذ.",
        }
