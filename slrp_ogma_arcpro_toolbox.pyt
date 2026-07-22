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
import importlib
import os
import sys


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Descriptive Name of your Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [FindDuplicates, UpdateSeqNumbers, UpdateSeqNumOgmaLegalandNon, GeometryCheckTool, AttributeQa, CompareNumRecords, CompareFGDBProperties, CheckInDataset]  
       
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
        self.label = "Update Any Sequential Numbers"
        self.description = (
            "Updates any field with the next highest sequential number. "
            "For text fields, specify a prefix (e.g. CAR_RCA_) and the tool fills "
            "blank records with the next sequential value. "
            "For numeric fields, fills zero or null records with the next integer."
        )
        self.enableUndo = True  # Shows 'Enable Undo' toggle in tool dialog; ArcGIS Pro manages the edit session

    def getParameterInfo(self):
        # Parameter 0: feature class to update (accepts a layer from the Contents pane)
        param_1 = arcpy.Parameter(
            displayName="Input Feature Class",
            name="param_1",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        # Parameter 1: field to update; dropdown populated from param_1
        param_2 = arcpy.Parameter(
            displayName="Field to Update",
            name="param_2",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        param_2.parameterDependencies = [param_1.name]

        # Parameter 2: prefix string (required for text fields; ignored for numeric fields)
        param_3 = arcpy.Parameter(
            displayName="Prefix (e.g. CAR_RCA_) *include trailing underscore*",
            name="param_3",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")

        # Parameter 3: safety check - must be checked if the prefix has never been used before
        param_4 = arcpy.Parameter(
            displayName="This will be a new prefix",
            name="param_4",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param_4.value = False
        param_4.enabled = False  # enabled only when a prefix is entered

        # Parameter 4: dry-run mode - reports the next value without writing any changes
        param_5 = arcpy.Parameter(
            displayName="Just display next value - do not update",
            name="param_5",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param_5.value = False

        # Derived output - tells ArcGIS Pro this tool modifies the input feature class
        # (triggers the 'This tool will modify the input data' banner in the tool dialog)
        param_out = arcpy.Parameter(
            displayName="Updated Feature Class",
            name="output_fc",
            datatype="GPFeatureLayer",
            parameterType="Derived",
            direction="Output")
        param_out.parameterDependencies = [param_1.name]
        param_out.schema.clone = True

        return [param_1, param_2, param_3, param_4, param_5, param_out]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # Enable 'This will be a new prefix' only when a prefix has been entered
        if parameters[2].value:
            parameters[3].enabled = True
        else:
            parameters[3].enabled = False
            parameters[3].value = False
        return

    def updateMessages(self, parameters):
        # Validate the prefix format as the user types, before execution
        prefix_param = parameters[2]
        if prefix_param.valueAsText:
            val = prefix_param.valueAsText
            if not val.endswith("_"):
                prefix_param.setWarningMessage(
                    "Prefix should end with an underscore (e.g. CAR_RCA_)."
                )
            elif "'" in val:
                prefix_param.setErrorMessage(
                    "Prefix must not contain single-quote characters."
                )
            else:
                prefix_param.clearMessage()
        return

    def execute(self, parameters, messages):
        selected_featureclass = parameters[0].valueAsText
        selected_field = parameters[1].valueAsText
        prefix = parameters[2].valueAsText or ""
        is_new_prefix = parameters[3].value or False
        just_display_dont_update = parameters[4].value or False

        # Ensure the script_modules directory is on sys.path so the module can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        import update_any_sequential_number
        importlib.reload(update_any_sequential_number)

        update_any_sequential_number.run(
            selected_featureclass, selected_field, prefix,
            is_new_prefix, just_display_dont_update
        )

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
        fc_1 = parameters[0].valueAsText
        field_1 = parameters[1].valueAsText
        fc_2 = parameters[2].valueAsText
        field_2 = parameters[3].valueAsText
        prefix = parameters[4].valueAsText
        is_new_prefix = parameters[5].value  # bool
        just_display = parameters[6].value   # bool

        # Ensure the script_modules directory is on sys.path so the module can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        import update_seq_num_ogma_legal_and_non
        importlib.reload(update_seq_num_ogma_legal_and_non)

        update_seq_num_ogma_legal_and_non.run(
            fc_1, field_1, fc_2, field_2, prefix, is_new_prefix, just_display
        )

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
            datatype="DEFeatureClass",
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
        in_fc = parameters[0].valueAsText

        # Ensure the script_modules directory is on sys.path so the module can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        import check_geometry
        importlib.reload(check_geometry)

        check_geometry.run(in_fc)

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

        # Ensure the script_modules directory is on sys.path so attribute_qa_v8 can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

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
        self.description = (
            "Compares record counts between staging area datasets and the "
            "corresponding published BC Geographic Warehouse (BCGW) datasets "
            "for OGMAs, Landscape Units, and SLRP planning features."
        )

    def getParameterInfo(self):
        staging_path = arcpy.Parameter(
            displayName="Staging Area Base Path",
            name="staging_path",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        # ORIGINAL: staging_path.value was a hardcoded UNC path literal.
        # CHANGE: Default is now read from config.json via config_loader so
        #         no real network path is committed to source control.
        # RISK: If config.json is absent or unpopulated, the default is left
        #       blank; the user can still type/browse the path in the dialog.
        # DOWNSTREAM: Only the default display value in the tool dialog is
        #             affected; execute() reads parameters[0].valueAsText.
        try:
            toolbox_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.join(toolbox_dir, 'script_modules')
            if modules_dir not in sys.path:
                sys.path.insert(0, modules_dir)
            import config_loader
            staging_path.value = config_loader.get("compare_num_records", "staging_base")
        except Exception:
            pass  # Leave blank if config.json is not yet set up

        bcgw_path = arcpy.Parameter(
            displayName="BCGW Connection .SDE file",
            name="bcgw_path",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")
        bcgw_path.filter.list = ["RemoteDatabaseConnection"]

        ogma_compare = arcpy.Parameter(
            displayName="Compare OGMAs",
            name="ogma_compare",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        ogma_compare.value = True

        lu_compare = arcpy.Parameter(
            displayName="Compare Landscape Units",
            name="lu_compare",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        lu_compare.value = True

        slrp_compare = arcpy.Parameter(
            displayName="Compare SLRP Datasets",
            name="slrp_compare",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        slrp_compare.value = True

        return [staging_path, bcgw_path, ogma_compare, lu_compare, slrp_compare]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # Pre-fill the BCGW SDE path from the current project's home folder
        # if the user has not yet altered the parameter
        if not parameters[1].altered:
            try:
                home = arcpy.mp.ArcGISProject("CURRENT").homeFolder
                candidate = os.path.join(home, "Oracle-bcgw.bcgov-idwprod1.bcgov.sde")
                if os.path.isfile(candidate):
                    parameters[1].value = candidate
            except Exception:
                pass
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        staging_path = parameters[0].valueAsText
        bcgw_path = parameters[1].valueAsText
        ogma_compare = parameters[2].value if parameters[2].value is not None else True
        lu_compare = parameters[3].value if parameters[3].value is not None else True
        slrp_compare = parameters[4].value if parameters[4].value is not None else True

        # Ensure the script_modules directory is on sys.path so the module can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        import compare_number_of_records_staging_vs_bcgw
        importlib.reload(compare_number_of_records_staging_vs_bcgw)

        compare_number_of_records_staging_vs_bcgw.run(
            ogma_compare, lu_compare, slrp_compare, staging_path, bcgw_path
        )

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
        master_fgdb = parameters[0].valueAsText
        returned_fgdb = parameters[1].valueAsText

        # Ensure the script_modules directory is on sys.path so compare_fgdb_properties_v2 can be found
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        # Import and reload to pick up any mid-session edits without restarting ArcGIS Pro
        import compare_fgdb_properties_v2
        importlib.reload(compare_fgdb_properties_v2)

        compare_fgdb_properties_v2.run(master_fgdb, returned_fgdb)

        # Set the derived output parameter to the log path (clickable in results)
        log_path = compare_fgdb_properties_v2.compareFGDBLogFile
        arcpy.SetParameterAsText(2, log_path)
        arcpy.AddMessage('')
        arcpy.AddMessage('Log file: ' + log_path)
        arcpy.AddMessage('Log folder: ' + os.path.dirname(log_path))



    def postExecute(self, parameters):
        return


class CheckInDataset(object):
    def __init__(self):
        """Automates the dataset check-in workflow:
        file checklist → Attribute QA → topology report display →
        copy Returned FGDB → copy reports to Update_Emails folder."""
        self.label = "Check In Dataset"
        self.description = (
            "Automates the OGMA/LU/SLRP/WHA dataset check-in workflow. "
            "Lists expected files in the update directory, runs Attribute "
            "QA/QC, displays the topology report, copies the Returned FGDB "
            "to UpdateManagement/CurrentUpdate, and copies QA and topology "
            "reports to the Update_Emails destination folder. "
            "Read-only on the source FGDB throughout."
        )

    def getParameterInfo(self):
        # ORIGINAL: No prior implementation — this is a new tool.
        # CHANGE: New getParameterInfo() providing 4 input parameters for the
        #         check-in workflow.
        # RISK: Default value for update_directory must match the actual UNC
        #       path used by staff; update the constant if the path changes.
        # DOWNSTREAM: parameters[0..3] consumed in execute(); all four paths
        #             are forwarded verbatim to check_in_dataset.run().

        update_directory = arcpy.Parameter(
            displayName="Update Work Area Directory",
            name="update_directory",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        # ORIGINAL: update_directory.value was a hardcoded UNC path literal.
        # CHANGE: Default is now read from config.json via config_loader so
        #         no real network path is committed to source control.
        # RISK: If config.json is absent or unpopulated, the default is left
        #       blank; the user can still type/browse the path in the dialog.
        # DOWNSTREAM: Only the default display value in the tool dialog is
        #             affected; execute() reads parameters[0].valueAsText.
        try:
            toolbox_dir = os.path.dirname(os.path.abspath(__file__))
            modules_dir = os.path.join(toolbox_dir, 'script_modules')
            if modules_dir not in sys.path:
                sys.path.insert(0, modules_dir)
            import config_loader
            update_directory.value = config_loader.get("check_in_dataset", "update_mgmt_base").replace(
                "UpdateManagement", "UpdateWorkArea\\OldGrowthManagementAreas"
            )
        except Exception:
            pass  # Leave blank if config.json is not yet set up

        input_feature_class = arcpy.Parameter(
            displayName="Input Feature Class (inside Returned FGDB)",
            name="input_feature_class",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        master_feature_class = arcpy.Parameter(
            displayName="Master Feature Class (for Attribute QA)",
            name="master_feature_class",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        update_email_folder = arcpy.Parameter(
            displayName="Update Email Folder for This Request",
            name="update_email_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        return [update_directory, input_feature_class, master_feature_class, update_email_folder]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Resolve full catalog paths (check_in_dataset derives GDB/folder
        # paths from these strings via os.path operations).
        update_dir = parameters[0].valueAsText
        in_dataset = arcpy.Describe(parameters[1].value).catalogPath
        master_dataset = arcpy.Describe(parameters[2].value).catalogPath
        email_folder = parameters[3].valueAsText

        # Ensure the script_modules directory is on sys.path so check_in_dataset
        # (and, transitively, attribute_qa_v8) can be imported.
        toolbox_dir = os.path.dirname(os.path.abspath(__file__))
        modules_dir = os.path.join(toolbox_dir, 'script_modules')
        if modules_dir not in sys.path:
            sys.path.insert(0, modules_dir)

        import check_in_dataset
        importlib.reload(check_in_dataset)

        check_in_dataset.run(update_dir, in_dataset, master_dataset, email_folder)

    def postExecute(self, parameters):
        return

