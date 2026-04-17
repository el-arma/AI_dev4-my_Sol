# 🐙 GitHub CLI Cheat Sheet (`gh`)
### Essential commands + setting up a portfolio + managing multiple accounts

> **What is `gh`?** The official GitHub CLI — lets you manage repos, PRs, issues, and your GitHub account directly from the terminal without touching the browser.
> Install: https://cli.github.com

---

## 🔧 Installation

```bash
# macOS
brew install gh

# Ubuntu / Debian
sudo apt install gh

# Windows (winget)
winget install GitHub.cli

# Verify install
gh --version
```

---

## 🔑 Authentication — First Login

```bash
# Interactive login wizard (recommended for first setup)
gh auth login

# Wizard will ask:
#   1. GitHub.com or GitHub Enterprise?  → GitHub.com
#   2. Protocol: HTTPS or SSH?           → SSH (recommended for portfolios)
#   3. Generate SSH key?                 → Yes (if you don't have one)
#   4. How to authenticate?              → Login with a web browser  (or paste token)

# Login directly with a Personal Access Token (PAT) — useful in CI / scripts
gh auth login --with-token <<< "ghp_yourTokenHere"

# Check who you're currently logged in as
gh auth status

# Log out
gh auth logout
```

---

## 👥 Multiple Accounts — Add & Switch

> This is one of the most common pain points. GitHub CLI v2.40+ supports multiple accounts natively.

```bash
# ─── Check your gh version first ───────────────────────────────────────────
gh --version
# Needs to be 2.40.0 or higher for native multi-account support

# ─── Add a second account ───────────────────────────────────────────────────
gh auth login
# Just run login again — gh will detect you already have one account
# and prompt you to add another. Give each account an SSH key of its own.

# List all authenticated accounts
gh auth status
# Shows each account, its token scopes, and which is active

# ─── Switch active account ──────────────────────────────────────────────────
gh auth switch --user your-other-username

# ─── Switch per-folder (recommended for portfolio vs work) ──────────────────
# Set an env var in your shell session to override the active account:
GH_USER=your-other-username gh repo list

# Or export it for the whole shell session:
export GH_USER=work-username
gh pr list    # now runs as work account

# ─── Per-repo override via git config ───────────────────────────────────────
# Inside a specific repo, tell gh which account to use:
gh config set -h github.com git_protocol ssh
git config user.email "work@example.com"
git config user.name  "Work Name"
# gh will use the account whose SSH key matches the repo remote

# ─── SSH key tip for multiple accounts ──────────────────────────────────────
# Generate separate keys per account and add to ~/.ssh/config:
# Host github-personal
#   HostName github.com
#   User git
#   IdentityFile ~/.ssh/id_ed25519_personal
#
# Host github-work
#   HostName github.com
#   User git
#   IdentityFile ~/.ssh/id_ed25519_work
#
# Then set remote URLs to use the alias:
# git remote set-url origin git@github-personal:yourusername/your-repo.git
```

---

## 🗂️ Repos — Basics

```bash
# List your repos
gh repo list

# List repos for another user or org
gh repo list other-username
gh repo list my-org --limit 50

# View a repo in the browser
gh repo view yourusername/repo-name --web

# Clone a repo (no need to copy the URL)
gh repo clone yourusername/repo-name

# Fork a repo and clone it locally in one step
gh repo fork other/repo --clone
```

---

## 🚀 Setting Up a New Portfolio Project

> Full walkthrough from zero to a live GitHub repo.

### Step 1 — Init locally

```bash
# Create a new project folder and enter it
mkdir my-portfolio && cd my-portfolio

# Initialize git
git init

# Create a README
echo "# My Portfolio" > README.md

# Stage and commit
git add .
git commit -m "initial commit"
```

### Step 2 — Create the GitHub repo with `gh`

```bash
# Create a new PUBLIC repo on GitHub and link it to the current folder
gh repo create my-portfolio --public --source=. --remote=origin --push

# Flags explained:
#   --public          → visible to everyone (use --private to hide it)
#   --source=.        → use the current directory as the source
#   --remote=origin   → set the new GitHub repo as the "origin" remote
#   --push            → immediately push the initial commit

# ── OR ── interactive wizard (asks you everything step by step)
gh repo create
```

### Step 3 — Add a description and topics (tags)

```bash
# Set a description and homepage URL
gh repo edit --description "Personal portfolio — projects & experiments" \
             --homepage "https://yourusername.github.io"

# Add topics (keywords that make the repo discoverable)
gh repo edit --add-topic portfolio --add-topic python --add-topic open-source
```

### Step 4 — Enable GitHub Pages (optional, for a live site)

```bash
# Enable Pages from the main branch (serves index.html or README)
gh api repos/yourusername/my-portfolio/pages \
  --method POST \
  --field source='{"branch":"main","path":"/"}'

# Or just open the settings page in the browser
gh repo view --web
# Then go to: Settings → Pages → Source → main branch
```

### Step 5 — Protect the main branch

```bash
# Open branch protection settings in the browser
gh api repos/yourusername/my-portfolio/branches/main/protection \
  --method PUT \
  --field required_status_checks=null \
  --field enforce_admins=true \
  --field required_pull_request_reviews=null \
  --field restrictions=null

# Simpler: open in browser and set manually
gh repo view --web   # → Settings → Branches → Add rule
```

### Step 6 — Day-to-day push workflow

```bash
# Create and switch to a feature branch
git checkout -b add-project-x

# ... make changes ...

git add .
git commit -m "add project x to portfolio"
git push origin add-project-x

# Open a Pull Request from CLI
gh pr create --title "Add Project X" --body "Adds my latest project" --base main

# Merge the PR (after review / checks pass)
gh pr merge --squash --delete-branch
```

---

## 🔀 Pull Requests

```bash
# List open PRs in current repo
gh pr list

# View a specific PR
gh pr view 42

# Check out a PR locally to review/test it
gh pr checkout 42

# Create a PR (interactive)
gh pr create

# Create a PR with all details inline
gh pr create --title "Fix login bug" --body "Resolves #12" --base main

# Approve a PR
gh pr review 42 --approve

# Request changes
gh pr review 42 --request-changes --body "Please add tests"

# Merge a PR
gh pr merge 42 --squash            # squash all commits into one
gh pr merge 42 --merge             # standard merge commit
gh pr merge 42 --rebase            # rebase onto base branch

# Close a PR without merging
gh pr close 42

# List PRs you need to review
gh pr list --search "review-requested:@me"
```

---

## 🐛 Issues

```bash
# List open issues
gh issue list

# List issues assigned to you
gh issue list --assignee @me

# View an issue
gh issue view 7

# Create an issue (interactive)
gh issue create

# Create an issue inline
gh issue create --title "Bug: login fails" --body "Steps to reproduce..." --label bug

# Close an issue
gh issue close 7

# Reopen a closed issue
gh issue reopen 7

# Add a comment to an issue
gh issue comment 7 --body "Fixed in PR #42"
```

---

## ⚡ Releases

```bash
# List all releases
gh release list

# Create a release from a tag
gh release create v1.0.0 --title "v1.0.0 — Initial Release" --notes "First stable version"

# Auto-generate release notes from merged PRs
gh release create v1.1.0 --generate-notes

# Upload files to a release (e.g. a build artifact)
gh release upload v1.0.0 ./dist/my-app.tar.gz

# View a release
gh release view v1.0.0
```

---

## 🔍 Search

```bash
# Search for repos by topic
gh search repos --topic python --topic portfolio --limit 10

# Search for repos by language and stars
gh search repos "data science" --language python --stars ">500"

# Search for issues across GitHub
gh search issues "auth bug" --repo yourusername/my-portfolio

# Search for code (opens in browser — API restricted)
gh search code "def login" --repo yourusername/my-portfolio
```

---

## 🤖 GitHub Actions (CI/CD) from CLI

```bash
# List recent workflow runs
gh run list

# Watch a workflow run in real time
gh run watch

# View details of a specific run
gh run view 1234567890

# Re-run a failed workflow
gh run rerun 1234567890

# Download workflow artifacts
gh run download 1234567890

# Trigger a workflow manually (must have workflow_dispatch trigger)
gh workflow run deploy.yml

# List all workflows
gh workflow list

# Enable or disable a workflow
gh workflow enable deploy.yml
gh workflow disable deploy.yml
```

---

## ⚙️ Config & Aliases

```bash
# Show current gh config
gh config list

# Set default editor
gh config set editor "code --wait"    # VS Code
gh config set editor vim

# Set default protocol
gh config set git_protocol ssh        # recommended
gh config set git_protocol https

# ─── Aliases — create shortcuts for long commands ───────────────────────────

# Create an alias
gh alias set prc 'pr create --web'
gh alias set tidy 'pr merge --squash --delete-branch'

# List all aliases
gh alias list

# Delete an alias
gh alias delete prc
```

---

## 🌐 Open Anything in the Browser

```bash
# Open the current repo
gh repo view --web

# Open a specific PR in browser
gh pr view 42 --web

# Open an issue in browser
gh issue view 7 --web

# Open the Actions tab
gh run list --web
```

---

## ⚡ Quick Reference

| Goal | Command |
|---|---|
| Check login status | `gh auth status` |
| Switch account | `gh auth switch --user username` |
| Create repo from current folder | `gh repo create name --public --source=. --remote=origin --push` |
| Clone any repo | `gh repo clone user/repo` |
| Open PR from current branch | `gh pr create` |
| Merge PR (squash) | `gh pr merge --squash --delete-branch` |
| Watch CI run | `gh run watch` |
| Re-run failed CI | `gh run rerun <id>` |
| Add topic to repo | `gh repo edit --add-topic topic-name` |
| Edit repo description | `gh repo edit --description "..."` |

---

## 🚨 Common Gotchas

1. **`gh` vs `git`** — `gh` talks to the GitHub API; `git` manages your local repo and commits. You need both.
2. **SSH vs HTTPS** — SSH is smoother for multi-account setups. Use `~/.ssh/config` host aliases to avoid conflicts.
3. **Token scopes** — if a command fails with `403`, your PAT may be missing scopes. Re-run `gh auth login` and select broader permissions.
4. **Multi-account `GH_TOKEN`** — setting `GH_TOKEN` env var overrides all account switching. Unset it if switching isn't working.
5. **`gh repo create` needs an empty or new folder** — if the remote already exists, use `gh repo clone` or add the remote manually with `git remote add`.
6. **`version: 2.40+` for multi-account** — older versions only support one account. Run `gh upgrade` or reinstall if needed.

---

*GitHub CLI docs: https://cli.github.com/manual*
