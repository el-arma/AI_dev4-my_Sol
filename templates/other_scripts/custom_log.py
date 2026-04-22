import json
import time
import datetime
from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.models.openrouter import OpenRouterModelSettings
from pydantic_ai.capabilities import Hooks
from pydantic_ai.messages import (
    ModelResponse,
    UserPromptPart, SystemPromptPart, TextPart,
    ToolCallPart, ToolReturnPart, RetryPromptPart,
)

load_dotenv()

settings = OpenRouterModelSettings(
    openrouter_provider={
        "order": ["OpenAI", "Google", "Anthropic"],
        "allow_fallbacks": False,
    },
    openrouter_usage={"include": False},
)

MODEL_ID = "openrouter:google/gemini-2.5-flash"
AGENT_NAME = "demo-agent"

_timing: dict = {}


# ── serialization helpers ──────────────────────────────────────────────────────

def _part(part) -> dict:
    t = type(part).__name__
    if isinstance(part, UserPromptPart):
        return {"type": t, "content": part.content, "timestamp": str(part.timestamp)}
    if isinstance(part, SystemPromptPart):
        return {"type": t, "content": part.content}
    if isinstance(part, TextPart):
        return {"type": t, "content": part.content}
    if isinstance(part, ToolCallPart):
        return {"type": t, "tool_name": part.tool_name, "args": part.args, "tool_call_id": part.tool_call_id}
    if isinstance(part, ToolReturnPart):
        return {"type": t, "tool_name": part.tool_name, "content": part.content, "tool_call_id": part.tool_call_id}
    if isinstance(part, RetryPromptPart):
        return {"type": t, "content": part.content}
    return {"type": t, "raw": str(part)}


def _messages(messages) -> list:
    out = []
    for msg in messages:
        d: dict = {"role": type(msg).__name__}
        if hasattr(msg, "parts"):
            d["parts"] = [_part(p) for p in msg.parts]
        if hasattr(msg, "timestamp"):
            d["timestamp"] = str(msg.timestamp)
        out.append(d)
    return out


def _model_name(ctx: RunContext) -> str:
    m = ctx.model
    for attr in ("model_name", "name"):
        v = getattr(m, attr, None)
        if isinstance(v, str):
            return v
    return str(m)


def _tools(ctx: RunContext) -> list:
    tools = []
    try:
        toolset = getattr(ctx.tool_manager, "toolset", None)
        if toolset and hasattr(toolset, "wrapped"):
            toolset = toolset.wrapped
        if toolset and hasattr(toolset, "toolsets"):
            for ts in toolset.toolsets:
                for attr in ("_function_tools", "_tools", "tools"):
                    tool_map = getattr(ts, attr, {})
                    if isinstance(tool_map, dict):
                        for name, tool in tool_map.items():
                            tools.append({
                                "name": name,
                                "description": getattr(tool, "description", None),
                                "schema": getattr(tool, "parameters_json_schema", None),
                            })
    except Exception as exc:
        tools.append({"error": str(exc)})
    return tools


def _sep(title: str):
    bar = "=" * 64
    print(f"\n{bar}\n  {title}\n{bar}")


def _j(obj) -> str:
    return json.dumps(obj, default=str, indent=4)


# ── hook ──────────────────────────────────────────────────────────────────────

async def log_request(ctx: RunContext[None], request_context: ModelRequestContext) -> ModelRequestContext:
    _timing["start"] = time.perf_counter()
    _timing["wall"] = datetime.datetime.now(datetime.timezone.utc)

    req_messages = getattr(request_context, "messages", None) or ctx.messages

    _sep("LLM REQUEST")
    print(f"  agent        : {AGENT_NAME}")
    print(f"  run_id       : {ctx.run_id}")
    print(f"  run_step     : {ctx.run_step}")
    print(f"  timestamp    : {_timing['wall'].isoformat()}")
    print(f"  model        : {_model_name(ctx)}")
    print(f"  prompt       : {ctx.prompt!r}")
    print(f"  deps         : {ctx.deps!r}")
    print(f"  max_retries  : {ctx.max_retries}")

    print(f"\n  [model_settings]")
    ms = ctx.model_settings
    if ms is None:
        print("  none")
    else:
        d = ms if isinstance(ms, dict) else {k: v for k, v in vars(ms).items() if not k.startswith('_') and v is not None}
        for k, v in d.items():
            print(f"  {k:<15}: {v}")

    print(f"\n  [messages → LLM]  ({len(req_messages)} message(s))")
    print(_j(_messages(req_messages)))

    available = _tools(ctx)
    print(f"\n  [tools available]  ({len(available)} tool(s))")
    print(_j(available) if available else "  none")

    return request_context


def greetings(ctx, name: str) -> str:
    """Greeting user by name """

    return f"Hello {name}"


# ── agent ─────────────────────────────────────────────────────────────────────

agent = Agent(
    MODEL_ID,
    system_prompt="Your are helphuf assistant!",
    name=AGENT_NAME,
    model_settings=settings,
    tools=[greetings],
    capabilities=[Hooks(before_model_request=log_request)],
)

result = agent.run_sync("Use tool to greet John!")

duration = time.perf_counter() - _timing.get("start", time.perf_counter())
usage = result.usage()

# ── response log ──────────────────────────────────────────────────────────────

_sep("LLM RESPONSE")
print(f"  agent        : {AGENT_NAME}")
print(f"  run_id       : {getattr(result, 'run_id', 'N/A')}")
print(f"  duration     : {duration:.3f}s")
print(f"  output       : {result.output!r}")
print(f"  input_tokens : {usage.input_tokens}")
print(f"  output_tokens: {usage.output_tokens}")
print(f"  requests     : {usage.requests}")
print(f"  usage_details: {usage.details}")

all_msgs = result.all_messages()
new_msgs  = result.new_messages()

# show what the LLM actually returned (ModelResponse parts only)
responses = [m for m in all_msgs if isinstance(m, ModelResponse)]
tool_calls_used = []
text_outputs = []
for resp in responses:
    for p in resp.parts:
        if isinstance(p, ToolCallPart):
            tool_calls_used.append({"tool": p.tool_name, "args": p.args, "id": p.tool_call_id})
        elif isinstance(p, TextPart):
            text_outputs.append(p.content)

print(f"\n  [text output(s)]")
for t in text_outputs:
    print(f"    {t!r}")

print(f"\n  [tool calls used]  ({len(tool_calls_used)} call(s))")
if tool_calls_used:
    for tc in tool_calls_used:
        print(f"  tool         : {tc['tool']}")
        print(f"  args         : {tc['args']}")
        print(f"  id           : {tc['id']}")
else:
    print("  none")

print(f"\n  [all messages this run]")
print(_j(_messages(new_msgs)))
