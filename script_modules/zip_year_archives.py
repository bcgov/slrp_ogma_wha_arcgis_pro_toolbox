"""
zip_year_archives.py

Recursively walks all subdirectories under ROOT_DIR and zips every .gdb
folder it finds, placing the .zip alongside the original .gdb.

- If a .zip with the same name already exists, the .gdb is skipped.
- Originals are kept after zipping.
- Errors on individual items are logged and execution continues.
- A log file is written to the same directory as this script.
"""

import os
import sys
import zipfile
import logging
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIGURATION — ROOT_DIR is loaded from config.json
# ---------------------------------------------------------------------------
# ORIGINAL: ROOT_DIR was a hardcoded placeholder string that the user had to
#           edit in-place before running the script.
# CHANGE: ROOT_DIR is now read from config.json (zip_year_archives.root_dir)
#         via config_loader so no path is ever committed to source control.
# RISK: If config.json is absent or the key is a placeholder, config_loader
#       raises before logging is set up; the error prints to stderr.
# DOWNSTREAM: Only ROOT_DIR is affected; all zip/walk logic below is unchanged.

# Ensure script_modules/ is on sys.path so config_loader can be imported
# when this script is run directly (not through the toolbox).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import config_loader
ROOT_DIR = config_loader.get("zip_year_archives", "root_dir")
# ---------------------------------------------------------------------------

SCRIPT_DIR = _SCRIPT_DIR
LOG_FILE = os.path.join(
     SCRIPT_DIR,
    f"zip_year_archives_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def zip_gdb(source_path: str, zip_path: str) -> None:
    """Recursively zip a .gdb folder to zip_path."""
    base_name = os.path.basename(source_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for dir_path, _sub_dirs, files in os.walk(source_path):
            for file_name in files:
                abs_file = os.path.join(dir_path, file_name)
                rel_path = os.path.join(
                    base_name,
                    os.path.relpath(abs_file, source_path),
                )
                zf.write(abs_file, rel_path)


def main() -> None:
    if not os.path.isdir(ROOT_DIR):
        log.error("ROOT_DIR does not exist or is not accessible: %s", ROOT_DIR)
        return

    log.info("Starting archive run. ROOT_DIR: %s", ROOT_DIR)

    total_zipped = 0
    total_skipped = 0
    total_errors = 0

    for dir_path, sub_dirs, _files in os.walk(ROOT_DIR):
        # Collect .gdb entries before pruning sub_dirs so os.walk does not
        # descend into them (a .gdb is a flat folder, no need to recurse inside).
        gdbs = [d for d in sub_dirs if d.lower().endswith(".gdb")]
        sub_dirs[:] = [d for d in sub_dirs if not d.lower().endswith(".gdb")]

        for gdb_name in sorted(gdbs):
            source_path = os.path.join(dir_path, gdb_name)
            zip_path = source_path + ".zip"

            if os.path.exists(zip_path):
                log.info("SKIP (zip exists): %s", source_path)
                total_skipped += 1
                continue

            log.info("Zipping: %s", source_path)
            try:
                zip_gdb(source_path, zip_path)
                log.info("OK: %s", zip_path)
                total_zipped += 1
            except Exception as exc:  # noqa: BLE001
                log.error("ERROR zipping %s: %s", source_path, exc)
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except OSError:
                        pass
                total_errors += 1

    log.info(
        "Done. Zipped: %d  |  Skipped: %d  |  Errors: %d",
        total_zipped,
        total_skipped,
        total_errors,
    )
    log.info("Log written to: %s", LOG_FILE)


if __name__ == "__main__":
    main()
