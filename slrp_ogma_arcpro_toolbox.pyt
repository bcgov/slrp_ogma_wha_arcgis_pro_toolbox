# ArcGIS Pro 3 Toolbox Template

#===========================================================================
# Script name: Arcgis Pro 3 Toolbox Template
# Author: https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/a-template-for-python-toolboxes.htm

# Created on: 03_18_26
# 
#

# 
#
# 
#============================================================================

import arcpy
import os


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Descriptive Name of your Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [FindDuplicates, UpdateSeqNumbers, UpdateSeqNumOgmaLegalandNon, CheckGeom, AttributeQa, CompareNumRecords]  
       
        # Insert the name of each tool in your toolbox if you have more than one. 
        # i.e. self.tools = [FullSiteOverviewMaps, ExportSiteAndImageryLayout, Amendment]


class FindDuplicates(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Find Duplicates"
        self.description = ""

    def getParameterInfo(self):

        #This parameter is your first parameter, you can change the name, display name, and data type as needed. 
        #You can also add more parameters by copying and pasting this code and changing the parameter name, display name, and data type as needed.
        param_1 = arcpy.Parameter(
            displayName = "Parameter 1",
            name="param_1",
            datatype="String",
            parameterType="Required",
            direction="Input")
        
        
        # Second parameter - optional string input
        param_2 = arcpy.Parameter(
            displayName="Parameter 2",
            name="param_2",
            datatype="String",
            parameterType="Optional",
            direction="Input"
            )

        # Third parameter - example of a feature class input with a filter
        param_3 = arcpy.Parameter(
            displayName="Parameter 3",
            name="param_3",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param_3.filter.list = ["Polygon"]  # Example filter: only allow polygon feature classes 

        parameters = [param_1, param_2, param_3]  # Each parameter name needs to be in here, separated by a comma

        return parameters

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        return

    def postExecute(self, parameters):
        return


class UpdateSeqNumbers(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Sequential Numbers"
        self.description = ""

    def getParameterInfo(self):


        param_1 = arcpy.Parameter(
            displayName = "Parameter 1",
            name="param_1",
            datatype="String",
            parameterType="Required",
            direction="Input")
        
        
        # Second parameter - optional string input
        param_2 = arcpy.Parameter(
            displayName="Parameter 2",
            name="param_2",
            datatype="String",
            parameterType="Optional",
            direction="Input"
            )

        # Third parameter - example of a feature class input with a filter
        param_3 = arcpy.Parameter(
            displayName="Parameter 3",
            name="param_3",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param_3.filter.list = ["Polygon"]  # Example filter: only allow polygon feature classes 

        parameters = [param_1, param_2, param_3]  # Each parameter name needs to be in here, separated by a comma

        return parameters

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        return

    def postExecute(self, parameters):
        return


class UpdateSeqNumOgmaLegalandNon(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Update Sequential Number OGMA Legal and Non-Legal"
        self.description = (
            "Finds the highest sequential number across both the legal and "
            "non-legal OGMA feature classes for a given prefix, then updates "
            "empty/null records in the non-legal feature class with the next "
            "sequential values."
        )

    def getParameterInfo(self):
        # Parameter 0: the non-legal OGMA feature class to be updated (accepts a layer from the Contents pane or a browsed path to a feature class)
        fc_1 = arcpy.Parameter(
            displayName="Non-Legal Feature Class to Update",
            name="fc_1",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 1: the PROVID field in the non-legal FC; filtered to fields in fc_1
        field_1 = arcpy.Parameter(
            displayName="Non-Legal FC PROVID Field",
            name="field_1",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        field_1.parameterDependencies = [fc_1.name]  # Populates the field dropdown from fc_1

        # Parameter 2: the legal OGMA feature class (read-only reference for finding the highest existing number)
        fc_2 = arcpy.Parameter(
            displayName="Legal Feature Class",
            name="fc_2",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 3: the PROVID field in the legal FC; filtered to fields in fc_2
        field_2 = arcpy.Parameter(
            displayName="Legal PROVID Field",
            name="field_2",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        field_2.parameterDependencies = [fc_2.name]  # Populates the field dropdown from fc_2

        # Parameter 4: the prefix string to search for and assign (e.g. "CAR_RCA_")
        prefix = arcpy.Parameter(
            displayName="Prefix (e.g. CAR_RCA_) *include trailing underscore*",
            name="prefix",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # Parameter 5: safety check - must be explicitly checked if the prefix has never been used before
        is_new_prefix = arcpy.Parameter(
            displayName="This will be a new prefix",
            name="is_new_prefix",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        is_new_prefix.value = False  # Default: assume the prefix already exists

        # Parameter 6: dry-run mode - reports the next value without writing any changes
        just_display = arcpy.Parameter(
            displayName="Just display next value - do not update",
            name="just_display",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        just_display.value = False  # Default: actually perform the update

        return [fc_1, field_1, fc_2, field_2, prefix, is_new_prefix, just_display]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        # Validate the prefix format as the user types, before execution
        prefix_param = parameters[4]
        if prefix_param.valueAsText:
            val = prefix_param.valueAsText
            if not val.endswith("_"):
                # Warn but don't block - the tool can still run
                prefix_param.setWarningMessage(
                    "Prefix should end with an underscore (e.g. CAR_RCA_)."
                )
            elif "'" in val:
                # Block execution - a single quote would break the SQL WHERE clause
                prefix_param.setErrorMessage(
                    "Prefix must not contain single-quote characters."
                )
            else:
                prefix_param.clearMessage()
        return

    def execute(self, parameters, messages):
        import uuid

        arcpy.env.overwriteOutput = True

        # Unpack all parameter values from the tool dialog
        fc_1 = parameters[0].valueAsText
        field_1 = parameters[1].valueAsText
        fc_2 = parameters[2].valueAsText
        field_2 = parameters[3].valueAsText
        prefix = parameters[4].valueAsText
        is_new_prefix = parameters[5].value  # bool
        just_display = parameters[6].value   # bool

        # Escape any single quotes in the prefix to prevent SQL injection in WHERE clauses
        safe_prefix = prefix.replace("'", "''")

        # A random 8-character UUID suffix is appended to each temporary layer name to prevent
        # collisions if the tool is run multiple times in the same ArcGIS Pro session.
        # The temp_layers list tracks all temporary layers created during execution so they
        # can be deleted during cleanup.
        uid = uuid.uuid4().hex[:8]
        lyr_1 = f"fc1_prefix_{uid}"   # Filtered view of fc_1: records matching the prefix
        lyr_2 = f"fc2_prefix_{uid}"   # Filtered view of fc_2: records matching the prefix
        lyr_null = f"fc1_null_{uid}"  # Filtered view of fc_1: records with null/empty PROVID
        temp_layers = []

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
            # Build SQL WHERE clauses using AddFieldDelimiters so the syntax is correct
            # regardless of data source type (File GDB, SDE, Shapefile, etc.)
            where_1 = f"{arcpy.AddFieldDelimiters(fc_1, field_1)} LIKE '{safe_prefix}%'"  # % wildcard matches any characters after the prefix
            
            # Create a temporary layer of only the records that have a PROVID starting with the prefix entered by the user in the non-legal FC, and count how many records match. 
            arcpy.management.MakeFeatureLayer(fc_1, lyr_1, where_1)  
            temp_layers.append(lyr_1)  # Register for cleanup at end of execution
            count_1 = int(arcpy.management.GetCount(lyr_1)[0])  # Count matching records in the non-legal FC

            where_2 = f"{arcpy.AddFieldDelimiters(fc_2, field_2)} LIKE '{safe_prefix}%'"  # Same filter applied to the legal FC
            
            # Create a temporary layer of only the records that have a PROVID starting with the prefix entered by the user in the legal FC, and count how many records match. 
            arcpy.management.MakeFeatureLayer(fc_2, lyr_2, where_2)  
            temp_layers.append(lyr_2)  # Register for cleanup at end of execution
            count_2 = int(arcpy.management.GetCount(lyr_2)[0])  # Count matching records in the legal FC

            total_prefix_count = count_1 + count_2  # Total records with this prefix across both FCs

            # --- Step 2: Validate whether is_new_prefix True/False matches reality ---
            # If no records exist for this prefix but the user hasn't checked "new prefix", stop and warn.
            # If records do exist but the user has checked "new prefix", stop and warn.
            # This prevents accidental numbering restarts or orphaned sequences.
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
            # For a new prefix, start at 1.
            # For an existing prefix, scan both FCs to find the highest current number,
            # then increment by 1 to get the next available value.
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

                # Create an empty list to hold all integer suffixes found across both FCs
                suffix_values = []  

                # Scan non-legal FC: strip the known prefix from each PROVID value to isolate
                # the numeric suffix, then collect it for max() comparison later
                with arcpy.da.SearchCursor(lyr_1, [field_1]) as cursor:
                    for (val,) in cursor:
                        if val and val.startswith(prefix):  # Guard against nulls and non-matching values
                            suffix_str = val[len(prefix):]  # Slice off the prefix, leaving just the number (e.g. "CAR_RCA_5" -> "5")
                            try:
                                suffix_values.append(int(suffix_str))  # Convert to int and store
                            except ValueError:
                                # Suffix is not a plain integer (e.g. "5A") - skip it with a warning
                                arcpy.AddWarning(
                                    f"            {val} does not have an integer suffix...skipping."
                                )

                # Scan legal FC: same logic as above, applied to the legal feature class
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

                # If no valid integer suffixes were found in either FC, something is wrong - stop
                if not suffix_values:
                    arcpy.AddError("No valid numbered suffixes found in either feature class. Check that you added an underscore to the end of your Prefix")
                    return

                highest_suffix = max(suffix_values)   # The highest existing number across both FCs
                next_value = highest_suffix + 1        # Next available number

                arcpy.AddWarning(
                    f"The highest value in either dataset is {prefix}{highest_suffix}. "
                    f"Numbering for new features will start at {prefix}{next_value}."
                )

            # --- Step 4: Update null/empty PROVID records in the non-legal FC ---
            # Skip this step entirely if the user checked the just display next value box and only wants to display the next value
            # Otherwise, proceed with the update and write each new value as it's assigned in the cursor loop
            if not just_display:
                arcpy.AddMessage(
                    f"Updating {field_1}, starting with {prefix}{next_value}:"
                )

                # Determine the geodatabase workspace path for the Editor session.
                # If the FC lives inside a Feature Dataset, walk up one level to get the GDB path.
                desc = arcpy.Describe(fc_1)
                container = desc.path
                container_desc = arcpy.Describe(container)
                if container_desc.dataType == "FeatureDataset":
                    workspace = container_desc.path  # GDB is one level above the Feature Dataset
                else:
                    workspace = container  # FC is directly in the GDB
                arcpy.AddMessage(f"Workspace: {workspace}")

                # Build a filter for records where the PROVID field is null, '0' empty string
                where_null = (
                    f"{arcpy.AddFieldDelimiters(fc_1, field_1)} = '' OR "
                    f"{arcpy.AddFieldDelimiters(fc_1, field_1)} IS NULL OR "
                    f"{arcpy.AddFieldDelimiters(fc_1, field_1)} = '0'"
                )
                # Creates a temporary layer containing only records where the PROVID field is null or an empty string,
                # ensuring the UpdateCursor only touches unassigned records and does not overwrite existing valid PROVID values.
                arcpy.management.MakeFeatureLayer(fc_1, lyr_null, where_null)
                
                # Append this null-filtered layer to the temp_layers list for cleanup later, even if the count is 0 (layer will be empty but still needs to be deleted at the end of execution)
                temp_layers.append(lyr_null)

                update_count = 0

                # Open an edit session on the GDB. The two True arguments enable undo/redo
                # support and allow editing of versioned data (safe for unversioned too).
                edit = arcpy.da.Editor(workspace)
                edit.startEditing(True, True)
                try:
                    edit.startOperation()  # Begin the editable transaction

                    # Iterate through each null/empty record and assign the next sequential value
                    with arcpy.da.UpdateCursor(lyr_null, [field_1]) as cursor:
                        for row in cursor:
                            arcpy.AddMessage(f"    {prefix}{next_value}")
                            row[0] = f"{prefix}{next_value}"  # Assign the new PROVID value
                            cursor.updateRow(row)              # Write the change to the row
                            next_value += 1                    # Increment so each record gets a unique number
                            update_count += 1

                    edit.stopOperation()
                    edit.stopEditing(True)  # Save all edits to disk
                except Exception:
                    edit.stopEditing(False)  # Rollback all edits if anything goes wrong
                    raise

                arcpy.AddMessage(f"\nDone. Updated {update_count} feature(s).")
            else:
                arcpy.AddWarning("Display only box checked - data was not updated.")

        finally:
            # --- Cleanup: delete all temporary in-memory feature layers ---
            # This runs whether the tool succeeded or failed, preventing layer name
            # buildup in the ArcGIS Pro session.
            for lyr in temp_layers:
                try:
                    arcpy.management.Delete(lyr)
                except Exception:
                    pass  # Ignore errors if a layer was never successfully created

    def postExecute(self, parameters):
        return


class GeometryCheckTool(object):
    def __init__(self):
        self.label = "Check for Geometry Issues"
        self.description = "Runs geometry checks before BCGW submission"

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Feature Class to Check",
            name="in_fc",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
        return [param0]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[0].value:
            desc = arcpy.Describe(parameters[0].value)
            if desc.shapeType == "Point":
                parameters[0].setWarningMessage(
                    "Point datasets do not require this tool."
                )

    def updateMessages(self, parameters):
        if not parameters[0].value:
            parameters[0].setErrorMessage("Input Feature Class is required.")
            return

        desc = arcpy.Describe(parameters[0].value)

        if desc.shapeType == "Point":
            parameters[0].setErrorMessage(
                "This tool does not support point feature classes."
            )

    def execute(self, parameters, messages):
        import arcpy
        import os
        from collections import Counter

        # ---------------- FUNCTIONS ----------------

        def repair_geometry(in_fc, fds_path, fc_name):
            arcpy.AddMessage("Repairing geometry where MODIFICATION_TYPE is not null...")

            lyr = arcpy.CreateUniqueName("fc_lyr")
            where_clause = "MODIFICATION_TYPE IS NOT NULL"

            arcpy.management.MakeFeatureLayer(in_fc, lyr, where_clause)
            arcpy.management.RepairGeometry(lyr)

            arcpy.AddMessage("✔ Geometry repair complete")
            arcpy.management.Delete(lyr)


        def identify_very_small_polygons_or_line_segments(in_fc, fds_path, fc_name):
            desc = arcpy.Describe(in_fc)

            fc_lyr = arcpy.CreateUniqueName("fc_lyr")
            where_clause = "MODIFICATION_TYPE IS NOT NULL"

            arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, where_clause)

            if desc.shapeType == "Polygon":
                arcpy.AddMessage("Checking for polygons <= 0.5 ha...")

                temp_fc = os.path.join(fds_path, f"temp_sliver_polygons_{fc_name}")
                temp_lyr = arcpy.CreateUniqueName("temp_lyr")

                arcpy.management.MultipartToSinglepart(fc_lyr, temp_fc)
                arcpy.management.MakeFeatureLayer(temp_fc, temp_lyr)

                geom_field = desc.shapeFieldName
                area_field = f"{geom_field}_Area"

                arcpy.management.SelectLayerByAttribute(temp_lyr, "NEW_SELECTION", f"{area_field} <= 5000")
                arcpy.management.SelectLayerByAttribute(temp_lyr, "SWITCH_SELECTION")
                arcpy.management.DeleteFeatures(temp_lyr)
                arcpy.management.SelectLayerByAttribute(temp_lyr, "CLEAR_SELECTION")

                count = int(arcpy.management.GetCount(temp_lyr)[0])

                if count > 0:
                    arcpy.AddWarning(f"{count} small polygon features found.")
                    arcpy.AddWarning(f"Review: temp_sliver_polygons_{fc_name}")
                else:
                    arcpy.AddMessage("No sliver polygons found.")

                arcpy.management.Delete(temp_lyr)

            else:
                arcpy.AddMessage("Checking for short line segments (< 1m)...")

                temp_fc = os.path.join(fds_path, f"temp_short_line_segments_{fc_name}")
                temp_lyr = arcpy.CreateUniqueName("temp_lyr")

                arcpy.management.MultipartToSinglepart(fc_lyr, temp_fc)
                arcpy.management.MakeFeatureLayer(temp_fc, temp_lyr)

                geom_field = desc.shapeFieldName
                length_field = f"{geom_field}_Length"

                arcpy.management.SelectLayerByAttribute(temp_lyr, "NEW_SELECTION", f"{length_field} <= 1")
                arcpy.management.SelectLayerByAttribute(temp_lyr, "SWITCH_SELECTION")
                arcpy.management.DeleteFeatures(temp_lyr)
                arcpy.management.SelectLayerByAttribute(temp_lyr, "CLEAR_SELECTION")

                count = int(arcpy.management.GetCount(temp_lyr)[0])

                if count > 0:
                    arcpy.AddWarning(f"{count} short line segments found.")
                    arcpy.AddWarning(f"Review: temp_short_line_segments_{fc_name}")
                else:
                    arcpy.AddMessage("No short segments found.")

                arcpy.management.Delete(temp_lyr)

            arcpy.management.Delete(fc_lyr)


        def check_for_max_vertices(in_fc, fds_path, fc_name):
            arcpy.AddMessage("Checking vertex count (< 524,000)...")

            fc_lyr = arcpy.CreateUniqueName("fc_lyr")
            arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, "MODIFICATION_TYPE IS NOT NULL")

            arcpy.management.AddField(fc_lyr, "VxCount", "LONG")
            arcpy.management.CalculateField(fc_lyr, "VxCount", "!shape!.pointCount", "PYTHON3")

            arcpy.management.SelectLayerByAttribute(fc_lyr, "NEW_SELECTION", "VxCount > 524000")

            count = int(arcpy.management.GetCount(fc_lyr)[0])

            if count > 0:
                arcpy.conversion.FeatureClassToFeatureClass(
                    fc_lyr, fds_path, f"temp_{fc_name}_OVER_MAX_VERTICES"
                )

                arcpy.AddWarning(f"{count} features exceed vertex limit.")
                arcpy.AddWarning(f"Review: temp_{fc_name}_OVER_MAX_VERTICES")
            else:
                arcpy.AddMessage("All features within vertex limit ✔")

            arcpy.management.DeleteField(fc_lyr, "VxCount")
            arcpy.management.Delete(fc_lyr)


        def check_for_multiple_identical_vertices(in_fc, fds_path, fc_name):
            arcpy.AddMessage("Checking for duplicate vertices (>=4)...")

            fc_lyr = arcpy.CreateUniqueName("fc_lyr")
            arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, "MODIFICATION_TYPE IS NOT NULL")

            temp_fc1 = os.path.join(fds_path, f"temp_identical_vertex_check_Step1_{fc_name}")
            temp_fc2 = os.path.join(fds_path, f"temp_identical_vertex_check_Step2_{fc_name}")

            if arcpy.Exists(temp_fc1):
                arcpy.management.Delete(temp_fc1)

            arcpy.management.CopyFeatures(fc_lyr, temp_fc1)
            arcpy.management.FeatureVerticesToPoints(temp_fc1, temp_fc2, "ALL")

            arcpy.management.AddXY(temp_fc2)
            arcpy.management.AddField(temp_fc2, "CHECK", "TEXT", field_length=100)
            arcpy.management.AddField(temp_fc2, "FLAG", "TEXT")

            temp_lyr = arcpy.CreateUniqueName("temp_lyr")
            arcpy.management.MakeFeatureLayer(temp_fc2, temp_lyr)

            feat_id_field = "OBJECTID"  # safe fallback

            calc_expr = f"str(!{feat_id_field}!) + '_' + str(!POINT_X!) + '_' + str(!POINT_Y!)"
            arcpy.management.CalculateField(temp_lyr, "CHECK", calc_expr, "PYTHON3")

            with arcpy.da.SearchCursor(temp_lyr, ["CHECK"]) as cursor:
                values = [row[0] for row in cursor]

            counts = Counter(values)
            flagged = [k for k, v in counts.items() if v > 3]

            for val in flagged:
                arcpy.management.SelectLayerByAttribute(temp_lyr, "NEW_SELECTION", f"CHECK = '{val}'")
                cnt = int(arcpy.management.GetCount(temp_lyr)[0])
                arcpy.management.CalculateField(temp_lyr, "FLAG", f'"{cnt}"', "PYTHON3")

            arcpy.management.SelectLayerByAttribute(temp_lyr, "NEW_SELECTION", "FLAG IS NULL")
            arcpy.management.DeleteFeatures(temp_lyr)

            if int(arcpy.management.GetCount(temp_lyr)[0]) > 0:
                arcpy.AddWarning("Duplicate vertices found (>=4).")
                arcpy.AddWarning(f"Review: temp_identical_vertex_check_Step2_{fc_name}")
            else:
                arcpy.AddMessage("No duplicate vertices found.")

            arcpy.management.Delete(fc_lyr)
            arcpy.management.Delete(temp_lyr)

            def postExecute(self, parameters):
                return


class AttributeQa(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Attribute QA"
        self.description = ""

    def getParameterInfo(self):

        #This parameter is your first parameter, you can change the name, display name, and data type as needed. 
        #You can also add more parameters by copying and pasting this code and changing the parameter name, display name, and data type as needed.
        param_1 = arcpy.Parameter(
            displayName = "Parameter 1",
            name="param_1",
            datatype="String",
            parameterType="Required",
            direction="Input")
        
        
        # Second parameter - optional string input
        param_2 = arcpy.Parameter(
            displayName="Parameter 2",
            name="param_2",
            datatype="String",
            parameterType="Optional",
            direction="Input"
            )

        # Third parameter - example of a feature class input with a filter
        param_3 = arcpy.Parameter(
            displayName="Parameter 3",
            name="param_3",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param_3.filter.list = ["Polygon"]  # Example filter: only allow polygon feature classes 

        parameters = [param_1, param_2, param_3]  # Each parameter name needs to be in here, separated by a comma

        return parameters
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        return

    def postExecute(self, parameters):
        return


class CompareNumRecords(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Compare Number of Records"
        self.description = ""

    def getParameterInfo(self):

        #This parameter is your first parameter, you can change the name, display name, and data type as needed. 
        #You can also add more parameters by copying and pasting this code and changing the parameter name, display name, and data type as needed.
        param_1 = arcpy.Parameter(
            displayName = "Parameter 1",
            name="param_1",
            datatype="String",
            parameterType="Required",
            direction="Input")
        
        
        # Second parameter - optional string input
        param_2 = arcpy.Parameter(
            displayName="Parameter 2",
            name="param_2",
            datatype="String",
            parameterType="Optional",
            direction="Input"
            )

        # Third parameter - example of a feature class input with a filter
        param_3 = arcpy.Parameter(
            displayName="Parameter 3",
            name="param_3",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param_3.filter.list = ["Polygon"]  # Example filter: only allow polygon feature classes 

        parameters = [param_1, param_2, param_3]  # Each parameter name needs to be in here, separated by a comma

        return parameters
    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        return

    def postExecute(self, parameters):
        return

