#!/usr/bin/env python3
"""Check that required environment variables are set before bootstrap proceeds.
Run by `task check-env`. dotenv loading is handled by Task itself.
"""
import os
import sys

REQUIRED = ["BOT_ID", "BOT_APP_INSTALLATION_ID", "BOT_PRIVATE_KEY"]


def main():
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        print("Missing required environment variables:")
        for name in missing:
            print(f"  - {name}")
        print("\nFill these in your .env file (see .env.example for where to find each value).")
        sys.exit(1)

    # Sanity-check the private key looks like a PEM, not a file path or empty string.
    key = os.environ["BOT_PRIVATE_KEY"]
    if "BEGIN" not in key or "PRIVATE KEY" not in key:
        sys.exit(
            "BOT_PRIVATE_KEY does not look like a PEM-formatted private key.\n"
            "Make sure you pasted the full contents of the .pem file, "
            "including the BEGIN/END lines."
        )

    print("Environment looks good.")


if __name__ == "__main__":
    main()
