"""
Fetch task content

Actions:
  1. Extracts episode ID (e.g. S04E02) from the URL slug.
  2. Downloads the .md file.
  3. Creates my_Solutions/<EPISODE>/ and saves task_content.md with only
     the content from '## Zadanie praktyczne' onwards.
  4. If 'Nazwa zadania: **name**' is found, appends <EPISODE>_TASK_NAME="name"
     to .env (skips if the key already exists).
"""


from pathlib import Path
import re
import requests

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"


def extract_episode_id(url: str) -> str:

    match = re.search(r's(\d{2})e(\d{2})', url, re.IGNORECASE)

    if not match:
        raise ValueError(f"Cannot extract episode ID from URL: {url}")
    
    return f"S{match.group(1)}E{match.group(2)}"

def fetch(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def trim_to_task_section(content: str) -> str:
    marker = "## Zadanie praktyczne"
    idx = content.find(marker)
    if idx == -1:
        print(f"WARNING: '{marker}' not found — saving full content.")
        return content
    return content[idx:]


def extract_task_name(content: str) -> str | None:
    match = re.search(r'Nazwa zadania:\s*\*\*(.+?)\*\*', content)
    return match.group(1).strip() if match else None


def append_to_env(episode_id: str, task_name: str) -> None:
    key = f"{episode_id}_TASK_NAME"
    text = ENV_PATH.read_text(encoding="utf-8")

    if key in text:
        print(f".env already has {key}, skipping.")
        return

    line = f'{key}="{task_name}"'

    if not text.endswith("\n"):
        text += "\n"

    ENV_PATH.write_text(text + line + "\n", encoding="utf-8")

    print(f"Added to .env: {line}")


def main(url) -> None:

    episode_id = extract_episode_id(url)

    print(f"Episode: {episode_id}")

    episode_dir = BASE_DIR / "my_Solutions" / episode_id
    episode_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching: {url}")

    raw = fetch(url)

    task_content = trim_to_task_section(raw)

    out = episode_dir / "task_content.md"

    out.write_text(task_content, encoding="utf-8")

    print(f"Saved: {out}")

    task_name = extract_task_name(task_content)
    if task_name:
        print(f"Task name: {task_name}")
        append_to_env(episode_id, task_name)
    else:
        print("No 'Nazwa zadania' found — .env not updated.")


if __name__ == "__main__":
    
    ULR: str = "https://cloud.overment.com/s04e04-projektowanie-wlasnej-bazy-wiedzy-dla-ai-1775085192.md"
    
    main(ULR)
