from __future__ import annotations

from threading import Lock

from core.agents.executor_contract import AgentExecutorProtocol


class AgentExecutorRegistry:
    """يربط معرّفات الوكلاء بمُنفّذات قابلة للاستبدال."""

    def __init__(self) -> None:
        self._executors: dict[str, AgentExecutorProtocol] = {}
        self._lock = Lock()

    def register(
        self,
        agent_id: str,
        executor: AgentExecutorProtocol,
    ) -> None:
        normalized = agent_id.strip()

        if not normalized:
            raise ValueError("agent_id is required.")

        with self._lock:
            if normalized in self._executors:
                raise ValueError(
                    f"Executor already registered: {normalized}"
                )

            self._executors[normalized] = executor

    def get(
        self,
        agent_id: str,
    ) -> AgentExecutorProtocol | None:
        with self._lock:
            return self._executors.get(agent_id.strip())
