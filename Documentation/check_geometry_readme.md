# Check for Geometry Issues

## What It Does

**Check for Geometry Issues** runs a battery of pre-BCGW geometry checks against a single feature class and writes a plain-text report to the Update Work Area folder. It is the geometry counterpart of the Attribute QA tool: the Attribute QA tool proves *attribute* integrity, this tool proves *geometry* integrity, and both drop a dated `.txt` report into the same Update Work Area folder for the DRM's records.

The tool performs four checks in order:

1. **Repair Geometry** — runs `arcpy.management.RepairGeometry` on every modified feature.
2. **Small Features** — flags sliver polygons (≤ 0.5 ha) or short line segments (≤ 1 m).
3. **Max Vertex Count Per Feature** — flags features with more than 524,000 vertices (a BCGW hard limit).
4. **Duplicate Vertices** — flags any location where the same coordinate is repeated ≥ 4 times in a single feature (BCGW load-blocker).

Only features whose `MODIFICATION_TYPE` field **is not null** are examined. The tool assumes the submitter has already populated `MODIFICATION_TYPE` on any feature they added or modified — that field is the sole scope filter.

---

## When to Use It

Run this tool **before** running the Check In Dataset tool. It is a sanity-check on the returned FGDB from the submitter that catches geometry problems that will otherwise cause a BCGW load failure downstream. Fix (or return to the submitter) anything the report flags, then re-run until the report is clean.

Typical order for a check-in cycle:

1. Receive returned FGDB from submitter into the Update Work Area folder (e.g. `M:\OldGrowthManagementAreas`).
2. Run **Check for Geometry Issues** (this tool).
3. Review the `*_geometry_check_<date>.txt` report and the temp review datasets it points at.
4. Run **Check In Dataset**.

---

## Prerequisites

The input feature class must:

- Have a `MODIFICATION_TYPE` field. The tool exits with an error if this field is missing.
- Have one of the following ID fields for the duplicate-vertex check to complete:
  - `LEGAL_OGMA_INTERNAL_ID`
  - `NON_LEGAL_OGMA_INTERNAL_ID`
  - `LANDSCAPE_UNIT_ID`
  - `LEGAL_FEAT_ID`
  - `NON_LEGAL_FEAT_ID`
  - `STRGC_LAND_RSRCE_PLAN_ID`

  If none of these are present the tool raises a clear error naming every candidate it looked for.

- Live inside a `.gdb`. The Update Work Area folder is derived as the parent of the containing `.gdb`. The feature class may sit directly inside the GDB or inside a Feature Dataset — both layouts work.

Point feature classes are rejected by the tool dialog and by the `execute()` guard in the toolbox.

---

## Parameters

| # | Parameter | Type | Description |
|---|---|---|---|
| 1 | **Feature Class to Check** | Feature Class | The feature class to run all four checks against. Must be a polygon or line dataset with a `MODIFICATION_TYPE` field. |

---

## Workflow Steps

The tool runs 4 steps in order. A progress bar tracks each step; each step also writes its findings as a section in the output `.txt` report.

### Step 1 — Repair Geometry
Creates a temporary feature layer restricted to `MODIFICATION_TYPE IS NOT NULL` and runs `arcpy.management.RepairGeometry` on it. This is destructive-in-place on the input feature class — invalid geometries are repaired on the actual source data, not a copy.

### Step 2 — Small Features (Sliver Polygons or Short Lines)

- **Polygons**: flags features with `Shape_Area ≤ 5000` m² (0.5 hectares) after being burst to single-part with `MultipartToSinglepart`. Flagged features are written to a temp FC named `temp_sliver_polygons_<fc_name>` in the same container (Feature Dataset or GDB) as the input.
- **Lines**: flags segments with `Shape_Length ≤ 1` m. Flagged features are written to `temp_short_line_segments_<fc_name>`.

Non-flagged features are removed from the temp FC so what remains is only the material to review.

### Step 3 — Max Vertex Count Per Feature
Adds a temporary `VxCount` field to a filtered layer and calculates `!shape!.pointCount` per feature. Any feature with `VxCount > 524000` is exported to `temp_<fc_name>_OVER_MAX_VERTICES`. `VxCount` is removed from the input after the check.

If any features exceed the limit, the report suggests: `Simplify Polygon` with a <1 m tolerance, splitting multipart polygons, or contacting the DRM.

### Step 4 — Duplicate Vertices (≥ 4 Identical Points)
Detects any point on any feature where the same `(feature_id, X, Y)` triple occurs four or more times — a well-known BCGW load-blocker.

Sequence:

1. Copy the modified features to `temp_identical_vertex_check_Step1_<fc_name>`.
2. Convert them to points with `FeatureVerticesToPoints ALL` into `temp_identical_vertex_check_Step2_<fc_name>`.
3. Auto-detect the feature ID field by inspecting field names on the input (see Prerequisites). Fail loudly if none present.
4. Build a `CHECK` field = `<feat_id>_<X>_<Y>` on every vertex.
5. Count occurrences of each `CHECK` value with `collections.Counter`; retain only those with count > 3.
6. Populate a `FLAG` field with the count on matching rows, then delete all unflagged rows so the temp FC contains only the problem vertices.

The temp FC path is written to the report so the DRM can inspect it directly.

---

## Output Report

### Location
The tool writes its report to the **Update Work Area folder**, defined as the parent folder of the containing `.gdb`. This is the same folder that receives the Attribute QA report and the topology report.

Example:
```
Input FC : M:\OldGrowthManagementAreas\old_growth_management_area_bc_update_Returned_20260807.gdb\
           old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly

Report   : M:\OldGrowthManagementAreas\
           old_growth_management_area_non_legal_bc_poly_geometry_check_2026-08-10.txt
```

### Naming Pattern
```
<fc_name>_geometry_check_<YYYY-MM-DD>.txt
```

The date comes from `datetime.date.today()` — so a same-day rerun **overwrites** the previous report. Re-runs on a different day create a new dated file alongside the older one.

### Contents

The report opens with a header block:

```
======================================================================
GEOMETRY CHECK REPORT
======================================================================
Feature Class : <fc_name>
Dataset Path  : <full catalog path>
Shape Type    : Polygon | Polyline
Run Timestamp : <ISO-ish YYYY-MM-DDTHH:MM:SS>
Operator IDIR : <USERNAME env var>
======================================================================
```

Then a section for each of the four checks:

```
------------------------------------------------------------
REPAIR GEOMETRY
------------------------------------------------------------
Repairing geometry where MODIFICATION_TYPE is not null...
✔ Geometry repair complete

------------------------------------------------------------
SMALL FEATURES (SLIVER POLYGONS OR SHORT LINES)
------------------------------------------------------------
Identifying small features where MODIFICATION_TYPE is not null...
Checking for polygons with area <= 0.5 ha...
[WARNING] There are 3 small polygon features (<= 0.5 ha).
[WARNING] Review: temp_sliver_polygons_old_growth_management_area_non_legal_bc_poly
Review dataset path: M:\...\<gdb>\<fds>\temp_sliver_polygons_...

------------------------------------------------------------
MAX VERTEX COUNT PER FEATURE
------------------------------------------------------------
Checking vertex count for modified features...
All features must have < 524,000 vertices for BCGW.
All features are under the vertex limit ✔
----- Vertex count check complete -----

------------------------------------------------------------
DUPLICATE VERTICES (>= 4 IDENTICAL POINTS)
------------------------------------------------------------
Checking for identical vertices (>= 4) in modified features...
Features with 4+ identical vertices will not load to BCGW.
 - Creating temp dataset of modified features
 - Converting features to vertices
Feature ID field used: NON_LEGAL_OGMA_INTERNAL_ID
 - Analyzing vertex duplication
No duplicate vertices found.
----- Vertex check complete -----
```

Lines prefixed with `[WARNING]` correspond to `arcpy.AddWarning` messages in the tool dialog. Lines without a prefix correspond to normal `arcpy.AddMessage` output. Nothing shown in the tool dialog is suppressed from the report, and nothing in the report is suppressed from the tool dialog — they are one-to-one.

### Fallback Location

If the Update Work Area folder cannot be written to (e.g. the input FC lives in a scratch GDB, an `in_memory` workspace, or the parent folder is read-only), the tool falls back **once** to `arcpy.env.scratchFolder` and prints a warning telling you where the report actually landed. If even the scratch folder is not writable, the checks still run to completion — only the report file is skipped.

The final line of the tool dialog always announces the report path so you never have to guess where it went:

```
Geometry report written to: M:\OldGrowthManagementAreas\old_growth_management_area_non_legal_bc_poly_geometry_check_2026-08-10.txt
```

---

## Temp Datasets Created

Every check writes its scratch data to the **same Feature Dataset (or GDB) that contains the input feature class**. Nothing is written to `in_memory` or the system scratch GDB — the temp data is meant to be reviewable by the DRM.

| Check | Temp dataset name |
|---|---|
| Small features (polygon input) | `temp_sliver_polygons_<fc_name>` |
| Small features (line input) | `temp_short_line_segments_<fc_name>` |
| Max vertices | `temp_<fc_name>_OVER_MAX_VERTICES` |
| Duplicate vertices — copy | `temp_identical_vertex_check_Step1_<fc_name>` |
| Duplicate vertices — points | `temp_identical_vertex_check_Step2_<fc_name>` |

The tool does not clean these up on its way out — that is intentional so the DRM can open them in a map and inspect the flagged features. Delete them manually once the issue is resolved. They are **not** copied into `CurrentUpdate` by the Check In Dataset tool.

The temporary in-memory *feature layers* the tool creates (via `CreateUniqueName("fc_lyr")` / `CreateUniqueName("temp_lyr")`) are always deleted before the function returns.

---

## Interpreting the Report

- **No warnings anywhere** → the feature class is clean for the four geometry rules the tool checks. Proceed to Check In Dataset.
- **Warnings under SMALL FEATURES** → not automatically fatal. Small polygons/lines are sometimes real. Open the temp FC named in the report, inspect each flagged feature, and decide whether to delete it, merge it, or accept it.
- **Warnings under MAX VERTEX COUNT PER FEATURE** → will fail BCGW load. Must be fixed before check-in. Follow the "Possible solutions" list in the report.
- **Warnings under DUPLICATE VERTICES** → will fail BCGW load. Must be fixed before check-in. Open the Step 2 temp FC to see the exact `(FEAT_ID, X, Y)` combinations that are duplicated.
- **Error before any check runs** → almost always `MODIFICATION_TYPE` field missing, or the input is a point FC. Fix the input and re-run.

---

## Known Limitations

- **Scope is `MODIFICATION_TYPE IS NOT NULL`**. Features the submitter did not flag as modified are not examined. If the submitter has failed to populate `MODIFICATION_TYPE` correctly, the tool will silently pass features that would otherwise fail. This is a design choice — matching the "check what the submitter says they changed" contract used elsewhere in the workflow.
- **`RepairGeometry` mutates the input**. This is intentional but worth calling out: the source feature class is modified in place. If you want an untouched original, make a copy of the returned FGDB before running the tool.
- **Small-feature thresholds are hard-coded**: 5000 m² for polygons, 1 m for lines. Both are single-line changes in [script_modules/check_geometry.py](../script_modules/check_geometry.py) if a dataset needs different thresholds.
- **The vertex duplicate check uses `POINT_X` / `POINT_Y` from `AddXY`**, which are computed in the feature class's spatial reference. Datasets in different projections will produce different `CHECK` string keys but the same *number* of duplicates.
- **ID field auto-detection is a hard-coded whitelist** (see Prerequisites). New dataset types with new ID fields need to be added to `id_field_candidates` in [script_modules/check_geometry.py](../script_modules/check_geometry.py).
- **Report I/O errors are non-fatal**. If the report can't be written, the geometry checks still run and their output still appears in the tool dialog. Only the archived `.txt` is lost.

---

## Related Tools

- **Attribute QA** — pairs with this tool. Writes `<fc_name>_attribute_check_<date>.txt` to the same Update Work Area folder.
- **Check In Dataset** — runs after this tool. Scans the Update Work Area folder for the topology and attribute-QA reports, promotes the returned FGDB into `CurrentUpdate`, and copies reports into the Update Emails folder. The geometry-check `.txt` produced by this tool is not currently part of Check In Dataset's file checklist.

---

## Source

- Script: [script_modules/check_geometry.py](../script_modules/check_geometry.py)
- Toolbox class: `GeometryCheckTool` in [slrp_ogma_arcpro_toolbox.pyt](../slrp_ogma_arcpro_toolbox.pyt)
