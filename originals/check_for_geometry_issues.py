import arcinfo
import arcpy, os, os.path

arcpy.env.overwriteOutput = True

in_fc = sys.argv[1]
##in_fc = r"\\spatialfiles3.bcgov\slrp\UpdateManagement\OldGrowthManagementAreas\CurrentUpdate\old_growth_management_area_bc_Update_20210426_RETURNED_20210518.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"

arcGIS_level = arcpy.ProductInfo()
print arcGIS_level
if arcGIS_level == "ArcView":
    arcpy.AddError("This tool needs an ArcEditor or ArcInfo license to run. Please switch licences and re-run the tool.")

    
fc_name_list = os.path.split(in_fc)
fc_name = fc_name_list[1]
fds_path = fc_name_list[0]

arcpy.AddMessage('`````````````````````````````````')
arcpy.AddMessage('CHECKING ' + fc_name)
arcpy.AddMessage('`````````````````````````````````')

desc = arcpy.Describe(in_fc)
 
 
 
#use on features with [MODIFICATION_TYPE] filled out 
 
def repair_geometry(in_fc):
    arcpy.AddMessage('Repairing geometry of all modified features (where MODIFICATION_TYPE is not null).')
    arcpy.MakeFeatureLayer_management(in_fc, 'fc_lyr', "\"MODIFICATION_TYPE\" is not null")
     
    arcpy.RepairGeometry_management('fc_lyr')
    arcpy.AddMessage('    - complete')
    arcpy.AddMessage('`````````````````````````````````')
     
def identify_very_small_polygons_or_line_segments(in_fc):
    desc = arcpy.Describe(in_fc)
     
    arcpy.MakeFeatureLayer_management(in_fc, 'fc_lyr', "\"MODIFICATION_TYPE\" is not null")
     
    if desc.shapeType == 'Polygon':
        arcpy.AddMessage(r'Identifying features (where MODIFICATION_TYPE is not null) that have areas of <= 0.5 ha.')
        arcpy.MultipartToSinglepart_management('fc_lyr', fds_path + "\\" + 'temp_sliver_polygons_' + fc_name)
        arcpy.MakeFeatureLayer_management(fds_path + "\\" + 'temp_sliver_polygons_' + fc_name, 'temp_lyr')
         
        geomField = desc.shapeFieldName
        areaFieldName = str(geomField) + "_Area"
        arcpy.SelectLayerByAttribute_management('temp_lyr', "NEW_SELECTION", "\"" + areaFieldName + "\" <= 5000")
        arcpy.SelectLayerByAttribute_management('temp_lyr', "SWITCH_SELECTION")
        arcpy.DeleteFeatures_management('temp_lyr')
        arcpy.SelectLayerByAttribute_management('temp_lyr', "CLEAR_SELECTION")
 
         
        sliver_count = int(str(arcpy.GetCount_management('temp_lyr')))
        if sliver_count > 0:
            arcpy.AddWarning('    There are ' + str(sliver_count) + ' modified features (or parts of modified features) with an area of < 0.1 ha.')
            arcpy.AddWarning('    A feature class named ' + 'temp_sliver_polygons_' + fc_name + ' has been added to your update fgdb so you can review these slivers.')
            arcpy.AddWarning('    Remove any sliver polygons from the data you are submitting if they are not valid.')
        arcpy.Delete_management('temp_lyr')
    else:
        arcpy.AddMessage(r'Identifying features (where MODIFICATION_TYPE is not null) that have lengths of < 10m.')
        arcpy.MakeFeatureLayer_management(in_fc, 'fc_lyr', "\"MODIFICATION_TYPE\" is not null")
         
        arcpy.MultipartToSinglepart_management('fc_lyr', fds_path + "\\" + 'temp_short_line_segments_' + fc_name)
        arcpy.MakeFeatureLayer_management(fds_path + "\\" + 'temp_short_line_segments_' + fc_name, 'temp_lyr')
 
        geomField = desc.shapeFieldName
        lengthFieldName = str(geomField) + "_Length"
        arcpy.SelectLayerByAttribute_management('temp_lyr', '')
         
        arcpy.SelectLayerByAttribute_management('temp_lyr', "NEW_SELECTION", "\"" + lengthFieldName + "\" <= 1")
        arcpy.SelectLayerByAttribute_management('temp_lyr', "SWITCH_SELECTION")
        arcpy.DeleteFeatures_management('temp_lyr')
        arcpy.SelectLayerByAttribute_management('temp_lyr', "CLEAR_SELECTION")
         
        short_segment_count = int(str(arcpy.GetCount_management('temp_lyr')))
        if sliver_count > 0:
            arcpy.AddWarning('    There are ' + str(short_segment_count) + ' modified features (or parts of modified features) with a length of < 1 meter.')
            arcpy.AddWarning('    Review the temp feature class named ' + 'temp_short_line_segments_' + fc_name + ' to review these short line segments.')
            arcpy.AddWarning('    Remove short line segments polygons from the data you are submitting if they are not valid.')
        arcpy.Delete_management('temp_lyr')
     
     
    arcpy.AddMessage('`````````````````````````````````')
 
def check_for_multiple_identical_vertices(in_fc):
    arcpy.AddMessage('Checking all modified features (where MODIFICATION_TYPE is not null) to see if there are any instances of 4 or more identical vertices in the same feature.')
    arcpy.AddMessage('Features with 4 or more identical vertices will not load to the BCGW.')
    arcpy.MakeFeatureLayer_management(in_fc, 'fc_lyr', "\"MODIFICATION_TYPE\" is not null")
     
    #export all modified features to a new shapefile - the feature classes have issues with non-nullable fields
    arcpy.AddMessage('    - Creating a temp dataset of only "modified" features.')
    if arcpy.Exists(fds_path + "\\" + 'temp_identical_vertex_check_Step1_' + fc_name):
        arcpy.Delete_management(fds_path + "\\" + 'temp_identical_vertex_check_Step1_' + fc_name)
    arcpy.CopyFeatures_management('fc_lyr', fds_path + "\\" + 'temp_identical_vertex_check_Step1_' + fc_name)
    arcpy.RefreshCatalog(fds_path)
    arcpy.AddMessage('    - Converting modified features to vertex points')
    arcpy.FeatureVerticesToPoints_management(fds_path + "\\" + 'temp_identical_vertex_check_Step1_' + fc_name, fds_path + "\\" + 'temp_identical_vertex_check_Step2_' + fc_name, "ALL")
    arcpy.AddMessage('    - Adding XY coordinates')
    arcpy.AddXY_management(fds_path + "\\" + 'temp_identical_vertex_check_Step2_' + fc_name)
    arcpy.AddField_management(fds_path + "\\" + 'temp_identical_vertex_check_Step2_' + fc_name, "CHECK", "TEXT", "", "100")
    arcpy.AddField_management(fds_path + "\\" + 'temp_identical_vertex_check_Step2_' + fc_name, "FLAG", "TEXT")
    arcpy.MakeFeatureLayer_management(fds_path + "\\" + 'temp_identical_vertex_check_Step2_' + fc_name, 'temp_lyr')
     
    arcpy.AddMessage('    - Checking coordinates to identify identical vertices (>=4 identical vertices from the same feature will be flagged)')
    if 'slrp' in fc_name:
        if 'boundary' in fc_name:
            feat_id_field = "STRGC_LAND_RSRCE_PLAN_ID"
        elif 'non' in fc_name:
            feat_id_field =  "NON_LEGAL_FEAT_ID"  
        else:
            feat_id_field =  "LEGAL_FEAT_ID"  
    if 'landscape' in fc_name:
        feat_id_field = "LANDSCAPE_UNIT_ID"
    if 'old_growth' in fc_name:
        if 'non' in fc_name:
            feat_id_field = "NON_LEGAL_OGMA_INTERNAL_ID"
        else:
            feat_id_field = "LEGAL_OGMA_INTERNAL_ID"
     
    calc_string =  'str(!' + feat_id_field + '!) + "_" + str(!POINT_X!) + "_" + str(!POINT_Y!)'
    arcpy.CalculateField_management('temp_lyr', "CHECK", calc_string, "PYTHON_9.3")
     
    rows = arcpy.SearchCursor('temp_lyr')
    point_coordinate_list = []
    for row in rows:
        point_coordinate_list.append(row.getValue("CHECK"))
    point_coordinate_list.sort()
      
    flagged_point_list = []
    for item in point_coordinate_list:
        count = point_coordinate_list.count(item)
        if count > 3:
            flagged_point_list.append(item)
    flagged_point_list.sort()
     
    for flagged_point in flagged_point_list:  
        select_statement = "\"CHECK\" = '" + flagged_point + "'"
        arcpy.SelectLayerByAttribute_management('temp_lyr', "NEW_SELECTION", select_statement)
        flag_count = str(arcpy.GetCount_management('temp_lyr'))

        arcpy.CalculateField_management('temp_lyr', "FLAG", '"' + flag_count + '"', "PYTHON_9.3" )
  
     
    arcpy.SelectLayerByAttribute_management('temp_lyr', "NEW_SELECTION", "\"FLAG\" is null")
    arcpy.DeleteFeatures_management('temp_lyr')
    point_count = int(str(arcpy.GetCount_management('temp_lyr')))
    if point_count > 0:
        arcpy.AddWarning('There are instances of 4 (or more) identical vertices in modified features!')
        arcpy.AddWarning('    A feature class named temp_identical_vertex_check_Step2_' + fc_name + ' has been added to your update fgdb.')
        arcpy.AddWarning('    This feature class contains the locations of the vertices that need to be resolved.')
     
    arcpy.AddMessage('`````````````````````````````````')
 
 
def check_for_max_vertices(in_fc):
    arcpy.AddMessage('Doing a vertex count of all modified features (where MODIFICATION_TYPE is not null).')
    arcpy.AddMessage('All modified features must have less than 524,000 vertices in order to load to the BCGW.')
    arcpy.MakeFeatureLayer_management(in_fc, 'fc_lyr', "\"MODIFICATION_TYPE\" is not null")
     
    arcpy.AddField_management('fc_lyr', "VxCount", "LONG")
    arcpy.CalculateField_management('fc_lyr', 'VxCount', "!shape!.pointcount", "PYTHON_9.3")
     
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"VxCount\" > 524000")
    over_vertex_limit_count = int(str(arcpy.GetCount_management('fc_lyr')))
     
    if over_vertex_limit_count > 0:
        arcpy.FeatureClassToFeatureClass_conversion('fc_lyr', fds_path, 'temp_' + fc_name + "_OVER_MAX_VERTICES")
        arcpy.AddWarning('    There are ' + str(over_vertex_limit_count) + ' "modified" features with a vertex count over 524000.')
        arcpy.AddWarning('    Features must have less than 524000 vertexes to load to the BCGW.')
        arcpy.AddWarning('    A feature class named temp_' + fc_name + '_OVER_MAX_VERTICES containing the offending features has been added to your update fgdb.')
        arcpy.AddWarning('')
        arcpy.AddWarning('    Possible solutions:')
        arcpy.AddWarning('        - use the "Simplify Polygon" tool to eliminate vertices that are very close together (<1 meter)')
        arcpy.AddWarning('        - split multi-part polygons into single-part (will require new PROVIDs or PROVID Part Numbers, plus new FEAT_IDs)')
        arcpy.AddWarning('        - contact your Data Resource Manager for advice.')
 
    else:
        arcpy.AddMessage('    All "modified" features have less than 524000 vertices - good work!')
     
    arcpy.DeleteField_management('fc_lyr', 'VxCount')
     
    arcpy.AddMessage('`````````````````````````````````')
 
if desc.shapeType != 'Point':
    repair_geometry(in_fc)
    identify_very_small_polygons_or_line_segments(in_fc)
    check_for_max_vertices(in_fc)
    check_for_multiple_identical_vertices(in_fc)
else:
    arcpy.AddWarning('Point datasets do not need to be run through this tool.')
    arcpy.AddMessage('`````````````````````````````````')