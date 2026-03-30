from datetime import datetime
from pathlib import Path
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    ToolCallPart,
    ToolReturnPart,
    TextPart,
    )

episode = "S01E05"

def get_log_file():
    log_dir = Path("my_Solutions") / episode / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return log_dir / f"agent_run_{timestamp}.log"

def parse_maybe_json(data):
    """Handle both JSON string and already-parsed dict"""
    import json

    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return data
    return data

def log_agent_run(result, tool_schemas=None):
    log_path = get_log_file()

    with open(log_path, "w", encoding="utf-8") as f:

        def write(*args, **kwargs):
            print(*args, **kwargs)
            print(*args, **kwargs, file=f)

        messages = result.all_messages()

        write("\n" + "-" * 100)
        write("AGENT EXECUTION LOG")
        write("-" * 100)

        for i, msg in enumerate(messages):
            write(f"\n--- STEP {i} ---")

            if isinstance(msg, ModelRequest):
                for part in msg.parts:

                    if isinstance(part, UserPromptPart):
                        write("[USER]")
                        write(part.content.strip())

                    elif isinstance(part, ToolReturnPart):
                        write(f"[TOOL RESULT] {part.tool_name}")

                        data = parse_maybe_json(part.content)

                        if tool_schemas and part.tool_name in tool_schemas:
                            _, OutputModel = tool_schemas[part.tool_name]
                            try:
                                parsed = OutputModel.model_validate(data)
                                write(parsed.model_dump_json(indent=2))
                                continue
                            except Exception as e:
                                write(f"[PARSE ERROR] {e}")

                        write(data)

            elif isinstance(msg, ModelResponse):
                for part in msg.parts:

                    if isinstance(part, ToolCallPart):
                        write(f"[TOOL CALL] {part.tool_name}")

                        data = parse_maybe_json(part.args)

                        if isinstance(data, dict) and "input" in data:
                            data = data["input"]

                        if tool_schemas and part.tool_name in tool_schemas:
                            InputModel, _ = tool_schemas[part.tool_name]
                            try:
                                parsed = InputModel.model_validate(data)
                                write(parsed.model_dump_json(indent=2))
                                continue
                            except Exception as e:
                                write(f"[PARSE ERROR] {e}")

                        write(data)

                    elif isinstance(part, TextPart):
                        write("[FINAL ANSWER]")
                        write(part.content.strip())

        write("\n" + "~" * 100)

    print(f"\n[LOG SAVED] {log_path}")