#!/usr/bin/env python3
"""Print the app name, derived from the git repo's toplevel directory name.
Strips a trailing '-config' suffix if present, so both the app repo and
its companion config repo resolve to the same app name.
"""
import subprocess
import sys
from pathlib import Path


def get_app_name():
    try:
        repo_name = Path(
            subprocess.check_output(
                ['git', 'rev-parse', '--show-toplevel'], text=True
            ).strip()
        ).name
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("Must be run inside a git repository (and git must be installed).")
    return repo_name[:-len('-config')] if repo_name.endswith('-config') else repo_name


if __name__ == "__main__":
    print(get_app_name())
