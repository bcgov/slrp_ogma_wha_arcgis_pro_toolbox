import os
import uuid
import arcpy


def run(fc_1, field_1, fc_2, field_2, prefix, is_new_prefix, just_display):
    """Update sequential PROVID numbers across Legal and Non-Legal OGMA feature classes.

    Parameters
    ----------
    fc_1 : str
        Path/layer name of the non-legal OGMA feature class to be updated.
    field_1 : str
        Name of the PROVID field in fc_1.
    fc_2 : str
        Path/layer name of the legal OGMA feature class (read-only reference).
    field_2 : str
        Name of the PROVID field in fc_2.
    prefix : str
        Prefix string to search for and assign (e.g. "CAR_RCA_").
    is_new_prefix : bool
        True if this prefix has never been used before.
    just_display : bool
        True to report the next value without writing any changes.
    """

    arcpy.env.overwriteOutput = True

    # Escape any single quotes in the prefix to prevent SQL injection in WHERE clauses
    safe_prefix = prefix.replace("'", "''")

    # A random 8-character UUID suffix is appended to each temporary layer name to prevent
    # collisions if the tool is run multiple times in the same ArcGIS Pro session.
    uid = uuid.uuid4().hex[:8]
    lyr_1 = f"fc1_prefix_{uid}"   # Filtered view of fc_1: records matching the prefix
    lyr_2 = f"fc2_prefix_{uid}"   # Filtered view of fc_2: records matching the prefix
    lyr_null = f"fc1_null_{uid}"  # Filtered view of fc_1: records with null/empty PROVID
    temp_layers = []

    arcpy.SetProgressor("step", "Checking prefix existence...", 0, 4, 1)

    try:
        # Display all input parameters to the tool messages for traceability
        arcpy.AddMessage(f"Non-Legal FC: {fc_1}")
        arcpy.AddMessage(f"Non-Legal Field: {field_1}")
        arcpy.AddMessage(f"Legal FC: {fc_2}")
        arcpy.AddMessage(f"Legal Field: {field_2}")
        arcpy.AddMessage(f"Prefix: {prefix}")
        arcpy.AddMessage(f"Is a new prefix? {is_new_prefix}")
        arcpy.AddMessage(f"Just display value, don't update? {just_display}\n")

        # --- Step 1: Check whether the prefix already exists in either FC ---
        arcpy.SetProgressorLabel("Step 1 of 4: Checking prefix in both feature classes...")
        arcpy.SetProgressorPosition()
        # Build SQL WHERE clauses using AddFieldDelimiters so the syntax is correct
        # regardless of data source type (File GDB, SDE, Shapefile, etc.)
        where_1 = f"{arcpy.AddFieldDelimiters(fc_1, field_1)} LIKE '{safe_prefix}%'"

        # Create a temporary layer of only the records that have a PROVID starting with
        # the prefix entered by the user in the non-legal FC, and count matching records.
        arcpy.management.MakeFeatureLayer(fc_1, lyr_1, where_1)
        temp_layers.append(lyr_1)
        count_1 = int(arcpy.management.GetCount(lyr_1)[0])

        where_2 = f"{arcpy.AddFieldDelimiters(fc_2, field_2)} LIKE '{safe_prefix}%'"

        # Create a temporary layer of only the records that have a PROVID starting with
        # the prefix entered by the user in the legal FC, and count matching records.
        arcpy.management.MakeFeatureLayer(fc_2, lyr_2, where_2)
        temp_layers.append(lyr_2)
        count_2 = int(arcpy.management.GetCount(lyr_2)[0])

        total_prefix_count = count_1 + count_2

        # --- Step 2: Validate whether is_new_prefix True/False matches reality ---
        arcpy.SetProgressorLabel("Step 2 of 4: Validating prefix...")
        arcpy.SetProgressorPosition()
        if total_prefix_count == 0:
            arcpy.AddWarning(f"{prefix} is a new prefix.")
            if not is_new_prefix:
                arcpy.AddError(
                    'Please rerun the tool with the "This will be a new prefix" box checked.'
                )
                return
        else:
            arcpy.AddWarning(f"{prefix} already exists in one of the feature classes.\n")
            if is_new_prefix:
                arcpy.AddError(
                    "If you are sure you want to proceed using this prefix, "
                    'rerun the tool with the "This will be a new prefix" box unchecked.'
                )
                return

        # --- Step 3: Determine the next sequential value ---
        arcpy.SetProgressorLabel("Step 3 of 4: Finding highest sequential value...")
        arcpy.SetProgressorPosition()
        if is_new_prefix:
            arcpy.AddWarning(
                f"{prefix} is a new prefix. Numbering will start at {prefix}1."
            )
            next_value = 1

        else:
            arcpy.AddWarning(
                f"Found {count_1} features with prefix {prefix} "
                f"in {os.path.basename(fc_1)}"
            )
            arcpy.AddWarning(
                f"Found  {count_2} features with prefix {prefix} "
                f"in {os.path.basename(fc_2)}\n"
            )

            suffix_values = []

            # Scan non-legal FC
            with arcpy.da.SearchCursor(lyr_1, [field_1]) as cursor:
                for (val,) in cursor:
                    if val and val.startswith(prefix):
                        suffix_str = val[len(prefix):]
                        try:
                            suffix_values.append(int(suffix_str))
                        except ValueError:
                            arcpy.AddWarning(
                                f"            {val} does not have an integer suffix...skipping."
                            )

            # Scan legal FC
            with arcpy.da.SearchCursor(lyr_2, [field_2]) as cursor:
                for (val,) in cursor:
                    if val and val.startswith(prefix):
                        suffix_str = val[len(prefix):]
                        try:
                            suffix_values.append(int(suffix_str))
                        except ValueError:
                            arcpy.AddWarning(
                                f"            {val} does not have an integer suffix...skipping."
                            )

            if not suffix_values:
                arcpy.AddError(
                    "No valid numbered suffixes found in either feature class. "
                    "Check that you added an underscore to the end of your Prefix"
                )
                return

            highest_suffix = max(suffix_values)
            next_value = highest_suffix + 1

            arcpy.AddWarning(
                f"The highest value in either dataset is {prefix}{highest_suffix}. "
                f"Numbering for new features will start at {prefix}{next_value}."
            )

        # --- Step 4: Update null/empty PROVID records in the non-legal FC ---
        if just_display:
            arcpy.SetProgressorLabel("Step 4 of 4: Calculating next value (display only)...")
        else:
            arcpy.SetProgressorLabel("Step 4 of 4: Updating records...")
        arcpy.SetProgressorPosition()
        if not just_display:
            arcpy.AddMessage(
                f"Updating {field_1}, starting with {prefix}{next_value}:"
            )

            # Determine the geodatabase workspace path for the Editor session.
            desc = arcpy.Describe(fc_1)
            container = desc.path
            container_desc = arcpy.Describe(container)
            if container_desc.dataType == "FeatureDataset":
                workspace = container_desc.path
            else:
                workspace = container
            arcpy.AddMessage(f"Workspace: {workspace}")

            where_null = (
                f"{arcpy.AddFieldDelimiters(fc_1, field_1)} = '' OR "
                f"{arcpy.AddFieldDelimiters(fc_1, field_1)} IS NULL OR "
                f"{arcpy.AddFieldDelimiters(fc_1, field_1)} = '0'"
            )
            arcpy.management.MakeFeatureLayer(fc_1, lyr_null, where_null)
            temp_layers.append(lyr_null)

            update_count = 0

            edit = arcpy.da.Editor(workspace)
            edit.startEditing(True, True)
            try:
                edit.startOperation()

                with arcpy.da.UpdateCursor(lyr_null, [field_1]) as cursor:
                    for row in cursor:
                        arcpy.AddMessage(f"    {prefix}{next_value}")
                        row[0] = f"{prefix}{next_value}"
                        cursor.updateRow(row)
                        next_value += 1
                        update_count += 1

                edit.stopOperation()
                edit.stopEditing(True)
            except Exception:
                edit.stopEditing(False)
                raise

            arcpy.AddMessage(f"\nDone. Updated {update_count} feature(s).")
        else:
            arcpy.AddWarning("Display only box checked - data was not updated.")

    finally:
        # --- Cleanup: delete all temporary in-memory feature layers ---
        for lyr in temp_layers:
            try:
                arcpy.management.Delete(lyr)
            except Exception:
                pass
