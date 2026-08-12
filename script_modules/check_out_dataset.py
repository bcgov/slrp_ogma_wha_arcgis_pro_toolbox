# ===========================================================================
# Script name: check_out_dataset.py
# Purpose:     Standalone module for the OGMA dataset check-OUT workflow.
#              Called by the CheckOutDataset tool in
#              slrp_ogma_arcpro_toolbox.pyt. Simplifies the manual steps a
#              GIS updater performs when checking out a dataset for editing.
#
# Workflow steps (in order):
#   1. Validate parameters. Abort non-OGMA requests (not yet developed).
#   2. Create the project request folder in the Update_Emails area, named
#      <RequestType>_<YYYYMMDD>_<Region>_<GSSNumber>.
#   3. Copy DataUpdateChecklist.xlsx into the project folder and fill in the
#      "1 Initial Request" tab (values + the correct dataset checkbox).
#   4. Write request_details.json into the project folder (machine-readable
#      record consumed by later tools; the spreadsheet is the human record).
#   5. Copy each FGDB in CurrentUpdate to Archives and zip it
#      (any GDB whose name contains "_to_delete" is ignored).
#   6. Delete everything from CurrentUpdate.
#   7. Copy the MASTER FGDB into CurrentUpdate, renamed with a
#      "_Update_YYYYMMDD" suffix (date = Date Checkout Requested).
#   8. Delete everything from the Update WorkArea except the keep-list
#      ("UpdateProcessDocs", "Update_Emails - Shortcut").
#   9. Copy the MASTER FGDB into the Update WorkArea, renamed with the same
#      "_Update_YYYYMMDD" suffix.
#
# Testing mode:
#   When enabled, every directory resolves to a sandbox path (TEST_* keys in
#   .env) so no production data is renamed, deleted, or archived.
#
# The checklist spreadsheet is edited by surgically rewriting the worksheet
# XML inside the .xlsx zip. This is deliberate: openpyxl silently drops the
# Form-Control checkboxes (VML drawings + ctrlProps) on save, so it cannot be
# used here.
#
# Created: 2026-08-12
# ===========================================================================

import arcpy
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime

# Ensure script_modules/ is on sys.path so config_loader can be found whether
# this file is run standalone or imported from the .pyt toolbox.
_modules_dir = os.path.dirname(os.path.abspath(__file__))
if _modules_dir not in sys.path:
    sys.path.insert(0, _modules_dir)

import config_loader


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

REQUEST_TYPES = ["OGMA", "LU", "SLRP"]

UPDATE_REGIONS = [
    "Cariboo", "Thompson_Okanagan", "Omineca", "South_Coast",
    "Skeena", "KBR", "West_Coast",
]

# Exact labels as they appear in column A of the "1 Initial Request" tab.
DATASETS = [
    "Landscape Units",
    "OGMA - Legal",
    "OGMA - Non Legal",
    "SLRP - Boundaries",
    "SLRP - Legal Polygons",
    "SLRP - Legal Lines",
    "SLRP - Legal Points",
    "SLRP - Non Legal Polygons",
    "SLRP - Non Legal Lines",
    "SLRP - Non Legal Points",
]

# Entries in the Update WorkArea that must never be deleted by Step 8.
# Compared case-insensitively against each entry's name and its stem
# (so "Update_Emails - Shortcut.lnk" is kept).
WORKAREA_KEEP = {"updateprocessdocs", "update_emails - shortcut"}

# The one real MASTER FGDB; the Master directory always holds extra GDBs
# (e.g. *_OLD Test.gdb, *_PRE_COIRM_v1.gdb) that must be ignored.
MASTER_GDB_NAME = "old_growth_management_area_bc.gdb"

CHECKLIST_FILENAME = "DataUpdateChecklist.xlsx"

# The tab to fill and its worksheet part inside the .xlsx zip.
_SHEET_PART = "xl/worksheets/sheet1.xml"
_SHEET_RELS_PART = "xl/worksheets/_rels/sheet1.xml.rels"
_SHARED_PART = "xl/sharedStrings.xml"
_MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _fail(message):
    """Report an error to the tool dialog and abort the run."""
    arcpy.AddError(message)
    raise RuntimeError(message)


def _coerce_date(value):
    """Return a datetime from a GPDate value (datetime) or a string."""
    if isinstance(value, datetime):
        return value
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("Date Checkout Requested is required but was empty.")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S",
                "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(
        "Could not parse the Date Checkout Requested value '" + text
        + "'. Expected a date like 2025-07-23."
    )


def _require(value, field_name):
    """Ensure a text parameter is present and non-blank."""
    if value is None or not str(value).strip():
        _fail("The required field '" + field_name + "' is empty. "
              "Please provide a value and re-run the tool.")
    return str(value).strip()


def _list_gdbs(directory):
    """Return full paths of all .gdb folders directly inside directory."""
    try:
        entries = os.listdir(directory)
    except OSError as exc:
        _fail("Cannot read directory '" + directory + "': " + str(exc))
    return [
        os.path.join(directory, e)
        for e in entries
        if e.lower().endswith(".gdb") and os.path.isdir(os.path.join(directory, e))
    ]


def _zip_gdb(source_path, zip_path):
    """Recursively zip a .gdb folder to zip_path (the .gdb stays as the
    top-level folder inside the archive)."""
    base_name = os.path.basename(source_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for dir_path, _sub_dirs, files in os.walk(source_path):
            for file_name in files:
                abs_file = os.path.join(dir_path, file_name)
                rel_path = os.path.join(base_name, os.path.relpath(abs_file, source_path))
                zf.write(abs_file, rel_path)


# ---------------------------------------------------------------------------
# Step 1: Resolve directories from the testing-mode flag
# ---------------------------------------------------------------------------

def resolve_directories(testing_mode):
    """Return a dict of the six directories/paths this workflow needs,
    switching between production and sandbox based on testing_mode."""
    def cfg(key):
        try:
            return getattr(config_loader, key)
        except AttributeError:
            _fail("Missing '" + key + "' in the .env file. Add it and re-run. "
                  "See the .env comments for the required keys.")

    if testing_mode:
        dirs = {
            "workarea":       cfg("TEST_UPDATEWORKAREA"),
            "current":        cfg("TEST_CURRENT"),
            "master":         cfg("TEST_MASTER"),
            "archive":        cfg("TEST_ARCHIVE"),
            "project_parent": cfg("TEST_EMAIL_FOLDER"),
        }
    else:
        dirs = {
            "workarea":       cfg("UPDATEWORKAREA"),
            "current":        cfg("CURRENT"),
            "master":         cfg("MASTER"),
            "archive":        cfg("ARCHIVE"),
            "project_parent": cfg("EMAIL_FOLDER"),
        }
    dirs["checklist_template"] = cfg("CHECKLIST_TEMPLATE")

    # Validate every directory up front so we fail before touching any data.
    for key in ("workarea", "current", "master", "archive", "project_parent"):
        path = dirs[key]
        if not path or not os.path.isdir(path):
            _fail("The '" + key + "' directory does not exist or is not "
                  "accessible:\n  " + str(path) + "\n"
                  "Check the path in .env and that the network share is mapped.")
    if not os.path.isfile(dirs["checklist_template"]):
        _fail("The checklist template was not found:\n  "
              + str(dirs["checklist_template"]) + "\n"
              "Check the CHECKLIST_TEMPLATE path in .env.")
    return dirs


# ---------------------------------------------------------------------------
# Step 2: Create the project request folder
# ---------------------------------------------------------------------------

def build_folder_name(request_type, date_obj, region, gss_number):
    """Compose the project folder name, e.g.
    OGMA_20250723_Thompson_Okanagan_gr_2026_746."""
    return "{0}_{1}_{2}_{3}".format(
        request_type, date_obj.strftime("%Y%m%d"), region, gss_number
    )


def create_project_folder(project_parent, folder_name):
    """Create (or reuse) the project folder and return its full path."""
    project_folder = os.path.join(project_parent, folder_name)
    if os.path.isdir(project_folder):
        arcpy.AddWarning(
            "  Project folder already exists — reusing it:\n    " + project_folder
        )
    else:
        try:
            os.makedirs(project_folder)
        except OSError as exc:
            _fail("Could not create the project folder:\n  " + project_folder
                  + "\n" + str(exc))
        arcpy.AddMessage("  Created project folder:\n    " + project_folder)
    return project_folder


# ---------------------------------------------------------------------------
# Step 3: Copy the checklist spreadsheet and fill in the first tab
# ---------------------------------------------------------------------------

def _xml_escape_text(value):
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _xml_escape_attr(value):
    return _xml_escape_text(value).replace('"', "&quot;")


def _set_value_cell(sheet_xml, ref, value):
    """Set a text (inline string) value on cell `ref`, preserving its style.
    Creates the cell (after the column-A cell of the same row) if absent."""
    esc = _xml_escape_text(value)
    pattern = r'<c r="' + re.escape(ref) + r'"([^>]*?)(/>|>.*?</c>)'
    match = re.search(pattern, sheet_xml, re.DOTALL)
    if match:
        style = re.search(r's="(\d+)"', match.group(1))
        style_attr = ' s="{0}"'.format(style.group(1)) if style else ''
        new_cell = ('<c r="{0}"{1} t="inlineStr"><is>'
                    '<t xml:space="preserve">{2}</t></is></c>').format(ref, style_attr, esc)
        return sheet_xml[:match.start()] + new_cell + sheet_xml[match.end():]

    # Cell absent — insert after the column-A cell of the same row.
    row_num = re.search(r'\d+', ref).group()
    new_cell = ('<c r="{0}" t="inlineStr"><is>'
                '<t xml:space="preserve">{1}</t></is></c>').format(ref, esc)
    anchor = re.search(r'<c r="A' + row_num + r'"[^>]*?(/>|>.*?</c>)', sheet_xml, re.DOTALL)
    if anchor:
        return sheet_xml[:anchor.end()] + new_cell + sheet_xml[anchor.end():]
    row_open = re.search(r'<row r="' + row_num + r'"[^>]*>', sheet_xml)
    if row_open:
        return sheet_xml[:row_open.end()] + new_cell + sheet_xml[row_open.end():]
    arcpy.AddWarning("  Could not locate cell " + ref + " in the checklist worksheet.")
    return sheet_xml


def _set_bool_cell(sheet_xml, ref, state):
    """Set a boolean (checkbox link) cell to 1/0."""
    val = "1" if state else "0"
    new_cell = '<c r="{0}" t="b"><v>{1}</v></c>'.format(ref, val)
    pattern = r'<c r="' + re.escape(ref) + r'"([^>]*?)(/>|>.*?</c>)'
    match = re.search(pattern, sheet_xml, re.DOTALL)
    if match:
        return sheet_xml[:match.start()] + new_cell + sheet_xml[match.end():]
    row_num = re.search(r'\d+', ref).group()
    for col in ("B", "A"):
        anchor = re.search(r'<c r="' + col + row_num + r'"[^>]*?(/>|>.*?</c>)',
                           sheet_xml, re.DOTALL)
        if anchor:
            return sheet_xml[:anchor.end()] + new_cell + sheet_xml[anchor.end():]
    arcpy.AddWarning("  Could not locate checkbox cell " + ref + ".")
    return sheet_xml


def _set_ctrlprop_checked(ctrl_xml, checked):
    """Toggle the stored Checked state of a Form-Control checkbox part."""
    if checked:
        if 'checked="Checked"' not in ctrl_xml:
            ctrl_xml = ctrl_xml.replace(
                'objectType="CheckBox"', 'objectType="CheckBox" checked="Checked"', 1)
    else:
        ctrl_xml = ctrl_xml.replace(' checked="Checked"', '', 1)
    return ctrl_xml


def _set_hyperlink_target(rels_xml, new_target):
    """Point the worksheet's hyperlink relationship at the project folder."""
    esc = _xml_escape_attr(new_target)
    pattern = r'(<Relationship[^>]*Type="[^"]*hyperlink"[^>]*Target=")[^"]*(")'
    return re.sub(pattern, lambda m: m.group(1) + esc + m.group(2), rels_xml)


def _shared_strings(shared_xml):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(shared_xml)
    strings = []
    for si in root.findall(_MAIN_NS + "si"):
        strings.append("".join(t.text or "" for t in si.iter(_MAIN_NS + "t")))
    return strings


def _all_label_cells(sheet_xml, strings):
    """Return a list of (col, row_number, label_text) for every non-empty cell,
    resolving shared strings so labels can be located by their text."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(sheet_xml)
    sheet_data = root.find(_MAIN_NS + "sheetData")
    cells = []
    for row in sheet_data.findall(_MAIN_NS + "row"):
        for cell in row.findall(_MAIN_NS + "c"):
            ref = cell.get("r") or ""
            m = re.match(r'^([A-Z]+)(\d+)$', ref)
            if not m:
                continue
            col, row_num = m.group(1), int(m.group(2))
            cell_type = cell.get("t")
            v = cell.find(_MAIN_NS + "v")
            text = ""
            if cell_type == "s" and v is not None:
                idx = int(v.text)
                text = strings[idx] if 0 <= idx < len(strings) else ""
            elif v is not None:
                text = v.text or ""
            else:
                inline = cell.find(_MAIN_NS + "is")
                if inline is not None:
                    text = "".join(t.text or "" for t in inline.iter(_MAIN_NS + "t"))
            if text:
                cells.append((col, row_num, text))
    return cells


def copy_and_fill_checklist(template_path, project_folder, details):
    """Copy the checklist template into the project folder and populate the
    "1 Initial Request" tab, preserving all Form-Control checkboxes."""
    dest = os.path.join(project_folder, CHECKLIST_FILENAME)
    try:
        shutil.copy2(template_path, dest)
    except OSError as exc:
        _fail("Could not copy the checklist template into the project folder:\n  "
              + str(exc))
    arcpy.AddMessage("  Copied checklist to:\n    " + dest)

    # Read every part of the .xlsx so we can rewrite it byte-for-byte,
    # changing only the worksheet, its rels, and the ctrlProps.
    with zipfile.ZipFile(dest) as zin:
        infos = zin.infolist()
        parts = {info.filename: zin.read(info.filename) for info in infos}

    if _SHEET_PART not in parts:
        arcpy.AddWarning("  Checklist worksheet not found; spreadsheet left blank.")
        return dest

    sheet_xml = parts[_SHEET_PART].decode("utf-8")
    strings = _shared_strings(parts[_SHARED_PART].decode("utf-8")) \
        if _SHARED_PART in parts else []
    all_cells = _all_label_cells(sheet_xml, strings)
    col_a = [(row_num, text) for col, row_num, text in all_cells if col == "A"]

    def row_where(predicate):
        for row_num, text in col_a:
            if predicate(text.strip().casefold()):
                return row_num
        return None

    # --- Text value cells (column B) ---
    text_fields = [
        (row_where(lambda t: t == "update region"),          details["update_region"],        "Update Region"),
        (row_where(lambda t: t == "gis update person"),      details["gis_update_person"],     "GIS Update Person"),
        (row_where(lambda t: t == "data resource manager"),  details["data_resource_manager"], "Data Resource Manager"),
        (row_where(lambda t: t == "initiator of change"),    details["initiator_of_change"],   "Initiator of Change"),
        (row_where(lambda t: t == "date checkout requested"), details["date_checkout_requested"], "Date Checkout Requested"),
        (row_where(lambda t: t.startswith("request email")), details["gss_portal_request_number"], "GSS Portal Request Number"),
    ]
    for row_num, value, label in text_fields:
        if row_num is None:
            arcpy.AddWarning("  Could not find the '" + label + "' row in the checklist.")
            continue
        sheet_xml = _set_value_cell(sheet_xml, "B{0}".format(row_num), value)

    # --- Project folder path (cell below the "Paste your project folder path"
    #     hint, which sits in column D) ---
    path_hint = next(
        ((col, row_num) for col, row_num, text in all_cells
         if text.strip().casefold().startswith("paste your project folder path")),
        None)
    if path_hint is not None:
        col, row_num = path_hint
        sheet_xml = _set_value_cell(sheet_xml, "{0}{1}".format(col, row_num + 1), project_folder)
    else:
        arcpy.AddWarning("  Could not find the project-folder-path cell in the checklist.")

    # --- Dataset checkboxes: set the linked boolean cells (column C) ---
    dataset_rows = {text.strip(): row_num for row_num, text in col_a
                    if text.strip() in DATASETS}
    selected = details["dataset_being_updated"]
    if selected not in dataset_rows:
        arcpy.AddWarning("  Selected dataset '" + str(selected)
                         + "' was not found among the checklist dataset rows.")
    cell_to_dataset = {}
    for dataset, row_num in dataset_rows.items():
        cell = "C{0}".format(row_num)
        cell_to_dataset[cell] = dataset
        sheet_xml = _set_bool_cell(sheet_xml, cell, dataset == selected)

    # --- Dataset checkboxes: update each Form-Control's stored Checked state ---
    for name in list(parts):
        if re.match(r'xl/ctrlProps/ctrlProp\d+\.xml$', name):
            ctrl_xml = parts[name].decode("utf-8")
            link = re.search(r'fmlaLink="\$?([A-Z]+)\$?(\d+)"', ctrl_xml)
            dataset = cell_to_dataset.get(link.group(1) + link.group(2)) if link else None
            parts[name] = _set_ctrlprop_checked(
                ctrl_xml, dataset is not None and dataset == selected).encode("utf-8")

    # --- Make the worksheet hyperlink point at the project folder ---
    if _SHEET_RELS_PART in parts:
        parts[_SHEET_RELS_PART] = _set_hyperlink_target(
            parts[_SHEET_RELS_PART].decode("utf-8"), project_folder).encode("utf-8")

    parts[_SHEET_PART] = sheet_xml.encode("utf-8")

    # Rewrite the archive, preserving original entry metadata/compression.
    tmp = dest + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zout:
        for info in infos:
            zout.writestr(info, parts[info.filename])
    os.replace(tmp, dest)
    arcpy.AddMessage("  Filled '1 Initial Request' tab and checked: " + str(selected))
    return dest


# ---------------------------------------------------------------------------
# Step 4: Write the machine-readable request record
# ---------------------------------------------------------------------------

def write_request_details_json(project_folder, details):
    """Write request_details.json for later tools to consume."""
    record = dict(details)
    record["project_folder"] = project_folder
    record["created_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    path = os.path.join(project_folder, "request_details.json")
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
    except OSError as exc:
        _fail("Could not write request_details.json:\n  " + str(exc))
    arcpy.AddMessage("  Wrote request record:\n    " + path)
    return path


# ---------------------------------------------------------------------------
# Step 5: Archive the CurrentUpdate FGDB(s)
# ---------------------------------------------------------------------------

def archive_current_update(current_dir, archive_dir):
    """Copy each FGDB in CurrentUpdate to Archives and zip it. GDBs whose
    name contains '_to_delete' are ignored."""
    gdbs = _list_gdbs(current_dir)
    to_archive = [g for g in gdbs if "_to_delete" not in os.path.basename(g).lower()]
    ignored = [g for g in gdbs if "_to_delete" in os.path.basename(g).lower()]

    for g in ignored:
        arcpy.AddMessage("  Ignoring (contains '_to_delete'): " + os.path.basename(g))

    if not to_archive:
        arcpy.AddWarning("  No FGDB found in CurrentUpdate to archive:\n    " + current_dir)
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for src_gdb in to_archive:
        name = os.path.basename(src_gdb)
        dest_gdb = os.path.join(archive_dir, name)
        if os.path.exists(dest_gdb):
            alt = name[:-4] + "_archived_" + stamp + ".gdb"
            arcpy.AddWarning("  '" + name + "' already exists in Archives; "
                             "archiving as '" + alt + "' instead.")
            dest_gdb = os.path.join(archive_dir, alt)

        arcpy.AddMessage("  Copying to Archives: " + os.path.basename(dest_gdb))
        try:
            arcpy.management.Copy(src_gdb, dest_gdb)
        except arcpy.ExecuteError:
            _fail("Failed to copy FGDB to Archives:\n  " + src_gdb + "\n"
                  + arcpy.GetMessages(2))

        zip_path = dest_gdb + ".zip"
        arcpy.AddMessage("  Zipping: " + os.path.basename(zip_path))
        try:
            _zip_gdb(dest_gdb, zip_path)
        except Exception as exc:
            _fail("Failed to zip archived FGDB:\n  " + dest_gdb + "\n" + str(exc))
        if not os.path.isfile(zip_path) or os.path.getsize(zip_path) == 0:
            _fail("Zip archive was not created or is empty:\n  " + zip_path)
        arcpy.AddMessage("  Archived + zipped OK: " + os.path.basename(zip_path))


# ---------------------------------------------------------------------------
# Steps 6 & 8: Delete directory contents
# ---------------------------------------------------------------------------

def _delete_entry(path):
    """Delete a file, folder, or FGDB, using arcpy for .gdb to clear locks."""
    if path.lower().endswith(".gdb") and os.path.isdir(path):
        try:
            arcpy.management.Delete(path)
            return
        except arcpy.ExecuteError:
            pass  # fall through to shutil, then report if that fails too
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def clear_current_update(current_dir):
    """Delete everything from the CurrentUpdate directory."""
    try:
        entries = os.listdir(current_dir)
    except OSError as exc:
        _fail("Cannot read CurrentUpdate directory:\n  " + current_dir + "\n" + str(exc))

    if not entries:
        arcpy.AddMessage("  CurrentUpdate is already empty.")
        return

    for entry in entries:
        target = os.path.join(current_dir, entry)
        try:
            _delete_entry(target)
            arcpy.AddMessage("  Deleted: " + entry)
        except Exception as exc:
            _fail("Could not delete '" + entry + "' from CurrentUpdate. It may be "
                  "open or locked in ArcGIS Pro or Windows Explorer.\n  " + str(exc))


def clean_workarea(workarea_dir):
    """Delete everything from the Update WorkArea except the keep-list."""
    try:
        entries = os.listdir(workarea_dir)
    except OSError as exc:
        _fail("Cannot read Update WorkArea directory:\n  " + workarea_dir + "\n" + str(exc))

    for entry in entries:
        stem = os.path.splitext(entry)[0].strip().casefold()
        if entry.strip().casefold() in WORKAREA_KEEP or stem in WORKAREA_KEEP:
            arcpy.AddMessage("  Keeping: " + entry)
            continue
        target = os.path.join(workarea_dir, entry)
        try:
            _delete_entry(target)
            arcpy.AddMessage("  Deleted: " + entry)
        except Exception as exc:
            _fail("Could not delete '" + entry + "' from the Update WorkArea. It may "
                  "be open or locked.\n  " + str(exc))


# ---------------------------------------------------------------------------
# Steps 7 & 9: Copy the MASTER FGDB with an _Update_YYYYMMDD suffix
# ---------------------------------------------------------------------------

def _master_gdb_path(master_dir):
    """Return the path to the one real MASTER FGDB, ignoring the others."""
    path = os.path.join(master_dir, MASTER_GDB_NAME)
    if not os.path.isdir(path):
        others = [os.path.basename(g) for g in _list_gdbs(master_dir)]
        _fail("The MASTER FGDB '" + MASTER_GDB_NAME + "' was not found in:\n  "
              + master_dir + "\n"
              "GDBs present: " + (", ".join(others) if others else "(none)") + ".")
    return path


def _updated_gdb_name(date_obj):
    base = MASTER_GDB_NAME[:-4]  # strip ".gdb"
    return "{0}_Update_{1}.gdb".format(base, date_obj.strftime("%Y%m%d"))


def copy_master_to(master_gdb, dest_dir, date_obj, dest_label):
    """Copy the MASTER FGDB into dest_dir with the _Update_YYYYMMDD name."""
    dest_gdb = os.path.join(dest_dir, _updated_gdb_name(date_obj))
    if os.path.exists(dest_gdb):
        _fail("Destination FGDB already exists in " + dest_label + ":\n  " + dest_gdb
              + "\nRemove or rename it and re-run the tool.")
    arcpy.AddMessage("  Copying MASTER into " + dest_label + " as:\n    "
                     + os.path.basename(dest_gdb))
    try:
        arcpy.management.Copy(master_gdb, dest_gdb)
    except arcpy.ExecuteError:
        _fail("Failed to copy the MASTER FGDB into " + dest_label + ":\n  "
              + arcpy.GetMessages(2))
    return dest_gdb


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(testing_mode, request_type, update_region, gis_update_person,
        data_resource_manager, initiator_of_change, date_checkout_requested,
        gss_portal_request_number, dataset_being_updated):
    """Orchestrate the full check-out workflow."""

    # ------------------------------------------------------------------
    # Step 1: Validate parameters
    # ------------------------------------------------------------------
    request_type = _require(request_type, "Request Type").upper()
    if request_type != "OGMA":
        _fail("Sorry the script hasnt been developed for Non Ogma Requests yet")

    update_region             = _require(update_region, "Update Region")
    gis_update_person         = _require(gis_update_person, "GIS Update Person")
    data_resource_manager     = _require(data_resource_manager, "Data Resource Manager")
    initiator_of_change       = _require(initiator_of_change, "Initiator of Change")
    gss_portal_request_number = _require(gss_portal_request_number, "GSS Portal Request Number")
    dataset_being_updated     = _require(dataset_being_updated, "Dataset Being Updated")

    try:
        date_obj = _coerce_date(date_checkout_requested)
    except ValueError as exc:
        _fail(str(exc))

    details = {
        "request_type": request_type,
        "update_region": update_region,
        "gis_update_person": gis_update_person,
        "data_resource_manager": data_resource_manager,
        "initiator_of_change": initiator_of_change,
        "date_checkout_requested": date_obj.strftime("%Y-%m-%d"),
        "gss_portal_request_number": gss_portal_request_number,
        "dataset_being_updated": dataset_being_updated,
        "testing_mode": bool(testing_mode),
    }

    arcpy.AddMessage("")
    arcpy.AddMessage("*" * 60)
    arcpy.AddMessage("CHECK-OUT DATASET WORKFLOW")
    arcpy.AddMessage("Testing mode          : " + ("ON (sandbox)" if testing_mode else "OFF (production)"))
    arcpy.AddMessage("Request type          : " + request_type)
    arcpy.AddMessage("Update region         : " + update_region)
    arcpy.AddMessage("Dataset being updated : " + dataset_being_updated)
    arcpy.AddMessage("Date checkout req.    : " + details["date_checkout_requested"])
    arcpy.AddMessage("GSS portal request    : " + gss_portal_request_number)
    arcpy.AddMessage("*" * 60)

    dirs = resolve_directories(testing_mode)
    arcpy.AddMessage("Resolved directories:")
    for key in ("workarea", "current", "master", "archive", "project_parent"):
        arcpy.AddMessage("  {0:15}: {1}".format(key, dirs[key]))

    master_gdb = _master_gdb_path(dirs["master"])

    total = 9
    arcpy.SetProgressor("step", "Starting check-out...", 0, total, 1)

    # ------------------------------------------------------------------
    # Step 2: Create the project folder
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 2 of 9: Creating project folder...")
    arcpy.AddMessage("\n[Step 2/9] Creating project folder")
    folder_name = build_folder_name(request_type, date_obj, update_region,
                                    gss_portal_request_number)
    details["folder_name"] = folder_name
    project_folder = create_project_folder(dirs["project_parent"], folder_name)
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 3: Copy + fill the checklist spreadsheet
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 3 of 9: Copying and filling checklist spreadsheet...")
    arcpy.AddMessage("\n[Step 3/9] Copying and filling the checklist spreadsheet")
    copy_and_fill_checklist(dirs["checklist_template"], project_folder, details)
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 4: Write request_details.json
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 4 of 9: Writing request record...")
    arcpy.AddMessage("\n[Step 4/9] Writing request_details.json")
    write_request_details_json(project_folder, details)
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 5: Archive the CurrentUpdate FGDB(s)
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 5 of 9: Archiving + zipping CurrentUpdate FGDB(s)...")
    arcpy.AddMessage("\n[Step 5/9] Archiving CurrentUpdate FGDB(s) to Archives")
    archive_current_update(dirs["current"], dirs["archive"])
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 6: Clear CurrentUpdate
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 6 of 9: Clearing CurrentUpdate...")
    arcpy.AddMessage("\n[Step 6/9] Deleting everything from CurrentUpdate")
    clear_current_update(dirs["current"])
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 7: Copy MASTER -> CurrentUpdate (renamed)
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 7 of 9: Copying MASTER into CurrentUpdate...")
    arcpy.AddMessage("\n[Step 7/9] Copying MASTER FGDB into CurrentUpdate")
    copy_master_to(master_gdb, dirs["current"], date_obj, "CurrentUpdate")
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 8: Clean the Update WorkArea
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 8 of 9: Cleaning the Update WorkArea...")
    arcpy.AddMessage("\n[Step 8/9] Cleaning the Update WorkArea (keeping the whitelist)")
    clean_workarea(dirs["workarea"])
    arcpy.SetProgressorPosition()

    # ------------------------------------------------------------------
    # Step 9: Copy MASTER -> Update WorkArea (renamed)
    # ------------------------------------------------------------------
    arcpy.SetProgressorLabel("Step 9 of 9: Copying MASTER into the Update WorkArea...")
    arcpy.AddMessage("\n[Step 9/9] Copying MASTER FGDB into the Update WorkArea")
    copy_master_to(master_gdb, dirs["workarea"], date_obj, "Update WorkArea")
    arcpy.SetProgressorPosition()

    arcpy.ResetProgressor()
    arcpy.AddMessage("")
    arcpy.AddMessage("*" * 60)
    arcpy.AddMessage("CHECK-OUT COMPLETE.")
    arcpy.AddMessage("Project folder: " + project_folder)
    arcpy.AddMessage("*" * 60)
    return project_folder


# ---------------------------------------------------------------------------
# Standalone execution (testing sandbox only)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Runs entirely against the sandbox (testing_mode=True) with sample values
    # so a direct `python check_out_dataset.py` never touches production data.
    print("Standalone test run — testing mode ON (sandbox paths from .env).")
    run(
        testing_mode=True,
        request_type="OGMA",
        update_region="Thompson_Okanagan",
        gis_update_person="Test Person",
        data_resource_manager="Test Manager",
        initiator_of_change="Test Initiator",
        date_checkout_requested=datetime.now(),
        gss_portal_request_number="gr_2026_746",
        dataset_being_updated="OGMA - Legal",
    )
