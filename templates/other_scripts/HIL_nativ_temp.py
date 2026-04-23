# Works, but probably won't be usefull, to complicated, to bloated

"""
Human-in-the-Loop (HIL) helper for PydanticAI agents.

Flow:
  1. Agent runs, returns DeferredToolRequests instead of executing protected tools.
  2. `review_and_approve()` shows each pending call and collects user input.
  3. Approved/denied results are fed back via `deferred_tool_results=`.
"""

from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults, Tool, ToolDenied
from pydantic_ai.messages import ToolCallPart


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Email sent to {to!r} | subject: {subject!r} | body: {body!r}."

def _ask_user(call: ToolCallPart) -> bool:
    print("\n" + "=" * 60)
    print(f"  Tool : {call.tool_name}")
    print(f"  Args : {call.args}")
    print("=" * 60)
    while True:
        answer = input("  Allow? (y)es/(n)o: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please type 'y' or 'n'.")


def review_and_approve(
    requests: DeferredToolRequests,
    deny_message: str = "Action denied by the user.",
) -> DeferredToolResults:
    results = DeferredToolResults()
    for call in requests.approvals:
        meta = requests.metadata.get(call.tool_call_id)
        if meta:
            print(f"\n  [metadata] {meta}")
        if _ask_user(call):
            results.approvals[call.tool_call_id] = True
        else:
            results.approvals[call.tool_call_id] = ToolDenied(deny_message)
    return results

demo_agent = Agent(
    "anthropic:claude-haiku-4-5",
    # Agent stops and surfaces DeferredToolRequests instead of auto-running tools
    output_type=[str, DeferredToolRequests],
    tools=[Tool(send_email, requires_approval=True)],
)

if __name__ == "__main__":

    first_result = demo_agent.run_sync("Send a test email to alice@example.com.")
    
    history = first_result.all_messages()

    if isinstance(first_result.output, DeferredToolRequests):
        approved_results = review_and_approve(first_result.output)
        final_result = demo_agent.run_sync(
            "Continue.",
            message_history=history,
            deferred_tool_results=approved_results,
        )
        print("\nAgent final response:", final_result.output)
    else:
        print("Agent response:", first_result.output)
