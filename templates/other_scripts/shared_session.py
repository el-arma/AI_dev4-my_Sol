"""
SharedSession implementation to shared a context between agents
==========================================================
"""

import asyncio
from dataclasses import dataclass, field
import logfire
from pathlib import Path
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from typing import Iterable, Set

# ======================================================================
# LOGFIRE SETUP
# ======================================================================

# Configure Logfire:
logfire.configure(
    send_to_logfire='if-token-present' 
    )

logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)

# ======================================================================
# SHARED SESSION
# ======================================================================
class ContextItem(BaseModel):
    description: str
    content: str | bytes | None = None

@dataclass
class SharedSession:
    items: dict[str, ContextItem] = field(default_factory=dict)

    def put(self, key: str, description: str, content: str | bytes | None = None):
        self.items[key] = ContextItem(description=description, content=content)

# ---------------------------------------------------------------------------
# PRIVATE PRIMITIVES  (single responsibility, no cross-concerns)
# ---------------------------------------------------------------------------

def _save_to_disk(
    txt_content: Iterable[str],
    file_name: str,
    folder_path: Path,
) -> Path:
    
    """MULE: I/O write lines to disk. Returns the absolute path written."""

    TEXT_EXTENSIONS: Set = {".txt", ".log", ".md", ".csv", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}

    if Path(file_name).suffix not in TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported extension '{Path(file_name).suffix}'.")

    full_path = Path(folder_path) / file_name
    full_path.parent.mkdir(parents=True, exist_ok=True)

    with full_path.open("w", encoding="utf-8") as f:
        for line in txt_content:
            f.write(line.rstrip("\n") + "\n")

    return full_path

def _save_to_ctx_session(store: SharedSession, key: str, description: str, content: str | None) -> None:
    """Pure store update: put a text item into the shared session."""
    store.put(key, description, content)


# ---------------------------------------------------------------------------
# AGENT TOOLS
# ---------------------------------------------------------------------------
def save_to_text_file(
    ctx: RunContext[SharedSession],
    key: str,
    description: str,
    file_name: str,
    content: str,
    data_bank_path: str = ".",
    save_to_store: bool = True,        # ← set False to skip context registration
) -> str:
    """
    Save text content to disk, and optionally register it in the shared store.

    By default, content is mirrored to the shared store so downstream agents
    can access it. Pass save_to_store=False for sensitive or oversized content
    that should live on disk only.

    Args:
        key:            Store key, e.g. 'latin_sentences'.
        description:    Short label visible via peek_context() — always saved
                        to the store so agents know the file exists, even when
                        full content is withheld.
        file_name:      Output filename, e.g. 'sentences.txt'.
        content:        Full text to persist.
        data_bank_path: Directory to write the file into (default: cwd).
        save_to_store:  If True (default), mirror content to shared store.
                        If False, store only the description as a pointer.

    Returns:
        Confirmation string with the saved file path.
    """
    lines = content.splitlines()

    # 1. Always write to disk
    saved_path = _save_to_disk(lines, file_name, Path(data_bank_path))

    # 2. Always register at least a pointer so agents know the file exists
      

    if save_to_store:
        stored_content = content
    else: 
        stored_content = None

    _save_to_ctx_session(ctx.deps, key, description, stored_content)

    note = "and registered in shared store" if save_to_store else "registered as pointer only (content withheld)"
    return f"Saved '{key}' to disk at '{saved_path}', {note}."


def peek_context(ctx: RunContext[SharedSession]) -> dict[str, str]:
    """Return all keys and their short descriptions — no content."""
    result = {key: item.description for key, item in ctx.deps.items.items()}
    print(f"  [Agent 2 tool]  peek_context() → {result}")
    return result


def get_content(ctx: RunContext[SharedSession], key: str) -> str:
    """Fetch the full content of a store item by key."""
    if key not in ctx.deps.items:
        return f"Error: '{key}' not found. Available: {list(ctx.deps.items.keys())}"

    item = ctx.deps.items[key]

    if item.content is None:
        return "No content stored — description only."
    if isinstance(item.content, bytes):
        return f"Binary content ({len(item.content)} bytes)."

    print(f"  [Agent 2 tool]  get_content('{key}') → '{item.content}'")
    return item.content


# ---------------------------------------------------------------------------
# AGENTS
# ---------------------------------------------------------------------------
agent1 = Agent(
    "openai:gpt-4o",
    deps_type=SharedSession,
    system_prompt=(
        "Prepare 3 short Latin sentences."
        "Save them in one file using proper tools"
    ),
    tools=[save_to_text_file],
)

agent2 = Agent(
    "openai:gpt-4o",
    deps_type=SharedSession,
    system_prompt=(
        "Check the context to see what is available. "
        "Based on the description, decide if you need the full content. "
        "If yes — call get_content with the right key. "
        "Finally summarise what you found."
    ),
    tools=[peek_context, get_content],
)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
async def main():
    store = SharedSession()

    print("\n--- Agent 1: saving to store ---")
    result1 = await agent1.run("Create and save the file now.", deps=store)
    print(f"  Agent 1 says: {result1.output}")

    print("\n--- Agent 2: inspecting store ---")
    result2 = await agent2.run("Check what the previous agent left for you.", deps=store)
    print(f"  Agent 2 says: {result2.output}")


if __name__ == "__main__":
    asyncio.run(main())