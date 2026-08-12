# ===========================================================================
# Script name: config_loader.py
# Purpose:     Reads .env from the repository root and exposes every
#              KEY=VALUE pair as a module-level variable.
#
#              Usage in any script:
#                  import config_loader
#                  my_path = config_loader.MY_KEY
#
#              To add a new path: open .env and add a line:
#                  MY_NEW_PATH=\\server\share\folder
#              Then access it with: config_loader.MY_NEW_PATH
#
#              .env is listed in .gitignore — it is never committed.
#
# Created: 2026-07-22
# ===========================================================================

import os

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def _load_env(path):
    """Parse KEY=VALUE pairs from a .env file.
    Lines that are blank or start with # are ignored."""
    result = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip()
    return result


if not os.path.isfile(_ENV_PATH):
    raise FileNotFoundError(
        f".env file not found at:\n  {_ENV_PATH}\n"
        "Create a .env file at the repository root and add your paths.\n"
        "Example entry:  UPDATE_MGMT_BASE=\\\\server\\share\\folder\n"
        "See the existing .env entries for the full list of required keys."
    )

# Load all KEY=VALUE pairs and expose them as module-level attributes.
# After this block, any script can do:
#   import config_loader
#   config_loader.UPDATE_MGMT_BASE   # returns the path string
_env = _load_env(_ENV_PATH)
globals().update(_env)


