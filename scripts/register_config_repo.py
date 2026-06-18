#!/usr/bin/env python3
"""Register the GitOps config repo with ArgoCD, using GitHub App credentials
read from the environment (populated from .env by Task's dotenv loading).

No interactive prompts here by design — credentials come entirely from .env,
which the user fills in once from their GitHub App settings page.
"""
import os
import subprocess
import sys
import tempfile


def make_temp_file(content, suffix=''):
    """Write content to a secure tempfile (mode 0o600). Returns the path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        os.chmod(path, 0o600)
    except Exception:
        os.unlink(path)
        raise
    return path


def kubectl_apply_dry_run(args):
    """Run a kubectl command with --dry-run=client -o yaml, pipe result to kubectl apply.
    No shell involved — avoids injection risk from any interpolated values."""
    producer = subprocess.run(
        args + ['--dry-run=client', '-o', 'yaml'],
        check=True, capture_output=True, text=True
    )
    subprocess.run(['kubectl', 'apply', '-f', '-'], input=producer.stdout, check=True, text=True)


def get_repo_owner():
    result = subprocess.run(
        ['gh', 'repo', 'view', '--json', 'owner', '--jq', '.owner.login'],
        capture_output=True, text=True
    )
    owner = result.stdout.strip()
    if not owner:
        sys.exit("Failed to determine GitHub repo owner. Check that 'gh' is authenticated "
                  "(run 'gh auth login') and that you are inside a GitHub repo.")
    return owner


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: register_config_repo.py <app_name>")
    app_name = sys.argv[1]

    app_id          = os.environ.get("BOT_ID")
    installation_id = os.environ.get("BOT_APP_INSTALLATION_ID")
    private_key      = os.environ.get("BOT_PRIVATE_KEY")

    if not all([app_id, installation_id, private_key]):
        sys.exit("BOT_ID, BOT_APP_INSTALLATION_ID, and BOT_PRIVATE_KEY must be set in .env. "
                  "Run 'task check-env' for details.")

    owner = get_repo_owner()
    repo_url = f"https://github.com/{owner}/{app_name}-config"

    private_key_path = make_temp_file(private_key, suffix='.pem')
    try:
        kubectl_apply_dry_run([
            'kubectl', 'create', 'secret', 'generic', f'{app_name}-config-repo',
            '--namespace', 'argocd',
            '--from-literal=type=git',
            f'--from-literal=url={repo_url}',
            f'--from-literal=githubAppID={app_id}',
            f'--from-literal=githubAppInstallationID={installation_id}',
            f'--from-file=githubAppPrivateKey={private_key_path}',
        ])
        subprocess.run(
            ['kubectl', 'label', '--overwrite', 'secret', f'{app_name}-config-repo',
             '-n', 'argocd', 'argocd.argoproj.io/secret-type=repository'],
            check=True
        )
    finally:
        if os.path.exists(private_key_path):
            os.remove(private_key_path)

    print(f"[  OK  ] Config repo registered with ArgoCD: {repo_url}")


if __name__ == "__main__":
    main()
