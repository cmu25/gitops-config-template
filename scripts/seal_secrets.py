#!/usr/bin/env python3
"""Seal database credentials into k8s/secrets/<app>-db-secret.yaml using kubeseal.

Credentials come from DB_USERNAME / DB_PASSWORD in .env if set, otherwise
the script prompts interactively. Safe to re-run to rotate credentials.
"""
import getpass
import os
import subprocess
import sys


def kubectl_apply_dry_run(args):
    producer = subprocess.run(
        args + ['--dry-run=client', '-o', 'yaml'],
        check=True, capture_output=True, text=True
    )
    subprocess.run(['kubectl', 'apply', '-f', '-'], input=producer.stdout, check=True, text=True)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: seal_secrets.py <app_name>")
    app_name = sys.argv[1]

    secret_file = f"k8s/secrets/{app_name}-db-secret.yaml"
    if not os.path.exists(secret_file):
        sys.exit(f"Secret template not found: {secret_file}\n"
                  f"Ensure the file exists (even as a placeholder) before running this.")

    with open(secret_file, 'r') as f:
        content = f.read()

    if 'REPLACE_WITH_SEALED_VALUE' not in content:
        print("[  OK  ] Sealed secret already exists.")
        if input("Re-seal with new credentials? (y/n): ").strip().lower() != 'y':
            return

    username = os.environ.get("DB_USERNAME") or input("  Database username: ").strip()
    password = os.environ.get("DB_PASSWORD") or getpass.getpass("  Database password: ")

    if not username or not password:
        sys.exit("Username and password cannot be empty.")

    # Ensure the namespace exists before sealing into it.
    kubectl_apply_dry_run(['kubectl', 'create', 'namespace', app_name])

    print("Sealing secret...")
    secret_manifest = subprocess.run(
        ['kubectl', 'create', 'secret', 'generic', f'{app_name}-db-secret',
         f'--from-literal=username={username}',
         f'--from-literal=password={password}',
         f'--namespace={app_name}',
         '--dry-run=client', '-o', 'yaml'],
        check=True, capture_output=True, text=True
    )
    with open(secret_file, 'w') as out_f:
        subprocess.run(
            ['kubeseal', '--format', 'yaml'],
            input=secret_manifest.stdout, stdout=out_f, check=True, text=True
        )

    print(f"[  OK  ] Secret sealed into {secret_file} — remember to commit and push it.")


if __name__ == "__main__":
    main()
