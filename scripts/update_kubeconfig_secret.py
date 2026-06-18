#!/usr/bin/env python3
"""Push the local k3d kubeconfig to the GitHub repo's KUBECONFIG secret.

NOTE: This kubeconfig points at the local k3d cluster (127.0.0.1).
It is only reachable by a self-hosted GitHub Actions runner running on this
same machine. GitHub-hosted runners (runs-on: ubuntu-latest) cannot reach it.
If your CI/CD uses GitHub-hosted runners and ArgoCD's pull-based GitOps model,
you likely don't need this script at all — ArgoCD reads from the config repo
directly and CI never needs cluster access.
"""
import os
import subprocess
import sys
import tempfile


def make_temp_file(content, suffix=''):
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        os.chmod(path, 0o600)
    except Exception:
        os.unlink(path)
        raise
    return path


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: update_kubeconfig_secret.py <app_name>")
    app_name = sys.argv[1]

    print("This will upload your LOCAL k3d kubeconfig to GitHub secrets.")
    print("Only works with a self-hosted runner on this machine. See script docstring.")
    if input("Continue? (y/n): ").strip().lower() != 'y':
        return

    result = subprocess.run(
        ['k3d', 'kubeconfig', 'get', app_name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        sys.exit(f"Failed to get kubeconfig from k3d: {result.stderr}")

    kubeconfig_path = make_temp_file(result.stdout)
    try:
        with open(kubeconfig_path, 'r') as f:
            subprocess.run(['gh', 'secret', 'set', 'KUBECONFIG'], stdin=f, check=True)
    finally:
        if os.path.exists(kubeconfig_path):
            os.remove(kubeconfig_path)

    print("[  OK  ] KUBECONFIG secret updated.")


if __name__ == "__main__":
    main()
