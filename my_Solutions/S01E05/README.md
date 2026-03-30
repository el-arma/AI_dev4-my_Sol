
S01E05

**Stack:**
Ubuntu VPS (Hetzner) · Nginx · Docker · Docker Compose · GitHub Actions (self-hosted runner) · Cloudflare (DNS + TLS) · UFW · Python · uv

**What I practiced / learned:**

Inspired by the S01E05 lesson, I decided to do a little side quest, so:

## VPS Setup Checklist

1. 🖥️ Set up an Ubuntu VPS (provider: Hetzner).
   Configure SSH keys and apply SSH hardening (disable password login, create a dedicated user, etc.).
2. 📦 Install required tools:
   `git`, `python3`, `pip`, `uv`, `nginx`, `docker`, `docker compose`, `ufw`
3. 🔥 Configure UFW (Firewall).
4. 🌐 Set up a domain in Cloudflare and point DNS records to the VPS IP.
5. 🔒 Configure TLS via Cloudflare (SSL mode: Full / Full (strict)).
6. ⚙️ Set up a GitHub-hosted runner + SSH deploy on VPS.
7. 🔁 Configure Nginx as a reverse proxy.
8. 🧪 Inject `.env` variables using GitHub Secrets in the workflow.
9. 🚀 Configure GitHub Actions workflow (deploy on push to `master`).

All in templates\S01E05_VPS-deploy-ai-agent

Results: 
#### https://legiocybernetica.uk/

Check my progress at:
#### https://legiocybernetica.uk/ai-dev4

Simple AI endpoint with AI on top (send request via POST):
#### https://legiocybernetica.uk/ai-dev4/api/v1/agent-ear

```json
{
  "msg": "Agent response"
}
```

API docs at:
#### https://legiocybernetica.uk/docs

P.S. All in all, DevOps is not that hard - it took me only #74 attempts to deploy a simple app with a small agent (and I have cried only twice).