def queue_reducer(state: QueueState, event: dict) -> QueueState:
    event_type = event.get("type")
    
    if event_type == "AuthorizationReceivedEvent":
        task_id = event.get("task_id")
        
        # 1. Map over the tasks and replace the specific one using `replace()`
        # `replace()` is Python's functional equivalent of Dart's `copyWith`
        new_tasks = tuple(
            replace(task, state=TaskState.READY) if task.id == task_id else task
            for task in state.tasks
        )
        
        # 2. Return the entirely new immutable state
        return QueueState(tasks=new_tasks)
        
    elif event_type == "WorkerFailedEvent":
        task_id = event.get("task_id")
        critique = event.get("critique")
        
        # Circuit Breaker Logic (e.g., max 3 retries)
        new_tasks = tuple(
            replace(
                task,
                state=TaskState.BLOCKED_REQUIRES_REVIEW if task.retry_count >= 2 else TaskState.READY,
                retry_count=task.retry_count + 1,
                critiques=task.critiques + (critique,)
            ) if task.id == task_id else task
            for task in state.tasks
        )
        
        return QueueState(tasks=new_tasks)
        
    # If event is unhandled, return the state unchanged
    return state