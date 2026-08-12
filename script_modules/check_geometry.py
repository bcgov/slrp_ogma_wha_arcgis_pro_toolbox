import datetime
import os
from collections import Counter
import arcpy


def run(in_fc):
    """Run geometry checks on a feature class before BCGW submission.

    Parameters
    ----------
    in_fc : str
        Path or layer name of the feature class to check.
    """

    arcpy.env.overwriteOutput = True

    arcpy.AddMessage(f"ArcGIS license level: {arcpy.ProductInfo()}")

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
            "This tool only works with feature classes that have a MODIFICATION_TYPE field "
            "**Update this message after further investigation into the appropriate input types."
        )
        return

    # ---------------- REPORT SETUP ----------------
    # Walk up from the FC's catalog path to find the containing .gdb; the
    # Update Work Area folder is the GDB's parent. Handles FCs directly under
    # the GDB (no Feature Dataset) as well as FCs inside a FDS.
    def _derive_update_folder(catalog_path):
        p = os.path.dirname(catalog_path)
        while p:
            if p.lower().endswith(".gdb"):
                return os.path.dirname(p)
            parent = os.path.dirname(p)
            if parent == p:
                return None
            p = parent
        return None

    update_folder = _derive_update_folder(desc.catalogPath)
    report_filename = f"{fc_name}_geometry_check_{datetime.date.today()}.txt"
    report_state = {
        "path": os.path.join(update_folder, report_filename) if update_folder else None
    }

    def write_header():
        header_lines = [
            "=" * 70,
            "GEOMETRY CHECK REPORT",
            "=" * 70,
            f"Feature Class : {fc_name}",
            f"Dataset Path  : {desc.catalogPath}",
            f"Shape Type    : {desc.shapeType}",
            f"Run Timestamp : {datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",
            f"Operator IDIR : {os.environ.get('USERNAME', '')}",
            "=" * 70,
            "",
        ]
        # Try the derived Update Work Area folder first; on failure, fall back
        # once to arcpy.env.scratchFolder and warn the user where the report
        # actually ended up.
        for attempt in ("primary", "fallback"):
            if report_state["path"] is None:
                report_state["path"] = os.path.join(
                    arcpy.env.scratchFolder, report_filename
                )
                arcpy.AddWarning(
                    "Could not derive an Update Work Area folder from the input "
                    "feature class path. Geometry report will be written to the "
                    "scratch folder instead: " + report_state["path"]
                )
            try:
                with open(report_state["path"], "w", encoding="utf-8") as fh:
                    fh.write("\n".join(header_lines))
                return
            except OSError as exc:
                if attempt == "primary":
                    arcpy.AddWarning(
                        "Could not write geometry report to " + report_state["path"]
                        + " (" + str(exc) + "). Falling back to scratch folder."
                    )
                    report_state["path"] = os.path.join(
                        arcpy.env.scratchFolder, report_filename
                    )
                else:
                    arcpy.AddWarning(
                        "Could not write geometry report to scratch folder either: "
                        + str(exc) + ". Geometry checks will still run, but no "
                        "report file will be produced."
                    )
                    report_state["path"] = None
                    return

    def write_report(section_title, lines):
        if report_state["path"] is None:
            return
        block = [
            "",
            "-" * 60,
            section_title,
            "-" * 60,
        ] + list(lines) + [""]
        try:
            with open(report_state["path"], "a", encoding="utf-8") as fh:
                fh.write("\n".join(block))
        except OSError as exc:
            arcpy.AddWarning(
                "Could not append '" + section_title + "' section to geometry "
                "report at " + report_state["path"] + ": " + str(exc)
            )

    # msg/warn mirror arcpy console output into the report section lines.
    def msg(lines, text):
        arcpy.AddMessage(text)
        lines.append(text)

    def warn(lines, text):
        arcpy.AddWarning(text)
        lines.append("[WARNING] " + text)

    write_header()

    # ---------------- FUNCTIONS ----------------

    def repair_geometry(in_fc):
        lines = []
        msg(lines, "Repairing geometry where MODIFICATION_TYPE is not null...")

        lyr = arcpy.CreateUniqueName("fc_lyr")
        where_clause = "MODIFICATION_TYPE IS NOT NULL"

        arcpy.management.MakeFeatureLayer(in_fc, lyr, where_clause)
        arcpy.management.RepairGeometry(lyr)

        msg(lines, "✔ Geometry repair complete")
        write_report("REPAIR GEOMETRY", lines)


    def identify_very_small_polygons_or_line_segments(in_fc):
        desc = arcpy.Describe(in_fc)
        lines = []

        msg(lines, "Identifying small features where MODIFICATION_TYPE is not null...")

        fc_lyr = arcpy.CreateUniqueName("fc_lyr")
        where_clause = "MODIFICATION_TYPE IS NOT NULL"

        arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, where_clause)

        if desc.shapeType == "Polygon":
            msg(lines, "Checking for polygons with area <= 0.5 ha...")

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

            sliver_count = int(arcpy.management.GetCount(temp_lyr)[0])

            if sliver_count > 0:
                warn(lines, f"There are {sliver_count} small polygon features (<= 0.5 ha).")
                warn(lines, f"Review: temp_sliver_polygons_{fc_name}")
                lines.append(f"Review dataset path: {temp_fc}")
            else:
                msg(lines, "No sliver polygons found.")

            arcpy.management.Delete(temp_lyr)

        else:
            msg(lines, "Checking for short line segments (< 1 meter)...")

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

            short_segment_count = int(arcpy.management.GetCount(temp_lyr)[0])

            if short_segment_count > 0:
                warn(lines, f"There are {short_segment_count} short line segments (< 1 meter).")
                warn(lines, f"Review: temp_short_line_segments_{fc_name}")
                lines.append(f"Review dataset path: {temp_fc}")
            else:
                msg(lines, "No short segments found.")

            arcpy.management.Delete(temp_lyr)

        arcpy.management.Delete(fc_lyr)
        write_report("SMALL FEATURES (SLIVER POLYGONS OR SHORT LINES)", lines)


    def check_for_multiple_identical_vertices(in_fc):
        lines = []
        msg(lines, "Checking for identical vertices (>= 4) in modified features...")
        msg(lines, "Features with 4+ identical vertices will not load to BCGW.")

        fc_lyr = arcpy.CreateUniqueName("fc_lyr")
        where_clause = "MODIFICATION_TYPE IS NOT NULL"

        arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, where_clause)

        # Step 1: Copy features
        temp_fc1 = os.path.join(fds_path, f"temp_identical_vertex_check_Step1_{fc_name}")
        temp_fc2 = os.path.join(fds_path, f"temp_identical_vertex_check_Step2_{fc_name}")

        if arcpy.Exists(temp_fc1):
            arcpy.management.Delete(temp_fc1)

        msg(lines, " - Creating temp dataset of modified features")

        arcpy.management.CopyFeatures(fc_lyr, temp_fc1)

        # Step 2: Convert to points
        msg(lines, " - Converting features to vertices")
        arcpy.management.FeatureVerticesToPoints(temp_fc1, temp_fc2, "ALL")

        # Step 3: Add XY + fields
        arcpy.management.AddXY(temp_fc2)
        arcpy.management.AddField(temp_fc2, "CHECK", "TEXT", field_length=100)
        arcpy.management.AddField(temp_fc2, "FLAG", "TEXT")

        temp_lyr = arcpy.CreateUniqueName("temp_lyr")
        arcpy.management.MakeFeatureLayer(temp_fc2, temp_lyr)

        # ORIGINAL: ID field was inferred by matching keywords in fc_name
        #   (e.g. 'old_growth', 'slrp', 'landscape'). Broke when the feature
        #   class had a non-standard name such as 'ogma_legal_to_append'.
        # CHANGE: Inspect the actual fields present on the feature class.
        #   Each dataset type has a unique ID field, so presence of the field
        #   is an unambiguous identifier regardless of the FC name.
        # RISK: If a future dataset uses a new ID field not in this list, it
        #   will still raise ValueError — but with a more informative message.
        # DOWNSTREAM: Only the field-name variable is affected; all cursor
        #   and flag logic below uses feat_id_field unchanged.
        id_field_candidates = [
            "LEGAL_OGMA_INTERNAL_ID",
            "NON_LEGAL_OGMA_INTERNAL_ID",
            "LANDSCAPE_UNIT_ID",
            "LEGAL_FEAT_ID",
            "NON_LEGAL_FEAT_ID",
            "STRGC_LAND_RSRCE_PLAN_ID",
        ]
        fc_fields = {f.name for f in arcpy.ListFields(in_fc)}
        feat_id_field = next((f for f in id_field_candidates if f in fc_fields), None)
        if feat_id_field is None:
            warn(lines, "Could not determine feature ID field. Expected one of: "
                 + ", ".join(id_field_candidates))
            write_report("DUPLICATE VERTICES (>= 4 IDENTICAL POINTS)", lines)
            raise ValueError(
                f"Could not determine feature ID field for '{fc_name}'. "
                "Expected one of: " + ", ".join(id_field_candidates)
            )
        lines.append(f"Feature ID field used: {feat_id_field}")

        # Step 4: Calculate CHECK field
        calc_expr = f"str(!{feat_id_field}!) + '_' + str(!POINT_X!) + '_' + str(!POINT_Y!)"
        arcpy.management.CalculateField(temp_lyr, "CHECK", calc_expr, "PYTHON3")

        # Step 5: Use modern cursor (FAST)
        msg(lines, " - Analyzing vertex duplication")

        with arcpy.da.SearchCursor(temp_lyr, ["CHECK"]) as cursor:
            values = [row[0] for row in cursor]

        counts = Counter(values)
        flagged_points = [k for k, v in counts.items() if v > 3]

        # Step 6: Flag duplicates
        for flagged_point in flagged_points:
            where = f"CHECK = '{flagged_point}'"
            arcpy.management.SelectLayerByAttribute(temp_lyr, "NEW_SELECTION", where)

            count = int(arcpy.management.GetCount(temp_lyr)[0])

            arcpy.management.CalculateField(temp_lyr, "FLAG", f'"{count}"', "PYTHON3")

        # Step 7: Keep only flagged
        arcpy.management.SelectLayerByAttribute(temp_lyr, "NEW_SELECTION", "FLAG IS NULL")
        arcpy.management.DeleteFeatures(temp_lyr)

        point_count = int(arcpy.management.GetCount(temp_lyr)[0])

        if point_count > 0:
            warn(lines, "There are instances of 4+ identical vertices!")
            warn(lines, f"Review: temp_identical_vertex_check_Step2_{fc_name}")
            lines.append(f"Flagged vertex clusters: {len(flagged_points)}")
            lines.append(f"Flagged points remaining in temp dataset: {point_count}")
            lines.append(f"Review dataset path: {temp_fc2}")
        else:
            msg(lines, "No duplicate vertices found.")

        # Cleanup
        arcpy.management.Delete(fc_lyr)
        arcpy.management.Delete(temp_lyr)

        msg(lines, "----- Vertex check complete -----")
        write_report("DUPLICATE VERTICES (>= 4 IDENTICAL POINTS)", lines)


    def check_for_max_vertices(in_fc):
        lines = []
        msg(lines, "Checking vertex count for modified features...")
        msg(lines, "All features must have < 524,000 vertices for BCGW.")

        fc_lyr = arcpy.CreateUniqueName("fc_lyr")
        where_clause = "MODIFICATION_TYPE IS NOT NULL"

        arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, where_clause)

        # Add and calculate vertex count
        arcpy.management.AddField(fc_lyr, "VxCount", "LONG")
        arcpy.management.CalculateField(fc_lyr, "VxCount", "!shape!.pointCount", "PYTHON3")

        # Select features over limit
        arcpy.management.SelectLayerByAttribute(fc_lyr, "NEW_SELECTION", "VxCount > 524000")

        over_vertex_limit_count = int(arcpy.management.GetCount(fc_lyr)[0])

        if over_vertex_limit_count > 0:
            arcpy.conversion.FeatureClassToFeatureClass(fc_lyr, fds_path, f"temp_{fc_name}_OVER_MAX_VERTICES")

            warn(lines, f"There are {over_vertex_limit_count} features over the vertex limit.")
            warn(lines, "Features must have fewer than 524,000 vertices.")
            warn(lines, f"Review: temp_{fc_name}_OVER_MAX_VERTICES")
            lines.append(f"Review dataset path: {os.path.join(fds_path, f'temp_{fc_name}_OVER_MAX_VERTICES')}")

            warn(lines, "Possible solutions:")
            warn(lines, "- Use Simplify Polygon (<1m tolerance)")
            warn(lines, "- Split multipart polygons")
            warn(lines, "- Contact your Data Resource Manager")

        else:
            msg(lines, 'All features are under the vertex limit ✔')

        # Cleanup
        arcpy.management.DeleteField(fc_lyr, "VxCount")
        arcpy.management.Delete(fc_lyr)

        msg(lines, "----- Vertex count check complete -----")
        write_report("MAX VERTEX COUNT PER FEATURE", lines)

    # ---------------- CALL FUNCTIONS ----------------
    arcpy.SetProgressor("step", "Repairing geometry...", 0, 4, 1)

    arcpy.SetProgressorLabel("Step 1 of 4: Repairing geometry...")
    arcpy.SetProgressorPosition()
    repair_geometry(in_fc)

    arcpy.SetProgressorLabel("Step 2 of 4: Checking for small features...")
    arcpy.SetProgressorPosition()
    identify_very_small_polygons_or_line_segments(in_fc)

    arcpy.SetProgressorLabel("Step 3 of 4: Checking vertex count limit...")
    arcpy.SetProgressorPosition()
    check_for_max_vertices(in_fc)

    arcpy.SetProgressorLabel("Step 4 of 4: Checking for duplicate vertices...")
    arcpy.SetProgressorPosition()
    check_for_multiple_identical_vertices(in_fc)

    if report_state["path"]:
        arcpy.AddMessage("")
        arcpy.AddMessage("Geometry report written to: " + report_state["path"])
