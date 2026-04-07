# Update Sequential Number — OGMA Legal and Non-Legal

## Purpose

This ArcGIS Pro Python Toolbox tool assigns sequential PROVID (Provincial Identifier) values to new (null/empty) records in a **non-legal** OGMA feature class. It does so by first scanning **both** the legal and non-legal feature classes to find the highest existing sequential number for a given prefix, then numbering the new records starting from the next value. This ensures PROVID numbering remains unique and continuous across both datasets.

## About the PROVID Field

PROVID is a `VARCHAR2(20)` field that serves as the **unique provincial identifier** for an OGMA polygon (or collection of polygons sharing the same attribute values). It is unique for any polygon that does not have a retirement date, and is used to track change in a feature over time.

A PROVID value is made up of three components:
1. A **regional prefix** (e.g. `KAM`, `KOR`, `PRG`, `SKE`, `CAR`, `NAN`, `FSJ`, or `SRY`)
2. A **planning area** (e.g. `TSA`, `LU`, etc.)
3. An **OGMA number** (the sequential integer this tool assigns)

For example: `CAR_RCA_42`

**PROVID tracks the full lifecycle of an OGMA feature from non-legal to legal.** The same PROVID is used across both the non-legal and legal feature classes — there is no duplication of PROVID for current (non-retired) features between the two datasets. This is why the tool scans **both** feature classes before assigning a new number.

## Parameters

| # | Parameter | Type | Required | Description |
|---|-----------|------|----------|-------------|
| 1 | **Non-Legal Feature Class** | Feature Class | Yes | The non-legal OGMA feature class that contains records to be updated. |
| 2 | **Non-Legal PROVID Field** | Field | Yes | The PROVID field in the non-legal feature class (field list is filtered to the selected FC). |
| 3 | **Legal Feature Class** | Feature Class | Yes | The legal OGMA feature class used as a reference to determine the current highest sequential number. |
| 4 | **Legal PROVID Field** | Field | Yes | The PROVID field in the legal feature class. |
| 5 | **Prefix** | String | Yes | The prefix for the PROVID values (e.g. `CAR_RCA_`). Should end with an underscore. |
| 6 | **This will be a new prefix** | Boolean | No | Check this box if the prefix does not yet exist in either feature class. Defaults to unchecked. |
| 7 | **Just display next value — do not update** | Boolean | No | If checked, the tool reports what the next sequential number would be without writing any changes. Defaults to unchecked. |

## How It Works

### 1. Input Validation (updateMessages)

- Warns the user if the prefix does not end with an underscore (`_`).
- Blocks execution if the prefix contains a single-quote character (prevents SQL injection).

### 2. Prefix Existence Check

The tool queries both feature classes for records whose PROVID value starts with the supplied prefix (using a `LIKE '<prefix>%'` filter).

- **If no records match in either FC:** The prefix is treated as new. The user must have the "This will be a new prefix" checkbox enabled; otherwise the tool errors out.
- **If records are found:** The prefix already exists. If the user has the "new prefix" checkbox checked, the tool errors out and asks them to uncheck it.

### 3. Determine the Next Sequential Value

- **New prefix:** Numbering starts at `1` (e.g. `CAR_RCA_1`).
- **Existing prefix:** The tool scans every matching record in both the non-legal and legal feature classes. For each record it strips the prefix and attempts to parse the remainder as an integer. Non-integer suffixes are skipped with a warning. The highest integer suffix found across both datasets is incremented by one to become the starting value.

### 4. Update Null/Empty Records

If "Just display next value" is **not** checked:

1. The tool identifies all records in the **non-legal** feature class where the PROVID field is null or empty.
2. It opens an edit session on the workspace (geodatabase) using `arcpy.da.Editor`.
3. Each null/empty record is assigned the next sequential PROVID value in order (e.g. `CAR_RCA_42`, `CAR_RCA_43`, …).
4. The edit session is saved and closed. If an error occurs, the edit session is rolled back (edits are **not** saved).
5. A summary message reports how many features were updated.

If "Just display next value" **is** checked, the tool simply reports the next value and exits without modifying any data.

> **Important — Split Polygons:** When a single polygon is split into multiple polygons that have **different attribute values** for different portions, each group of polygons requires a manually-calculated PROVID. In this case:
> 1. Append your data to the master feature class.
> 2. Run this tool with **"Just display next value"** checked to find the next available number without writing any changes.
> 3. Manually calculate the PROVID for each group of polygons, incrementing the number for each group.
>
> For all other new polygons (standard case), set PROVID to `""`, append to the master feature class, and run the tool **without** "Just display next value" to have values assigned automatically.

### 5. Cleanup

All temporary feature layers created during execution are deleted in a `finally` block, ensuring cleanup occurs even if the tool encounters an error.

## Key Behaviors

- **Cross-dataset uniqueness:** PROVID must be unique across both the non-legal and legal feature classes for any current (non-retired) feature. The tool enforces this by finding the highest existing number across both datasets before assigning new values.
- **Only the non-legal FC is modified.** The legal feature class is read-only within this tool.
- **Lifecycle awareness:** The same PROVID follows a feature from non-legal through to legal status. This tool only assigns values at the point of creation (null/empty records) — it does not modify existing PROVIDs.
- **Safe SQL handling:** The prefix is sanitised (single quotes escaped) before being used in SQL WHERE clauses.
- **Unique layer names:** A UUID fragment is appended to temporary layer names to prevent collisions if the tool is run concurrently.
- **Edit session with rollback:** Updates are wrapped in an `arcpy.da.Editor` session with undo/redo support. If an error occurs mid-update, all changes are discarded.

## Out of Scope

This tool only assigns new PROVIDs to null/empty records. The following scenarios must be handled manually:

- **Updates:** When updating an existing OGMA feature, carry the existing PROVID forward unchanged. Do not modify it.
- **Retirements:** Do not change the PROVID on a feature being retired.
- **Split polygons with differing attributes:** Use the "Just display next value" option to find the next available number, then manually calculate and assign PROVIDs to each group (see note in Step 4 above).
- **UPDATE WITHOUT REPLACEMENT:** Consult the Data Resource Manager before making any changes.

## Example

Given:

- Non-legal FC contains: `CAR_RCA_1`, `CAR_RCA_2`, and **3 records with null PROVID**
- Legal FC contains: `CAR_RCA_3`, `CAR_RCA_4`

The tool finds the highest suffix across both FCs is **4**, so the three null records in the non-legal FC are assigned `CAR_RCA_5`, `CAR_RCA_6`, and `CAR_RCA_7`.
