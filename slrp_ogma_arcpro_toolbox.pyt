# ArcGIS Pro 3 Toolbox Template

#===========================================================================
# Script name: Arcgis Pro 3 Toolbox Template
# Author: https://pro.arcgis.com/en/pro-app/latest/arcpy/geoprocessing_and_python/a-template-for-python-toolboxes.htm

# Created on: 03_18_26
# ##
#

# 
#
# 
#============================================================================

import arcpy
import os
import sys
import importlib


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Descriptive Name of your Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [FindDuplicates, UpdateSeqNumbers, UpdateSeqNumOgmaLegalandNon, GeometryCheckTool, AttributeQa, CompareNumRecords, CompareFGDBProperties]  
       
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
        from collections import Counter

        arcpy.env.overwriteOutput = True

        in_fc = parameters[0].valueAsText


        ##in_fc = r"\\spatialfiles3.bcgov\slrp\UpdateManagement\OldGrowthManagementAreas\CurrentUpdate\old_growth_management_area_bc_Update_20210426_RETURNED_20210518.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"

        arcpy.AddMessage(f"ArcGIS license level: {arcpy.ProductInfo()}") # This can be removed totally. 

        workspace_path, fc_name = os.path.split(in_fc)
        arcpy.AddMessage("----- Checking {} -----".format(fc_name))

        desc = arcpy.Describe(in_fc)
        fc_name = desc.baseName
        fds_path = os.path.dirname(desc.catalogPath)

        # Validate that the required MODIFICATION_TYPE field exists
        field_names = [f.name for f in arcpy.ListFields(in_fc)]
        if "MODIFICATION_TYPE" not in field_names:
            arcpy.AddError(
                "The input feature class does not have a MODIFICATION_TYPE field. "
                "This tool only works with feature classes that have a MODIFICATION_TYPE field **Update this message after further investigation into the appropriate input types."
            )
            return

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

        # ---------------- CALL FUNCTIONS ----------------
        repair_geometry(in_fc, fds_path, fc_name)
        identify_very_small_polygons_or_line_segments(in_fc, fds_path, fc_name)
        check_for_max_vertices(in_fc, fds_path, fc_name)
        check_for_multiple_identical_vertices(in_fc, fds_path, fc_name)

    def postExecute(self, parameters):
        return


class AttributeQa(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Attribute QA"
        self.description = (
            "Runs a comprehensive attribute quality assurance check on a "
            "post-update feature class, comparing it against a pre-update "
            "(master) dataset. Produces a text report listing errors."
        )

    def getParameterInfo(self):
        in_dataset = arcpy.Parameter(
            displayName="Post-Update Feature Class (to check)",
            name="in_dataset",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        master_dataset = arcpy.Parameter(
            displayName="Pre-Update (Master) Feature Class",
            name="master_dataset",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        report_file = arcpy.Parameter(
            displayName="Output Report File",
            name="report_file",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output")

        return [in_dataset, master_dataset, report_file]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Resolve full catalog paths (the QA script derives GDB/folder paths via os.path)
        in_dataset = arcpy.Describe(parameters[0].value).catalogPath
        master_dataset = arcpy.Describe(parameters[1].value).catalogPath

        # Ensure the toolbox directory is on sys.path so attribute_qa_v8 can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        if toolbox_dir not in sys.path:
            sys.path.insert(0, toolbox_dir)

        # Import and reload to pick up any mid-session edits
        import attribute_qa_v8
        importlib.reload(attribute_qa_v8)

        attribute_qa_v8.run(in_dataset, master_dataset)

        # Set the derived output parameter to the report path (clickable in results)
        report_path = attribute_qa_v8.attributeQAReportFile
        arcpy.SetParameterAsText(2, report_path)
        arcpy.AddMessage('')
        arcpy.AddMessage('Report file: ' + report_path)
        arcpy.AddMessage('Report folder: ' + os.path.dirname(report_path))

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


class CompareFGDBProperties(object):
    def __init__(self):
        self.label = "Compare FGDB Properties"
        self.description = (
            "Compares the properties of a Returned File Geodatabase against a "
            "Master File Geodatabase: domains, domain coded values, coordinate "
            "systems, tolerances, spatial domain/extent, fields, field "
            "properties, and topology rules. Outputs a text log file."
        )

    def getParameterInfo(self):
        # ORIGINAL: gp.GetParameterAsText(0) / gp.GetParameterAsText(1) at module level
        # CHANGE: .pyt getParameterInfo() pattern; DEWorkspace parameters with LocalDatabase filter
        # RISK: LocalDatabase filter allows both File GDB and Personal GDB; extension check in execute()
        #       catches non-FGDB inputs at runtime
        # DOWNSTREAM: parameters[0]/[1] consumed in execute(); parameters[2] is derived log file output
        master_gdb = arcpy.Parameter(
            displayName="Master File Geodatabase",
            name="master_gdb",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        master_gdb.filter.list = ["LocalDatabase"]

        returned_gdb = arcpy.Parameter(
            displayName="Returned File Geodatabase",
            name="returned_gdb",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        returned_gdb.filter.list = ["LocalDatabase"]

        log_file_param = arcpy.Parameter(
            displayName="Output Log File",
            name="log_file",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output")

        return [master_gdb, returned_gdb, log_file_param]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # ORIGINAL: import arcgisscripting; gp = arcgisscripting.create(9.3); win32com fallback
        # CHANGE: arcpy already imported at toolbox level; no geoprocessor object needed
        # RISK: None; arcpy is the ArcGIS Pro 3 replacement for arcgisscripting
        # DOWNSTREAM: All gp.* calls throughout replaced with arcpy.*
        import time
        import datetime

        master_fgdb = parameters[0].valueAsText
        returned_fgdb = parameters[1].valueAsText

        # --- Set up log file ---
        # ORIGINAL: gdbPath = os.path.dirname(returnedFGDB); open(LogFile, 'w')
        # CHANGE: open(..., encoding='utf-8') added; os.path.join() for cross-platform path safety
        # RISK: If returned_fgdb parent folder is read-only, open() raises PermissionError
        # DOWNSTREAM: fh used by _log() for all file output throughout the tool
        now = time.localtime()
        t1 = str(now.tm_hour) + str(now.tm_min) + str(now.tm_sec)
        gdb_path = os.path.dirname(returned_fgdb)
        log_file = os.path.join(
            gdb_path,
            f"DataPropertiesCheck_Log_{datetime.date.today()}_{t1}.txt"
        )
        fh = open(log_file, 'w', encoding='utf-8')

        def _log(msg):
            # ORIGINAL: __printMsg — print msg (Python 2); conditional gp.AddMessage if toolFlag='YES'
            # CHANGE: arcpy.AddMessage() always (toolbox context); write to file unconditionally
            # RISK: None; toolbox tools always use arcpy.AddMessage()
            # DOWNSTREAM: Every output line in domain_properties, dataset_properties, topology_check
            arcpy.AddMessage(msg)
            fh.write(msg + '\n')

        # -----------------------------------------------------------------------
        # Build dictionary of CODE -> DESCRIPTION from a domain export table
        # Called from domain_properties()
        # -----------------------------------------------------------------------
        def _build_dict(input_table):
            # ORIGINAL: cur = gp.SearchCursor(inputFC); row = cur.Next(); while row: d[row.CODE]=[row.DESCRIPT]; del cur
            # CHANGE: arcpy.da.SearchCursor context manager with explicit field list; tuple unpacking
            # RISK: Column names CODE and DESCRIPT are hardcoded; must match DomainToTable output columns
            # DOWNSTREAM: Returns dict used in domain code/description comparisons
            d = {}
            with arcpy.da.SearchCursor(input_table, ["CODE", "DESCRIPT"]) as cur:
                for row in cur:
                    d[row[0]] = [row[1]]
            return d

        # -----------------------------------------------------------------------
        # Compare domain names and coded values/descriptions between master and returned
        # -----------------------------------------------------------------------
        def domain_properties():
            _log('----------------------------------------------------------------------------\n')
            _log('STARTING Checking FGDB Domains...\n')
            dom_check_error_count = 0

            # ORIGINAL: domains1 = desc1.Domains — property on 9.3 workspace describe object
            # CHANGE: arcpy.Describe(workspace).domains — same property, valid in ArcGIS Pro
            # RISK: .domains returns [] if workspace has no domains; handled by if/else below
            # DOWNSTREAM: domain name lists drive all subsequent domain comparisons
            desc1 = arcpy.Describe(master_fgdb)
            desc2 = arcpy.Describe(returned_fgdb)
            domains1 = list(desc1.domains)
            domains2 = list(desc2.domains)
            domains1.sort()
            domains2.sort()

            _log('Master Domains:  \t' + str(domains1))
            _log('Returned Domains: \t' + str(domains2) + '\n')

            if not domains1 and not domains2:
                _log('OK \t Neither the Master nor the Returned FGDB have any domains.')
            if domains1 and not domains2:
                _log('ERROR \t The Returned FGDB has no domains, but the Master has the following domains:')
                _log('\t' + str(domains1))
                dom_check_error_count += 1
            if not domains1 and domains2:
                _log('ERROR \t The Master FGDB has no domains, but the Returned FGDB does have domains')
                _log('Extra domains from Returned FGDB:  ' + str(domains2))
                dom_check_error_count += 1

            if len(domains1) > 0 and len(domains2) > 0:
                for dom in domains1:
                    if domains2.count(dom) == 0:
                        _log('ERROR    ' + dom + ' is not present in Returned FGDB...')
                        dom_check_error_count += 1

                _log('-----------------------------------------\n')
                _log('Preparing to check Domain Values...\n')

                # ORIGINAL: gp.overwriteoutput=1; gp.Workspace = "in_memory"; gp.DomainToTable_management(...)
                # CHANGE: arcpy.env.overwriteOutput = True; arcpy.env.workspace = "memory";
                #         arcpy.management.DomainToTable(...)
                # RISK: "memory" workspace is session-scoped; tables are cleared after tool finishes (intended)
                # DOWNSTREAM: Temporary tables read by _build_dict() for code/description comparison
                arcpy.env.overwriteOutput = True
                arcpy.env.workspace = "memory"

                _log('\t Exporting MASTER Domains to temporary tables...')
                for dom1 in domains1:
                    _log('\t\t ...' + dom1)
                    arcpy.management.DomainToTable(master_fgdb, dom1, f"memory/{dom1}_dom1", "CODE", "DESCRIPT")
                _log('\n')

                _log('\t Exporting RETURNED Domains to temporary tables...')
                for dom2 in domains2:
                    _log('\t\t ... ' + dom2)
                    arcpy.management.DomainToTable(returned_fgdb, dom2, f"memory/{dom2}_dom2", "CODE", "DESCRIPT")

                for dom in domains2:
                    _log('\n-----------------------------------------\n')
                    _log('Checking CODES and DESCRIPTIONS in Returned FGDB for domain:   ' + dom + '\n')
                    if domains1.count(dom):
                        d1 = _build_dict(f"memory/{dom}_dom1")
                        d2 = _build_dict(f"memory/{dom}_dom2")

                        _log('Master Domain - ' + dom + ' - has ' + str(len(d1)) + ' values:')
                        # ORIGINAL: for vcode, desc in d1.iteritems(): — Python 2 dict method
                        # CHANGE: .items() — Python 3 equivalent; no behavioural difference
                        # RISK: None
                        # DOWNSTREAM: Logging only
                        for vcode, desc_val in d1.items():
                            _log('\t' + vcode + '\t' + str(desc_val))
                        _log('\n')
                        _log('Returned Domain - ' + dom + ' - has ' + str(len(d2)) + ' values:')
                        for vcode, desc_val in d2.items():
                            _log('\t' + vcode + '\t' + str(desc_val))
                        _log('\n')

                        if len(d1) == 0 and len(d2) == 0:
                            _log('Both Master and Returned FGDB have no domains.')
                        else:
                            for key in d1.keys():
                                if key in d2.keys():
                                    if d1[key] != d2[key]:
                                        _log('ERROR    Description or case for ' + dom + ' ' + key +
                                             ' does not match: ' + str(d1[key]) + ' vs ' + str(d2[key]))
                                        dom_check_error_count += 1
                                else:
                                    _log('ERROR    No Domain value for: ' + key + ' or case mismatch.')
                                    dom_check_error_count += 1

                            out_list2 = [k for k in d2.keys() if k not in d1.keys()]
                            if out_list2:
                                _log('ERROR    The following coded values are extra in the Returned domain ' + dom + ':')
                                _log('\t' + str(out_list2))
                                dom_check_error_count += 1
                    else:
                        _log('ERROR    Domain: ' + dom + ' does not exist in the Master FGDB ... Returned FGDB has an extra domain.')
                        dom_check_error_count += 1

                arcpy.env.overwriteOutput = False

        # -----------------------------------------------------------------------
        # Generic field/index property comparison using two object lists
        # -----------------------------------------------------------------------
        def _dict_compare(obj_list1, obj_list2, prop_list, dtype, msg):
            dict1 = {item.name: item for item in obj_list1}
            dict2 = {item.name: item for item in obj_list2}

            for key in dict1:
                if key != 'FDO_Shape':
                    # ORIGINAL: if Dict2.has_key(key): — Python 2 dict method
                    # CHANGE: 'key in dict2' — Python 3 standard
                    # RISK: None; direct equivalent
                    # DOWNSTREAM: Controls whether field properties are compared or reported missing
                    if key in dict2:
                        obj1 = dict1[key]
                        obj2 = dict2[key]
                        for prop in prop_list:
                            # ORIGINAL: val1 = eval('Obj1.'+property) — eval() for dynamic property access
                            # CHANGE: getattr(obj, prop, None) — no code-injection risk; returns None if absent
                            # RISK: If ArcGIS Pro property name casing differs from prop_list values, returns None
                            #       (comparison None==None passes silently; discrepancy won't be reported)
                            # DOWNSTREAM: Drives field/index mismatch warning messages
                            val1 = getattr(obj1, prop, None)
                            val2 = getattr(obj2, prop, None)
                            if val2 != val1:
                                v1_str = val1 if val1 else '<not defined>'
                                v2_str = val2 if val2 else '<not defined>'
                                _log(f'\t\tWARNING     {dtype} {key} {prop} is NOT the same: {v1_str} vs {v2_str} {msg}')
                    else:
                        _log(f'\t\tERROR     {dtype} {key} is missing!! {msg}')

            for key in dict2:
                # ORIGINAL: if not Dict1.has_key(key): — Python 2
                # CHANGE: 'key not in dict1' — Python 3
                # RISK: None
                # DOWNSTREAM: Catches extra fields/indexes in returned FC
                if key not in dict1:
                    _log(f'\t\tERROR     {dtype} {key} is extra!! {msg}')

        # -----------------------------------------------------------------------
        # Compare feature classes within a feature dataset
        # -----------------------------------------------------------------------
        def _fc_props(dataset):
            _log('\n-----------------------------------------\n')
            _log('Checking Feature Classes for...')
            _log('  DATASET:  ' + dataset)

            dataset1 = os.path.join(master_fgdb, dataset)
            dataset2 = os.path.join(returned_fgdb, dataset)

            # ORIGINAL: gp.workspace = dataset1; fcList1 = gp.ListFeatureClasses()
            # CHANGE: arcpy.env.workspace; arcpy.ListFeatureClasses()
            # RISK: ListFeatureClasses() returns None if no FCs; handled by 'or []' default
            # DOWNSTREAM: fc_list1/fc_list2 drive all FC-level comparisons
            arcpy.env.workspace = dataset1
            fc_list1 = arcpy.ListFeatureClasses() or []
            _log('\nMaster Feature Classes in ' + dataset + ':')
            for item in fc_list1:
                _log('\t' + item)

            arcpy.env.workspace = dataset2
            fc_list2 = arcpy.ListFeatureClasses() or []
            _log('\nReturned Feature Classes in ' + dataset + ':')
            for item in fc_list2:
                _log('\t' + item)

            _log('\n\tComparing FCs...')

            for fc in fc_list1:
                if not arcpy.Exists(os.path.join(dataset2, fc)):
                    _log('\tERROR     ' + fc + ' DOES NOT EXIST in Returned FGDB.  Cannot check FC or field properties.')
            for fc in fc_list2:
                if not arcpy.Exists(os.path.join(dataset1, fc)):
                    _log('\tERROR    The Returned FGDB has an ADDITIONAL feature class: ' + fc + ' in Dataset ' + dataset)

            _log('\n-----------------------------------------\n')
            for fc in fc_list1:
                if arcpy.Exists(os.path.join(dataset2, fc)):
                    _log('Describing Feature Classes...')
                    _log('  FEATURE CLASS:  ' + fc)
                    fc1 = os.path.join(dataset1, fc)
                    fc2 = os.path.join(dataset2, fc)

                    # ORIGINAL: gp.describe(fc1) — arcgisscripting describe
                    # CHANGE: arcpy.Describe(fc1) — direct ArcGIS Pro replacement
                    # RISK: None; arcpy.Describe() is identical in purpose
                    # DOWNSTREAM: fc_desc1/fc_desc2 used for property and field comparisons
                    fc_desc1 = arcpy.Describe(fc1)
                    fc_desc2 = arcpy.Describe(fc2)

                    _log('\nPreliminary check of Feature Class (FC) properties...')
                    # ORIGINAL: fcPropList = ['HasSpatialIndex','FeatureType',...]; eval('fcDesc1.'+property)
                    # CHANGE: lowercase Pro property names; getattr() replaces eval()
                    # RISK: If any property name is wrong for Pro, getattr returns None; mismatch silent
                    # DOWNSTREAM: Reports ERROR for any property mismatch
                    fc_prop_list = ['hasSpatialIndex', 'featureType', 'shapeFieldName',
                                    'shapeType', 'areaFieldName', 'lengthFieldName', 'defaultSubtypeCode']
                    for prop in fc_prop_list:
                        val1 = getattr(fc_desc1, prop, None)
                        val2 = getattr(fc_desc2, prop, None)
                        if val2 != val1:
                            _log(f'\tERROR     {prop} is NOT the same in the Returned feature class {fc_desc2.name}')

                    _log('\nChecking Fields...')
                    fld_obj1 = arcpy.ListFields(fc1)
                    fld_obj2 = arcpy.ListFields(fc2)
                    _log('\n\tChecking Number of fields, field order, and field properties ...\n')

                    if len(fld_obj2) != len(fld_obj1):
                        _log(f'\t\tERROR     The number of fields in {fc2} are NOT equal: {len(fld_obj1)} vs {len(fld_obj2)}')
                    else:
                        _log('\t\tThe number of fields match! Now checking field order....\n')

                        cnt = 0
                        order = 1
                        df1 = {}
                        dict_temp1 = {}
                        while cnt < len(fld_obj1):
                            if fld_obj1[cnt].name in [fc_desc1.shapeFieldName,
                                                       fc_desc1.areaFieldName,
                                                       fc_desc1.lengthFieldName]:
                                dict_temp1[fld_obj1[cnt].name] = cnt
                            else:
                                df1[order] = fld_obj1[cnt].name
                                order += 1
                            cnt += 1

                        cnt = 0
                        order = 1
                        df2 = {}
                        dict_temp2 = {}
                        while cnt < len(fld_obj2):
                            if fld_obj2[cnt].name in [fc_desc2.shapeFieldName,
                                                       fc_desc2.areaFieldName,
                                                       fc_desc2.lengthFieldName]:
                                dict_temp2[fld_obj2[cnt].name] = cnt
                            else:
                                df2[order] = fld_obj2[cnt].name
                                order += 1
                            cnt += 1

                        cnt = 0
                        for key in df1.keys():
                            if df1.get(key) != df2.get(key):
                                _log(f'\t\tWARNING   Fields are out of Order at {df2.get(key)} in the returned features. Quitting field order comparison...')
                                cnt += 1
                                break
                        if cnt == 0:
                            _log('\t\tOK    Main fields are in the same order.\n')

                        for key in dict_temp1.keys():
                            try:
                                if dict_temp1[key] != dict_temp2[key]:
                                    _log(f'\t\tWARNING    Internal field {key} is not in the same order as the master Feature Class.')
                            except LookupError:
                                _log(f'\t\tERROR     Internal field {key} does not exist in the returned features.')

                    prop_list = ['domain', 'isNullable', 'type', 'length']
                    msg = '     ...in Returned FC ' + fc_desc2.name
                    _dict_compare(fld_obj1, fld_obj2, prop_list, 'Field', msg)

                    _log('\n\tChecking Field Indexes...')
                    index_obj1 = arcpy.ListIndexes(fc1) or []
                    index_obj2 = arcpy.ListIndexes(fc2) or []

                    if not index_obj1 and not index_obj2:
                        _log('\t\tOK \t Neither the Master nor the Returned FC have any Field Indexes.')
                    if index_obj1 and not index_obj2:
                        _log('\t\tERROR \t The Returned FC has no Field Indexes, but the Master FC does.')
                    if not index_obj1 and index_obj2:
                        _log('\t\tERROR \t The Master FC has no Field Indexes, but the Returned FC does.')

                    if len(index_obj1) > 0 or len(index_obj2) > 0:
                        prop_list = ['name', 'isAscending', 'isUnique']
                        msg = '     ...in Returned FC ' + fc_desc2.name
                        _dict_compare(index_obj1, index_obj2, prop_list, 'Field Index', msg)

        # -----------------------------------------------------------------------
        # Compare feature dataset and FC properties
        # -----------------------------------------------------------------------
        def dataset_properties():
            _log('\n----------------------------------------------------------------------------')
            _log('STARTING checking Dataset, Feature Class, and Field properties...')
            _log('\nNOTE: While this script can detect if a Default Subtype Code is applied to a FC,')
            _log('it DOES NOT detect the actual Subtype values, or if they match.')
            _log('The script CAN detect if a domain is applied to a field (applies to all records).')
            _log('-----------------------------------------')
            _log('\nGetting Dataset Lists ... ')

            # ORIGINAL: gp.workspace = masterFGDB; dsets1 = gp.ListDatasets()
            # CHANGE: arcpy.env.workspace; arcpy.ListDatasets(); 'or []' guards against None return
            # RISK: None
            # DOWNSTREAM: dsets1/dsets2 drive all dataset/FC comparisons
            arcpy.env.workspace = master_fgdb
            dsets1 = [str(i) for i in (arcpy.ListDatasets() or [])]
            if not dsets1:
                _log('\t\tWARNING   Master has no Datasets...')
            _log('\tMaster Feature Datasets:  \t' + str(dsets1))

            arcpy.env.workspace = returned_fgdb
            dsets2 = [str(i) for i in (arcpy.ListDatasets() or [])]
            if not dsets2:
                _log('\t\tWARNING   Returned has no Datasets...')
            _log('\tReturned Feature Datasets:  \t' + str(dsets2) + '\n')

            for dataset in dsets1:
                if not arcpy.Exists(os.path.join(returned_fgdb, dataset)):
                    _log('\tERROR    No matching feature dataset in Returned FGDB for: ' + dataset)
            for dataset in dsets2:
                if not arcpy.Exists(os.path.join(master_fgdb, dataset)):
                    _log('\tERROR    The Returned FGDB has an extra feature dataset: ' + dataset)

            for dataset in dsets1:
                if arcpy.Exists(os.path.join(returned_fgdb, dataset)):
                    _log('\n-----------------------------------------\n')
                    _log('Now Comparing FD properties for...\n')
                    _log('  DATASET: ' + dataset)
                    _log('\n\tDescribing FDs...')

                    fd_desc1 = arcpy.Describe(os.path.join(master_fgdb, dataset))
                    fd_desc2 = arcpy.Describe(os.path.join(returned_fgdb, dataset))

                    if fd_desc1.datasetType != fd_desc2.datasetType:
                        _log('\t\tERROR    Dataset Type Mismatch.')
                    if fd_desc1.spatialReference.isHighPrecision != fd_desc2.spatialReference.isHighPrecision:
                        _log('\t\tERROR     Precision Mismatch.')

                    _log('\n\tComparing Coordinate System details for FDs....')
                    # ORIGINAL: srPropList = ['Type','Name','ProjectionName',...]; eval('fdDesc1.SpatialReference.'+srProp)
                    # CHANGE: lowercase Pro property names in list; getattr() replaces eval()
                    # RISK: Pro SpatialReference uses camelCase; if a property name differs from 9.3, getattr
                    #       returns None for both objects (None==None -> no false positive, but silent miss)
                    # DOWNSTREAM: Reports mismatch per SR property; breaks on 'name' mismatch
                    sr_prop_list = ['type', 'name', 'projectionName', 'falseEasting', 'falseNorthing',
                                    'centralMeridian', 'standardParallel1', 'standardParallel2', 'linearUnitName']
                    for sr_prop in sr_prop_list:
                        val1 = getattr(fd_desc1.spatialReference, sr_prop, None)
                        val2 = getattr(fd_desc2.spatialReference, sr_prop, None)
                        if val1 != val2:
                            _log(f'\t\tERROR     Mismatching {sr_prop}: {val1} vs {val2}')
                            if sr_prop == 'name':
                                break

                    _log('\n\tChecking Tolerance Properties for FD....')
                    for sr_prop in ['XYTolerance', 'ZTolerance', 'MTolerance']:
                        val1 = getattr(fd_desc1.spatialReference, sr_prop, None)
                        val2 = getattr(fd_desc2.spatialReference, sr_prop, None)
                        if val1 != val2:
                            _log(f'\t\tERROR     Mismatching {sr_prop}: {val1} vs {val2}')

                    _log('\n\tChecking Resolution Properties for FD....')
                    for sr_prop in ['XYResolution', 'ZResolution', 'MResolution']:
                        val1 = getattr(fd_desc1.spatialReference, sr_prop, None)
                        val2 = getattr(fd_desc2.spatialReference, sr_prop, None)
                        if val1 != val2:
                            _log(f'\t\tERROR     Mismatching {sr_prop}: {val1} vs {val2}')

                    _log('\n\tChecking Spatial Domain Properties for FD....')
                    for sr_prop in ['domain', 'ZDomain', 'MDomain']:
                        val1 = getattr(fd_desc1.spatialReference, sr_prop, None)
                        val2 = getattr(fd_desc2.spatialReference, sr_prop, None)
                        if val1 != val2:
                            _log(f'\t\tERROR     Mismatching {sr_prop}: {val1} vs {val2}')

                    _log('\n\tChecking Spatial Extents for FD....')
                    # ORIGINAL: eval('fdDesc1.Extent.'+srProp) — eval() on describe extent object
                    # CHANGE: getattr(fd_desc.extent, sr_prop) — no eval(); safer
                    # RISK: .extent may be None for empty datasets; getattr returns None -> None==None (silent)
                    # DOWNSTREAM: Extent differences reported as WARNING (not ERROR) per original intent
                    for sr_prop in ['XMin', 'YMin', 'XMax', 'YMax']:
                        val1 = getattr(fd_desc1.extent, sr_prop, None)
                        val2 = getattr(fd_desc2.extent, sr_prop, None)
                        if val1 != val2:
                            _log(f'\t\tWARNING     Mismatching {sr_prop}: {val1} vs {val2}')

                    _fc_props(dataset)

        # -----------------------------------------------------------------------
        # Check topology elements in master and returned FGDBs
        # -----------------------------------------------------------------------
        def topology_check():
            arcpy.env.workspace = master_fgdb

            _log('\n----------------------------------------------------------------------------\n')
            _log('STARTING Topology check...')
            _log('\nNOTE:  This script finds which FCs participate in a topology but CAN NOT detect rules.')
            _log('-----------------------------------------')
            _log('\nLooking for matching Topology Elements....')

            dsets1 = arcpy.ListDatasets() or []
            for dataset1 in dsets1:
                _log('\n\tDataset: ' + dataset1 + '\n')
                arcpy.env.workspace = master_fgdb
                ds_desc1 = arcpy.Describe(dataset1)

                # ORIGINAL: children1 = dsDescribe1.Children; children1.Reset(); child1 = children1.Next(); while child1:
                # CHANGE: arcpy.Describe().children in ArcGIS Pro returns a Python list; iterate directly
                # RISK: If .children is absent (non-dataset type), AttributeError
                # DOWNSTREAM: Drives topology name/tolerance/FC comparisons
                top_count = 0
                for child1 in ds_desc1.children:
                    if child1.dataType == 'Topology':
                        _log(f'\t\t{child1.dataType}: {child1.name}')
                        top_count += 1
                        arcpy.env.workspace = dataset1
                        topo_desc1 = arcpy.Describe(child1.name)
                        # ORIGINAL: topoDesc1.ClusterTolerance / topoDesc1.FeatureClassNames
                        # CHANGE: .clusterTolerance / .featureClassNames — camelCase Pro convention
                        # RISK: If property name differs in Pro, AttributeError; test with real topology data
                        # DOWNSTREAM: Values compared against returned FGDB topology
                        top_ctol1 = topo_desc1.clusterTolerance
                        top_fclass1_str = [str(i) for i in topo_desc1.featureClassNames]
                        _log('\n\t\tTopology Cluster Tolerance: ' + str(top_ctol1))
                        _log('\t\tTopology FeatureClasses: ' + str(top_fclass1_str))

                        compare_path = os.path.join(returned_fgdb, dataset1, child1.name)
                        if arcpy.Exists(compare_path):
                            _log('\n\tMatching Topology EXISTS in the Returned FGDB')
                            topo_desc2 = arcpy.Describe(compare_path)
                            top_ctol2 = topo_desc2.clusterTolerance
                            top_fclass2_str = [str(i) for i in topo_desc2.featureClassNames]
                            if top_ctol2 == top_ctol1:
                                _log('\t\tTolerance is equal: ' + str(top_ctol1))
                            else:
                                _log('\t\tERROR    Returned tolerance not equal: ' + str(top_ctol1) + ' vs ' + str(top_ctol2))
                            if top_fclass2_str == top_fclass1_str:
                                _log('\t\tParticipating feature classes are equal: ' + str(top_fclass1_str))
                            else:
                                _log('\t\tERROR    Returned participating FCs not equal: ' +
                                     str(top_fclass1_str) + ' vs ' + str(top_fclass2_str))
                        else:
                            _log('\n\tERROR    Dataset and/or Topology does not exist: ' + compare_path)

                if top_count == 0:
                    _log('\nNOTE     No topology elements in Master FGDB for dataset ' + dataset1)
                else:
                    _log('\nNOTE     ' + str(top_count) + ' Topology element(s) in Master FGDB for dataset ' + dataset1)

            arcpy.env.workspace = returned_fgdb
            _log('\n\nLooking for extra Topology Elements in the returned FGDB datasets....')
            dsets2 = arcpy.ListDatasets() or []
            top_count2 = 0
            for dataset2 in dsets2:
                arcpy.env.workspace = returned_fgdb
                ds_desc2 = arcpy.Describe(dataset2)
                for child2 in ds_desc2.children:
                    if child2.dataType == 'Topology':
                        compare_path2 = os.path.join(master_fgdb, dataset2, child2.name)
                        if not arcpy.Exists(compare_path2):
                            _log('\tERROR    Extra TOPOLOGY in Returned Dataset: ' +
                                 dataset2 + '\\' + child2.name)
                            top_count2 += 1
            if top_count2 == 0:
                _log('\t...None found...OK.')

        # -----------------------------------------------------------------------
        # Main execution
        # -----------------------------------------------------------------------
        _log(' Writing to Log File ' + log_file + ' ...\n')

        # ORIGINAL: startTime = time.clock() — removed in Python 3
        # CHANGE: time.perf_counter() — direct Python 3 replacement for elapsed time
        # RISK: None; perf_counter() returns float seconds
        # DOWNSTREAM: Used only for elapsed time display at end of run
        start_time = time.perf_counter()
        _log('   Starting : ' + time.ctime(time.time()))
        _log('\n----------------------------------------------------------------------------\n')
        _log('Master FGDB: ' + master_fgdb)
        _log('Returned FGDB: ' + returned_fgdb)
        _log('\n Describing Master and Returned GeoDatabases...\n')

        desc1 = arcpy.Describe(master_fgdb)
        desc2 = arcpy.Describe(returned_fgdb)

        # ORIGINAL: if not desc1.datatype == 'Workspace' and not desc1.extension == 'gdb'
        #BUG - MEDIUM: original used 'and' — only quits if BOTH conditions fail simultaneously.
        #              A workspace with dataType=='Workspace' but extension!='gdb' would pass incorrectly.
        # CHANGE: 'or' — quits if either condition fails (correct intent)
        # RISK: None; 'or' is the correct logic here
        # DOWNSTREAM: Prevents domain/dataset/topology checks running on non-FGDB inputs
        if desc1.dataType != 'Workspace' or desc1.extension != 'gdb':
            _log('QUITTING - Master is not a File Geodatabase.  Must be a File GDB...')
            fh.close()
            return
        if desc2.dataType != 'Workspace' or desc2.extension != 'gdb':
            _log('QUITTING - Returned is not a File Geodatabase.  Must be a File GDB...')
            fh.close()
            return

        # ORIGINAL: if desc1.WorkspaceType <> desc2.WorkspaceType — Python 2 not-equal operator
        # CHANGE: != operator (Python 3); .workspaceType (Pro camelCase)
        # RISK: None; != is standard Python 3
        # DOWNSTREAM: Mismatched types abort before any comparison runs
        if desc1.workspaceType != desc2.workspaceType:
            _log('\t\tERROR    Workspace Type Mismatch: ' + desc1.workspaceType + ' vs ' + desc2.workspaceType)
            _log('QUITTING - Cannot proceed.')
            fh.close()
            return

        arcpy.env.workspace = master_fgdb
        if not arcpy.ListDatasets():
            _log('\t\tWARNING   Master has no Datasets...')
        arcpy.env.workspace = returned_fgdb
        if not arcpy.ListDatasets():
            _log('\t\tWARNING   Returned has no Datasets...')

        domain_properties()
        dataset_properties()
        topology_check()

        elapsed = time.perf_counter() - start_time
        _log(f'\n\nDone.  Elapsed time: {elapsed:.2f} seconds')
        _log('Log file written to: ' + log_file)
        fh.close()

        arcpy.SetParameterAsText(2, log_file)
        arcpy.AddMessage('')
        arcpy.AddMessage('Log file: ' + log_file)
        arcpy.AddMessage('Log folder: ' + os.path.dirname(log_file))

    def postExecute(self, parameters):
        return


