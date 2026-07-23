# ===========================================================================
# Script name: check_in_dataset.py
# Purpose:     Standalone module for the OGMA/LU/SLRP/WHA dataset check-in
#              workflow. Called by the CheckInDataset tool in
#              slrp_ogma_arcpro_toolbox.pyt.
#
# Workflow steps (in order):
#   1. List files present in the UpdateWorkArea directory (checklist)
#   2. Run Attribute QA/QC on the chosen feature class
#   3. Display topology report rows (user determines pass/fail)
#   4. Copy the Returned FGDB to UpdateManagement\<Type>\CurrentUpdate
#   5. Copy QA reports and topology report to Update_Emails destination folder
#
# IMPORTANT — read-only on source data:
#   This script MUST NOT modify, lock, or write to the source FGDB in any way.
#   It copies data out; it never edits data in.
#
# Created: 2026-06-04
# ===========================================================================

import arcpy
import csv
import importlib
import os
import shutil
import sys

# Ensure script_modules/ is on sys.path so config_loader (and other peer
# modules) can be found whether this file is run standalone or imported from
# the .pyt toolbox.  __file__ lives in script_modules/, so its dirname IS the
# correct directory — no subdirectory navigation needed.
_modules_dir = os.path.dirname(os.path.abspath(__file__))
if _modules_dir not in sys.path:
    sys.path.insert(0, _modules_dir)

import config_loader


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Maps a substring found in the Returned GDB basename (lowercased) to the
# short TYPE token used in destination path construction.
GDB_NAME_TO_TYPE = {
    "old_growth_management_area": "OGMA",
    "landscape_unit":             "LU",
    "slrp_planning":              "SLRP",
    "wildlife_habitat_area":      "WHA",
}

# Maps the TYPE token to the folder name used under UpdateManagement.
TYPE_TO_FOLDER = {
    "OGMA": "OldGrowthManagementAreas",
    "LU":   "LandscapeUnits",
    "SLRP": "StrategicLandResourcePlans",
    "WHA":  "WildlifeHabitatAreas",
}

# Root of UpdateManagement on spatialfiles3.
# Loaded from .env via config_loader — do NOT hardcode this path here.
# NOTE: This constant is retained as an informational reference only. It is
# NO LONGER used to derive the copy destination in copy_returned_fgdb().
# The destination CurrentUpdate folder is now supplied by the caller (the
# CheckInDataset toolbox parameter, or the standalone __main__ block) so the
# tool cannot silently write to production when the operator has selected
# sandbox inputs. See the incident on 2026-07-23 that motivated the change.
UPDATE_MGMT_BASE = config_loader.UPDATE_MGMT_BASE


# ---------------------------------------------------------------------------
# Step 2: List files present in the update directory
# ---------------------------------------------------------------------------

def list_update_directory_files(update_dir):
    """Scan *update_dir* for the files expected at check-in time and report
    which are present and which are missing.

    Expected files
    --------------
    - Returned FGDB  : the single .gdb folder in the update directory
                       (naming convention varies in practice; the user has
                       confirmed there is only ever one .gdb per update dir)
    - QA/QC report(s): one or more *.txt files
    - Topology report: topology_report.csv

    Returns a dict with keys:
        'returned_gdb'    : full path to the Returned GDB folder, or None
        'qa_reports'      : list of full .txt paths (may be empty)
        'topology_report' : full path to topology_report.csv, or None
    """
    arcpy.AddMessage("")
    arcpy.AddMessage("=" * 60)
    arcpy.AddMessage("FILE CHECKLIST — " + update_dir)
    arcpy.AddMessage("=" * 60)

    result = {
        "returned_gdb":    None,
        "qa_reports":      [],
        "topology_report": None,
    }

    if not os.path.isdir(update_dir):
        arcpy.AddError("Update directory does not exist or is not accessible: " + update_dir)
        return result

    entries = os.listdir(update_dir)

    # --- Returned GDB ---
    # Expectation (set by the user): the update directory contains exactly
    # one .gdb. Doesnt enforce a strict naming pattern — actual files in
    # the wild use varying conventions (e.g. _Update_YYYYMMDD_Returned_YYYYMMDD,
    # _update_YYYYMMDD, _returned_YYYYMMDD). Just pick the single .gdb.
    gdbs_found = [
        os.path.join(update_dir, e)
        for e in entries
        if e.lower().endswith(".gdb") and os.path.isdir(os.path.join(update_dir, e))
    ]
    if len(gdbs_found) == 1:
        result["returned_gdb"] = gdbs_found[0]
        arcpy.AddMessage("  [PRESENT] Returned FGDB : " + os.path.basename(gdbs_found[0]))
    elif len(gdbs_found) == 0:
        arcpy.AddWarning("  [MISSING] Returned FGDB  (no .gdb found in the update directory)")
    else:
        arcpy.AddWarning(
            "  [AMBIGUOUS] More than one .gdb found in the update directory: "
            + ", ".join(os.path.basename(p) for p in gdbs_found)
        )

    # --- QA/QC reports (.txt) ---
    for entry in entries:
        full_path = os.path.join(update_dir, entry)
        if entry.lower().endswith(".txt") and os.path.isfile(full_path):
            result["qa_reports"].append(full_path)
            arcpy.AddMessage("  [PRESENT] QA/QC report   : " + entry)
    if not result["qa_reports"]:
        arcpy.AddWarning("  [MISSING] QA/QC report   (expected: *_attribute_check_*.txt)")

    # --- Topology report ---
    topo_path = os.path.join(update_dir, "topology_report.csv")
    if os.path.isfile(topo_path):
        result["topology_report"] = topo_path
        arcpy.AddMessage("  [PRESENT] Topology report: topology_report.csv")
    else:
        arcpy.AddWarning("  [MISSING] Topology report: topology_report.csv")

    arcpy.AddMessage("=" * 60)
    return result


# ---------------------------------------------------------------------------
# Step 3: Run Attribute QA/QC
# ---------------------------------------------------------------------------

def run_attribute_qa(in_dataset_path, master_dataset_path):
    """Import and run attribute_qa_v8.run() against the chosen feature class.

    Parameters
    ----------
    in_dataset_path    : str  Full catalog path to the feature class being checked in.
    master_dataset_path: str  Full catalog path to the master/replica reference FC.

    Returns
    -------
    str  Path to the generated .txt QA report file (attribute_qa_v8.attributeQAReportFile).

    Raises
    ------
    Exception  Re-raises any exception from attribute_qa_v8 so the caller can
               block the copy steps.
    """
    arcpy.AddMessage("")
    arcpy.AddMessage("=" * 60)
    arcpy.AddMessage("ATTRIBUTE QA/QC")
    arcpy.AddMessage("=" * 60)
    arcpy.AddMessage("Input dataset : " + in_dataset_path)
    arcpy.AddMessage("Master dataset: " + master_dataset_path)

    # Ensure the script_modules directory is on sys.path so attribute_qa_v8 can be found
    # __file__ is script_modules/check_in_dataset.py, so script_modules is its own directory
    modules_dir = os.path.dirname(os.path.abspath(__file__))
    if modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    import attribute_qa_v8
    importlib.reload(attribute_qa_v8)

    # This call raises on failure — let it propagate to run() which will abort
    attribute_qa_v8.run(in_dataset_path, master_dataset_path)

    report_path = attribute_qa_v8.attributeQAReportFile
    arcpy.AddMessage("")
    arcpy.AddMessage("QA report: " + report_path)
    return report_path


# ---------------------------------------------------------------------------
# Step 4: Display topology report
# ---------------------------------------------------------------------------

def read_topology_report(update_dir):
    """Read topology_report.csv from *update_dir* and print every row as a
    message. The user is responsible for determining pass/fail.

    The file is encoded in UTF-16 LE (exported by ArcGIS Pro topology viewer).
    The 'utf-16' codec auto-detects the BOM, so no explicit byte-order mark
    handling is required.

    Returns the number of data rows found (0 if file absent or empty).
    """
    arcpy.AddMessage("")
    arcpy.AddMessage("=" * 60)
    arcpy.AddMessage("TOPOLOGY REPORT")
    arcpy.AddMessage("=" * 60)

    topo_path = os.path.join(update_dir, "topology_report.csv")
    if not os.path.isfile(topo_path):
        arcpy.AddWarning("topology_report.csv not found in " + update_dir + " — skipping.")
        return 0

    row_count = 0
    try:
        with open(topo_path, encoding="utf-16") as f:
            reader = csv.reader(f)
            for row in reader:
                arcpy.AddMessage("  " + ", ".join(row))
                row_count += 1
    except Exception as exc:
        arcpy.AddWarning("Could not read topology_report.csv: " + str(exc))
        return 0

    arcpy.AddMessage("Total rows in topology report: " + str(row_count))
    arcpy.AddMessage("=" * 60)
    return row_count


# ---------------------------------------------------------------------------
# Step 5: Copy the Returned FGDB
# ---------------------------------------------------------------------------

def _derive_type_token(gdb_path):
    """Derive the short TYPE token from the Returned GDB path by substring-
    matching the GDB basename (lowercased) against GDB_NAME_TO_TYPE.

    Returns the token string (e.g. 'OGMA') or None if no match found.
    """
    gdb_basename_lower = os.path.basename(gdb_path).lower()
    for substring, token in GDB_NAME_TO_TYPE.items():
        if substring in gdb_basename_lower:
            return token
    return None


def copy_returned_fgdb(returned_gdb_path, dest_current_dir, type_token):
    """Copy the entire Returned FGDB into *dest_current_dir* (a CurrentUpdate
    folder chosen by the caller).

    Uses arcpy.management.Copy() which creates a fresh copy and leaves the
    source completely unmodified (no schema locks acquired on the source GDB).

    Parameters
    ----------
    returned_gdb_path : str  Full path to the Returned FGDB folder.
    dest_current_dir  : str  Full path to the destination CurrentUpdate folder.
                              Supplied by the caller (toolbox parameter or
                              standalone __main__) so the destination is
                              always driven by an explicit user choice, never
                              by an implicit .env constant.
    type_token        : str  One of OGMA / LU / SLRP / WHA. Used ONLY for
                              logging so the operator can confirm the tool
                              correctly recognised the dataset type; the
                              destination path no longer depends on it.

    Returns
    -------
    str  Full path to the copied GDB in the destination.

    Raises
    ------
    Exception  Re-raises arcpy errors so the caller can report them.
    """
    arcpy.AddMessage("")
    arcpy.AddMessage("=" * 60)
    arcpy.AddMessage("COPYING RETURNED FGDB")
    arcpy.AddMessage("=" * 60)

    dest_dir = dest_current_dir
    gdb_basename = os.path.basename(returned_gdb_path)
    dest_gdb_path = os.path.join(dest_dir, gdb_basename)

    arcpy.AddMessage("Detected dataset type : " + type_token)
    arcpy.AddMessage("Source                : " + returned_gdb_path)
    arcpy.AddMessage("Destination folder    : " + dest_dir)
    arcpy.AddMessage("Destination GDB       : " + dest_gdb_path)

    if not os.path.isdir(dest_dir):
        arcpy.AddError("Destination directory does not exist: " + dest_dir)
        raise FileNotFoundError("Destination directory does not exist: " + dest_dir)

    # ORIGINAL: When a GDB already existed at the destination, the code only logged
    #           a warning and let arcpy.management.Copy() overwrite it. That overwrite
    #           succeeded ONLY because attribute_qa_v8 (imported in Step 3) sets
    #           env.overwriteOutput = True at module level — an inherited global side
    #           effect, not a decision made here. Result: the previous CurrentUpdate
    #           GDB was silently destroyed with no backup and no provenance.
    # CHANGE:   Before copying, rename EVERY existing (not-already-flagged) .gdb in
    #           CurrentUpdate by appending "_to_delete", leaving it in place for the
    #           DRM to remove later. Then copy the new Returned FGDB in alongside it
    #           with overwriteOutput explicitly forced False, so a residual name
    #           collision errors loudly instead of silently clobbering. Nothing is
    #           deleted or overwritten by this tool.
    # RISK:     os.rename raises OSError (e.g. PermissionError) if the existing GDB
    #           holds a schema lock — most often because it is open in this Pro
    #           session. That is caught below and re-raised with a detailed, actionable
    #           message; the check-in aborts before any copy, so nothing is destroyed.
    #           A leftover "*_to_delete.gdb" from a prior cycle also aborts (fail-safe)
    #           rather than being silently removed.
    # DOWNSTREAM: After check-in, CurrentUpdate holds TWO gdbs: the fresh Returned FGDB
    #           and the "_to_delete" incumbent. Any later step that assumes exactly one
    #           .gdb in CurrentUpdate must skip "*_to_delete.gdb". CheckInDataset.md
    #           Step 5 still documents the old "overwritten" behavior — separate doc fix.
    flagged_gdbs = []  # list of (original_name, flagged_name) tuples for the summary block
    for entry in os.listdir(dest_dir):
        entry_path = os.path.join(dest_dir, entry)
        if (entry.lower().endswith(".gdb")
                and os.path.isdir(entry_path)
                and not entry.lower().endswith("_to_delete.gdb")):
            flagged_name = entry[:-len(".gdb")] + "_to_delete.gdb"
            flagged_path = os.path.join(dest_dir, flagged_name)
            if os.path.exists(flagged_path):
                arcpy.AddError(
                    "Cannot flag the existing GDB for deletion — a '_to_delete' copy "
                    "already exists at:\n"
                    "    " + flagged_path + "\n"
                    "This is a leftover from a previous check-in cycle. Delete (or "
                    "move) it manually, then re-run check-in. No data was copied or "
                    "deleted."
                )
                raise FileExistsError(flagged_path)
            try:
                os.rename(entry_path, flagged_path)
            except OSError as exc:
                arcpy.AddError(
                    "Could not flag the existing CurrentUpdate GDB for deletion, so "
                    "check-in has been aborted. No data was copied or deleted.\n"
                    "  Tried to rename:\n"
                    "    " + entry_path + "\n"
                    "  to:\n"
                    "    " + flagged_path + "\n"
                    "  The operating system reported: " + str(exc) + "\n"
                    "  This almost always means the GDB is locked. The most common "
                    "cause is that the GDB — or a feature class inside it — is "
                    "currently open in this ArcGIS Pro session (or in ArcCatalog / "
                    "another application), which leaves a schema lock (.lock files "
                    "inside the .gdb folder).\n"
                    "  To fix: remove any layers from this GDB from the map, close "
                    "any other application that has it open, then re-run this tool. "
                    "If the lock persists, closing and reopening ArcGIS Pro will "
                    "clear it."
                )
                raise
            flagged_gdbs.append((entry, flagged_name))
            arcpy.AddMessage(
                "  Renamed in place:  " + entry + "  ->  " + flagged_name
            )

    if flagged_gdbs:
        arcpy.AddMessage("")
        arcpy.AddMessage("-" * 60)
        arcpy.AddMessage("EXISTING GDB(s) FLAGGED FOR LATER DELETION")
        arcpy.AddMessage("-" * 60)
        arcpy.AddMessage(
            "The previous CurrentUpdate GDB(s) were renamed in place (NOT moved). "
            "They are still located in the destination CurrentUpdate folder shown "
            "below, alongside the newly checked-in GDB. The DRM should review and "
            "delete them manually once the new check-in is confirmed good."
        )
        arcpy.AddMessage("")
        arcpy.AddMessage("Location: " + dest_dir)
        arcpy.AddMessage("")
        arcpy.AddMessage("Flagged GDBs (full paths):")
        for _, flagged_name in flagged_gdbs:
            arcpy.AddMessage("  " + os.path.join(dest_dir, flagged_name))
        arcpy.AddMessage("-" * 60)

    # Copy with overwrite explicitly disabled so any residual name collision raises
    # loudly rather than silently replacing data. Restore the prior value afterward so
    # this function does not leak an env change to later steps.
    previous_overwrite = arcpy.env.overwriteOutput
    arcpy.env.overwriteOutput = False
    try:
        arcpy.management.Copy(returned_gdb_path, dest_gdb_path)
    finally:
        arcpy.env.overwriteOutput = previous_overwrite
    arcpy.AddMessage("FGDB copy complete.")
    return dest_gdb_path


# ---------------------------------------------------------------------------
# Step 6: Copy reports to UpdateEmail destination folder
# ---------------------------------------------------------------------------

def copy_reports_to_email_folder(qa_report_txt_path, topology_report_path, email_folder):
    """Copy QA/QC report files and the topology report directly into the
    UpdateEmail folder the user navigated to.

    QA report files copied (all co-located, derived by swapping extension):
        *.txt, *.json, *.html

    Parameters
    ----------
    qa_report_txt_path   : str or None  Path to the .txt QA report.
    topology_report_path : str or None  Path to topology_report.csv, or None.
    email_folder         : str          Path of the UpdateEmail folder the user
                                        navigated to. Files are written here
                                        directly (no subfolder is created).
    """
    arcpy.AddMessage("")
    arcpy.AddMessage("=" * 60)
    arcpy.AddMessage("COPYING REPORTS TO UPDATE_EMAILS")
    arcpy.AddMessage("=" * 60)

    dest_dir = email_folder
    arcpy.AddMessage("Destination folder: " + dest_dir)

    if not os.path.isdir(dest_dir):
        arcpy.AddError("Update Email folder does not exist: " + dest_dir)
        return

    # --- QA report files (.txt / .json / .html) ---
    if qa_report_txt_path and os.path.isfile(qa_report_txt_path):
        txt_base = os.path.splitext(qa_report_txt_path)[0]
        for ext in (".txt", ".json", ".html"):
            candidate = txt_base + ext
            if os.path.isfile(candidate):
                shutil.copy2(candidate, dest_dir)
                arcpy.AddMessage("  Copied: " + os.path.basename(candidate))
            else:
                arcpy.AddWarning("  Not found, skipped: " + os.path.basename(candidate))
    else:
        arcpy.AddWarning("  QA report .txt path not provided or file not found — skipping QA report copy.")

    # --- Topology report ---
    if topology_report_path and os.path.isfile(topology_report_path):
        shutil.copy2(topology_report_path, dest_dir)
        arcpy.AddMessage("  Copied: topology_report.csv")
    else:
        arcpy.AddWarning("  topology_report.csv not present — skipping.")

    arcpy.AddMessage("=" * 60)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(update_dir, in_dataset, master_dataset, email_folder, dest_current_dir):
    """Orchestrate the full check-in workflow.

    Parameters
    ----------
    update_dir       : str  Full path to the UpdateWorkArea\\<Type> directory.
    in_dataset       : str  Full catalog path to the feature class being checked in.
    master_dataset   : str  Full catalog path to the master/replica reference FC.
    email_folder     : str  Full path to the existing UpdateEmail folder for this
                            request (its basename is reused as the destination
                            subfolder name).
    dest_current_dir : str  Full path to the destination CurrentUpdate folder
                            (where the Returned FGDB will be copied). Supplied
                            explicitly by the caller so sandbox / production
                            destinations are never confused.

    Flow
    ----
    1. List files in update_dir (checklist — always runs)
    2. Derive Returned GDB path and TYPE token — abort if missing/unknown
    3. Run Attribute QA/QC — abort copy steps if QA raises
    4. Display topology report rows (informational only — no pass/fail gate)
    5. Copy entire Returned FGDB to UpdateManagement\\<Type>\\CurrentUpdate
    6. Copy QA reports + topology report to Update_Emails destination
    7. Report completion
    """
    arcpy.AddMessage("")
    arcpy.AddMessage("*" * 60)
    arcpy.AddMessage("CHECK-IN DATASET WORKFLOW")
    arcpy.AddMessage("Update directory      : " + update_dir)
    arcpy.AddMessage("Input FC              : " + in_dataset)
    arcpy.AddMessage("Master FC             : " + master_dataset)
    arcpy.AddMessage("Update Email dir      : " + email_folder)
    arcpy.AddMessage("Destination CurrentUp : " + dest_current_dir)
    arcpy.AddMessage("*" * 60)

    arcpy.SetProgressor("step", "Listing update directory files...", 0, 6, 1)

    # ------------------------------------------------------------------
    # Step 1: File checklist
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 1 of 6: Listing update directory files...")
    arcpy.SetProgressorPosition()
    checklist = list_update_directory_files(update_dir)

    # ------------------------------------------------------------------
    # Step 2: Derive Returned GDB path and TYPE token
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 2 of 6: Deriving dataset type from GDB name...")
    arcpy.SetProgressorPosition()
    returned_gdb_path = checklist["returned_gdb"]
    if returned_gdb_path is None:
        arcpy.AddError(
            "No (or more than one) .gdb found in the update directory. "
            "Expected exactly one .gdb in: " + update_dir + ". "
            "Aborting check-in."
        )
        return

    type_token = _derive_type_token(returned_gdb_path)
    if type_token is None:
        arcpy.AddError(
            "Could not determine the dataset TYPE from the Returned GDB name: "
            + os.path.basename(returned_gdb_path)
            + ". Expected one of: old_growth_management_area, landscape_unit, "
            "slrp_planning, wildlife_habitat_area. Aborting check-in."
        )
        return

    arcpy.AddMessage("")
    arcpy.AddMessage("Derived TYPE token: " + type_token + " (" + TYPE_TO_FOLDER[type_token] + ")")

    # ------------------------------------------------------------------
    # Step 3: Attribute QA/QC (BLOCK gate — abort copies on failure)
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 3 of 6: Running Attribute QA/QC...")
    arcpy.SetProgressorPosition()
    qa_report_txt_path = None
    try:
        qa_report_txt_path = run_attribute_qa(in_dataset, master_dataset)
    except Exception as exc:
        arcpy.AddError(
            "Attribute QA/QC failed with an error: " + str(exc)
            + ". Copy steps will NOT run until QA passes. "
            "Fix the reported issues and re-run this tool."
        )
        return

    # ------------------------------------------------------------------
    # Step 4: Display topology report (informational — no gate)
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 4 of 6: Reading topology report...")
    arcpy.SetProgressorPosition()
    read_topology_report(update_dir)

    # ------------------------------------------------------------------
    # Step 5: Copy Returned FGDB
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 5 of 6: Copying Returned FGDB...")
    arcpy.SetProgressorPosition()
    try:
        copy_returned_fgdb(returned_gdb_path, dest_current_dir, type_token)
    except Exception as exc:
        arcpy.AddError("FGDB copy failed: " + str(exc))
        return

    # ------------------------------------------------------------------
    # Step 6: Copy reports to Update_Emails folder
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 6 of 6: Copying reports to Update Emails folder...")
    arcpy.SetProgressorPosition()
    copy_reports_to_email_folder(
        qa_report_txt_path,
        checklist["topology_report"],
        email_folder,
    )

    # ------------------------------------------------------------------
    # Step 7: Done
    # ------------------------------------------------------------------
    arcpy.AddMessage("")
    arcpy.AddMessage("*" * 60)
    arcpy.AddMessage("CHECK-IN COMPLETE.")
    arcpy.AddMessage("*" * 60)


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # ------------------------------------------------------------------
    # Standalone execution — two modes:
    #
    # TESTING (no arguments):
    #   python check_in_dataset.py
    #   Reads all five paths from the TEST_* keys in .env, including
    #   TEST_CURRENT which becomes the destination CurrentUpdate folder.
    #   This guarantees standalone test runs write to the sandbox, never
    #   to production.
    #
    # EXPLICIT (five arguments):
    #   python check_in_dataset.py \
    #       <update_dir> <in_dataset> <master_dataset> \
    #       <email_folder> <dest_current_dir>
    #   Uses the supplied paths directly, ignoring TEST_* keys.
    # ------------------------------------------------------------------
    if len(sys.argv) == 1:
        # Testing mode — load paths from .env TEST_* keys.
        # NOTE: TEST_CURRENT / TEST_MASTER are folder paths in .env; run()
        # expects feature class catalog paths for in_dataset / master_dataset.
        # Adjust the two lines below if your test FCs live at a deeper path.
        update_dir       = config_loader.TEST_UPDATEWORKAREA
        in_dataset       = config_loader.TEST_CURRENT
        master_dataset   = config_loader.TEST_MASTER
        email_folder     = config_loader.TEST_EMAIL_FOLDER
        dest_current_dir = config_loader.TEST_CURRENT
        print("Standalone test mode — paths loaded from .env TEST_* keys:")
        print("  update_dir      :", update_dir)
        print("  in_dataset      :", in_dataset)
        print("  master_dataset  :", master_dataset)
        print("  email_folder    :", email_folder)
        print("  dest_current_dir:", dest_current_dir)
    elif len(sys.argv) == 6:
        update_dir       = sys.argv[1]
        in_dataset       = sys.argv[2]
        master_dataset   = sys.argv[3]
        email_folder     = sys.argv[4]
        dest_current_dir = sys.argv[5]
    else:
        print(
            "Usage:\n"
            "  python check_in_dataset.py\n"
            "      (no args — uses TEST_* paths from .env)\n"
            "  python check_in_dataset.py"
            " <update_dir> <in_dataset> <master_dataset>"
            " <email_folder> <dest_current_dir>"
        )
        sys.exit(1)

    run(update_dir, in_dataset, master_dataset, email_folder, dest_current_dir)
