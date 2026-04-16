# 🐳 Docker Cheat Sheet

> Most useful Docker commands with clear, concise explanations.

---

## 📦 Images

```bash
# Download an image from Docker Hub
docker pull nginx

# Download a specific version (tag)
docker pull nginx:1.25

# List all locally available images
docker images

# Remove an image by name or ID
docker rmi nginx

# Remove all unused images (not referenced by any container)
docker image prune -a

# Build an image from a Dockerfile in the current directory
docker build -t my-app:1.0 .

# Tag an existing image with a new name/version
docker tag my-app:1.0 my-app:latest
```

---

## 🚀 Containers — Run & Create

```bash
# Run a container (downloads image if missing, then starts it)
docker run nginx

# Run in detached mode (background), so the terminal stays free
docker run -d nginx

# Run with a custom name (easier to reference later)
docker run -d --name my-nginx nginx

# Map host port 8080 → container port 80 (host:container)
docker run -d -p 8080:80 nginx

# Mount a host directory into the container (host:container)
docker run -d -v /my/data:/app/data nginx

# Pass an environment variable into the container
docker run -d -e APP_ENV=production my-app

# Run interactively with a terminal (great for debugging)
docker run -it ubuntu bash

# Automatically remove the container when it stops
docker run --rm ubuntu echo "hello"
```

---

## 📋 Containers — List & Inspect

```bash
# List all running containers
docker ps

# List ALL containers (including stopped ones)
docker ps -a

# Show detailed info about a container (IP, mounts, config, etc.)
docker inspect my-nginx

# Show live resource usage (CPU, RAM, network)
docker stats

# Show resource usage for a specific container (non-streaming)
docker stats my-nginx --no-stream

# Show the processes running inside a container
docker top my-nginx
```

---

## ▶️ Containers — Start, Stop & Remove

```bash
# Stop a running container gracefully (sends SIGTERM)
docker stop my-nginx

# Start a stopped container
docker start my-nginx

# Restart a container (stop + start)
docker restart my-nginx

# Kill a container immediately (sends SIGKILL, no grace period)
docker kill my-nginx

# Remove a stopped container
docker rm my-nginx

# Force-remove a running container without stopping it first
docker rm -f my-nginx

# Remove ALL stopped containers at once
docker container prune
```

---

## 🔍 Logs & Debugging

```bash
# View logs from a container
docker logs my-nginx

# Follow logs in real time (like tail -f)
docker logs -f my-nginx

# Show only the last 50 lines of logs
docker logs --tail 50 my-nginx

# Open an interactive shell inside a running container
docker exec -it my-nginx bash

# Run a one-off command inside a running container
docker exec my-nginx cat /etc/nginx/nginx.conf

# Copy a file FROM the container to the host
docker cp my-nginx:/etc/nginx/nginx.conf ./nginx.conf

# Copy a file FROM the host INTO the container
docker cp ./nginx.conf my-nginx:/etc/nginx/nginx.conf
```

---

## 💾 Volumes

```bash
# Create a named volume (managed by Docker, persists data)
docker volume create my-data

# List all volumes
docker volume ls

# Show detailed info about a volume (location, driver, etc.)
docker volume inspect my-data

# Remove a specific volume
docker volume rm my-data

# Remove all unused volumes (not mounted by any container)
docker volume prune

# Run a container with a named volume attached
docker run -d -v my-data:/app/data my-app
```

---

## 🌐 Networks

```bash
# List all Docker networks
docker network ls

# Create a custom bridge network (containers on it can talk to each other by name)
docker network create my-network

# Connect a running container to a network
docker network connect my-network my-nginx

# Disconnect a container from a network
docker network disconnect my-network my-nginx

# Run a container directly on a custom network
docker run -d --network my-network --name api my-app

# Inspect a network (see connected containers, IPs, etc.)
docker network inspect my-network

# Remove a network
docker network rm my-network
```

---

## 🐙 Docker Compose

```bash
# Start all services defined in docker-compose.yml (detached)
docker compose up -d

# Stop and remove all containers defined in compose file
docker compose down

# Stop and also remove volumes (WARNING: deletes data)
docker compose down -v

# Rebuild images before starting (picks up code/config changes)
docker compose up -d --build

# View logs from all services
docker compose logs -f

# View logs from a specific service only
docker compose logs -f web

# List running compose services
docker compose ps

# Run a one-off command in a compose service container
docker compose exec web bash

# Scale a service to N replicas
docker compose up -d --scale worker=3
```

---

## 🧹 System Cleanup

```bash
# Show how much disk space Docker is using
docker system df

# Remove ALL unused data: stopped containers, unused images, networks, volumes
docker system prune -a --volumes

# Remove only dangling images (untagged, not referenced by anything)
docker image prune

# Remove all stopped containers
docker container prune

# Remove all unused networks
docker network prune
```

---

## 📤 Registry — Push & Pull

```bash
# Log in to Docker Hub (prompts for username + password)
docker login

# Log in to a private registry
docker login registry.example.com

# Tag an image for pushing to Docker Hub (username/repo:tag)
docker tag my-app:1.0 johndoe/my-app:1.0

# Push the tagged image to the registry
docker push johndoe/my-app:1.0

# Pull a specific image from a private registry
docker pull registry.example.com/my-app:1.0

# Log out from the registry
docker logout
```

---

## 📝 Dockerfile — Common Instructions

```dockerfile
# Base image to build from
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy files from host into the image
COPY package*.json ./

# Run a shell command during image build
RUN npm install

# Copy the rest of the source code
COPY . .

# Declare a port the container listens on (documentation only)
EXPOSE 3000

# Set an environment variable available at runtime
ENV NODE_ENV=production

# Set the default command to run when the container starts
CMD ["node", "server.js"]

# Like CMD, but harder to override — used for the main executable
ENTRYPOINT ["node"]

# Declare a mount point for a volume
VOLUME ["/app/data"]

# Add metadata labels to the image
LABEL maintainer="you@example.com"
```

---

## ⚡ Quick Reference

| Goal | Command |
|---|---|
| Shell into running container | `docker exec -it <name> bash` |
| Follow container logs | `docker logs -f <name>` |
| Stop all running containers | `docker stop $(docker ps -q)` |
| Remove all stopped containers | `docker container prune` |
| Remove everything unused | `docker system prune -a` |
| See port mappings | `docker port <name>` |
| Check container IP address | `docker inspect -f '{{.NetworkSettings.IPAddress}}' <name>` |

---

*Docker version referenced: 25+. Some commands may vary slightly on older versions.*
