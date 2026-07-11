import sys
import json
import os

MAX_ATTEMPTS = 3

def check_circuit_breaker(task_id: str, retry_count: int) -> bool:
    """
    Circuit Breaker: Prevents infinite loops by tracking retry counts.
    Transitions task to Blocked_Requires_Review if breached.
    """
    if retry_count >= MAX_ATTEMPTS:
        print(f"CIRCUIT BREAKER TRIPPED for task {task_id}. Max attempts ({MAX_ATTEMPTS}) reached.", file=sys.stderr)
        return False
    return True

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print("CIRCUIT BREAKER: No input provided.", file=sys.stderr)
            sys.exit(1)
            
        payload = json.loads(input_data)
        task_id = payload.get("task_id", "unknown")
        retry_count = payload.get("retry_count", 0)
        
        is_safe = check_circuit_breaker(task_id, retry_count)
        
        if is_safe:
            print(json.dumps({"status": "safe", "action": "continue"}))
            sys.exit(0)
        else:
            print(json.dumps({"status": "tripped", "action": "block_requires_review"}))
            # Emit CircuitBreakerTrippedEvent logic here
            sys.exit(1)
            
    except Exception as e:
        print(f"CIRCUIT BREAKER ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
