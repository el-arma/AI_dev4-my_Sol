import json
import time
import datetime
from pathlib import Path

from pydantic_ai import RunContext, ModelRequestContext
from pydantic_ai.capabilities import Hooks
from pydantic_ai.messages import (
    ModelResponse,
    UserPromptPart, SystemPromptPart, TextPart,
    ToolCallPart, ToolReturnPart, RetryPromptPart,
)

BASE_DIR = Path(__file__).resolve().parent


class AgentLogger:
    """
    Simple per-session file logger using Pydantic AI Hooks.

    Safe to define at module level — log file is created lazily on the first
    request, not at construction. Each close() finalises the current file;
    the next run opens a fresh one automatically.

    One logger per agent:
        smith_log = AgentLogger("Agent_Smith")
        jones_log = AgentLogger("Agent_Jones")

        Agent_Smith = Agent(..., capabilities=[smith_log.get_hooks()])
        Agent_Jones = Agent(..., capabilities=[jones_log.get_hooks()])

    In your run function:
        try:
            result = await agent.run(...)      # or agent.run_sync(...)
        finally:
            smith_log.close()
    """

    def __init__(self, agent_name: str, log_dir: Path | None = None):
        self.agent_name = agent_name
        self._log_dir = log_dir or (BASE_DIR / "logs")
        self._file = None
        self._log_path: Path | None = None
        self._request_count = 0
        self._step_start: float | None = None

    # ======================================================================
    # FILE LIFECYCLE
    # ======================================================================

    def _ensure_open(self):
        if self._file is None or self._file.closed:
            self._log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self._log_path = self._log_dir / f"{self.agent_name}_{ts}.log"
            self._file = open(self._log_path, "w", encoding="utf-8", buffering=1)
            self._request_count = 0
            print(f"[LOG] {self._log_path}")
            self._write(f"[SESSION START]  agent={self.agent_name}  ts={ts}")

    def close(self):
        if self._file and not self._file.closed:
            self._write(
                f"\n{'=' * 64}\n"
                f"  [SESSION END]  total_requests={self._request_count}\n"
                f"{'=' * 64}"
            )
            self._file.close()

    # ======================================================================
    # I/O
    # ======================================================================

    def _write(self, line: str):
        if self._file and not self._file.closed:
            self._file.write(line + "\n")

    def _sep(self, title: str):
        self._write(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")

    # ======================================================================
    # MESSAGE SERIALIZATION
    # ======================================================================

    def _part(self, part) -> dict:
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

    def _messages(self, messages) -> list:
        out = []
        for msg in messages:
            d: dict = {"role": type(msg).__name__}
            if hasattr(msg, "parts"):
                d["parts"] = [self._part(p) for p in msg.parts]
            if hasattr(msg, "timestamp"):
                d["timestamp"] = str(msg.timestamp)
            out.append(d)
        return out

    def _model_name(self, ctx: RunContext) -> str:
        for attr in ("model_name", "name"):
            v = getattr(ctx.model, attr, None)
            if isinstance(v, str):
                return v
        return str(ctx.model)

    # ======================================================================
    # HOOKS
    # ======================================================================

    def before_model_request(
        self, ctx: RunContext, request_context: ModelRequestContext, /
    ) -> ModelRequestContext:
        self._ensure_open()
        self._request_count += 1
        self._step_start = time.perf_counter()
        wall = datetime.datetime.now(datetime.timezone.utc)
        req_messages = getattr(request_context, "messages", None) or ctx.messages

        self._sep(f"REQUEST #{self._request_count}")
        self._write(f"  agent      : {self.agent_name}")
        self._write(f"  run_id     : {ctx.run_id}")
        self._write(f"  run_step   : {ctx.run_step}")
        self._write(f"  timestamp  : {wall.isoformat()}")
        self._write(f"  model      : {self._model_name(ctx)}")
        self._write(f"\n  [messages → LLM]  ({len(req_messages)} message(s))")
        self._write(json.dumps([self._part(p) for msg in req_messages
                                for p in getattr(msg, "parts", [])],
                               default=str, indent=2))
        return request_context

    def after_model_request(
        self, ctx: RunContext, /, *, request_context, response: ModelResponse
    ) -> ModelResponse:
        duration = time.perf_counter() - (self._step_start or time.perf_counter())
        text_parts = [p for p in response.parts if isinstance(p, TextPart)]
        tool_calls = [p for p in response.parts if isinstance(p, ToolCallPart)]

        self._sep(f"RESPONSE #{self._request_count}")
        self._write(f"  run_step   : {ctx.run_step}")
        self._write(f"  duration   : {duration:.3f}s")

        if text_parts:
            self._write(f"\n  [text]")
            for p in text_parts:
                self._write(f"    {p.content!r}")

        if tool_calls:
            self._write(f"\n  [tool calls]  ({len(tool_calls)})")
            for p in tool_calls:
                self._write(f"    tool={p.tool_name}  args={p.args!r}")

        return response

    def get_hooks(self) -> Hooks:
        return Hooks(
            before_model_request=self.before_model_request,
            after_model_request=self.after_model_request,
        )
