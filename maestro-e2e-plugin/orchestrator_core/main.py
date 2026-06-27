import argparse
from .state import WorkflowTarget, QueueState, Task, TaskState, StageMode
from .stream import OrchestratorStream
from .hooks import cli_ui_hook

def init_workflow(module: str, flow: str = None, dry_run: bool = False, manual: bool = False) -> QueueState:
    target = WorkflowTarget(
        module=module,
        flow=flow,
        dry_run=dry_run,
        approval_mode="manual" if manual else "auto"
    )
    
    # Define the 5 strict pipeline stages as dependencies
    tasks = {
        "stage_0": Task(id="stage_0", skill_name="domain_discovery", dependencies=[]),
        "stage_1": Task(id="stage_1", skill_name="test_plan_author", dependencies=["stage_0"]),
        "stage_2": Task(id="stage_2", skill_name="widget_blueprint", dependencies=["stage_1"]),
        "stage_3": Task(id="stage_3", skill_name="maestro_implementer", dependencies=["stage_2"]),
        "stage_4": Task(id="stage_4", skill_name="execution_and_healing", dependencies=["stage_3"]),
    }
    
    # We pass an empty event list initially
    return QueueState(target=target, tasks=tasks)

def main():
    parser = argparse.ArgumentParser(description="Agentic E2E Orchestrator (Maestro)")
    parser.add_argument("--init", action="store_true", help="Scaffold E2E infrastructure in the current project")
    parser.add_argument("--module", required=False, help="Target module (e.g., 'attendance')")
    parser.add_argument("--flow", help="Specific business flow (e.g., 'archive student')")
    parser.add_argument("--dry-run", action="store_true", help="Run without side effects or disk mutability")
    parser.add_argument("--manual", action="store_true", help="Pause for manual checklist approvals")
    
    args = parser.parse_args()
    
    if args.init:
        from .init_scaffold import scaffold_workspace
        from pathlib import Path
        scaffold_workspace(Path.cwd(), Path(__file__).parent.parent)
        return
        
    if not args.module:
        parser.error("--module is required when not using --init")
    
    # 1. Initialize State Machine
    initial_state = init_workflow(args.module, args.flow, args.dry_run, args.manual)
    stream = OrchestratorStream(initial_state)
    
    # 2. Register Global Hooks
    stream.subscribe(cli_ui_hook)
    
    print(f"[*] Maestro Orchestrator Initialized")
    print(f"    - Target Module : {args.module}")
    print(f"    - Target Flow   : {args.flow or 'ALL (Discovery Selection)'}")
    print(f"    - Dry-run mode  : {'ON (No mutations)' if args.dry_run else 'OFF'}")
    print(f"    - Approvals     : {'MANUAL' if args.manual else 'AUTO'}")
    print("-" * 50)
    
    # 3. Resolve Routing (Drift Detection)
    from .router import resolve_routing
    print("[*] Analyzing workspace artifacts for drift...")
    routing_event = resolve_routing(initial_state)
    
    if routing_event.type == "RequireFlowSelectionEvent":
        print(f"\n[!] Paused: Stage 0 complete, but no specific flow selected.")
        print(f"[!] Please inspect modules/{args.module}/domain.md and run again with --flow '<target_flow>'")
    elif routing_event.type == "PipelineUpToDateEvent":
        print(f"\n[+] All artifacts up to date! Proceeding to E2E execution suite...")
        # Phase 4 triggers here: run-e2e.sh
    else:
        task_id = routing_event.payload.get("task_id")
        mode = routing_event.payload.get("mode")
        print(f"\n[>] Routing Decision: Missing or outdated artifact detected.")
        print(f"[>] Dispatching {task_id} in mode: '{mode}'")
        
        # 4. Wire up the Executor Hook (Phase 3)
        from .executor import executor_hook
        from pathlib import Path
        
        # Prompts are located inside the installed plugin folder
        prompts_dir = Path(__file__).parent / "prompts"
        # The workspace is the `e2e_test` folder inside the user's current working directory (the target project)
        workspace_dir = Path.cwd() / "e2e_test"
        
        stream.subscribe(lambda state, event, s: executor_hook(state, event, s, prompts_dir, str(workspace_dir)))
        
        # Kick off the cascade!
        stream.dispatch(routing_event)

if __name__ == "__main__":
    main()
