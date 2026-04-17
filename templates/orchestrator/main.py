"""
main.py  —  Wire executors to the workflow and run.

This is the ONLY file you edit when adding real business logic.
The workflow shape lives in workflow.yaml.
The engine lives in orchestrator.py.
"""

import asyncio
from pathlib import Path

from orchestrator import Step, run_workflow


# ─────────────────────────────────────────────────────────────
# Your real step implementations go here.
# Each executor:  async (step: Step) -> str  (short result msg)
# Raise any Exception to trigger a hard halt.
# ─────────────────────────────────────────────────────────────

async def fetch_file(step: Step) -> str:
    await asyncio.sleep(0.1)          # simulate network I/O
    return "downloaded 42 MB"

async def load_config(step: Step) -> str:
    await asyncio.sleep(0.05)
    return "12 keys validated"

async def process_chunk_a(step: Step) -> str:
    await asyncio.sleep(0.2)          # batch steps run in parallel
    return "5 000 rows processed"

async def process_chunk_b(step: Step) -> str:
    await asyncio.sleep(0.2)
    return "4 800 rows processed"

async def validate_results(step: Step) -> str:
    await asyncio.sleep(0.05)
    return "all checks passed"

async def upload_report(step: Step) -> str:
    await asyncio.sleep(0.1)
    return "uploaded → s3://bucket/report.csv"


# ─────────────────────────────────────────────────────────────
# Map step ids (must match workflow.yaml) → executor functions
# ─────────────────────────────────────────────────────────────

EXECUTORS = {
    "step_1":  fetch_file,
    "step_2":  load_config,
    "step_3a": process_chunk_a,
    "step_3b": process_chunk_b,
    "step_4":  validate_results,
    "step_5":  upload_report,
}


if __name__ == "__main__":
    asyncio.run(
        run_workflow(
            yaml_path=Path("workflow.yaml"),
            executors=EXECUTORS,
        )
    )
