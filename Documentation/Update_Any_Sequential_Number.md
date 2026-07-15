# Update Sequential Numbers — How It Works and How to Use It

## How It Works

The script handles two field types differently but follows the same four-step pattern in both cases.

**Text fields** (e.g. `(NON)LEGAL_OGMA_PROVID`): scans every record and splits each value into a text prefix and a trailing numeric suffix (e.g. `CAR_RCA_135` → prefix `CAR_RCA_`, suffix `135`). It builds a dictionary of every prefix found and the highest suffix seen for each. It then validates that the prefix you entered either already exists or is genuinely new (depending on which checkbox you set), determines the next number, and fills every blank (`""`) record with the next value in sequence, incrementing by one per record.

**Numeric fields** (e.g. `(NON)LEGAL_OGMA_INTERNAL_ID`): scans every record to find the highest existing integer, then fills every zero or null record starting from highest + 1.

In both cases, a display-only mode lets you see what the next value would be without writing any changes.

---

## How to Use It

1. Open the tool from the toolbox — do **not** run it on a selection, run it on the whole feature class.
2. Select your feature class and the field you want to update from the dropdowns.
3. If the field is a **text field**, enter the prefix (e.g. `CAR_RCA_`) including the trailing underscore.
   - If this prefix has never been used before, check **"This will be a new prefix"**. If it already exists, leave it unchecked. The tool will error if these don't match.
   - If the field is **numeric**, leave the prefix blank — it is ignored.
4. Optionally check **"Just display next value — do not update"** to do a dry run and confirm the next number before committing any changes.
5. Run the tool. The messages panel will show every prefix and its current highest value, then list each record that was updated.
