# Test Data Creation Tutorial
## Python 2 → Python 3 / ArcGIS Pro Migration
### BC Ministry of Water, Land and Resource Stewardship — Geomatics Branch

---

**Document Version:** 1.0  
**Date:** April 22, 2026  
**Audience:** Junior GIS staff assisting with legacy script migration  
**Software Required:** ArcGIS Pro 3.x with an active licence (Basic or higher)

---

## How to Use This Tutorial

This document guides you through creating and running tests for every script being migrated from Python 2 / ArcGIS 10.x to Python 3 / ArcGIS Pro 3. Each script section follows the same structure:

| Section | What it covers |
|---|---|
| **Overview** | What the script does, in plain English |
| **How to Run** | Inputs, parameters, and expected outputs |
| **Test Setup** | How to create the working test environment |
| **Known-Bad Tests** | One test per error condition — these MUST produce a FAIL |
| **Known-Good Test** | Clean data — this MUST produce a PASS |
| **Checklist** | Tick off before marking the test complete |

> **CRITICAL RULE — READ BEFORE STARTING**
>
> A tool that has never been seen to fail cannot be trusted to detect failures.
> **Every script MUST be run against known-bad data and produce the expected FAIL before it is considered ready.**
> Running against clean data only is not sufficient. Do not skip the known-bad tests.

---

## General Setup — Do This Once Before Any Test

These steps apply to all scripts. Do them once at the start of the testing session.

### Step 1 — Create a test workspace

1. On your local drive (e.g. `C:\GIS_Testing\`), create a folder called `script_migration_tests`.
2. Inside that folder, create one sub-folder per script:
   - `01_attribute_qa`
   - `02_geometry_checks`
   - `03_find_duplicates`
   - `04_find_duplicates_2_datasets`
   - `05_update_seq_num`
   - `06_update_seq_num_ogma`
   - `07_record_count_compare`
3. **Never use a UNC network path** (e.g. `\\spatialfiles.bcgov\...`) as your test workspace. Write to a local drive first.

### Step 2 — Open ArcGIS Pro and create a new project

1. Open ArcGIS Pro.
2. Create a new project (choose "Blank") saved inside `C:\GIS_Testing\script_migration_tests\`.
3. This project will hold all test file geodatabases (FGDBs).

### Step 3 — Know where to find the scripts

The scripts are located in the repository at:
```
\\spatialfiles.bcgov\work\srm\nel\Local\Geomatics\Workarea\csostad\
    GitHub_Repositories\slrp_ogma_wha_arcgis_pro_toolbox\
```
The ArcGIS Pro toolbox (`.pyt` file) in that folder connects the scripts to the Pro interface.

---

## Script 1 — `attribute_qa_v8.py`

### Overview

This script runs **13 sections of attribute quality checks** on a post-update feature class (the version that has just been edited) and compares it against a master (pre-update) copy. Think of the master as the "before" copy and the post-update as the "after" copy. The script checks things like: are there any fields with the literal text `<NULL>` typed in them? Are the change management fields filled in? Are feature IDs valid? It then writes three output files to the same folder as the FGDB:

- A `.txt` text report listing every error found
- A `.json` file with machine-readable results
- An `.html` dashboard that colour-codes pass/fail sections (open this in a web browser)

The script reports each section as **PASS** or **FAIL**. A single error in any section causes that section to FAIL.

**Status:** Migrated to Python 3 / ArcGIS Pro — ready for testing.

---

### How to Run

| Parameter | Description | Example |
|---|---|---|
| **Post-update feature class** | The feature class that has been edited (the "after" FC) | `C:\GIS_Testing\...\test_update.gdb\ogma_albers\old_growth_management_area_legal_bc_poly` |
| **Master feature class** | The untouched "before" copy | `C:\GIS_Testing\...\test_master.gdb\ogma_albers\old_growth_management_area_legal_bc_poly` |

**To run in ArcGIS Pro:**
1. In the Catalog pane, navigate to the `.pyt` toolbox file.
2. Double-click **Attribute QA** to open the tool dialog.
3. Enter the post-update and master feature class paths.
4. Click **Run**.
5. After the run, look in the **same folder as the post-update FGDB** for three output files named `old_growth_management_area_legal_bc_poly_attribute_check_YYYY-MM-DD.txt`, `.json`, and `.html`.

> **WARNING — Do not run this tool on a live production dataset.**
> Always run it on a copy stored in your local test workspace. The script writes output files to the folder containing the FGDB, which could create clutter in shared network locations.

---

### Test Setup — Script 1

You will create two FGDBs for all Script 1 tests:

- `test_master.gdb` — the "before" copy (clean data, never change this)
- `test_update.gdb` — the "after" copy (you will introduce errors into this one for each test)

Both FGDBs must contain a Feature Dataset and a feature class with the **exact name** `old_growth_management_area_legal_bc_poly`.

**Step-by-step: Create the base test FGDBs**

1. In ArcGIS Pro, open the **Catalog** pane (View → Catalog Pane).
2. Right-click your `01_attribute_qa` folder → **New → File Geodatabase**. Name it `test_master.gdb`.
3. Repeat to create `test_update.gdb` in the same folder.
4. Right-click `test_master.gdb` → **New → Feature Dataset**. Name it `old_growth_management_area_albers`. Set the spatial reference to **BC Albers (EPSG:3005)**.
5. Right-click the new Feature Dataset → **New → Feature Class**. Set:
   - Name: `old_growth_management_area_legal_bc_poly`
   - Geometry: **Polygon**
   - Coordinate system: BC Albers (EPSG:3005)
6. Add the following fields to the feature class (right-click the FC → **Design → Fields**):

| Field Name | Type | Length |
|---|---|---|
| `LEGAL_OGMA_INTERNAL_ID` | Long Integer | — |
| `LEGAL_OGMA_PROVID` | Text | 30 |
| `PROVID_PART_NUMBER` | Long Integer | — |
| `MODIFICATION_TYPE` | Text | 30 |
| `STATUS` | Short Integer | — |
| `GIS_CHANGE_DATE` | Date | — |
| `GIS_CHANGE_PERSON` | Text | 50 |
| `CHANGE_REASON` | Text | 255 |
| `INITIATOR_OF_CHANGE` | Text | 50 |
| `RETIREMENT_DATE` | Date | — |
| `FEATURE_NOTES` | Text | 255 |

7. Repeat steps 4–6 to create the identical structure inside `test_update.gdb`.
8. You now have two empty, identically structured FGDBs.

**Add baseline clean records to `test_master.gdb`**

These records are your clean "before" data. The same records will also be copied into `test_update.gdb` as the starting point for each test.

Open the `test_master.gdb` feature class in an edit session and add these five records. Use any simple polygon shape (a small rectangle anywhere in BC is fine):

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE | RETIREMENT_DATE |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CAR_RCA_1 | 0 | `<null>` (true null) | 0 | 2025-01-01 | JSMITH | Initial load | JSMITH | `<null>` |
| 2 | CAR_RCA_2 | 0 | `<null>` | 0 | 2025-01-01 | JSMITH | Initial load | JSMITH | `<null>` |
| 3 | CAR_RCA_3 | 0 | `<null>` | 0 | 2025-01-01 | JSMITH | Initial load | JSMITH | `<null>` |
| 4 | CAR_RCA_4 | 0 | `<null>` | 0 | 2025-01-01 | JSMITH | Initial load | JSMITH | `<null>` |
| 5 | CAR_RCA_5 | 0 | `<null>` | 0 | 2025-01-01 | JSMITH | Initial load | JSMITH | `<null>` |

> **Note on MODIFICATION_TYPE being null in the master:** The master represents the live production database. Most existing records do not have a MODIFICATION_TYPE because they are not part of the current update. Only records involved in the current update cycle are assigned a MODIFICATION_TYPE.

9. Save and stop editing the master.
10. Copy all five master records into `test_update.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc_poly` using the **Append** tool (no field mapping changes needed). This is now your clean update FC baseline.

---

### Known-Bad Tests — Script 1

For each test below, start from a **fresh copy** of the clean update FC. The safest way is to delete all records in `test_update.gdb`'s FC, then append the five clean records again before introducing the specific error.

---

#### Test 1-A — False NULL string (Section 1)

**What this tests:** Section 1 checks every text field for the literal text string `<NULL>` (or variations: `<Null>`, `NULL`, `null`) typed in as data instead of a true database null.

**How to create the known-bad data:**

1. Open `test_update.gdb\...\old_growth_management_area_legal_bc_poly` in an edit session.
2. Locate the record with `LEGAL_OGMA_INTERNAL_ID = 1`.
3. In the `FEATURE_NOTES` field, type exactly: `<NULL>` (with angle brackets, all caps).
4. Save and stop editing.

**Expected FAIL output:**

In the `.txt` report, Section 1 will contain:
```
***ERROR --> [LEGAL_OGMA_INTERNAL_ID] has 1 features with <NULL>, <Null>, NULL, or Null
             as a string instead of a true NULL value:
     LEGAL_OGMA_INTERNAL_ID 1: False Null in FEATURE_NOTES
```
The Section 1 status in the `.html` dashboard will be shown as **FAIL** (red).

---

#### Test 1-B — Blank change attribute fields on an active record (Section 2)

**What this tests:** Section 2 checks that every record with an active MODIFICATION_TYPE (`NEW`, `MODIFIED`, `MODIFIED_NOREPLACE`) has all four change management fields filled in: `GIS_CHANGE_DATE`, `GIS_CHANGE_PERSON`, `CHANGE_REASON`, and `INITIATOR_OF_CHANGE`.

**How to create the known-bad data:**

1. Start from a fresh copy of the clean update FC.
2. Open the FC in an edit session.
3. Add a **new record** (row) with these values:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE |
|---|---|---|---|---|---|---|---|---|
| 6 | CAR_RCA_6 | 0 | `NEW` | 0 | `<null>` | `<null>` | `<null>` | `<null>` |

4. Save and stop editing.

**Expected FAIL output:**

Section 2 of the `.txt` report will contain errors about missing `GIS_CHANGE_DATE`, `GIS_CHANGE_PERSON`, `CHANGE_REASON`, and `INITIATOR_OF_CHANGE` for `LEGAL_OGMA_INTERNAL_ID 6`. The Section 2 status in the `.html` dashboard will be **FAIL** (red).

---

#### Test 1-C — Zero or null in FEATID / PROVID on an active record (Section 4)

**What this tests:** Section 4 checks that no active (non-retired) record has a value of 0 or null in the feature ID field (`LEGAL_OGMA_INTERNAL_ID`) or the PROVID field (`LEGAL_OGMA_PROVID`).

**How to create the known-bad data:**

1. Start from a fresh copy of the clean update FC.
2. Open the FC in an edit session.
3. Add a **new record** with these values — note the PROVID is null and the INTERNAL_ID is 0:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE |
|---|---|---|---|---|---|---|---|---|
| 0 | `<null>` | 0 | `NEW` | 0 | 2026-04-01 | BTEST | Test | BTEST |

4. Save and stop editing.

**Expected FAIL output:**

Section 4 of the `.txt` report will flag errors on this record for both `LEGAL_OGMA_INTERNAL_ID = 0` and for the null `LEGAL_OGMA_PROVID`. Section 4 status will be **FAIL** (red).

---

#### Test 1-D — Gap in sequential PROVID numbering (Section 5)

**What this tests:** Section 5 checks that the numeric suffixes of PROVID values form a complete sequence with no gaps (for example: `CAR_RCA_1`, `CAR_RCA_2`, `CAR_RCA_3` is fine; `CAR_RCA_1`, `CAR_RCA_2`, `CAR_RCA_4` is not — the `3` is missing).

**How to create the known-bad data:**

The five clean records have PROVIDs `CAR_RCA_1` through `CAR_RCA_5`. You need to add a record that skips a number.

1. Start from a fresh copy of the clean update FC.
2. Open the FC in an edit session.
3. Add a **new record** with `LEGAL_OGMA_PROVID = CAR_RCA_7` (skipping 6):

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE |
|---|---|---|---|---|---|---|---|---|
| 6 | CAR_RCA_7 | 0 | `NEW` | 0 | 2026-04-01 | BTEST | Test | BTEST |

4. Save and stop editing.

**Expected FAIL output:**

Section 5 of the `.txt` report will state that `CAR_RCA_6` is missing from the sequence. Section 5 status will be **FAIL** (red).

---

#### Test 1-E — MODIFIED record without a matching RETIREMENT (Section 9)

**What this tests:** Section 9 checks that every `MODIFIED` record (a feature being updated) has a corresponding `RETIREMENT` record with the same PROVID. This retirement record is the old version being replaced. If there is a `MODIFIED` with no matching `RETIREMENT`, or a `RETIREMENT` with no matching `MODIFIED`, it is an error.

**How to create the known-bad data — a MODIFIED with no matching RETIREMENT:**

1. Start from a fresh copy of the clean update FC.
2. Open the FC in an edit session.
3. Add a **new record** representing a MODIFIED feature — but do NOT add the corresponding RETIREMENT:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE |
|---|---|---|---|---|---|---|---|---|
| 6 | CAR_RCA_6 | 0 | `MODIFIED` | 0 | 2026-04-01 | BTEST | Updated boundary | BTEST |

4. Save and stop editing. There is no `RETIREMENT` record with `LEGAL_OGMA_PROVID = CAR_RCA_6`.

**Expected FAIL output:**

Section 9 of the `.txt` report will flag `CAR_RCA_6` as having a `MODIFIED` record with no matching `RETIREMENT`. Section 9 status will be **FAIL** (red).

---

#### Test 1-F — Two records share the same PROVID and PROVID_PART_NUMBER within the same MODIFICATION_TYPE (Section 10)

**What this tests:** Section 10 checks that within a single `MODIFICATION_TYPE` group, no two records share both the same PROVID and the same PROVID_PART_NUMBER. This is a direct data integrity violation — it means the same feature version has been entered twice.

**How to create the known-bad data:**

1. Start from a fresh copy of the clean update FC.
2. Open the FC in an edit session.
3. Add **two new records** that are identical in PROVID, PROVID_PART_NUMBER, and MODIFICATION_TYPE:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE |
|---|---|---|---|---|---|---|---|---|
| 6 | CAR_RCA_6 | 0 | `NEW` | 0 | 2026-04-01 | BTEST | Test | BTEST |
| 7 | CAR_RCA_6 | 0 | `NEW` | 0 | 2026-04-01 | BTEST | Test | BTEST |

4. Save and stop editing.

**Expected FAIL output:**

Section 10 of the `.txt` report will flag `CAR_RCA_6 / PROVID_PART_NUMBER 0` as a duplicate within the `NEW` MODIFICATION_TYPE group. Section 10 status will be **FAIL** (red).

---

#### Test 1-G — Field value not in assigned domain (Section 12)

**What this tests:** Section 12 checks that every field with a domain (an allowed list of values) contains only values from that list. The `MODIFICATION_TYPE` field has a domain of: `NEW`, `MODIFIED`, `RETIREMENT`, `PERMANENT RETIREMENT`, `MODIFIED_NOREPLACE`. Any other value is an error.

**How to create the known-bad data:**

1. Start from a fresh copy of the clean update FC.
2. First, assign a domain to the `MODIFICATION_TYPE` field in `test_update.gdb` so the script can check it:
   a. In the Catalog pane, right-click `test_update.gdb` → **Domains**.
   b. Click **New Domain**. Name it `MODIFICATION_TYPE_DOMAIN`. Type: Text.
   c. Add these coded values: `NEW`, `MODIFIED`, `RETIREMENT`, `PERMANENT RETIREMENT`, `MODIFIED_NOREPLACE`.
   d. Save. Then open the FC's Fields view and assign `MODIFICATION_TYPE_DOMAIN` to the `MODIFICATION_TYPE` field.
3. Open the FC in an edit session.
4. Add a **new record** with an invalid MODIFICATION_TYPE value:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE |
|---|---|---|---|---|---|---|---|---|
| 6 | CAR_RCA_6 | 0 | `UPDATED` | 0 | 2026-04-01 | BTEST | Test | BTEST |

5. Save and stop editing. (You may need to turn off field validation in the edit session to save an out-of-domain value.)

**Expected FAIL output:**

Section 12 of the `.txt` report will flag that `MODIFICATION_TYPE = 'UPDATED'` is not a valid domain value. Section 12 status will be **FAIL** (red).

---

### Known-Good Test — Script 1

Start from a fresh copy of the clean update FC (the five records from the Test Setup, no errors added). Add three records that represent a valid update scenario:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | MODIFICATION_TYPE | STATUS | GIS_CHANGE_DATE | GIS_CHANGE_PERSON | CHANGE_REASON | INITIATOR_OF_CHANGE | RETIREMENT_DATE |
|---|---|---|---|---|---|---|---|---|---|
| 6 | CAR_RCA_6 | 0 | `NEW` | 0 | 2026-04-01 | BTEST | New polygon added | BTEST | `<null>` |
| 7 | CAR_RCA_1 | 0 | `MODIFIED` | 0 | 2026-04-01 | BTEST | Boundary corrected | BTEST | `<null>` |
| 8 | CAR_RCA_1 | 0 | `RETIREMENT` | 1 | 2026-04-01 | BTEST | Replaced by MODIFIED | BTEST | 2026-04-01 |

Run the script with `test_update.gdb`'s FC as the post-update input and `test_master.gdb`'s FC as the master.

**Expected PASS output:**

All sections of the `.txt` report show `- No errors found`. The `.html` dashboard shows all sections as green (PASS). The overall status in the JSON file is `"overall_status": "PASS"`.

---

### Checklist — Script 1

Before marking Script 1 as tested, confirm every item below:

- [ ] `test_master.gdb` and `test_update.gdb` exist with the correct FC name `old_growth_management_area_legal_bc_poly`
- [ ] Test 1-A run — Section 1 reported FAIL for `<NULL>` string in `FEATURE_NOTES`
- [ ] Test 1-B run — Section 2 reported FAIL for blank change fields on a `NEW` record
- [ ] Test 1-C run — Section 4 reported FAIL for 0 / null in FEATID and PROVID
- [ ] Test 1-D run — Section 5 reported FAIL for a gap in PROVID sequence (`CAR_RCA_6` missing)
- [ ] Test 1-E run — Section 9 reported FAIL for `MODIFIED` without matching `RETIREMENT`
- [ ] Test 1-F run — Section 10 reported FAIL for duplicate PROVID + PROVID_PART_NUMBER within same MODIFICATION_TYPE
- [ ] Test 1-G run — Section 12 reported FAIL for `MODIFICATION_TYPE = 'UPDATED'` (invalid domain value)
- [ ] Known-good test run — All sections reported PASS, `.html` dashboard is all green
- [ ] Three output files (`.txt`, `.json`, `.html`) were created in the expected folder for every run
- [ ] No errors appeared in the ArcGIS Pro **Messages** pane that were not expected

---

## Script 2 — `check_for_geometry_issues.py`

### Overview

This script performs four geometry quality checks on any feature class where `MODIFICATION_TYPE` is not null (meaning features involved in the current update). First, it repairs any geometry errors that ArcGIS can fix automatically. Second, it flags any polygons with an area of 0.5 hectares (5,000 square metres) or less — these are called "sliver polygons" and are usually editing accidents. Third, it flags any features with more than 524,000 vertices — this is the maximum the BC Geographic Warehouse will accept. Fourth, it checks for features that have four or more identical vertices at the same X/Y location, which also prevents loading to the BCGW.

For each problem found, the script writes a warning message in the ArcGIS Pro tool dialog and creates a temporary feature class inside the same Feature Dataset for your review.

**Status:** Partially migrated — confirm full Python 3 migration before running these tests.

---

### How to Run

| Parameter | Description |
|---|---|
| **Input feature class** | The feature class to check |

**To run in ArcGIS Pro:**
1. In the Catalog pane, open the toolbox.
2. Double-click **Check for Geometry Issues**.
3. Enter the path to your test feature class.
4. Click **Run** and watch the **Messages** tab for warnings.

After the run, refresh the Feature Dataset in the Catalog pane. Any problem features will appear as new temporary feature classes.

> **WARNING — Do not run this script on the live staging dataset.**
> It adds temporary feature classes and modifies geometry. Always run on a local test copy.

---

### Test Setup — Script 2

1. In your `02_geometry_checks` folder, create a new FGDB: `geometry_test.gdb`.
2. Inside it, create a Feature Dataset named `old_growth_management_area_albers` (BC Albers / EPSG:3005).
3. Inside the Feature Dataset, create a polygon feature class named `old_growth_management_area_legal_bc_poly`.
4. Add these fields:

| Field Name | Type |
|---|---|
| `LEGAL_OGMA_INTERNAL_ID` | Long Integer |
| `MODIFICATION_TYPE` | Text (30) |

---

### Known-Bad Tests — Script 2

---

#### Test 2-A — Sliver polygon (area ≤ 5,000 sq metres)

**What this tests:** The script flags any polygon with `MODIFICATION_TYPE IS NOT NULL` and an area of 5,000 square metres or less (0.5 hectares).

**How to create the known-bad data:**

1. Open `old_growth_management_area_legal_bc_poly` in an edit session.
2. Create a **very small polygon** — draw a rectangle approximately 50 metres × 50 metres (that gives an area of 2,500 sq m, which is well under the 5,000 sq m threshold). Use the **Create Features** pane and draw it anywhere in BC.
3. Set the attributes:
   - `LEGAL_OGMA_INTERNAL_ID` = `1`
   - `MODIFICATION_TYPE` = `NEW`
4. Save and stop editing.

**Expected FAIL output:**

The tool dialog will show a warning similar to:
```
WARNING: There are 1 modified features (or parts of modified features) with an area of < 0.1 ha.
WARNING: A feature class named temp_sliver_polygons_old_growth_management_area_legal_bc_poly 
         has been added to your update fgdb so you can review these slivers.
```
A new feature class `temp_sliver_polygons_old_growth_management_area_legal_bc_poly` will appear in the Feature Dataset.

---

#### Test 2-B — Feature over 524,000 vertices (programmatic)

**What this tests:** The script flags any feature with `MODIFICATION_TYPE IS NOT NULL` that has more than 524,000 vertices.

**Why programmatic?** It is not practical to draw a polygon with over half a million vertices by hand. The following Python code creates one for you.

**How to create the known-bad data — run this code in the ArcGIS Pro Python window:**

1. In ArcGIS Pro, open the **Python** window (Analysis tab → Python).
2. Copy and paste the following code, updating the `fc_path` variable to point to your test feature class:

```python
import arcpy
import math

# Update this path to your test feature class
fc_path = r"C:\GIS_Testing\script_migration_tests\02_geometry_checks\geometry_test.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc_poly"

# Create a polygon with approximately 530,000 vertices by generating a
# circle approximated by many short line segments.
# The polygon is centred near Williams Lake, BC (BC Albers coordinates).
centre_x = 1_200_000  # BC Albers easting (metres)
centre_y = 700_000    # BC Albers northing (metres)
radius = 10_000       # 10 km radius
num_vertices = 530_000

points = []
for i in range(num_vertices):
    angle = 2 * math.pi * i / num_vertices
    x = centre_x + radius * math.cos(angle)
    y = centre_y + radius * math.sin(angle)
    points.append(arcpy.Point(x, y))

# Close the ring by repeating the first point
points.append(points[0])

polygon = arcpy.Polygon(arcpy.Array(points),
                        arcpy.SpatialReference(3005))  # BC Albers

with arcpy.da.InsertCursor(fc_path, ["SHAPE@", "LEGAL_OGMA_INTERNAL_ID", "MODIFICATION_TYPE"]) as cursor:
    cursor.insertRow([polygon, 2, "NEW"])

print("Done — high-vertex polygon inserted.")
```

3. Press **Enter** to run the code.
4. Refresh the Catalog pane to confirm the record was added.

**Expected FAIL output:**

The tool dialog will show:
```
WARNING: There are 1 "modified" features with a vertex count over 524000.
WARNING: Features must have less than 524000 vertexes to load to the BCGW.
WARNING: A feature class named temp_old_growth_management_area_legal_bc_poly_OVER_MAX_VERTICES
         containing the offending features has been added to your update fgdb.
```
A new feature class ending in `_OVER_MAX_VERTICES` will appear in the Feature Dataset.

---

#### Test 2-C — Five or more identical vertices at the same location (programmatic)

**What this tests:** The script flags any feature with `MODIFICATION_TYPE IS NOT NULL` that has four or more vertices at exactly the same X/Y coordinate. This is a BCGW load blocker.

**How to create the known-bad data — run this code in the ArcGIS Pro Python window:**

```python
import arcpy

# Update this path to your test feature class
fc_path = r"C:\GIS_Testing\script_migration_tests\02_geometry_checks\geometry_test.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc_poly"

# Build a polygon that has 5 identical vertices at point (1_150_000, 680_000).
# The polygon is otherwise a valid rectangle, but vertex 2 is repeated 5 times.
duplicate_x = 1_150_000.0
duplicate_y = 680_000.0

# Ring: bottom-left → duplicate point (5 times) → top-right → top-left → close
ring = arcpy.Array([
    arcpy.Point(1_140_000, 670_000),   # vertex 1 — bottom-left
    arcpy.Point(duplicate_x, duplicate_y),  # vertex 2 — duplicated below
    arcpy.Point(duplicate_x, duplicate_y),  # vertex 3
    arcpy.Point(duplicate_x, duplicate_y),  # vertex 4
    arcpy.Point(duplicate_x, duplicate_y),  # vertex 5
    arcpy.Point(duplicate_x, duplicate_y),  # vertex 6 — 5 identical = triggers check
    arcpy.Point(1_160_000, 690_000),   # vertex 7 — top-right
    arcpy.Point(1_140_000, 690_000),   # vertex 8 — top-left
    arcpy.Point(1_140_000, 670_000),   # close ring
])

polygon = arcpy.Polygon(ring, arcpy.SpatialReference(3005))

with arcpy.da.InsertCursor(fc_path,
        ["SHAPE@", "LEGAL_OGMA_INTERNAL_ID", "MODIFICATION_TYPE"]) as cursor:
    cursor.insertRow([polygon, 3, "NEW"])

print("Done — polygon with duplicate vertices inserted.")
```

**Expected FAIL output:**

The tool dialog will show:
```
WARNING: There are instances of 4 (or more) identical vertices in modified features!
WARNING: A feature class named temp_identical_vertex_check_Step2_old_growth_management_area_legal_bc_poly
         has been added to your update fgdb.
WARNING: This feature class contains the locations of the vertices that need to be resolved.
```

---

### Known-Good Test — Script 2

1. Delete all records from the test feature class (or create a fresh one).
2. Open it in an edit session and draw one **normal-sized polygon** — at least 1 hectare (10,000 sq m) in area, with a simple shape (a rough rectangle with four or five vertices is fine). Set `MODIFICATION_TYPE = 'NEW'`.
3. Save and stop editing.
4. Run the script.

**Expected PASS output:**

The tool dialog shows only informational messages (no warnings). The messages will look like:
```
Repairing geometry of all modified features (where MODIFICATION_TYPE is not null).
    - complete
Identifying features (where MODIFICATION_TYPE is not null) that have areas of <= 0.5 ha.
    (no warning message = no slivers found)
Doing a vertex count of all modified features...
    All "modified" features have less than 524000 vertices - good work!
Checking all modified features for identical vertices...
    (no warning message = no identical vertices found)
```
No temporary feature classes are created.

---

### Checklist — Script 2

- [ ] Test 2-A run — warning shown for sliver polygon; `temp_sliver_polygons_...` FC created in Feature Dataset
- [ ] Test 2-B run — Python code executed successfully; warning shown for over-vertex-limit feature; `..._OVER_MAX_VERTICES` FC created
- [ ] Test 2-C run — Python code executed successfully; warning shown for identical vertices; `temp_identical_vertex_check_Step2_...` FC created
- [ ] Known-good test run — no warnings shown; no temporary FCs created
- [ ] Confirmed the script is fully migrated to Python 3 before running any tests (no `import arcinfo`, no `arcpy.ProductInfo()` call, no `print` statements without parentheses)

---

## Script 3 — `find_duplicates.py`

### Overview

This script checks a single feature class for **duplicate values** in a field you specify. For example, if two records both have `LEGAL_OGMA_PROVID = 'CAR_RCA_5'`, the script will warn you. You can optionally tell it to only check current (non-retired) records — when the `process_current_only` option is turned on, any record that has a value in `RETIREMENT_DATE` is skipped. You can also check a composite key by specifying two field names separated by a semicolon — for example `LEGAL_OGMA_PROVID;PROVID_PART_NUMBER` would flag two records only if they share the same combination of PROVID *and* PROVID_PART_NUMBER.

**Status:** Python 2 — needs full migration before testing. Do not test until migration is complete.

---

### Python 2 Migration Checklist — Script 3

Before creating test data, the assigned developer must confirm every Python 2 pattern has been replaced:

| Original Python 2 pattern | Required Python 3 replacement |
|---|---|
| `import win32com.client` | Remove entirely |
| `gp = win32com.client.Dispatch(...)` | Remove entirely |
| `gp.searchcursor(fc)` | `arcpy.da.SearchCursor(fc, fields)` |
| `row = rowsObj.next()` / `while row:` | `for row in cursor:` |
| `eval("row." + field_name)` | Direct field access: `row[field_index]` |
| `print "text"` (no parentheses) | `print("text")` |
| `x <> y` | `x != y` |
| `dict.has_key(k)` | `k in dict` |
| `exec "statement"` | `exec("statement")` |
| `gp.addwarning(...)` | `arcpy.AddWarning(...)` |
| `gp.adderror(...)` | `arcpy.AddError(...)` |

---

### How to Run (after migration)

| Parameter | Description | Example |
|---|---|---|
| **Feature class path** | Full path to the FC to check | `C:\...\test.gdb\...\old_growth_management_area_legal_bc_poly` |
| **Field name(s)** | Field to check; for composite use semicolon separator | `LEGAL_OGMA_PROVID` or `LEGAL_OGMA_PROVID;PROVID_PART_NUMBER` |
| **process_current_only** | `true` to skip retired records | `true` |

---

### Test Setup — Script 3

1. In `03_find_duplicates`, create `find_dup_test.gdb` with Feature Dataset `ogma_albers` (BC Albers).
2. Inside, create polygon FC `old_growth_management_area_legal_bc_poly` with these fields:

| Field | Type |
|---|---|
| `LEGAL_OGMA_INTERNAL_ID` | Long Integer |
| `LEGAL_OGMA_PROVID` | Text (30) |
| `PROVID_PART_NUMBER` | Long Integer |
| `MODIFICATION_TYPE` | Text (30) |
| `RETIREMENT_DATE` | Date |

---

### Known-Bad Tests — Script 3

---

#### Test 3-A — Duplicate value, both records non-retired

**How to create the known-bad data:**

1. Open the test FC in an edit session.
2. Add these two records (same `LEGAL_OGMA_PROVID`, both with null `RETIREMENT_DATE`):

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | RETIREMENT_DATE |
|---|---|---|---|
| 1 | CAR_RCA_5 | 0 | `<null>` |
| 2 | CAR_RCA_5 | 0 | `<null>` |

3. Save and stop editing.
4. Run the script with `field = LEGAL_OGMA_PROVID` and `process_current_only = true`.

**Expected FAIL output:**
```
WARNING: LEGAL_OGMA_PROVID   CAR_RCA_5   has duplicate values.
```

---

#### Test 3-B — Duplicate value but one record is retired (should NOT flag)

**How to create the known-bad data:**

1. Delete all records. Add these two records — same PROVID but one has a RETIREMENT_DATE:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | RETIREMENT_DATE |
|---|---|---|---|
| 1 | CAR_RCA_5 | 0 | `<null>` |
| 2 | CAR_RCA_5 | 0 | 2025-06-01 |

2. Save and stop editing.
3. Run with `field = LEGAL_OGMA_PROVID` and `process_current_only = true`.

**Expected PASS output (no warning):**
```
No Duplicates Have Been Found
```
The record with `RETIREMENT_DATE` populated is skipped when `process_current_only = true`.

> **What to check:** If the tool warns about a duplicate here, the retirement date filtering logic is broken. This is the most important test for the `process_current_only` flag.

---

#### Test 3-C — Composite key duplicate

**How to create the known-bad data:**

1. Delete all records. Add these three records — Records 1 and 3 share the same PROVID+PART_NUMBER combination:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | RETIREMENT_DATE |
|---|---|---|---|
| 1 | CAR_RCA_5 | 0 | `<null>` |
| 2 | CAR_RCA_6 | 0 | `<null>` |
| 3 | CAR_RCA_5 | 0 | `<null>` |

2. Save and stop editing.
3. Run with `field = LEGAL_OGMA_PROVID;PROVID_PART_NUMBER` and `process_current_only = true`.

**Expected FAIL output:**
```
WARNING: LEGAL_OGMA_PROVID   CAR_RCA_5 -> 0   has duplicate values.
```
Records 1 and 3 share both `CAR_RCA_5` and `0` — the composite key triggers the warning. Record 2 (`CAR_RCA_6`) does not share this combination and is not flagged.

---

### Known-Good Test — Script 3

1. Delete all records. Add three records with unique PROVIDs, all non-retired:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | PROVID_PART_NUMBER | RETIREMENT_DATE |
|---|---|---|---|
| 1 | CAR_RCA_1 | 0 | `<null>` |
| 2 | CAR_RCA_2 | 0 | `<null>` |
| 3 | CAR_RCA_3 | 0 | `<null>` |

2. Run with `field = LEGAL_OGMA_PROVID` and `process_current_only = true`.

**Expected PASS output:**
```
No Duplicates Have Been Found
```

---

### Checklist — Script 3

- [ ] All Python 2 patterns in the migration checklist table have been removed and replaced
- [ ] Test 3-A run — duplicate warning shown for `CAR_RCA_5` (both records active)
- [ ] Test 3-B run — **no** duplicate warning shown when one record has a RETIREMENT_DATE and `process_current_only = true`
- [ ] Test 3-C run — composite key duplicate warning shown for `CAR_RCA_5 -> 0`
- [ ] Known-good test run — "No Duplicates Have Been Found" message shown
- [ ] No Python exceptions or stack trace errors occurred during any run

---

## Script 4 — `find_duplicates_2_datasets.py`

### Overview

This script does the same job as Script 3, but it checks for duplicates **across two separate feature classes** instead of within one. If the same value appears in Feature Class 1 and also in Feature Class 2, the script reports it as a cross-dataset duplicate. The most common use case is checking that Legal OGMA and Non-Legal OGMA do not share PROVID values — they should not, because each PROVID is unique province-wide. The `process_current_only` option works the same way as in Script 3.

**Status:** Python 2 — needs full migration before testing. The same Python 2 migration checklist from Script 3 applies here.

---

### How to Run (after migration)

| Parameter | Description |
|---|---|
| **Feature class 1 path** | First FC to check (e.g. legal OGMA) |
| **Field name for FC1** | Field to check in FC1 (e.g. `LEGAL_OGMA_PROVID`) |
| **process_current_only** | `true` to skip retired records |
| **Feature class 2 path** | Second FC to check (e.g. non-legal OGMA) |
| **Field name for FC2** | Field to check in FC2 (e.g. `NON_LEGAL_OGMA_PROVID`) |

---

### Test Setup — Script 4

1. In `04_find_duplicates_2_datasets`, create `find_dup_2ds_test.gdb` with Feature Dataset `ogma_albers` (BC Albers).
2. Create **two** polygon feature classes:
   - `old_growth_management_area_legal_bc_poly` — fields: `LEGAL_OGMA_INTERNAL_ID` (Long), `LEGAL_OGMA_PROVID` (Text 30), `RETIREMENT_DATE` (Date)
   - `old_growth_management_area_non_legal_bc_poly` — fields: `NON_LEGAL_OGMA_INTERNAL_ID` (Long), `NON_LEGAL_OGMA_PROVID` (Text 30), `RETIREMENT_DATE` (Date)

---

### Known-Bad Tests — Script 4

---

#### Test 4-A — Same PROVID exists in both datasets, both non-retired

**How to create the known-bad data:**

1. Add one record to the **legal** FC:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID | RETIREMENT_DATE |
|---|---|---|
| 1 | CAR_RCA_10 | `<null>` |

2. Add one record to the **non-legal** FC with the same PROVID value:

| NON_LEGAL_OGMA_INTERNAL_ID | NON_LEGAL_OGMA_PROVID | RETIREMENT_DATE |
|---|---|---|
| 1 | CAR_RCA_10 | `<null>` |

3. Run with FC1 = legal FC, field1 = `LEGAL_OGMA_PROVID`, FC2 = non-legal FC, field2 = `NON_LEGAL_OGMA_PROVID`, `process_current_only = true`.

**Expected FAIL output:**
```
WARNING: LEGAL_OGMA_PROVID   CAR_RCA_10   has duplicate values.
```

---

#### Test 4-B — Same PROVID in both datasets, one retired (should NOT flag)

**How to create the known-bad data:**

1. Clear both FCs. Add records such that FC1 has the value and it is active, but FC2 has the same value with a RETIREMENT_DATE:

| FC1 — LEGAL_OGMA_PROVID | RETIREMENT_DATE |
|---|---|
| CAR_RCA_10 | `<null>` |

| FC2 — NON_LEGAL_OGMA_PROVID | RETIREMENT_DATE |
|---|---|
| CAR_RCA_10 | 2025-06-01 |

2. Run with `process_current_only = true`.

**Expected PASS output:**
```
No Duplicates Have Been Found
```

---

### Known-Good Test — Script 4

1. Clear both FCs. Add records with **different** PROVIDs in each:

| Legal FC — LEGAL_OGMA_PROVID |
|---|
| CAR_RCA_1 |
| CAR_RCA_2 |

| Non-Legal FC — NON_LEGAL_OGMA_PROVID |
|---|
| CAR_RCA_3 |
| CAR_RCA_4 |

2. Run the script. No values overlap between the two datasets.

**Expected PASS output:**
```
No Duplicates Have Been Found
```

---

### Checklist — Script 4

- [ ] All Python 2 patterns migrated (same list as Script 3)
- [ ] Test 4-A run — cross-dataset duplicate warning shown for `CAR_RCA_10`
- [ ] Test 4-B run — **no** warning shown when one record is retired and `process_current_only = true`
- [ ] Known-good test run — "No Duplicates Have Been Found" shown
- [ ] No Python exceptions during any run

---

## Script 5 — `update_sequential_number.py`

### Overview

This script automatically fills in blank or zero-value sequential numbers in a field. It finds the highest number already assigned, then increments upward to fill any gaps. For a simple numeric field (like `LEGAL_OGMA_INTERNAL_ID`), it just adds 1 to the highest existing value. For a string field like `LEGAL_OGMA_PROVID`, where the values look like `SKE_KIS_135`, it strips off the text prefix, finds the highest number suffix (135 in this case), and then fills blank records with `SKE_KIS_136`, `SKE_KIS_137`, and so on. If you are starting a brand new prefix that has never been used before, set the `is_new_prefix` flag to `true`. The `just_display_dont_update` flag lets you preview what the starting value would be without actually writing anything to the data.

**Status:** Python 2 — needs full migration before testing.

---

### Python 2 Migration Checklist — Script 5

In addition to the patterns listed for Script 3, check for:

| Original Python 2 pattern | Required Python 3 replacement |
|---|---|
| `gp.updatecursor(fc)` | `arcpy.da.UpdateCursor(fc, fields)` |
| `row.setValue(field, value)` | `row[index] = value` inside `with arcpy.da.UpdateCursor` |
| `dict.iteritems()` | `dict.items()` |
| `exec "row." + field + " = value"` | `row[field_index] = value` |

---

### How to Run (after migration)

| Parameter | Description | Example |
|---|---|---|
| **Feature class path** | Path to the FC to update | `C:\...\test.gdb\...\old_growth_management_area_legal_bc_poly` |
| **Field name** | Field to populate | `LEGAL_OGMA_INTERNAL_ID` or `LEGAL_OGMA_PROVID` |
| **Prefix** | Text prefix for string fields (leave blank for numeric) | `SKE_KIS_` |
| **is_new_prefix** | `true` if this prefix has never existed | `false` |
| **just_display_dont_update** | `true` to preview only, no writes | `false` |

---

### Test Setup — Script 5

1. In `05_update_seq_num`, create `seq_num_test.gdb` with Feature Dataset `ogma_albers` (BC Albers).
2. Create polygon FC `old_growth_management_area_legal_bc_poly` with fields:
   - `LEGAL_OGMA_INTERNAL_ID` (Long Integer)
   - `LEGAL_OGMA_PROVID` (Text 30)
   - `MODIFICATION_TYPE` (Text 30)

---

### Known-Bad Tests — Script 5

(These tests verify that the tool updates correctly — they are "bad" in the sense that the data starts in an incomplete state that needs fixing.)

---

#### Test 5-A — Numeric field with zeros to fill

**How to create the test data:**

1. Open the FC in an edit session. Add these records:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID |
|---|---|
| 1 | CAR_RCA_1 |
| 2 | CAR_RCA_2 |
| 3 | CAR_RCA_3 |
| 4 | CAR_RCA_4 |
| 5 | CAR_RCA_5 |
| 0 | `<null>` |
| 0 | `<null>` |

2. The two records with `LEGAL_OGMA_INTERNAL_ID = 0` are the ones to be filled.
3. Run the script with `field = LEGAL_OGMA_INTERNAL_ID`, `prefix = ` (blank), `is_new_prefix = false`, `just_display_dont_update = false`.

**Expected result:**

The two zero records should now have `LEGAL_OGMA_INTERNAL_ID = 6` and `7`. The tool messages will show:
```
Updating LEGAL_OGMA_INTERNAL_ID, starting with 6:
```

**Verification:** After the run, open the FC attribute table and confirm no records have `LEGAL_OGMA_INTERNAL_ID = 0` any more.

---

#### Test 5-B — String field with existing prefix

**How to create the test data:**

1. Clear all records. Add these records with `LEGAL_OGMA_PROVID` values:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID |
|---|---|
| 1 | ABC_DEF_8 |
| 2 | ABC_DEF_9 |
| 3 | ABC_DEF_10 |
| 4 | `<null>` |
| 5 | `<null>` |

2. Run with `field = LEGAL_OGMA_PROVID`, `prefix = ABC_DEF_`, `is_new_prefix = false`, `just_display_dont_update = false`.

**Expected result:**

The two null PROVID records should become `ABC_DEF_11` and `ABC_DEF_12`. Tool messages will show:
```
WARNING: The highest value in the dataset is ABC_DEF_10. Numbering for new features will start at ABC_DEF_11.
```

---

#### Test 5-C — New prefix assigned starting at 1

**How to create the test data:**

1. Clear all records. Add two records with null PROVIDs:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID |
|---|---|
| 1 | `<null>` |
| 2 | `<null>` |

2. Run with `field = LEGAL_OGMA_PROVID`, `prefix = NEW_TST_`, `is_new_prefix = true`, `just_display_dont_update = false`.

**Expected result:**

The two null records should become `NEW_TST_1` and `NEW_TST_2`. Tool messages will show:
```
WARNING: NEW_TST_ is a new prefix. Numbering will start at NEW_TST_1.
```

---

#### Test 5-D — Conflict: new prefix already exists (should ERROR and NOT update)

**How to create the test data:**

1. Clear all records. Add records that already contain the prefix `NEW_TST_`:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID |
|---|---|
| 1 | NEW_TST_1 |
| 2 | `<null>` |

2. Run with `field = LEGAL_OGMA_PROVID`, `prefix = NEW_TST_`, `is_new_prefix = true`, `just_display_dont_update = false`.

**Expected FAIL output:**

The tool must raise an error and NOT change any records:
```
ERROR: If you are sure you want to proceed using this prefix, rerun the tool with the 
       "This will be a new prefix" box unchecked.
```
After the run, confirm the null record is still null — the tool must not have written anything.

---

#### Test 5-E — Preview mode (just_display_dont_update = true)

**How to create the test data:**

Use the same data as Test 5-B (with `ABC_DEF_8`, `ABC_DEF_9`, `ABC_DEF_10` and two null records).

Run with `just_display_dont_update = true`.

**Expected result:**

The tool will report the starting value:
```
WARNING: The highest value in the dataset is ABC_DEF_10. Numbering for new features will start at ABC_DEF_11.
```
But the two null records must remain null — **no values are written**. Verify in the attribute table.

---

### Known-Good Test — Script 5

Use the data from Test 5-A after the tool has successfully run (all records now have valid IDs from 1 to 7). Re-run the script with `just_display_dont_update = true`.

**Expected result:** The tool reports that the highest value is 7 and the next value would be 8. No records are changed.

---

### Checklist — Script 5

- [ ] All Python 2 patterns migrated (see both Script 3 and Script 5 checklists)
- [ ] Test 5-A run — zero values replaced with 6 and 7; confirmed in attribute table
- [ ] Test 5-B run — null PROVIDs replaced with `ABC_DEF_11` and `ABC_DEF_12`
- [ ] Test 5-C run — new prefix `NEW_TST_` assigned starting at 1
- [ ] Test 5-D run — **error raised** and null record not updated when `is_new_prefix = true` but prefix already exists
- [ ] Test 5-E run — no records changed when `just_display_dont_update = true`; correct starting value shown

---

## Script 6 — `update_sequential_number_ogma_legal_nonlegal_arcpy.py`

### Overview

This script is a specialised version of Script 5, written specifically for OGMA PROVID fields. The key difference is that it looks at the highest PROVID suffix **across both the legal OGMA and non-legal OGMA feature classes at the same time** before assigning new numbers. This matters because legal and non-legal OGMAs share the same PROVID numbering sequence — if the legal dataset already has `CAR_RCA_15` as its highest value, the non-legal dataset cannot start its new records at `CAR_RCA_13`. They must start at `CAR_RCA_16`. The script always writes new values into the **non-legal FC** (`fc_1`), reading the legal FC (`fc_2`) as a reference for finding the true highest value.

**Status:** Partially uses arcpy — review remaining legacy patterns before testing.

---

### How to Run

| Parameter | Description | Example |
|---|---|---|
| **fc_1** | Non-legal OGMA FC (the one to be updated) | `...\old_growth_management_area_non_legal_bc_poly` |
| **field_1** | PROVID field in the non-legal FC | `NON_LEGAL_OGMA_PROVID` |
| **fc_2** | Legal OGMA FC (read-only reference) | `...\old_growth_management_area_legal_bc_poly` |
| **field_2** | PROVID field in the legal FC | `LEGAL_OGMA_PROVID` |
| **prefix** | The PROVID prefix to work with | `CAR_RCA_` |
| **is_new_prefix** | `true` if this prefix has never existed | `false` |
| **just_display_dont_update** | `true` to preview only | `false` |

---

### Test Setup — Script 6

1. In `06_update_seq_num_ogma`, create `ogma_seq_test.gdb` with Feature Dataset `old_growth_management_area_albers` (BC Albers).
2. Create **two** polygon FCs:
   - `old_growth_management_area_legal_bc_poly` — fields: `LEGAL_OGMA_INTERNAL_ID` (Long), `LEGAL_OGMA_PROVID` (Text 30)
   - `old_growth_management_area_non_legal_bc_poly` — fields: `NON_LEGAL_OGMA_INTERNAL_ID` (Long), `NON_LEGAL_OGMA_PROVID` (Text 30)

---

### Known-Bad Tests — Script 6

---

#### Test 6-A — Cross-dataset highest value used correctly

**This is the critical test.** It verifies that the tool correctly finds the highest suffix across both datasets and does not reuse a number already assigned in the legal dataset.

**How to create the test data:**

1. Open the **legal** FC in an edit session. Add these records:

| LEGAL_OGMA_INTERNAL_ID | LEGAL_OGMA_PROVID |
|---|---|
| 1 | CAR_RCA_10 |
| 2 | CAR_RCA_11 |
| 3 | CAR_RCA_15 |

2. Open the **non-legal** FC in an edit session. Add these records:

| NON_LEGAL_OGMA_INTERNAL_ID | NON_LEGAL_OGMA_PROVID |
|---|---|
| 1 | CAR_RCA_8 |
| 2 | CAR_RCA_12 |
| 3 | `<null>` |
| 4 | `<null>` |

3. Note: The legal FC's highest is `CAR_RCA_15`. The non-legal FC's highest is `CAR_RCA_12`. The tool must use 15 as the highest across both and assign `CAR_RCA_16` and `CAR_RCA_17` to the two null records.

4. Run the script with `prefix = CAR_RCA_`, `is_new_prefix = false`, `just_display_dont_update = false`.

**Expected result:**

Tool messages will show:
```
WARNING: Searching through 2 features with prefix of CAR_RCA_ in old_growth_management_area_non_legal_bc_poly
WARNING: Searching through 3 features with prefix of CAR_RCA_ in old_growth_management_area_legal_bc_poly
WARNING: The highest value in either dataset is CAR_RCA_15. Numbering for new features will start at CAR_RCA_16.
```

After the run, the two null records in the non-legal FC will have `NON_LEGAL_OGMA_PROVID = CAR_RCA_16` and `CAR_RCA_17`.

> **What to look for if the test fails:** If the null records were assigned `CAR_RCA_13` and `CAR_RCA_14`, the tool only checked the non-legal FC and missed the legal FC's higher values. This would cause a PROVID collision in production.

---

#### Test 6-B — Prefix does not exist but is_new_prefix = false (should ERROR)

**How to create the test data:**

1. Clear both FCs entirely (no records with any PROVID prefix at all).
2. Add one null record to the non-legal FC:

| NON_LEGAL_OGMA_INTERNAL_ID | NON_LEGAL_OGMA_PROVID |
|---|---|
| 1 | `<null>` |

3. Run with `prefix = CAR_RCA_`, `is_new_prefix = false`.

**Expected FAIL output:**

```
WARNING: CAR_RCA_ is a new prefix.
ERROR: Please rerun the tool with the "This will be a new prefix" box checked
```
No records are updated.

---

#### Test 6-C — Prefix already exists but is_new_prefix = true (should ERROR)

**How to create the test data:**

1. Clear both FCs. Add one record to the **legal** FC with `LEGAL_OGMA_PROVID = CAR_RCA_1`. Add one null record to the non-legal FC.
2. Run with `prefix = CAR_RCA_`, `is_new_prefix = true`.

**Expected FAIL output:**

```
WARNING: CAR_RCA_ already exists in one of the feature classes.
ERROR: If you are sure you want to proceed using this prefix, rerun the tool 
       with the "This will be a new prefix" box unchecked.
```
The null record in the non-legal FC must remain null.

---

### Known-Good Test — Script 6

1. Use the same data as Test 6-A after it has run successfully (non-legal FC now has `CAR_RCA_16` and `CAR_RCA_17`).
2. Run again with `just_display_dont_update = true`.

**Expected result:** The tool reports the highest value as `CAR_RCA_17` and that the next value would be `CAR_RCA_18`. No records are changed.

---

### Checklist — Script 6

- [ ] Test 6-A run — non-legal FC received `CAR_RCA_16` and `CAR_RCA_17` (not 13 and 14); confirmed in attribute table
- [ ] Test 6-B run — error raised when prefix is missing and `is_new_prefix = false`
- [ ] Test 6-C run — error raised when prefix already exists and `is_new_prefix = true`; null record remains null
- [ ] Known-good preview run — correct highest value reported; no records changed
- [ ] Confirmed no remaining legacy Python 2 patterns in the script

---

## Script 7 — `compare_number_of_records_in_staging_and_lrdw_20200501.py`

### Overview

This script compares the number of records in the **staging area GDB** (the local working copy before publishing) against the number of records in the **live BC Geographic Warehouse (BCGW)** via a database connection. It checks three optional groups of datasets: OGMA (legal and non-legal), Landscape Units, and SLRP planning data. For each dataset, it counts records in both the staging and live locations and reports whether they match. If the counts differ, it reports an error with the exact difference. This script is used as a final check after replication to confirm that what was loaded into the BCGW matches what was sent from staging.

**Status:** Partially migrated (uses arcpy) — review and test. Note that `arcpy.overwriteOutput = True` should be `arcpy.env.overwriteOutput = True`.

---

### Special Requirement — BCGW Connection

This script **cannot be run without a live BCGW connection.** It connects to the BCGW using a file named `BCGW.sde` in the ArcGIS Pro database connections folder.

#### How to set up the BCGW.sde connection in ArcGIS Pro Catalog

1. In ArcGIS Pro, open the **Catalog** pane.
2. In the Catalog pane, expand **Databases**.
3. Right-click **Databases** → **New Database Connection**.
4. In the dialog:
   - **Database Platform:** Oracle
   - **Instance:** `bcgw.bcgov` (or the current BCGW service name — confirm with your DRM)
   - **Authentication:** Database authentication
   - **Username / Password:** Your BCGW read-only credentials
5. Name the connection file exactly `BCGW.sde` and save it to the default database connections folder.
6. The script references the connection as: `Database Connections\BCGW.sde`.

> **WARNING — BCGW credentials are not stored in this tutorial.**
> Contact your Data Resource Manager (DRM) for current BCGW connection details and read-only credentials. Do not use write-access credentials with this script.

#### What to do if a BCGW connection is not available

If you are testing in an environment without BCGW access (e.g. off-network):

1. **Document the expected outputs only** — record the expected output messages that the script should produce (see Known-Bad and Known-Good tests below).
2. **Verify the staging GDB paths are correct** before running:
   - Open the script and locate the `staging_path` variable.
   - Confirm the path exists and contains the expected feature classes using the Catalog pane.
   - The expected staging path is: `\\data.bcgov\data_staging_bcgw\land_use_plans_secure\slrp`
3. Mark the test as **BLOCKED — requires BCGW connection** in your test log, and arrange a time to run it with network access.

---

### How to Run

| Parameter | Description |
|---|---|
| **ogmaCompare** | `true` to compare Legal and Non-Legal OGMA counts |
| **luCompare** | `true` to compare Landscape Unit counts |
| **slrpCompare** | `true` to compare all SLRP dataset counts |

**At least one parameter must be set to `true`.**

---

### Test Setup — Script 7

Because this script connects directly to the live BCGW, you cannot create a fully isolated local test in the same way as the other scripts. Instead, the tests below describe the scenario to set up in the **staging GDB** and what outputs to look for when run against the live BCGW.

**Before running any test:**

1. Confirm the staging GDB at `\\data.bcgov\data_staging_bcgw\land_use_plans_secure\slrp\old_growth_management_area_bc.gdb` is accessible.
2. Confirm your `BCGW.sde` connection is working by double-clicking it in the Catalog pane. If a list of tables appears, the connection is live.
3. Note the current record counts in both staging and BCGW for `old_growth_management_area_legal_bc_poly` — write these down before testing.

---

### Known-Bad Tests — Script 7

> **IMPORTANT:** These tests require temporarily modifying the staging GDB. Coordinate with your DRM before running. Do not perform these tests during an active update cycle.

---

#### Test 7-A — Staging has MORE records than BCGW

**Scenario:** The staging OGMA legal FC has been updated with new records that have not yet been published to the BCGW.

**How to create this scenario:**

1. Confirm the staging and BCGW counts currently match (run the script first with all flags `true` — it should show matching counts).
2. Add **one extra record** to the staging `old_growth_management_area_legal_bc_poly`. Use a temporary polygon with a placeholder attribute.
3. Run the script with `ogmaCompare = true`.

**Expected FAIL output:**

```
ERROR: Number of features in staging area Legal OGMA dataset: [staging count]
ERROR: Number of features in BCGW RMP_OGMA_LEGAL_SP dataset: [bcgw count]
ERROR: There are [N] more Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_SP dataset
```
The ArcGIS Pro tool dialog will highlight the error in red.

4. After confirming the FAIL, delete the temporary record you added.

---

#### Test 7-B — BCGW has MORE records than staging

**Scenario:** The BCGW has been updated but the staging GDB has not been refreshed to match.

**How to create this scenario:**

1. Temporarily remove one record from the staging OGMA legal FC (note the OBJECTID so you can re-add it).
2. Run the script with `ogmaCompare = true`.

**Expected FAIL output:**

```
ERROR: Number of features in staging area Legal OGMA dataset: [staging count]
ERROR: Number of features in BCGW RMP_OGMA_LEGAL_SP dataset: [bcgw count]
ERROR: There are [N] less Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_SP dataset
```

3. After confirming the FAIL, restore the record you removed.

---

### Known-Good Test — Script 7

Run the script after restoring the staging GDB to its correct state (same record count as BCGW).

Run with `ogmaCompare = true`, `luCompare = true`, `slrpCompare = true`.

**Expected PASS output:**

For each dataset checked, the messages pane will show only `AddMessage` lines (not `AddError`):
```
Checking RMP_OGMA_LEGAL_SP
Number of features in staging area Legal OGMA dataset: [N]
Number of features in BCGW RMP_OGMA_LEGAL_SP dataset: [N]
There are the same number of Legal OGMA features in both the staging and RMP_OGMA_LEGAL_SP datasets

Checking RMP_OGMA_NON_LEGAL_SP
...
```
No red error messages appear in the tool dialog.

---

### Checklist — Script 7

- [ ] `BCGW.sde` connection confirmed working in ArcGIS Pro Catalog pane
- [ ] Staging GDB paths confirmed accessible before running
- [ ] Test 7-A run — error shown with exact count difference when staging has more records
- [ ] Test 7-B run — error shown with exact count difference when BCGW has more records
- [ ] Staging GDB restored to correct state after each bad test
- [ ] Known-good test run — all datasets show matching counts with no error messages
- [ ] `arcpy.overwriteOutput = True` corrected to `arcpy.env.overwriteOutput = True` in the script
- [ ] Script confirmed to run without Python exceptions

---

## Master Testing Checklist

Use this table to track overall test progress across all seven scripts. A script is not ready for production use until every row in its section is ticked.

| # | Script | Migration Status | Known-Bad Tests Passed | Known-Good Test Passed | Ready? |
|---|---|---|---|---|---|
| 1 | `attribute_qa_v8.py` | Migrated | 7 known-bad tests (1-A through 1-G) | All sections PASS | ☐ |
| 2 | `check_for_geometry_issues.py` | Partial — confirm before testing | 3 known-bad tests (2-A, 2-B, 2-C) | No warnings shown | ☐ |
| 3 | `find_duplicates.py` | Python 2 — migrate first | 2 known-bad + 1 boundary test (3-A, 3-B, 3-C) | "No Duplicates" shown | ☐ |
| 4 | `find_duplicates_2_datasets.py` | Python 2 — migrate first | 2 known-bad tests (4-A, 4-B) | "No Duplicates" shown | ☐ |
| 5 | `update_sequential_number.py` | Python 2 — migrate first | 4 tests (5-A through 5-D) + preview test 5-E | Preview shows correct value, no writes | ☐ |
| 6 | `update_sequential_number_ogma_legal_nonlegal_arcpy.py` | Partial — review | 3 known-bad tests (6-A, 6-B, 6-C) | Preview shows correct value, no writes | ☐ |
| 7 | `compare_number_of_records_in_staging_and_lrdw_20200501.py` | Partial — review | 2 known-bad tests (7-A, 7-B) | All counts match, no errors | ☐ |

### Final Sign-Off

Before any script is deployed to production, the tester must confirm:

- [ ] Every known-bad test produced a FAIL (not a false PASS)
- [ ] Every known-good test produced a clean PASS (no unexpected errors or warnings)
- [ ] No changes were made to any live production dataset during testing
- [ ] Test FGDBs are stored in the tester's local workarea, not on the shared network staging path
- [ ] Test results (including any unexpected behaviour) have been documented and shared with the assigned developer

---

*End of tutorial. Questions? Contact the Data Resource Manager for your region.*
