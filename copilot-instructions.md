# SLRP GIS Project — AI Assistant Standing Instructions
# BC Ministry of Forests, Lands and Natural Resource Operations

---

## How to Use This File

### VS Code GitHub Copilot
Place this file at: `.github/copilot-instructions.md` in your repository root.
Copilot Chat loads it automatically on every session. No extra steps needed.

### Claude.ai (Projects)
1. Open Claude.ai → click **Projects** in the left sidebar
2. Create or open your SLRP project
3. Click **Project Settings** (gear icon)
4. Under **Project Instructions**, paste the entire contents of the `## Standing Instructions` section below
5. Save. Claude will apply these instructions to every conversation in the project.

### ChatGPT (Custom GPT or System Prompt)
**Option A — Custom GPT (recommended for teams):**
1. Go to chat.openai.com → click your profile → **My GPTs** → **Create a GPT**
2. In the **Instructions** field, paste the `## Standing Instructions` section
3. Name it "SLRP GIS Assistant" and share the link with your team

**Option B — Per-session system prompt:**
1. Start a new chat
2. Paste the `## Standing Instructions` section as your first message, prefixed with:
   "For this entire conversation, treat the following as your system instructions:"
3. Confirm Claude/ChatGPT acknowledges them before proceeding

---

## Standing Instructions

### Domain Context
- This project manages spatial data for the BC Geographic Warehouse (BCGW)
- Primary datasets: Legal OGMAs, Non-Legal OGMAs, Wildlife Habitat Areas, Landscape Units, SLRP Planning Boundaries and Features
- **Modernization mission: all legacy scripts are Python 2 / ArcGIS 10.x and are being migrated to Python 3 / ArcGIS Pro 3**
- All new code, fixes, and automation MUST target Python 3 and ArcGIS Pro 3
- Do NOT suggest Python 2 syntax, arcgisscripting, win32com, or ArcGIS 10.x-only patterns

### Critical Data Philosophy
- **NEVER delete records** — features are retired via MODIFICATION_TYPE = 'RETIREMENT' or 'PERMANENT RETIREMENT'
- PROVID is the immutable provincial identifier; it must never be reassigned, reused, or substituted
- PROVID_PART_NUMBER tracks polygon splits; always recalculate when splitting
- Five lifecycle phases: REQUEST → CHECKOUT → EDITING → QA/QC → CHECK-IN & REPLICATION
- Only one update can be in progress province-wide at a time (checkout lock)

### Code Standards
- Target: **Python 3 / ArcGIS Pro 3 / arcpy (Pro)**
- Use f-strings, pathlib, and Python 3 idioms
- Use `arcpy.AddMessage()` for all toolbox output — never bare `print()` in toolbox tools
- Bug annotations: `#BUG - {CRITICAL|HIGH|MEDIUM|LOW}` for TODO Tree
- Migration annotations: `#LEGACY - Python 2` on any block not yet migrated
- Blocked migration: `#MIGRATION-BLOCKED` on any block that cannot be safely migrated yet

### Python 2 to 3 Migration Watchpoints
- Replace `print` statements → `print()` functions
- Replace `win32com.client` / `arcgisscripting` → `arcpy`
- Replace `gp.searchcursor` / `gp.updatecursor` → `arcpy.da.SearchCursor` / `arcpy.da.UpdateCursor`
- Replace `.iteritems()` / `.has_key()` / `xrange` with Python 3 equivalents
- Replace `exec` statements → `exec()` function
- Replace `<>` operator → `!=`
- Replace `arcpy.mapping` → `arcpy.mp`
- Replace `arcpy.MakeFeatureLayer_management` → `arcpy.management.MakeFeatureLayer`
- All file writes: use `open(file, 'w', encoding='utf-8')`
- Integer division: audit all `/` operators — use `//` where integer result was intended

### ArcGIS Pro Environment Safety
- Always check `arcpy.Exists()` and delete before creating any temp feature class
- After every `MakeFeatureLayer`, verify the layer has records before running selection logic
- Use `arcpy.CreateUniqueName()` for EVERY in-memory layer name without exception
- `CalculateField` shape expressions: use `!shape.pointCount!` syntax (not `!shape!.pointCount`)
- Writing temp FCs to a Feature Dataset path: verify spatial reference matches before writing

### Change Discipline — Read Before Every Edit

#### Surgical Changes Only
- Change the **minimum code** necessary to achieve the goal
- Do not refactor, rename, or reorganize anything not directly related to the task
- Do not add imports, functions, or classes not required by the immediate change
- One concern per change — if a second issue is spotted, flag it separately

#### Comment Before Code (Mandatory)
Before changing any line, write this block above it:
```python
# ORIGINAL: [What this code does and why it exists]
# CHANGE: [What is being changed and why]
# RISK: [What could go wrong if this change is incorrect]
# DOWNSTREAM: [What other sections, outputs, or tools does this touch]
```
If you cannot complete all four fields, you do not yet understand the code well enough to change it.

#### Fidelity to Original Logic
- Preserve every conditional block, field resolution, and validation from the original
- If a block appears complex or replaceable, preserve it and flag it — do not substitute without instruction
- A "safe fallback" is NEVER acceptable — it is a red flag, not a solution
- OBJECTID is never a valid substitute for a domain identifier field on derived feature classes

#### Pre-Change Analysis (Always Required)
Before writing any code change, explicitly state:
1. What downstream sections, functions, or outputs does this change touch?
2. Could this change produce a PASS/clean result when the data actually has errors? (Silent false-pass risk)
3. Does this change affect any field used as a grouping key, composite key, or join field?

#### Migration — Never Drop Logic
- Every block present in the original must appear in the migrated version
- If a block cannot be migrated, annotate it `#MIGRATION-BLOCKED` with explanation
- Never silently omit complex logic — flag it for team review

### Silent False-Pass Detection (Highest Priority)
This is the most dangerous failure mode in this codebase:
- A silent false-pass = tool completes without error but reports clean when issues exist
- Before any change to detection/QA logic, ask: "Could this cause the tool to miss a real error?"
- Flag any such risk with: `#BUG - CRITICAL - SILENT FALSE PASS RISK`

### Error and Anomaly Scanning
When reading any code block, actively check for:
- Off-by-one errors in sequential number logic
- Silent exception swallowing (`except: pass` or bare `except`)
- Temp feature classes not cleaned up between runs
- Fields used as composite keys being substituted with auto-generated IDs
- `GetCount` being called after a failed layer creation (returns 0, looks like clean pass)

Do not fix incidentally discovered bugs — report them with `#BUG` annotation and wait for instruction.

### Prohibited Actions
- Do NOT write Python 2-only syntax in any new or modified code
- Do NOT suggest `arcpy.mapping` — use `arcpy.mp`
- Do NOT suggest `win32com`, `arcgisscripting`, or `gp.searchcursor`
- Do NOT substitute OBJECTID for a named domain identifier field
- Do NOT suggest DELETE, TRUNCATE, or DROP for spatial records
- Do NOT silently omit logic blocks during migration
- Do NOT fix a second bug while fixing the first — flag it separately
