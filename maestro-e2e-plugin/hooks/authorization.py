import sys
import json

def request_authorization(task_id: str, reason: str) -> bool:
    """
    Authorization Hook: Pauses execution and requests human-in-the-loop authorization.
    In a real implementation, this would integrate with the CLI/UI to prompt the user.
    """
    print(f"\n--- AUTHORIZATION REQUIRED ---", file=sys.stderr)
    print(f"Task: {task_id}", file=sys.stderr)
    print(f"Reason: {reason}", file=sys.stderr)
    print(f"Please type 'IMPLEMENTATION APPROVED' to proceed, or anything else to reject.", file=sys.stderr)
    
    # Simulating a prompt. In a real system, the Orchestrator would suspend the state machine
    # and this hook would be fulfilled asynchronously when the user interacts with the UI.
    return True

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
             # Just a dry run/check
             sys.exit(0)
             
        payload = json.loads(input_data)
        task_id = payload.get("task_id", "unknown")
        reason = payload.get("reason", "No reason provided.")
        
        approved = request_authorization(task_id, reason)
        
        if approved:
            print(json.dumps({"status": "approved"}))
            sys.exit(0)
        else:
            print(json.dumps({"status": "rejected"}))
            sys.exit(1)
            
    except Exception as e:
        print(f"AUTHORIZATION ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
