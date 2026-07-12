from typing import Any, Dict, List, Optional

from .state import Event


def worker_spawned(task_id: str, model: str = "default") -> Event:
    return Event("WorkerSpawnedEvent", {"task_id": task_id, "model": model})


def artifact_generated(task_id: str, artifact: str) -> Event:
    return Event("ArtifactGeneratedEvent", {"task_id": task_id, "artifact": artifact})


def task_failed(
    task_id: str, critique: str, failure_context: Optional[Dict[str, Any]] = None
) -> Event:
    payload: Dict[str, Any] = {"task_id": task_id, "critique": critique}
    if failure_context is not None:
        payload["failure_context"] = failure_context
    return Event("TaskFailedEvent", payload)


def circuit_breaker_tripped(task_id: str, critiques: List[str]) -> Event:
    return Event(
        "CircuitBreakerTrippedEvent",
        {"task_id": task_id, "critiques": list(critiques)},
    )
