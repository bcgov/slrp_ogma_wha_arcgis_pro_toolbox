# SLRP GIS Scripts — Team Migration Rules
**BC Ministry of Water Land Resource Stewardship — SLRP/OGMA Spatial Data Modernization**
Last updated: 2026-04-22

---

## The Mission
We are migrating all legacy Python 2 / ArcGIS 10.x scripts to **Python 3 / ArcGIS Pro 3**.
Every script in this repo was written for Python 2. Our job is to modernize them — carefully.

---

## The Golden Rules

### Before You Write a Single Line of Code
- [ ] Read the original script fully before changing anything
- [ ] Be sure to  **understand** the code first — ask "what does this block do?" before asking it to change anything (Use Ai if necessary)
- [ ] Write a comment above every block you intend to change (see Comment Format below)
- [ ] If you can't explain what the original does, stop and ask someone or ask ai

### When Making Changes
- [ ] Updates should be done in several stages/passess. Change only what is necessary in the first pass — do not tidy, rename, or reorganize other code. Keep in mind that renaming a variable can have several unintended downstream consequences
- [ ] One change at a time — never fix two things in the same edit (Mass changing all Da Search Cursors is considered 1 change)
- [ ] If you find another bug while fixing one, add a `#BUG` comment and move on
- [ ] Never delete logic — if you can't migrate (update/refactor) a block, mark it `#MIGRATION-BLOCKED`
- [ ] Common things that need to be updated are gp.addmessage() --> arcpy.AddMessage (AddWarning, AddError)
- [ ] gp.search cursors will be updated to arcpy.da cursors
- [ ] Print statements become print() functions # LEGACY
print "no arguments"
print selected_field, selected_field_part2

      print 'no arguments"
      becomes
      print("no arguments")
- [ ] Print statements become arcpy.AddMessage (to display in the toolbox)\
- [ ] Except statements used to only print, should be changed to "except Exception as E:"



### The Biggest Danger: Silent False-Pass
A silent false-pass is when a tool runs successfully and says "no errors found" — but is actually broken and missing real errors. This is **worse than a crash** because no one knows it's wrong.
- This is the smoke detector analogy, we need to blow smoke on the sensor, not just push the test button.

**Before accepting any AI suggestion, always ask:**
> "Could this change cause the tool to say PASS when it should say FAIL?"

If the answer is "maybe" — do not accept the change. Flag it for review.



## Required Comment Format

Paste this above **every block you change** before you change it:

```python
# ORIGINAL: [What this code does and why — in your own words] **MUST DO
# CHANGE:   [What you are changing and why] *MUST DO
# RISK:     [What could go wrong if this change is incorrect] 
# DOWNSTREAM: [What other parts of the script depend on this]
```

If you cannot fill in all four lines, you do not yet understand the code well enough to change it.

---

## Annotation Tags (Use These in Code)

| Tag | Meaning |
|-----|---------|
| `#BUG - CRITICAL` | Will cause wrong results or data corruption |
| `#BUG - HIGH` | Significant logic error, needs fixing soon |
| `#BUG - MEDIUM` | Minor logic issue, lower risk |
| `#BUG - LOW` | Style or label issue only |
| `#LEGACY - Python 2` | This block has not been migrated yet |
| `#MIGRATION-BLOCKED` | Cannot safely migrate — needs team review |
| `#BUG - CRITICAL - SILENT FALSE PASS RISK` | Could report clean when data has errors |

---

## Python 2 → 3 Quick Reference

| Old (Python 2) | New (Python 3) |
|---|---|
| `print "hello"` | `print("hello")` |
| `win32com.client` | `arcpy` |
| `gp.searchcursor(fc)` | `arcpy.da.SearchCursor(fc, fields)` |
| `gp.updatecursor(fc)` | `arcpy.da.UpdateCursor(fc, fields)` |
| `dict.has_key(k)` | `k in dict` |
| `dict.iteritems()` | `dict.items()` |
| `xrange(n)` | `range(n)` |
| `a <> b` | `a != b` |
| `exec "string"` | `exec("string")` |
| `arcpy.mapping` | `arcpy.mp` |
| `open(f, 'w')` | `open(f, 'w', encoding='utf-8')` |

---

## Before Submitting Any Migrated Script as 100% Complete

- [ ] Every changed block has the four-line comment above it
- [ ] No `#LEGACY - Python 2` tags remain (or all are intentionally blocked)
- [ ] Script has been run against a **known-bad test dataset** and produced the expected FAIL
- [ ] Script has been run against a **known-good test dataset** and produced all PASS
- [ ] A second team member has reviewed the comparison between old and new

**A tool that has never been seen to fail cannot be trusted to detect failures.**

---

## Scripts in This Repo

| Script | Status | Purpose |
|--------|--------|---------|
| `attribute_qa_v8.py` | In progress | 13-section attribute QA/QC — main QA tool |
| `check_for_geometry_issues.py` | Partially migrated | Geometry checks: slivers, vertices, duplicates |
| `find_duplicates.py` | Python 2 — needs full migration | Find duplicate values in a field |
| `find_duplicates_2_datasets.py` | Python 2 — needs full migration | Find duplicates across two datasets |
| `update_sequential_number.py` | Python 2 — needs full migration | Assign sequential IDs/PROVIDs |
| `update_sequential_number_ogma_legal_nonlegal_arcpy.py` | Python 2 — needs full migration | OGMA-specific sequential number update |
| `compare_number_of_records_in_staging_and_lrdw_20200501.py` | Python 2 — needs full migration | Record count comparison staging vs LRDW |

---

*Questions? Talk to the team lead before making changes you are unsure about.*
