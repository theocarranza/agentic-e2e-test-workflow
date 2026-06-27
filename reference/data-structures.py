from dataclasses import dataclass, replace
from enum import Enum
from typing import List, Optional, Tuple

class TaskState(Enum):
    BLOCKED = "blocked"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED_REQUIRES_REVIEW = "blocked_requires_review"

@dataclass(frozen=True)
class Task:
    id: str
    state: TaskState
    dependencies: Tuple[str, ...] = ()  # Tuple used for immutability instead of List
    retry_count: int = 0
    critiques: Tuple[str, ...] = ()

@dataclass(frozen=True)
class QueueState:
    tasks: Tuple[Task, ...]
    
    # Helper to find a task by ID without mutating
    def get_task(self, task_id: str) -> Optional[Task]:
        return next((t for t in self.tasks if t.id == task_id), None)