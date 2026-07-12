import unittest

from orchestrator_core.events import (
    artifact_generated,
    circuit_breaker_tripped,
    worker_spawned,
)
from orchestrator_core.main import init_workflow
from orchestrator_core.meta_agent import propose_instruction_update
from orchestrator_core.reducers import reduce_queue_state
from orchestrator_core.state import Event, TaskState


class EventsAndReducersTests(unittest.TestCase):
    def test_event_factories_create_immutable_event_records(self):
        self.assertEqual(worker_spawned("stage_1").type, "WorkerSpawnedEvent")
        self.assertEqual(
            artifact_generated("stage_1", "content").payload["artifact"], "content"
        )
        self.assertEqual(
            circuit_breaker_tripped("stage_1", ["bad"]).payload["critiques"], ["bad"]
        )

    def test_task_failure_appends_structured_failure_context(self):
        state = init_workflow("attendance", "create")

        updated = reduce_queue_state(
            state,
            Event(
                "TaskFailedEvent",
                {
                    "task_id": "stage_1",
                    "critique": "Missing scenario",
                    "failure_context": {"attempt": 1, "artifact_path": "test-plan.md"},
                },
            ),
        )

        task = updated.tasks["stage_1"]
        self.assertEqual(task.state, TaskState.READY)
        self.assertEqual(task.retry_count, 1)
        self.assertEqual(task.critiques, ["Missing scenario"])
        self.assertEqual(
            updated.events_history[-1].payload["failure_context"]["artifact_path"],
            "test-plan.md",
        )

    def test_circuit_breaker_uses_task_max_retries(self):
        state = init_workflow("attendance", "create")
        state = reduce_queue_state(
            state, Event("TaskFailedEvent", {"task_id": "stage_1", "critique": "first"})
        )
        state = reduce_queue_state(
            state, Event("TaskFailedEvent", {"task_id": "stage_1", "critique": "second"})
        )
        state = reduce_queue_state(
            state, Event("TaskFailedEvent", {"task_id": "stage_1", "critique": "third"})
        )

        task = state.tasks["stage_1"]

        self.assertEqual(task.state, TaskState.BLOCKED_REQUIRES_REVIEW)
        self.assertEqual(task.retry_count, 3)
        self.assertEqual(task.critiques, ["first", "second", "third"])

    def test_meta_agent_proposes_authorization_gated_update(self):
        proposal = propose_instruction_update(
            "stage_2",
            ["Missing widget table", "Missing semantics section"],
        )

        self.assertEqual(proposal["operation"], "Update")
        self.assertEqual(proposal["requires_authorization"], "IMPLEMENTATION APPROVED")
        self.assertIn("stage_2", proposal["summary"])
        self.assertIn("Missing widget table", proposal["candidate_instruction"])


if __name__ == "__main__":
    unittest.main()
