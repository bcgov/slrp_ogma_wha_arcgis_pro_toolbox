import arcpy
import os

arcpy.env.overwriteOutput = True

in_fc = arcpy.GetParameterAsText(0)


##in_fc = r"\\spatialfiles3.bcgov\slrp\UpdateManagement\OldGrowthManagementAreas\CurrentUpdate\old_growth_management_area_bc_Update_20210426_RETURNED_20210518.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"

arcpy.AddMessage(f"ArcGIS license level: {arcpy.ProductInfo()}") # This can be removed totally. 

workspace_path, fc_name = os.path.split(in_fc)
arcpy.AddMessage("----- Checking {} -----".format(fc_name))

desc = arcpy.Describe(in_fc)
fc_name = desc.baseName
fds_path = os.path.dirname(desc.catalogPath)
 
 
#use on features with [MODIFICATION_TYPE] filled out 
 
def repair_geometry(in_fc):
    arcpy.AddMessage("Repairing geometry where MODIFICATION_TYPE is not null...")

    lyr = "fc_lyr"
    where_clause = "MODIFICATION_TYPE IS NOT NULL"

    arcpy.management.MakeFeatureLayer(in_fc, lyr, where_clause)
    arcpy.management.RepairGeometry(lyr)

    arcpy.AddMessage("Geometry repair complete")
     
def identify_very_small_polygons_or_line_segments(in_fc):
    desc = arcpy.Describe(in_fc)

    arcpy.AddMessage("Identifying small features where MODIFICATION_TYPE is not null...")

    fc_lyr = arcpy.CreateUniqueName("fc_lyr")
    where_clause = "MODIFICATION_TYPE IS NOT NULL"

    arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, where_clause)

    if desc.shapeType == "Polygon":
        arcpy.AddMessage("Checking for polygons with area <= 0.5 ha...")

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
            arcpy.AddWarning(f"There are {sliver_count} small polygon features (<= 0.5 ha).")
            arcpy.AddWarning(f"Review: temp_sliver_polygons_{fc_name}")
        else:
            arcpy.AddMessage("No sliver polygons found.")

        arcpy.management.Delete(temp_lyr)

    else:
        arcpy.AddMessage("Checking for short line segments (< 1 meter)...")

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
            arcpy.AddWarning(f"There are {short_segment_count} short line segments (< 1 meter).")
            arcpy.AddWarning(f"Review: temp_short_line_segments_{fc_name}")
        else:
            arcpy.AddMessage("No short line segments found.")

        arcpy.management.Delete(temp_lyr)

    arcpy.management.Delete(fc_lyr)

    arcpy.AddMessage("----- Check complete -----")
 
def check_for_multiple_identical_vertices(in_fc):
    arcpy.AddMessage("Checking for identical vertices (>= 4) in modified features...")
    arcpy.AddMessage("Features with 4+ identical vertices will not load to BCGW.")

    fc_lyr = arcpy.CreateUniqueName("fc_lyr")
    where_clause = "MODIFICATION_TYPE IS NOT NULL"

    arcpy.management.MakeFeatureLayer(in_fc, fc_lyr, where_clause)

    # Step 1: Copy features
    temp_fc1 = os.path.join(fds_path, f"temp_identical_vertex_check_Step1_{fc_name}")
    temp_fc2 = os.path.join(fds_path, f"temp_identical_vertex_check_Step2_{fc_name}")

    if arcpy.Exists(temp_fc1):
        arcpy.management.Delete(temp_fc1)

    arcpy.AddMessage(" - Creating temp dataset of modified features")
    arcpy.management.CopyFeatures(fc_lyr, temp_fc1)

    # Step 2: Convert to points
    arcpy.AddMessage(" - Converting features to vertices")
    arcpy.management.FeatureVerticesToPoints(temp_fc1, temp_fc2, "ALL")

    # Step 3: Add XY + fields
    arcpy.management.AddXY(temp_fc2)
    arcpy.management.AddField(temp_fc2, "CHECK", "TEXT", field_length=100)
    arcpy.management.AddField(temp_fc2, "FLAG", "TEXT")

    temp_lyr = arcpy.CreateUniqueName("temp_lyr")
    arcpy.management.MakeFeatureLayer(temp_fc2, temp_lyr)

    # Determine ID field
    if 'slrp' in fc_name:
        if 'boundary' in fc_name:
            feat_id_field = "STRGC_LAND_RSRCE_PLAN_ID"
        elif 'non' in fc_name:
            feat_id_field = "NON_LEGAL_FEAT_ID"
        else:
            feat_id_field = "LEGAL_FEAT_ID"
    elif 'landscape' in fc_name:
        feat_id_field = "LANDSCAPE_UNIT_ID"
    elif 'old_growth' in fc_name:
        if 'non' in fc_name:
            feat_id_field = "NON_LEGAL_OGMA_INTERNAL_ID"
        else:
            feat_id_field = "LEGAL_OGMA_INTERNAL_ID"
    else:
        raise ValueError("Could not determine feature ID field.")

    # Step 4: Calculate CHECK field
    calc_expr = f"!{feat_id_field}! + '_' + str(!POINT_X!) + '_' + str(!POINT_Y!)"
    arcpy.management.CalculateField(temp_lyr, "CHECK", calc_expr, "PYTHON3")

    # Step 5: Use modern cursor (FAST)
    arcpy.AddMessage(" - Analyzing vertex duplication")

    from collections import Counter

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
        arcpy.AddWarning("There are instances of 4+ identical vertices!")
        arcpy.AddWarning(f"Review: temp_identical_vertex_check_Step2_{fc_name}")
    else:
        arcpy.AddMessage("No duplicate vertices found.")

    # Cleanup
    arcpy.management.Delete(fc_lyr)
    arcpy.management.Delete(temp_lyr)

    arcpy.AddMessage("----- Vertex check complete -----")
 
 
def check_for_max_vertices(in_fc):
    arcpy.AddMessage("Checking vertex count for modified features...")
    arcpy.AddMessage("All features must have < 524,000 vertices for BCGW.")

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
        out_fc = os.path.join(fds_path, f"temp_{fc_name}_OVER_MAX_VERTICES")

        arcpy.conversion.FeatureClassToFeatureClass(fc_lyr, fds_path, f"temp_{fc_name}_OVER_MAX_VERTICES")

        arcpy.AddWarning(f"There are {over_vertex_limit_count} features over the vertex limit.")
        arcpy.AddWarning("Features must have fewer than 524,000 vertices.")
        arcpy.AddWarning(f"Review: temp_{fc_name}_OVER_MAX_VERTICES")

        arcpy.AddWarning("Possible solutions:")
        arcpy.AddWarning("- Use Simplify Polygon (<1m tolerance)")
        arcpy.AddWarning("- Split multipart polygons")
        arcpy.AddWarning("- Contact your Data Resource Manager")

    else:
        arcpy.AddMessage('All features are under the vertex limit ✔')

    # Cleanup
    arcpy.management.DeleteField(fc_lyr, "VxCount")
    arcpy.management.Delete(fc_lyr)

    arcpy.AddMessage("----- Vertex count check complete -----")