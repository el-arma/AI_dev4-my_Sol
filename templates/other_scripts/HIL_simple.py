"""
Human-in-the-Loop (HIL) for PydanticAI: wrap any tool with HIL() to gate
execution behind a y/n/s prompt.

Usage:
    agent = Agent("model", tools=[HIL(my_tool), HIL(other_tool)])
    # or use as a decorator: @HIL

The agent runs normally — execution pauses at each protected tool call until
the user approves (y), denies (n), or stops (s). On denial, the user's
alternative instruction is returned to the agent as the tool result so it can
adjust its plan. On stop, UserHalt is raised and the agent exits immediately.
No two-pass run or custom agent loop needed.
"""

import json
from functools import wraps
from pydantic_ai import Agent


class UserHalt(Exception):
    pass


def HIL(fn):

    """Require human approval before a tool executes."""

    @wraps(fn)
    def wrapper(*args, **kwargs):

        print("\n" + "=" * 60)
        
        print(f"  Tool : {fn.__name__}")
        print(f"  Args : {json.dumps(kwargs, indent=2, default=str)}")
        print("=" * 60)

        while True:

            answer = input("  Grant the Agent permission to run the tool: (y)es/(n)o or (s)top: ").strip().lower()
            
            if answer in ("y", "yes"):
                
                # move on
                break

            if answer in ("n", "no"):
                
                print("Action denied by user.")

                alter_instr = input("Please provide an alternative instruction for the Agent: \n")

                return alter_instr
            
            if answer in ("s", "stop"):

                print("AI System halted.")

                raise UserHalt()
            
            print("Please type only 'y' or 'n' or 's'.")

        return fn(*args, **kwargs)
    
    return wrapper

# --- demo ---

@HIL
def send_email(to: str, subject: str, body: str) -> bool:
    
    """
    Send an email .

    Args:
        to: Recipient email address.
        subject: Email subject.
        body: Email content.
    
    Output:
        retuns True (if all executed correctly)
    """

    print(f"TO: {to}")
    print(f"SUB: {subject}")
    print(f"BODY: {body}")
    return True

def read_file(path: str) -> str:
    """Read a file from disk."""
    with open(path) as f:
        return f.read()

agent = Agent(
    "anthropic:claude-haiku-4-5",
    tools=[send_email, HIL(read_file)],
)

if __name__ == "__main__":

    try:
        # result = agent.run_sync("Send a test email to alice@example.com about the planed meeting on Monday.")
        result = agent.run_sync("Read the sample.tx file using proper tool.")
        print("\nAgent:", result.output)
    except UserHalt:
        print("Agent stopped manually.")
