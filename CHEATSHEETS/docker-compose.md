# 🐙 Docker Compose Cheat Sheet
### v1 vs v2 — with a Python Slim example throughout

> **TL;DR on versions:**
> - `docker-compose` (with hyphen) = **Compose v1** — old Python-based standalone CLI, deprecated since 2023
> - `docker compose` (with space) = **Compose v2** — built into Docker CLI as a plugin, current standard
> - Functionally similar, but syntax, behavior, and features differ in key areas marked below.

---

## 🆚 Version at a Glance

| | v1 | v2 |
|---|---|---|
| Command | `docker-compose` | `docker compose` |
| Written in | Python | Go |
| Install | Separate binary | Ships with Docker Desktop / Docker Engine |
| Status | **Deprecated** (EOL Jan 2024) | **Current standard** |
| Compose file spec | up to `version: "3.9"` | uses Compose Spec (no `version:` needed) |
| Profiles support | Limited | Full |
| `depends_on` conditions | Basic | Extended (`service_healthy`, `service_completed_successfully`) |

---

## 🐍 Example Project — Python Slim App

We'll use this setup throughout the cheat sheet.

### Project layout
```
my-app/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── app.py
```

### `Dockerfile`
```dockerfile
# Use the official slim Python image — smaller footprint than full python:3.12
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (allows Docker to cache this layer)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app will listen on
EXPOSE 8000

# Start the app
CMD ["python", "app.py"]
```

### `docker-compose.yml` — v2 style (recommended)
```yaml
# ✅ v2: No "version:" field needed — Docker reads the Compose Spec automatically
# ❌ v1: Required "version: '3.9'" at the top

services:
  web:
    build: .                        # Build from the Dockerfile in current dir
    ports:
      - "8000:8000"                 # Map host port 8000 → container port 8000
    environment:
      - APP_ENV=production          # Pass env var into the container
    volumes:
      - .:/app                      # Mount current dir for live code reloading
    depends_on:
      db:
        condition: service_healthy  # ✅ v2 only: wait for DB health check to pass
                                    # ❌ v1: only supported "condition: service_started"

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=secret
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:                    # Define when "healthy" means ready to accept connections
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  db-data:                          # Named volume — data persists across container restarts
```

---

## ▶️ Start & Stop

```bash
# Start all services in detached (background) mode
docker compose up -d          # ✅ v2
docker-compose up -d          # v1

# Start and force rebuild images (picks up code or Dockerfile changes)
docker compose up -d --build

# Start only a specific service (and its dependencies)
docker compose up -d web

# Stop all services (keeps containers and volumes)
docker compose stop

# Stop AND remove containers + networks (volumes are kept)
docker compose down

# Stop, remove containers, AND delete named volumes (⚠️ destroys DB data)
docker compose down -v
```

---

## 📋 Status & Inspection

```bash
# List running compose services and their status
docker compose ps

# Show all services including stopped ones
docker compose ps -a           # ✅ v2 only — v1 shows stopped too but flag behavior differs

# Show which host ports are mapped for a service
docker compose port web 8000

# Show the full resolved config (with defaults filled in)
docker compose config          # ✅ v2: validates and pretty-prints merged config
                               # v1: similar but less reliable with newer spec features
```

---

## 📜 Logs

```bash
# Stream logs from all services
docker compose logs -f

# Stream logs from the Python web service only
docker compose logs -f web

# Show only the last 100 lines from the web service
docker compose logs --tail 100 web

# ✅ v2: show log timestamps
docker compose logs -f --timestamps web
```

---

## 🔧 Exec & Run

```bash
# Open an interactive shell inside the running web container
docker compose exec web bash

# Run a one-off Python command inside the web container
docker compose exec web python -c "import sys; print(sys.version)"

# Run a one-off container (not the already-running one) and remove after
docker compose run --rm web python manage.py migrate

# ✅ v2: pass env vars directly to a run command
docker compose run --rm -e DEBUG=true web python app.py

# ❌ v1 vs ✅ v2: In v2, `exec` and `run` handle TTY allocation more reliably
#    In v1 you sometimes needed -T to disable pseudo-TTY in CI environments
docker compose exec -T web python -m pytest   # use -T in CI to avoid TTY errors (still works in v2)
```

---

## 🔄 Rebuild & Update

```bash
# Rebuild only the web service image (without restarting others)
docker compose build web

# Pull latest base images before building (e.g. get newest python:3.12-slim)
docker compose build --pull web

# Rebuild and restart only the web service
docker compose up -d --build web

# Pull updated images for services that use pre-built images (not built locally)
docker compose pull db

# ✅ v2: Check which services have image updates available
docker compose pull --dry-run
```

---

## ⚖️ Scaling

```bash
# ✅ v2 preferred syntax — scale web to 3 replicas
docker compose up -d --scale web=3

# ❌ v1 used the same flag but required avoid port conflicts manually
#    (can't map a fixed host port if running 3 replicas — use port range or remove fixed port)

# In docker-compose.yml, for scaling to work, remove fixed host port:
#   ports:
#     - "8000"       # Docker assigns a random available host port per replica
#     # NOT "8000:8000"  ← this would conflict across replicas
```

---

## 🏷️ Profiles — run only what you need

```yaml
# docker-compose.yml — only available cleanly in v2 / Compose Spec
services:
  web:
    build: .
    ports:
      - "8000:8000"

  db:
    image: postgres:16-alpine
    profiles:
      - full                  # Only starts when "full" profile is active

  redis:
    image: redis:7-alpine
    profiles:
      - full
      - cache                 # Starts when either "full" or "cache" profile is active
```

```bash
# Start only the web service (no db, no redis)
docker compose up -d

# Start web + db + redis (full profile)
docker compose --profile full up -d

# Start web + redis only (cache profile)
docker compose --profile cache up -d

# ❌ v1: profiles exist but are unreliable — avoid using them in v1
```

---

## 🌐 Networks

```yaml
# docker-compose.yml — defining custom networks
services:
  web:
    build: .
    networks:
      - frontend
      - backend

  db:
    image: postgres:16-alpine
    networks:
      - backend               # db is only reachable from backend network, not exposed to frontend

networks:
  frontend:
  backend:
    internal: true            # Prevents external internet access from this network
```

```bash
# Inspect the auto-created network for your compose project
docker network inspect my-app_backend

# ✅ v2: network names are prefixed with the project name automatically
#    Project name = folder name by default, or set with -p / COMPOSE_PROJECT_NAME
```

---

## 🔑 Environment Variables

```bash
# Option 1: inline in compose file
environment:
  - APP_ENV=production
  - SECRET_KEY=abc123

# Option 2: load from a .env file (auto-loaded by both v1 and v2 if named .env)
env_file:
  - .env

# Option 3: pass host env vars into the container (no value = uses host's value)
environment:
  - SECRET_KEY          # takes SECRET_KEY from the shell running docker compose

# ✅ v2: .env is loaded for variable substitution in the compose file itself too
#    e.g. image: python:${PYTHON_VERSION}-slim  →  PYTHON_VERSION=3.12 in .env
```

```bash
# Override env vars at runtime without editing the file
APP_ENV=staging docker compose up -d

# ✅ v2: use --env-file to load a non-default env file
docker compose --env-file .env.staging up -d
# ❌ v1: --env-file flag not supported
```

---

## 🩺 Health Checks in `depends_on`

```yaml
# ✅ v2 / Compose Spec only — wait for real readiness, not just container start

services:
  web:
    build: .
    depends_on:
      db:
        condition: service_healthy          # waits for db healthcheck to pass
      migrations:
        condition: service_completed_successfully  # waits for one-off job to finish

  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 10s     # Grace period before health checks start counting failures

  migrations:
    build: .
    command: python manage.py migrate
    depends_on:
      db:
        condition: service_healthy

# ❌ v1: depends_on only supports "condition: service_started"
#    meaning it starts after the container exists, NOT after it's actually ready
```

---

## 🧹 Cleanup

```bash
# Remove stopped containers for this project
docker compose rm

# Remove and don't ask for confirmation
docker compose rm -f

# Stop + remove containers + networks (keep volumes)
docker compose down

# Stop + remove containers + networks + volumes (⚠️ data loss)
docker compose down -v

# Stop + remove + delete built images too
docker compose down --rmi all

# ✅ v2: remove orphan containers (services removed from compose file but still running)
docker compose down --remove-orphans
# ❌ v1: --remove-orphans exists but is less reliable
```

---

## 📁 Multiple Compose Files (overrides)

```bash
# ✅ v2: merge a base file with an override (later file wins on conflicts)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Common pattern:
#   docker-compose.yml         → base config
#   docker-compose.override.yml → auto-loaded by default in both v1 and v2
#   docker-compose.prod.yml    → manually specified for production

# ✅ v2: set a project name to avoid collisions between environments
docker compose -p my-app-staging up -d
```

---

## ⚡ Quick Reference

| Goal | Command |
|---|---|
| Start everything | `docker compose up -d` |
| Rebuild + restart one service | `docker compose up -d --build web` |
| Shell into web container | `docker compose exec web bash` |
| Follow web logs | `docker compose logs -f web` |
| Run DB migrations | `docker compose run --rm web python manage.py migrate` |
| Tear down (keep data) | `docker compose down` |
| Tear down + wipe data | `docker compose down -v` |
| Check service health | `docker compose ps` |
| Load staging env | `docker compose --env-file .env.staging up -d` |
| Scale web to 3 | `docker compose up -d --scale web=3` |

---

## 🚨 Key v1 → v2 Migration Notes

1. **Replace `docker-compose`** with `docker compose` in all scripts and CI pipelines.
2. **Drop `version:`** from the top of your `docker-compose.yml` — it's ignored in v2 and triggers a warning.
3. **Upgrade `depends_on`** from plain list form to the condition-based map form to actually wait for readiness.
4. **Use `--env-file`** flag instead of workarounds for non-default env files.
5. **Named volumes and networks** get the project name as a prefix — check `docker volume ls` / `docker network ls` after migrating.
6. **`-T` flag** (`docker compose exec -T`) may no longer be needed in v2 for CI, but keeping it doesn't break anything.

---

*Compose Spec: https://compose-spec.io — Docker Compose v2 docs: https://docs.docker.com/compose/*
