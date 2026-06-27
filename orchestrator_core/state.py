from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class TaskState(Enum):
    READY = "Ready"
    IN_PROGRESS = "In_Progress"
    COMPLETED = "Completed"
    BLOCKED = "Blocked"
    BLOCKED_REQUIRES_REVIEW = "Blocked_Requires_Review"

class StageMode(Enum):
    NOVO = "novo"
    ATUALIZACAO = "atualizacao"
    RESUME = "resume"
    EXTEND = "extend"

@dataclass(frozen=True)
class Task:
    """Represents a workflow stage (0-Discovery, 1-Plan, 2-Blueprint, 3-Implementer)."""
    id: str  # e.g., "stage_0"
    skill_name: str
    state: TaskState = TaskState.READY
    mode: StageMode = StageMode.NOVO
    dependencies: List[str] = field(default_factory=list)
    critiques: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    output: Optional[Any] = None

@dataclass(frozen=True)
class WorkflowTarget:
    module: str  # e.g., "attendance"
    flow: Optional[str] = None  # e.g., "archive student"
    dry_run: bool = False
    approval_mode: str = "auto" # "auto" or "manual"

@dataclass(frozen=True)
class QueueState:
    target: WorkflowTarget
    tasks: Dict[str, Task] = field(default_factory=dict)
    events_history: List['Event'] = field(default_factory=list)

@dataclass(frozen=True)
class Event:
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
