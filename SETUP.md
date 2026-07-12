# Setup

## Prerequisites (one-time, per machine)

1. **Docker**
    - macOS / Linux: [Docker Desktop](https://www.docker.com/products/docker-desktop) or Docker Engine
    - Windows: see the [Windows section](#windows) below — Docker Desktop with WSL2 backend

2. **Mise** — manages all other tool versions ([install instructions](https://mise.jdx.dev/getting-started.html))
    - macOS: `brew install mise`
    - Linux: `curl https://mise.run | sh`
    - Windows: run from inside WSL2, same as Linux
Confirm mise is activated in your shell (`which mise` should return a path); if not, add `eval "$(mise activate bash)"` to your `~/.bashrc`

3. **A GitHub App** already created and installed on your repos, with:
    - App ID
    - Installation ID
    - A private key (.pem)

   (If you don't have one yet, create it from your GitHub account: Settings → Developer settings → GitHub Apps → New GitHub App, then generate a private key and install it on this repo.)

## First-time setup

```bash
git clone <repo>
cd <repo>

mise install              # installs kubectl, helm, k3d, kubeseal, gh, task — all pinned versions

cp .env.example .env      # then fill in BOT_ID, BOT_APP_INSTALLATION_ID, BOT_PRIVATE_KEY. Just paste the content of the .env file you downloaded.
                           # (see .env.example for exactly where to find each value)

task bootstrap             # creates the cluster, installs ArgoCD, registers GitOps apps
task seal-secrets          # one-time: prompts for DB credentials, seals them
```

That's it. `task bootstrap` is fully automated once `.env` is filled in.

## Day-to-day commands

```bash
task up        # start a previously-stopped cluster
task down      # stop the cluster (frees resources, preserves state)
task status    # check cluster and ArgoCD health
task reset     # destroy and recreate everything from scratch
```

## Windows

Local Kubernetes tooling (k3d, Docker) works best through WSL2 rather than native Windows. The setup:

1. Install WSL2: open PowerShell **as Administrator** and run:
   ```powershell
   wsl --install
   ```
   Reboot if prompted.

2. Install Docker Desktop for Windows, and during setup ensure **"Use WSL 2 based engine"** is checked.

3. In Docker Desktop: **Settings → Resources → WSL Integration**, enable your installed Linux distro (e.g. Ubuntu).

4. **Run all commands from inside your WSL2 terminal** (open "Ubuntu" from the Start menu), not from PowerShell or cmd. From there, `mise`, `task`, `k3d`, `kubectl`, etc. all behave exactly as they would on native Linux.

5. Avoid passing `--network=host` to k3d — the default Docker bridge network works correctly through Docker Desktop's WSL2 integration and is what this template uses.

## Troubleshooting

**`task bootstrap` fails partway through.** Each step is independently re-runnable — re-run `task bootstrap` and steps that already succeeded (cluster exists, ArgoCD installed, etc.) will be skipped automatically.

**Docker daemon not running.** Start Docker Desktop (macOS/Windows) or `sudo systemctl start docker` (Linux), then re-run.

**`.env` validation fails.** Run `task check-env` directly for a detailed error message about which variable is missing or malformed.

**CI/CD and the local cluster.** If your GitHub Actions workflows run on GitHub-hosted runners, they cannot reach this local k3d cluster directly. The intended flow is: CI builds and pushes an image, then updates the image tag in your config repo — ArgoCD (running inside the cluster) pulls that change and redeploys. CI never needs direct cluster access. `task update-kubeconfig-secret` exists only for self-hosted runner setups; most users won't need it.
