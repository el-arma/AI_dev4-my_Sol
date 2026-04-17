"""
orchestrator.py  —  Deterministic Workflow Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads a YAML master plan, checks the JSON ledger for completed steps,
executes what needs to run (sequential or batched), and saves state back.

No AI. 100% deterministic.
"""

import asyncio
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Coroutine

import logfire
import yaml
from pydantic import BaseModel, Field

# ── configure logfire ──────────────────────────────────────────
logfire.configure()


# ─────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────

class RunPolicy(str, Enum):
    ALWAYS = "always"
    ONCE   = "once"

class ExecMode(str, Enum):
    SEQUENTIAL = "sequential"
    BATCH      = "batch"

class StepStatus(str, Enum):
    DONE   = "DONE"
    FAILED = "FAILED"


# ─────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────

class Step(BaseModel):
    id:          str
    name:        str
    policy:      RunPolicy
    mode:        ExecMode
    batch_id:    str | None = None
    description: str = ""


class LedgerEntry(BaseModel):
    status:       StepStatus
    completed_at: str
    duration_ms:  float
    error:        str | None = None


class Ledger(BaseModel):
    """
    JSON checkpoint file — only 'once' steps are persisted here.
    On each run we load this first, so completed steps are skipped automatically.
    """
    entries: dict[str, LedgerEntry] = Field(default_factory=dict)

    # ── I/O ──────────────────────────────────────────

    @classmethod
    def load(cls, path: Path) -> "Ledger":
        if path.exists():
            logfire.info("ledger.load", path=str(path))
            return cls.model_validate_json(path.read_text())
        logfire.info("ledger.new", path=str(path))
        return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2))
        logfire.info("ledger.saved", path=str(path), total_entries=len(self.entries))

    # ── helpers ──────────────────────────────────────

    def is_done(self, step_id: str) -> bool:
        return step_id in self.entries and self.entries[step_id].status == StepStatus.DONE

    def mark_done(self, step_id: str, duration_ms: float) -> None:
        self.entries[step_id] = LedgerEntry(
            status=StepStatus.DONE,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=round(duration_ms, 2),
        )

    def mark_failed(self, step_id: str, duration_ms: float, error: str) -> None:
        self.entries[step_id] = LedgerEntry(
            status=StepStatus.FAILED,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=round(duration_ms, 2),
            error=error,
        )

    def print_summary(self) -> None:
        print("─" * 58)
        print(f"  {'STEP':<22} {'STATUS':<10} {'MS':>8}  COMPLETED AT")
        print("─" * 58)
        for sid, e in self.entries.items():
            icon = "✅" if e.status == StepStatus.DONE else "❌"
            print(f"  {icon} {sid:<20} {e.status:<10} {e.duration_ms:>8.1f}  {e.completed_at[:19]}")
        if not self.entries:
            print("  (no 'once' steps recorded yet)")
        print("─" * 58 + "\n")


# ─────────────────────────────────────────────────────────────
# YAML loader  →  list[Step]
# ─────────────────────────────────────────────────────────────

def load_workflow(yaml_path: Path) -> tuple[str, Path, list[Step]]:
    """
    Parse the YAML master plan.
    Returns: (workflow_name, ledger_path, steps)
    """
    raw         = yaml.safe_load(yaml_path.read_text())
    wf_name     = raw["workflow"]["name"]
    ledger_path = Path(raw["workflow"]["ledger"])
    steps       = [Step(**s) for s in raw["steps"]]

    logfire.info(
        "workflow.loaded",
        name=wf_name,
        yaml=str(yaml_path),
        total_steps=len(steps),
    )
    return wf_name, ledger_path, steps


# ─────────────────────────────────────────────────────────────
# Execution units builder
#   Collapses the flat step list into ordered execution units:
#   - a unit of 1   →  sequential step
#   - a unit of N>1 →  batch group (runs concurrently)
# ─────────────────────────────────────────────────────────────

def build_execution_units(steps: list[Step]) -> list[list[Step]]:
    units:     list[list[Step]]       = []
    batch_map: dict[str, list[Step]]  = {}
    seen:      set[str]               = set()

    for step in steps:
        if step.mode == ExecMode.SEQUENTIAL:
            units.append([step])
        else:
            bid = step.batch_id or step.id
            batch_map.setdefault(bid, []).append(step)
            if bid not in seen:
                seen.add(bid)
                units.append(batch_map[bid])  # reference fills as we iterate

    return units


# ─────────────────────────────────────────────────────────────
# Custom exception
# ─────────────────────────────────────────────────────────────

class StepFailedError(RuntimeError):
    def __init__(self, step_id: str, step_name: str, reason: str) -> None:
        self.step_id   = step_id
        self.step_name = step_name
        self.reason    = reason
        super().__init__(
            f"[{step_id}] '{step_name}' failed → {reason}\n"
            f"  ↳ Workflow halted. Fix the issue and re-run."
        )


# ─────────────────────────────────────────────────────────────
# Core step executor
# ─────────────────────────────────────────────────────────────

StepExecutor = Callable[[Step], Coroutine[Any, Any, str]]


async def _run_step(
    step:      Step,
    ledger:    Ledger,
    executors: dict[str, StepExecutor],
) -> None:

    # ── gate: skip if once + already done ────
    if step.policy == RunPolicy.ONCE and ledger.is_done(step.id):
        logfire.info(
            "step.skipped",
            step_id=step.id,
            step_name=step.name,
            reason="policy=once, already DONE",
        )
        print(f"  ⏭️  [{step.id}] {step.name} — SKIPPED (once / already done)")
        return

    executor = executors.get(step.id)
    if not executor:
        raise KeyError(f"No executor registered for step id '{step.id}'")

    # ── run & time it ────────────────────────
    logfire.info("step.start", step_id=step.id, step_name=step.name, policy=step.policy.value)
    print(f"  ▶  [{step.id}] {step.name} …")
    t0 = time.perf_counter()

    try:
        with logfire.span("step", step_id=step.id, step_name=step.name):
            result = await executor(step)

        ms = (time.perf_counter() - t0) * 1000

        # persist only 'once' steps
        if step.policy == RunPolicy.ONCE:
            ledger.mark_done(step.id, ms)

        logfire.info(
            "step.done",
            step_id=step.id,
            step_name=step.name,
            duration_ms=round(ms, 2),
            result=result,
        )
        print(f"  ✅  [{step.id}] {step.name} — {result}  ({ms:.0f} ms)")

    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000
        error_desc = f"{type(exc).__name__}: {exc}"

        # persist failure for 'once' steps so we know it was attempted
        if step.policy == RunPolicy.ONCE:
            ledger.mark_failed(step.id, ms, error_desc)

        logfire.error(
            "step.failed",
            step_id=step.id,
            step_name=step.name,
            duration_ms=round(ms, 2),
            error=error_desc,
        )
        print(f"  ❌  [{step.id}] {step.name} — FAILED  ({ms:.0f} ms)")
        print(f"       ↳ {error_desc}")

        raise StepFailedError(step.id, step.name, error_desc) from exc


# ─────────────────────────────────────────────────────────────
# Main engine
# ─────────────────────────────────────────────────────────────

async def run_workflow(
    yaml_path: Path,
    executors: dict[str, StepExecutor],
) -> None:
    """
    Full workflow execution:
      1. Parse YAML master plan
      2. Load ledger.json  →  know which 'once' steps are already done
      3. Build ordered execution units  (sequential / batch)
      4. Execute each unit; halt immediately on any failure
      5. Save ledger back to disk
    """
    wf_name, ledger_path, steps = load_workflow(yaml_path)
    ledger = Ledger.load(ledger_path)
    units  = build_execution_units(steps)

    # print what the ledger already knows before we start
    already_done = [sid for sid in ledger.entries if ledger.is_done(sid)]
    print(f"\n{'━' * 58}")
    print(f"  🚀  {wf_name}  |  {len(steps)} steps defined")
    if already_done:
        print(f"  📋  Already done (will skip): {', '.join(already_done)}")
    print(f"{'━' * 58}")

    with logfire.span("workflow.run", workflow=wf_name):
        try:
            for unit in units:
                if len(unit) == 1:
                    # ── sequential ───────────────────────
                    await _run_step(unit[0], ledger, executors)
                else:
                    # ── batch (concurrent) ───────────────
                    batch_label = unit[0].batch_id or unit[0].id
                    print(f"\n  ⚡  batch '{batch_label}'  ({len(unit)} steps in parallel)")

                    with logfire.span("batch", batch_id=batch_label, size=len(unit)):
                        results = await asyncio.gather(
                            *[_run_step(s, ledger, executors) for s in unit],
                            return_exceptions=True,
                        )

                    failures = [r for r in results if isinstance(r, BaseException)]
                    if failures:
                        raise failures[0]

                    print()  # spacing after batch block

        except StepFailedError as e:
            print(f"\n  🛑  Halted — {e}\n")
            logfire.error("workflow.halted", step_id=e.step_id, reason=e.reason)
        else:
            print(f"\n  🏁  All done.\n")
            logfire.info("workflow.complete", workflow=wf_name)
        finally:
            ledger.save(ledger_path)
            ledger.print_summary()
