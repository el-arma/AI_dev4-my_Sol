# UV Cheat Sheet (Python Package Manager)

## 🔧 Basic Project Setup

```bash
uv init
uv venv
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate   # Windows
```

---

## 📦 Add / Remove Packages

```bash
uv add requests
uv add numpy==1.26.4

uv remove requests
```

---

## 🔄 Sync Environment

```bash
uv sync
uv sync --dry-run
```

---

## 🔒 Lockfile Management

```bash
uv lock
uv lock --check
```

---

## 🔍 Inspect Dependencies

```bash
uv tree
uv pip list
```

---

## 🧪 Run Commands in Env

```bash
uv run python script.py
uv run pytest
```

---

## 📥 Install from Requirements

```bash
uv pip install -r requirements.txt
```

---

## 📤 Export Requirements

```bash
uv pip freeze > requirements.txt
```

---

## 🧹 Cleanup

```bash
uv remove <package>
uv sync
```

---

## ⚡ Useful Combos

### Health check
```bash
uv sync --dry-run
```

### Update everything
```bash
uv lock
uv sync
```

### Rebuild env
```bash
rm -rf .venv
uv venv
uv sync
```

---

## 🧠 Tips

- `uv sync` = install exactly what's in lockfile
- `uv lock` = resolve dependencies
- Prefer `uv add` over manual edits
- Use `--dry-run` before big changes
