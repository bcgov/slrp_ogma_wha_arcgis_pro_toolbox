'''
Author: Carole Bjorkman
Purpose: This script compares the number of records in a published (BC Geographic Warehouse) dataset
            and a non-published (staging area) dataset.

Date: December 9, 2009

Arguments: argv[1] = boolean - compare legal & non-legal ogma count
           argv[2] = boolean - compare all slrp data counts
           argv[3] = boolean - compare landscape unit count

Outputs: None - on-screen display only

Dependencies: Must have an BCGW (BC Geographic Warehouse) database connection named as 'BCGW.sde'


History:
----------------------------------------------------------------------------------------------
Date: March 22, 2010
Author: C. Bjorkman
Modification: Changed so only 3 arguments - one for each geodatabase being tested
                New Arguments: argv[1] = boolean - compare ogma gdb load
                               argv[2] = boolean - compare landscape unit gdb load
                               argv[3] = boolean - compare slrp gdb load

              Changed to compare base LRDW load, plus all spatial views
-----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------
Date: November 19, 2014
Author: C. Mahood
Modification: Updated source/bcgw paths

-----------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------
Date: October 24, 2016
Author: C. Mahood
Modification: Updated staging area path to \\data.bcgov\data_staging_bcgw\land_use_plans_secure\slrp

-----------------------------------------------------------------------------------------------
Date: May 5th, 2020
Author: Lisa Forman
Modification: Changed over to using arcpy

-----------------------------------------------------------------------------------------------
'''

# Import system modules
import sys, string, os, os.path, arcpy, sys

# Create the Geoprocessor object
#gp = win32com.client.Dispatch("esriGeoprocessing.GpDispatch.1")
arcpy.overwriteOutput = True

##Script arguments...
argScriptName = sys.argv[0]

ogmaCompare = False
argOgmaCompare =sys.argv[1]
if argOgmaCompare =='true':
   ogmaCompare = True

luCompare = False
argLUCompare =sys.argv[2]
if argLUCompare =='true':
   luCompare = True

slrpCompare = False
argSlrpCompare =sys.argv[3]
if argSlrpCompare =='true':
   slrpCompare = True

#############################################################
##  TESTING BLOCK
#ogmaCompare = True
#luCompare = True
#slrpCompare = True
##############################################################

##############################################################
#Datasets to compare
##############################################################

staging_path = r"\\data.bcgov\data_staging_bcgw\land_use_plans_secure\slrp"
bcgw_path = r"Database Connections\BCGW.sde"

ogmaLegal_staging = staging_path + r"\old_growth_management_area_bc.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc_poly"
ogmaLegal_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_SP"
ogmaLegal_BCGW_current_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_CURRENT_SVW"
ogmaLegal_BCGW_all_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_ALL_SVW"

ogmaNonLegal_staging = staging_path + r"\old_growth_management_area_bc.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"
ogmaNonLegal_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_SP"
ogmaNonLegal_BCGW_current_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_CURRENT_SVW"
ogmaNonLegal_BCGW_all_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_ALL_SVW"

lu_staging = staging_path + r"\landscape_unit_bc.gdb\landscape_unit_albers\landscape_unit_poly"
lu_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_LANDSCAPE_UNIT_SP"
lu_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_LANDSCAPE_UNIT_SVW"

slrpBoundary_staging = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_boundary_bc_poly"
slrpBoundary_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_STRGC_LAND_RSRCE_PLAN_SP"
slrpBoundary_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_STRGC_LAND_RSRCE_PLAN_SVW"

legalPoly_staging_CAR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_CAR_poly"
legalPoly_staging_FSJ = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_FSJ_poly"
legalPoly_staging_KAM = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_KAM_poly"
legalPoly_staging_KOR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_KOR_poly"
legalPoly_staging_NAN = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_NAN_poly"
legalPoly_staging_PRG = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_PRG_poly"
legalPoly_staging_SKE = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_SKE_poly"
legalPoly_staging_SUR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_SUR_poly"
legalPoly_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POLY"
legalPoly_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POLY_SVW"

legalLine_staging_CAR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_CAR_line"
legalLine_staging_FSJ = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_FSJ_line"
legalLine_staging_KAM = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_KAM_line"
legalLine_staging_KOR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_KOR_line"
legalLine_staging_NAN = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_NAN_line"
legalLine_staging_PRG = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_PRG_line"
legalLine_staging_SKE = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_SKE_line"
legalLine_staging_SUR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_SUR_line"
legalLine_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_LINE"
legalLine_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_LINE_SVW"

legalPoint_staging_CAR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_CAR_point"
legalPoint_staging_FSJ = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_FSJ_point"
legalPoint_staging_KAM = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_KAM_point"
legalPoint_staging_KOR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_KOR_point"
legalPoint_staging_NAN = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_NAN_point"
legalPoint_staging_PRG = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_PRG_point"
legalPoint_staging_SKE = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_SKE_point"
legalPoint_staging_SUR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_legal_SUR_point"
legalPoint_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POINT"
legalPoint_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POINT_SVW"

nonlegalPoly_staging_CAR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_CAR_poly"
nonlegalPoly_staging_FSJ = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_FSJ_poly"
nonlegalPoly_staging_KAM = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_KAM_poly"
nonlegalPoly_staging_KOR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_KOR_poly"
nonlegalPoly_staging_NAN = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_NAN_poly"
nonlegalPoly_staging_PRG = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_PRG_poly"
nonlegalPoly_staging_SKE = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_SKE_poly"
nonlegalPoly_staging_SUR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_SUR_poly"
nonlegalPoly_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POLY"
nonlegalPoly_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POLY_SVW"

nonlegalLine_staging_CAR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_CAR_line"
nonlegalLine_staging_FSJ = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_FSJ_line"
nonlegalLine_staging_KAM = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_KAM_line"
nonlegalLine_staging_KOR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_KOR_line"
nonlegalLine_staging_NAN = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_NAN_line"
nonlegalLine_staging_PRG = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_PRG_line"
nonlegalLine_staging_SKE = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_SKE_line"
nonlegalLine_staging_SUR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_SUR_line"
nonlegalLine_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_LINE"
nonlegalLine_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_LINE_SVW"

nonlegalPoint_staging_CAR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_CAR_point"
nonlegalPoint_staging_FSJ = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_FSJ_point"
nonlegalPoint_staging_KAM = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_KAM_point"
nonlegalPoint_staging_KOR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_KOR_point"
nonlegalPoint_staging_NAN = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_NAN_point"
nonlegalPoint_staging_PRG = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_PRG_point"
nonlegalPoint_staging_SKE = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_SKE_point"
nonlegalPoint_staging_SUR = staging_path + r"\strategic_land_resource_plan_bc.gdb\strategic_land_resource_plan_albers\slrp_planning_feature_non_legal_SUR_point"
nonlegalPoint_BCGW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POINT"
nonlegalPoint_BCGW_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POINT_SVW"

################################################################
#Start dataset count comparison if comparison is set to 'True'
################################################################

#OGMA's
if ogmaCompare is False:
    arcpy.AddMessage("OGMA geodatabase not selected for comparison...")

if ogmaCompare is True:
    #check RMP_OGMA_LEGAL_SP
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_OGMA_LEGAL_SP")
    ogmaLegalStagingCount = arcpy.GetCount_management(ogmaLegal_staging)
    ogmaLegalBCGWCount = arcpy.GetCount_management(ogmaLegal_BCGW)
    ogmaLegalDifference = int(ogmaLegalStagingCount.getOutput(0)) - int(ogmaLegalBCGWCount.getOutput(0))
    if ogmaLegalDifference == 0:
        arcpy.AddMessage("Number of features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_OGMA_LEGAL_SP dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddMessage("There are the same number of Legal OGMA features in both the staging and RMP_OGMA_LEGAL_SP datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaLegalDifference > 0:
        arcpy.AddError("Number of features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_LEGAL_SP dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaLegalDifference) + " more Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaLegalDifference < 0:
        arcpy.AddError("Number of features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_LEGAL_SP dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaLegalDifference) + " less Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #check RMP_OGMA_LEGAL_ALL_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_OGMA_LEGAL_ALL_SVW")
    ogmaLegalStagingCount = arcpy.GetCount_management(ogmaLegal_staging)
    ogmaLegalBCGWCount = arcpy.GetCount_management(ogmaLegal_BCGW_all_SVW)
    ogmaLegalDifference = int(ogmaLegalStagingCount.getOutput(0)) - int(ogmaLegalBCGWCount.getOutput(0))
    if ogmaLegalDifference == 0:
        arcpy.AddMessage("Number of features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_OGMA_LEGAL_ALL_SVW dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddMessage("There are the same number of Legal OGMA features in both the staging and RMP_OGMA_LEGAL_ALL_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaLegalDifference > 0:
        arcpy.AddError("Number of features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_LEGAL_ALL_SVW dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaLegalDifference) + " more Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_ALL_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaLegalDifference < 0:
        arcpy.AddError("Number of features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_LEGAL_ALL_SVW dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaLegalDifference) + " less Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_ALL_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #check RMP_OGMA_LEGAL_CURRENT_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_OGMA_LEGAL_CURRENT_SVW")
    arcpy.MakeFeatureLayer_management(ogmaLegal_staging, "ogmaLegal_current_lyr", "\"STATUS\" = 0")
    ogmaLegalStagingCount = arcpy.GetCount_management("ogmaLegal_current_lyr")
    ogmaLegalBCGWCount = arcpy.GetCount_management(ogmaLegal_BCGW_current_SVW)
    ogmaLegalDifference = int(ogmaLegalStagingCount.getOutput(0)) - int(ogmaLegalBCGWCount.getOutput(0))
    if ogmaLegalDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_OGMA_LEGAL_CURRENT_SVW dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddMessage("There are the same number of current Legal OGMA features in both the staging and RMP_OGMA_LEGAL_CURRENT_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaLegalDifference > 0:
        arcpy.AddError("Number of current features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_LEGAL_CURRENT_SVW dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaLegalDifference) + " more current Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_CURRENT_SVW dataset")
        arcpy.AddMessage("")
    if ogmaLegalDifference < 0:
        arcpy.AddError("Number of current features in staging area Legal OGMA dataset: " + str(ogmaLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_LEGAL_CURRENT_SVW dataset: " + str(ogmaLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaLegalDifference) + " less current Legal OGMA features in the staging dataset than in the RMP_OGMA_LEGAL_CURRENT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #check RMP_OGMA_NON_LEGAL_SP
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_OGMA_NON_LEGAL_SP")
    ogmaNonLegalStagingCount = arcpy.GetCount_management(ogmaNonLegal_staging)
    ogmaNonLegalBCGWCount = arcpy.GetCount_management(ogmaNonLegal_BCGW)
    ogmaNonLegalDifference = int(ogmaNonLegalStagingCount.getOutput(0)) - int(ogmaNonLegalBCGWCount.getOutput(0))
    if ogmaNonLegalDifference == 0:
        arcpy.AddMessage("Number of features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_OGMA_NON_LEGAL_SP dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddMessage("There are the same number of Non-Legal OGMA features in both the staging and RMP_OGMA_NON_LEGAL_SP datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaNonLegalDifference > 0:
        arcpy.AddError("Number of features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_NON_LEGAL_SP dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaNonLegalDifference) + " more Non-Legal OGMA features in the staging dataset than in the RMP_OGMA_NON_LEGAL_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaNonLegalDifference < 0:
        arcpy.AddError("Number of features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_NON_LEGAL_SP dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaNonLegalDifference) + " less Non-Legal OGMA features in the staging dataset than in the RMP_OGMA_NON_LEGAL_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #check RMP_OGMA_NON_LEGAL_ALL_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_OGMA_NON_LEGAL_ALL_SVW")
    ogmaNonLegalStagingCount = arcpy.GetCount_management(ogmaNonLegal_staging)
    ogmaNonLegalBCGWCount = arcpy.GetCount_management(ogmaNonLegal_BCGW_all_SVW)
    ogmaNonLegalDifference = int(ogmaNonLegalStagingCount.getOutput(0)) - int(ogmaNonLegalBCGWCount.getOutput(0))
    if ogmaNonLegalDifference == 0:
        arcpy.AddMessage("Number of features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_OGMA_NON_LEGAL_ALL_SVW dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddMessage("There are the same number of Non-Legal OGMA features in both the staging and RMP_OGMA_NON_LEGAL_ALL_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaNonLegalDifference > 0:
        arcpy.AddError("Number of features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_NON_LEGAL_ALL_SVW dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaNonLegalDifference) + " more Non-Legal OGMA features in the staging dataset than in the RMP_OGMA_NON_LEGAL_ALL_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaNonLegalDifference < 0:
        arcpy.AddError("Number of features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_NON_LEGAL_ALL_SVW dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaNonLegalDifference) + " less Non-Legal OGMA features in the staging dataset than in the RMP_OGMA_NON_LEGAL_ALL_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #check RMP_OGMA_NON_LEGAL_CURRENT_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_OGMA_NON_LEGAL_CURRENT_SVW")
    arcpy.MakeFeatureLayer_management(ogmaNonLegal_staging, "ogmaNonLegal_current_lyr", "\"STATUS\" = 0")
    ogmaNonLegalStagingCount = arcpy.GetCount_management("ogmaNonLegal_current_lyr")
    ogmaNonLegalBCGWCount = arcpy.GetCount_management(ogmaNonLegal_BCGW_current_SVW)
    ogmaNonLegalDifference = int(ogmaNonLegalStagingCount.getOutput(0)) - int(ogmaNonLegalBCGWCount.getOutput(0))
    if ogmaNonLegalDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_OGMA_NON_LEGAL_CURRENT_SVW dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddMessage("There are the same number of current Non-Legal OGMA features in both the staging and RMP_OGMA_NON_LEGAL_CURRENT_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaNonLegalDifference > 0:
        arcpy.AddError("Number of current features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_NON_LEGAL_CURRENT_SVW dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaNonLegalDifference) + " more current Non-Legal OGMA features in the staging dataset than in the RMP_OGMA_NON_LEGAL_CURRENT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if ogmaNonLegalDifference < 0:
        arcpy.AddError("Number of current features in staging area Non-Legal OGMA dataset: " + str(ogmaNonLegalStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_OGMA_NON_LEGAL_CURRENT_SVW dataset: " + str(ogmaNonLegalBCGWCount))
        arcpy.AddError("There are " + str(ogmaNonLegalDifference) + " less current Non-Legal OGMA features in the staging dataset than in the RMP_OGMA_NON_LEGAL_CURRENT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")



#Landscape Units
if luCompare is False:
    arcpy.AddMessage("Landscape Unit geodatabase not selected for comparison...")

if luCompare is True:
    #Check RMP_LANDSCAPE_UNIT_SP
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_LANDSCAPE_UNIT_SP")
    luStagingCount = arcpy.GetCount_management(lu_staging)
    luBCGWCount = arcpy.GetCount_management(lu_BCGW)
    luDifference = int(luStagingCount.getOutput(0))- int(luBCGWCount.getOutput(0))
    if luDifference == 0:
        arcpy.AddMessage("Number of features in staging area Landscape Unit dataset: " + str(luStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_LANDSCAPE_UNIT_SP dataset: " + str(luBCGWCount))
        arcpy.AddMessage("There are the same number of Landscape Unit features in both the staging and RMP_LANDSCAPE_UNIT_SP datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if luDifference > 0:
        arcpy.AddError("Number of features in staging area Landscape Unit dataset: " + str(luStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_LANDSCAPE_UNIT_SP dataset: " + str(luBCGWCount))
        arcpy.AddError("There are " + str(luDifference) + " more Landscape Unit features in the staging dataset than in the RMP_LANDSCAPE_UNIT_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if luDifference < 0:
        arcpy.AddError("Number of features in staging area Landscape Unit dataset: " + str(luStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_LANDSCAPE_UNIT_SP dataset: " + str(luBCGWCount))
        arcpy.AddError("There are " + str(luDifference) + " less Landscape Unit features in the staging dataset than in the RMP_LANDSCAPE_UNIT_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_LANDSCAPE_UNIT_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_LANDSCAPE_UNIT_SVW")
    arcpy.MakeFeatureLayer_management(lu_staging, "lu_current_lyr", "\"STATUS\" in (0,1)")
    luStagingCount = arcpy.GetCount_management("lu_current_lyr")
    luBCGWCount = arcpy.GetCount_management(lu_BCGW_SVW)
    luDifference = int(luStagingCount.getOutput(0))- int(luBCGWCount.getOutput(0))
    if luDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Landscape Unit dataset: " + str(luStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_LANDSCAPE_UNIT_SVW dataset: " + str(luBCGWCount))
        arcpy.AddMessage("There are the same number of current Landscape Unit features in both the staging and RMP_LANDSCAPE_UNIT_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if luDifference > 0:
        arcpy.AddError("Number of current features in staging area Landscape Unit dataset: " + str(luStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_LANDSCAPE_UNIT_SVW dataset: " + str(luBCGWCount))
        arcpy.AddError("There are " + str(luDifference) + " more current Landscape Unit features in the staging dataset than in the RMP_LANDSCAPE_UNIT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if luDifference < 0:
        arcpy.AddError("Number of current features in staging area Landscape Unit dataset: " + str(luStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_LANDSCAPE_UNIT_SVW dataset: " + str(luBCGWCount))
        arcpy.AddError("There are " + str(luDifference) + " less current Landscape Unit features in the staging dataset than in the RMP_LANDSCAPE_UNIT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")


#SLRP Boundaries
if slrpCompare is False:
    arcpy.AddMessage("Strategic Land Resource Plan geodatabase not selected for comparison...")

if slrpCompare is True:
    #check RMP_STRGC_LAND_RSRCE_PLAN_SP
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_STRGC_LAND_RSRCE_PLAN_SP")
    slrpStagingCount = arcpy.GetCount_management(slrpBoundary_staging)
    slrpBCGWCount = arcpy.GetCount_management(slrpBoundary_BCGW)
    slrpDifference = int(slrpStagingCount.getOutput(0)) - int(slrpBCGWCount.getOutput(0))
    if slrpDifference == 0:
        arcpy.AddMessage("Number of features in staging area Strategic Land Use Plan Boundaries dataset: " + str(slrpStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_STRGC_LAND_RSRCE_PLAN_SP dataset: " + str(slrpBCGWCount))
        arcpy.AddMessage("There are the same number of Strategic Land Use Plan Boundaries features in both the staging and RMP_STRGC_LAND_RSRCE_PLAN_SP datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if slrpDifference > 0:
        arcpy.AddError("Number of features in staging area Strategic Land Use Plan Boundaries dataset: " + str(slrpStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_STRGC_LAND_RSRCE_PLAN_SP dataset: " + str(slrpBCGWCount))
        arcpy.AddError("There are " + str(slrpDifference) + " more Strategic Land Use Plan Boundaries features in the staging dataset than in the RMP_STRGC_LAND_RSRCE_PLAN_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if slrpDifference < 0:
        arcpy.AddError("Number of features in staging area Strategic Land Use Plan Boundaries dataset: " + str(slrpStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_STRGC_LAND_RSRCE_PLAN_SP dataset: " + str(slrpBCGWCount))
        arcpy.AddError("There are " + str(slrpDifference) + " less Strategic Land Use Plan Boundaries features in the staging dataset than in the RMP_STRGC_LAND_RSRCE_PLAN_SP dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #check RMP_STRGC_LAND_RSRCE_PLAN_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_STRGC_LAND_RSRCE_PLAN_SVW")
    arcpy.MakeFeatureLayer_management(slrpBoundary_staging, "slrpBoundary_current_lyr", "\"STATUS\" = 0")
    slrpStagingCount = arcpy.GetCount_management("slrpBoundary_current_lyr")
    slrpBCGWCount = arcpy.GetCount_management(slrpBoundary_BCGW_SVW)
    slrpDifference = int(slrpStagingCount.getOutput(0)) - int(slrpBCGWCount.getOutput(0))
    if slrpDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Strategic Land Use Plan Boundaries dataset: " + str(slrpStagingCount))
        arcpy.AddMessage("Number of features in BCGW RMP_STRGC_LAND_RSRCE_PLAN_SVW dataset: " + str(slrpBCGWCount))
        arcpy.AddMessage("There are the same number of current Strategic Land Use Plan Boundaries features in both the staging and RMP_STRGC_LAND_RSRCE_PLAN_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if slrpDifference > 0:
        arcpy.AddError("Number of current features in staging area Strategic Land Use Plan Boundaries dataset: " + str(slrpStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_STRGC_LAND_RSRCE_PLAN_SVW dataset: " + str(slrpBCGWCount))
        arcpy.AddError("There are " + str(slrpDifference) + " more current Strategic Land Use Plan Boundaries features in the staging dataset than in the RMP_STRGC_LAND_RSRCE_PLAN_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if slrpDifference < 0:
        arcpy.AddError("Number of current features in staging area Strategic Land Use Plan Boundaries dataset: " + str(slrpStagingCount))
        arcpy.AddError("Number of features in BCGW RMP_STRGC_LAND_RSRCE_PLAN_SVW dataset: " + str(slrpBCGWCount))
        arcpy.AddError("There are " + str(slrpDifference) + " less current Strategic Land Use Plan Boundaries features in the staging dataset than in the RMP_STRGC_LAND_RSRCE_PLAN_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_LEGAL_POLY
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POLY")
    legalPolyCARStagingCount = int(arcpy.GetCount_management(legalPoly_staging_CAR).getOutput(0))
    legalPolyFSJStagingCount = int(arcpy.GetCount_management(legalPoly_staging_FSJ).getOutput(0))
    legalPolyKAMStagingCount = int(arcpy.GetCount_management(legalPoly_staging_KAM).getOutput(0))
    legalPolyKORStagingCount = int(arcpy.GetCount_management(legalPoly_staging_KOR).getOutput(0))
    legalPolyNANStagingCount = int(arcpy.GetCount_management(legalPoly_staging_NAN).getOutput(0))
    legalPolyPRGStagingCount = int(arcpy.GetCount_management(legalPoly_staging_PRG).getOutput(0))
    legalPolySKEStagingCount = int(arcpy.GetCount_management(legalPoly_staging_SKE).getOutput(0))
    legalPolySURStagingCount = int(arcpy.GetCount_management(legalPoly_staging_SUR).getOutput(0))

    legalPolyStagingCountTotal = legalPolyCARStagingCount + legalPolyFSJStagingCount + legalPolyKAMStagingCount + legalPolyKORStagingCount + legalPolyNANStagingCount + legalPolyPRGStagingCount + legalPolySKEStagingCount + legalPolySURStagingCount
    legalPolyBCGWCount = arcpy.GetCount_management(legalPoly_BCGW)
    legalPolyDifference = legalPolyStagingCountTotal - int(legalPolyBCGWCount.getOutput(0))
    if legalPolyDifference == 0:
        arcpy.AddMessage("Number of features in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_LEGAL_POLY dataset: " + str(legalPolyBCGWCount))
        arcpy.AddMessage("There are the same number of Legal Planning Objectives (Polygon) features in both the staging and RMP_PLAN_LEGAL_POLY datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPolyDifference > 0:
        arcpy.AddError("Number of features in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POLY dataset: " + str(legalPolyBCGWCount))
        arcpy.AddError("There are " + str(legalPolyDifference) + " more Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_LEGAL_POLY dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPolyDifference < 0:
        arcpy.AddError("Number of features in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POLY dataset: " + str(legalPolyBCGWCount))
        arcpy.AddError("There are " + str(legalPolyDifference) + " less Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_LEGAL_POLY dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_LEGAL_POLY_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POLY_SVW")
    arcpy.MakeFeatureLayer_management(legalPoly_staging_CAR, "legalPolyCAR_staging_current_lyr", "\"STATUS\" = 0")
    legalPolyCARStagingCount = int(arcpy.GetCount_management("legalPolyCAR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_FSJ, "legalPolyFSJ_staging_current_lyr", "\"STATUS\" = 0")
    legalPolyFSJStagingCount = int(arcpy.GetCount_management("legalPolyFSJ_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_KAM, "legalPolyKAM_staging_current_lyr", "\"STATUS\" = 0")
    legalPolyKAMStagingCount = int(arcpy.GetCount_management("legalPolyKAM_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_KOR, "legalPolyKOR_staging_current_lyr", "\"STATUS\" = 0")
    legalPolyKORStagingCount = int(arcpy.GetCount_management("legalPolyKOR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_NAN, "legalPolyNAN_staging_current_lyr", "\"STATUS\" = 0")
    legalPolyNANStagingCount = int(arcpy.GetCount_management("legalPolyNAN_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_PRG, "legalPolyPRG_staging_current_lyr", "\"STATUS\" = 0")
    legalPolyPRGStagingCount = int(arcpy.GetCount_management("legalPolyPRG_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_SKE, "legalPolySKE_staging_current_lyr", "\"STATUS\" = 0")
    legalPolySKEStagingCount = int(arcpy.GetCount_management("legalPolySKE_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoly_staging_SUR, "legalPolySUR_staging_current_lyr", "\"STATUS\" = 0")
    legalPolySURStagingCount = int(arcpy.GetCount_management("legalPolySUR_staging_current_lyr").getOutput(0))

    legalPolyStagingCountTotal = legalPolyCARStagingCount + legalPolyFSJStagingCount + legalPolyKAMStagingCount + legalPolyKORStagingCount + legalPolyNANStagingCount + legalPolyPRGStagingCount + legalPolySKEStagingCount + legalPolySURStagingCount
    legalPolyBCGWCount = arcpy.GetCount_management(legalPoly_BCGW_SVW)
    legalPolyDifference = legalPolyStagingCountTotal - int(legalPolyBCGWCount.getOutput(0))
    if legalPolyDifference == 0:
        arcpy.AddMessage("Number of current eatures in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_LEGAL_POLY_SVW dataset: " + str(legalPolyBCGWCount))
        arcpy.AddMessage("There are the same number of current Legal Planning Objectives (Polygon) features in both the staging and RMP_PLAN_LEGAL_POLY_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPolyDifference > 0:
        arcpy.AddError("Number of current features in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POLY_SVW dataset: " + str(legalPolyBCGWCount))
        arcpy.AddError("There are " + str(legalPolyDifference) + " more current Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_LEGAL_POLY_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPolyDifference < 0:
        arcpy.AddError("Number of current features in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POLY_SVW dataset: " + str(legalPolyBCGWCount))
        arcpy.AddError("There are " + str(legalPolyDifference) + " less current Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_LEGAL_POLY_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")


    #Check RMP_PLAN_LEGAL_LINE
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_LEGAL_LINE")
    legalLineCARStagingCount = int(arcpy.GetCount_management(legalLine_staging_CAR).getOutput(0))
    legalLineFSJStagingCount = int(arcpy.GetCount_management(legalLine_staging_FSJ).getOutput(0))
    legalLineKAMStagingCount = int(arcpy.GetCount_management(legalLine_staging_KAM).getOutput(0))
    legalLineKORStagingCount = int(arcpy.GetCount_management(legalLine_staging_KOR).getOutput(0))
    legalLineNANStagingCount = int(arcpy.GetCount_management(legalLine_staging_NAN).getOutput(0))
    legalLinePRGStagingCount = int(arcpy.GetCount_management(legalLine_staging_PRG).getOutput(0))
    legalLineSKEStagingCount = int(arcpy.GetCount_management(legalLine_staging_SKE).getOutput(0))
    legalLineSURStagingCount = int(arcpy.GetCount_management(legalLine_staging_SUR).getOutput(0))

    legalLineStagingCountTotal = legalLineCARStagingCount + legalLineFSJStagingCount + legalLineKAMStagingCount + legalLineKORStagingCount + legalLineNANStagingCount + legalLinePRGStagingCount + legalLineSKEStagingCount + legalLineSURStagingCount
    legalLineBCGWCount = arcpy.GetCount_management(legalLine_BCGW)
    legalLineDifference = legalLineStagingCountTotal - int(legalLineBCGWCount.getOutput(0))
    if legalLineDifference == 0:
        arcpy.AddMessage("Number of features in staging area Legal Planning Objectives (Line) dataset: " + str(legalLineStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_LEGAL_LINE dataset: " + str(legalLineBCGWCount))
        arcpy.AddMessage("There are the same number of Legal Planning Objectives (Line) features in both the staging and RMP_PLAN_LEGAL_LINE datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalLineDifference > 0:
        arcpy.AddError("Number of features in staging area Legal Planning Objectives (Line) dataset: " + str(legalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_LINE) dataset: " + str(legalLineBCGWCount))
        arcpy.AddError("There are " + str(legalLineDifference) + " more Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_LEGAL_LINE dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalLineDifference < 0:
        arcpy.AddError("Number of features in staging area Legal Planning Objectives (Line) dataset: " + str(legalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_LINE dataset: " + str(legalLineBCGWCount))
        arcpy.AddError("There are " + str(legalLineDifference) + " less Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_LEGAL_LINE dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_LEGAL_LINE_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_LEGAL_LINE_SVW")
    arcpy.MakeFeatureLayer_management(legalLine_staging_CAR, "legalLineCAR_staging_current_lyr", "\"STATUS\" = 0")
    legalLineCARStagingCount = int(arcpy.GetCount_management("legalLineCAR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_FSJ, "legalLineFSJ_staging_current_lyr", "\"STATUS\" = 0")
    legalLineFSJStagingCount = int(arcpy.GetCount_management("legalLineFSJ_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_KAM, "legalLineKAM_staging_current_lyr", "\"STATUS\" = 0")
    legalLineKAMStagingCount = int(arcpy.GetCount_management("legalLineKAM_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_KOR, "legalLineKOR_staging_current_lyr", "\"STATUS\" = 0")
    legalLineKORStagingCount = int(arcpy.GetCount_management("legalLineKOR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_NAN, "legalLineNAN_staging_current_lyr", "\"STATUS\" = 0")
    legalLineNANStagingCount = int(arcpy.GetCount_management("legalLineNAN_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_PRG, "legalLinePRG_staging_current_lyr", "\"STATUS\" = 0")
    legalLinePRGStagingCount = int(arcpy.GetCount_management("legalLinePRG_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_SKE, "legalLineSKE_staging_current_lyr", "\"STATUS\" = 0")
    legalLineSKEStagingCount = int(arcpy.GetCount_management("legalLineSKE_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalLine_staging_SUR, "legalLineSUR_staging_current_lyr", "\"STATUS\" = 0")
    legalLineSURStagingCount = int(arcpy.GetCount_management("legalLineSUR_staging_current_lyr").getOutput(0))

    legalLineStagingCountTotal = legalLineCARStagingCount + legalLineFSJStagingCount + legalLineKAMStagingCount + legalLineKORStagingCount + legalLineNANStagingCount + legalLinePRGStagingCount + legalLineSKEStagingCount + legalLineSURStagingCount
    legalLineBCGWCount = arcpy.GetCount_management(legalLine_BCGW_SVW)
    legalLineDifference = legalLineStagingCountTotal - int(legalLineBCGWCount.getOutput(0))
    if legalLineDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Legal Planning Objectives (Line) dataset: " + str(legalLineStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_LEGAL_LINE_SVW dataset: " + str(legalLineBCGWCount))
        arcpy.AddMessage("There are the same number of current Legal Planning Objectives (Line) features in both the staging and RMP_PLAN_LEGAL_LINE_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalLineDifference > 0:
        arcpy.AddError("Number of current features in staging area Legal Planning Objectives (Line) dataset: " + str(legalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_LINE_SVW dataset: " + str(legalLineBCGWCount))
        arcpy.AddError("There are " + str(legalLineDifference) + " more current Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_LEGAL_LINE_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalLineDifference < 0:
        arcpy.AddError("Number of current features in staging area Legal Planning Objectives (Line) dataset: " + str(legalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_LINE_SVW dataset: " + str(legalLineBCGWCount))
        arcpy.AddError("There are " + str(legalLineDifference) + " less current Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_LEGAL_LINE_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_LEGAL_POINT
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POINT")
    legalPointCARStagingCount = int(arcpy.GetCount_management(legalPoint_staging_CAR).getOutput(0))
    legalPointFSJStagingCount = int(arcpy.GetCount_management(legalPoint_staging_FSJ).getOutput(0))
    legalPointKAMStagingCount = int(arcpy.GetCount_management(legalPoint_staging_KAM).getOutput(0))
    legalPointKORStagingCount = int(arcpy.GetCount_management(legalPoint_staging_KOR).getOutput(0))
    legalPointNANStagingCount = int(arcpy.GetCount_management(legalPoint_staging_NAN).getOutput(0))
    legalPointPRGStagingCount = int(arcpy.GetCount_management(legalPoint_staging_PRG).getOutput(0))
    legalPointSKEStagingCount = int(arcpy.GetCount_management(legalPoint_staging_SKE).getOutput(0))
    legalPointSURStagingCount = int(arcpy.GetCount_management(legalPoint_staging_SUR).getOutput(0))

    legalPointStagingCountTotal = legalPointCARStagingCount + legalPointFSJStagingCount + legalPointKAMStagingCount + legalPointKORStagingCount + legalPointNANStagingCount + legalPointPRGStagingCount + legalPointSKEStagingCount + legalPointSURStagingCount
    print str(legalPointStagingCountTotal)
    legalPointBCGWCount = arcpy.GetCount_management(legalPoint_BCGW)
    legalPointDifference = legalPointStagingCountTotal - int(legalPointBCGWCount.getOutput(0))
    if legalPointDifference == 0:
        arcpy.AddMessage("Number of features in staging area Legal Planning Objectives (Point) dataset: " + str(legalPointStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_LEGAL_POINT dataset: " + str(legalPointBCGWCount))
        arcpy.AddMessage("There are the same number of Legal Planning Objectives (Point) features in both the staging and RMP_PLAN_LEGAL_POINT datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPointDifference > 0:
        arcpy.AddError("Number of features in staging area Legal Planning Objectives (Point) dataset: " + str(legalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POINT dataset: " + str(legalPointBCGWCount))
        arcpy.AddError("There are " + str(legalPointDifference) + " more Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_LEGAL_POINT dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPointDifference < 0:
        arcpy.AddError("Number of features in staging area Legal Planning Objectives (Point) dataset: " + str(legalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POINT dataset: " + str(legalPointBCGWCount))
        arcpy.AddError("There are " + str(legalPointDifference) + " less Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_LEGAL_POINT dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_LEGAL_POINT_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POINT_SVW")
    arcpy.MakeFeatureLayer_management(legalPoint_staging_CAR, "legalPointCAR_staging_current_lyr", "\"STATUS\" = 0")
    legalPointCARStagingCount = int(arcpy.GetCount_management("legalPointCAR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_FSJ, "legalPointFSJ_staging_current_lyr", "\"STATUS\" = 0")
    legalPointFSJStagingCount = int(arcpy.GetCount_management("legalPointFSJ_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_KAM, "legalPointKAM_staging_current_lyr", "\"STATUS\" = 0")
    legalPointKAMStagingCount = int(arcpy.GetCount_management("legalPointKAM_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_KOR, "legalPointKOR_staging_current_lyr", "\"STATUS\" = 0")
    legalPointKORStagingCount = int(arcpy.GetCount_management("legalPointKOR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_NAN, "legalPointNAN_staging_current_lyr", "\"STATUS\" = 0")
    legalPointNANStagingCount = int(arcpy.GetCount_management("legalPointNAN_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_PRG, "legalPointPRG_staging_current_lyr", "\"STATUS\" = 0")
    legalPointPRGStagingCount = int(arcpy.GetCount_management("legalPointPRG_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_SKE, "legalPointSKE_staging_current_lyr", "\"STATUS\" = 0")
    legalPointSKEStagingCount = int(arcpy.GetCount_management("legalPointSKE_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(legalPoint_staging_SUR, "legalPointSUR_staging_current_lyr", "\"STATUS\" = 0")
    legalPointSURStagingCount = int(arcpy.GetCount_management("legalPointSUR_staging_current_lyr").getOutput(0))

    legalPointStagingCountTotal = legalPointCARStagingCount + legalPointFSJStagingCount + legalPointKAMStagingCount + legalPointKORStagingCount + legalPointNANStagingCount + legalPointPRGStagingCount + legalPointSKEStagingCount + legalPointSURStagingCount
    print str(legalPointStagingCountTotal)
    legalPointBCGWCount = arcpy.GetCount_management(legalPoint_BCGW_SVW)
    legalPointDifference = legalPointStagingCountTotal - int(legalPointBCGWCount.getOutput(0))
    if legalPointDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Legal Planning Objectives (Point) dataset: " + str(legalPointStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_LEGAL_POINT_SVW dataset: " + str(legalPointBCGWCount))
        arcpy.AddMessage("There are the same number of current Legal Planning Objectives (Point) features in both the staging and RMP_PLAN_LEGAL_POINT_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPointDifference > 0:
        arcpy.AddError("Number of current features in staging area Legal Planning Objectives (Point) dataset: " + str(legalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POINT_SVW dataset: " + str(legalPointBCGWCount))
        arcpy.AddError("There are " + str(legalPointDifference) + " more current Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_LEGAL_POINT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if legalPointDifference < 0:
        arcpy.AddError("Number of current features in staging area Legal Planning Objectives (Point) dataset: " + str(legalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_LEGAL_POINT_SVW dataset: " + str(legalPointBCGWCount))
        arcpy.AddError("There are " + str(legalPointDifference) + " less current Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_LEGAL_POINT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")


    #Check RMP_PLAN_NON_LEGAL_POLY
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POLY")
    nonlegalPolyCARStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_CAR).getOutput(0))
    nonlegalPolyFSJStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_FSJ).getOutput(0))
    nonlegalPolyKAMStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_KAM).getOutput(0))
    nonlegalPolyKORStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_KOR).getOutput(0))
    nonlegalPolyNANStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_NAN).getOutput(0))
    nonlegalPolyPRGStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_PRG).getOutput(0))
    nonlegalPolySKEStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_SKE).getOutput(0))
    nonlegalPolySURStagingCount = int(arcpy.GetCount_management(nonlegalPoly_staging_SUR).getOutput(0))

    nonlegalPolyStagingCountTotal = nonlegalPolyCARStagingCount + nonlegalPolyFSJStagingCount + nonlegalPolyKAMStagingCount + nonlegalPolyKORStagingCount + nonlegalPolyNANStagingCount + nonlegalPolyPRGStagingCount + nonlegalPolySKEStagingCount + nonlegalPolySURStagingCount
    nonlegalPolyBCGWCount = arcpy.GetCount_management(nonlegalPoly_BCGW)
    nonlegalPolyDifference = nonlegalPolyStagingCountTotal - int(nonlegalPolyBCGWCount.getOutput(0))
    if nonlegalPolyDifference == 0:
        arcpy.AddMessage("Number of features in staging area Non Legal Planning Objectives (Polygon) dataset: " + str(nonlegalPolyStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_NON_LEGAL_POLY dataset: " + str(nonlegalPolyBCGWCount))
        arcpy.AddMessage("There are the same number of Non Legal Planning Objectives (Polygon) features in both the staging and RMP_PLAN_NON_LEGAL_POLY datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPolyDifference > 0:
        arcpy.AddError("Number of features in staging area Non Legal Planning Objectives (Polygon) dataset: " + str(nonlegalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POLY dataset: " + str(nonlegalPolyBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPolyDifference) + " more Non Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POLY dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPolyDifference < 0:
        arcpy.AddError("Number of features in staging area Non Legal Planning Objectives (Polygon) dataset: " + str(nonlegalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POLY dataset: " + str(nonlegalPolyBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPolyDifference) + " less Non Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POLY dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")


    #Check RMP_PLAN_NON_LEGAL_POLY_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POLY_SVW")
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_CAR, "nonlegalPolyCAR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolyCARStagingCount = int(arcpy.GetCount_management("nonlegalPolyCAR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_FSJ, "nonlegalPolyFSJ_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolyFSJStagingCount = int(arcpy.GetCount_management("nonlegalPolyFSJ_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_KAM, "nonlegalPolyKAM_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolyKAMStagingCount = int(arcpy.GetCount_management("nonlegalPolyKAM_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_KOR, "nonlegalPolyKOR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolyKORStagingCount = int(arcpy.GetCount_management("nonlegalPolyKOR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_NAN, "nonlegalPolyNAN_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolyNANStagingCount = int(arcpy.GetCount_management("nonlegalPolyNAN_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_PRG, "nonlegalPolyPRG_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolyPRGStagingCount = int(arcpy.GetCount_management("nonlegalPolyPRG_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_SKE, "nonlegalPolySKE_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolySKEStagingCount = int(arcpy.GetCount_management("nonlegalPolySKE_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoly_staging_SUR, "nonlegalPolySUR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPolySURStagingCount = int(arcpy.GetCount_management("nonlegalPolySUR_staging_current_lyr").getOutput(0))

    nonlegalPolyStagingCountTotal = nonlegalPolyCARStagingCount + nonlegalPolyFSJStagingCount + nonlegalPolyKAMStagingCount + nonlegalPolyKORStagingCount + nonlegalPolyNANStagingCount + nonlegalPolyPRGStagingCount + nonlegalPolySKEStagingCount + nonlegalPolySURStagingCount
    nonlegalPolyBCGWCount = arcpy.GetCount_management(nonlegalPoly_BCGW_SVW)
    nonlegalPolyDifference = nonlegalPolyStagingCountTotal - int(nonlegalPolyBCGWCount.getOutput(0))
    if nonlegalPolyDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Non Legal Planning Objectives (Polygon) dataset: " + str(nonlegalPolyStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_NON_LEGAL_POLY_SVW dataset: " + str(nonlegalPolyBCGWCount))
        arcpy.AddMessage("There are the same number of current Non Legal Planning Objectives (Polygon) features in both the staging and RMP_PLAN_NON_LEGAL_POLY_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPolyDifference > 0:
        arcpy.AddError("Number of current features in staging area Non Legal Planning Objectives (Polygon) dataset: " + str(nonlegalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POLY_SVW dataset: " + str(nonlegalPolyBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPolyDifference) + " more current Non Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POLY_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPolyDifference < 0:
        arcpy.AddError("Number of current features in staging area Non Legal Planning Objectives (Polygon) dataset: " + str(nonlegalPolyStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POLY_SVW dataset: " + str(nonlegalPolyBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPolyDifference) + " less current Non Legal Planning Objectives (Polygon) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POLY_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_NON_LEGAL_LINE
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_LINE")
    nonlegalLineCARStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_CAR).getOutput(0))
    nonlegalLineFSJStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_FSJ).getOutput(0))
    nonlegalLineKAMStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_KAM).getOutput(0))
    nonlegalLineKORStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_KOR).getOutput(0))
    nonlegalLineNANStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_NAN).getOutput(0))
    nonlegalLinePRGStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_PRG).getOutput(0))
    nonlegalLineSKEStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_SKE).getOutput(0))
    nonlegalLineSURStagingCount = int(arcpy.GetCount_management(nonlegalLine_staging_SUR).getOutput(0))

    nonlegalLineStagingCountTotal = nonlegalLineCARStagingCount + nonlegalLineFSJStagingCount + nonlegalLineKAMStagingCount + nonlegalLineKORStagingCount + nonlegalLineNANStagingCount + nonlegalLinePRGStagingCount + nonlegalLineSKEStagingCount + nonlegalLineSURStagingCount
    nonlegalLineBCGWCount = arcpy.GetCount_management(nonlegalLine_BCGW)
    nonlegalLineDifference = nonlegalLineStagingCountTotal - int(nonlegalLineBCGWCount.getOutput(0))
    if nonlegalLineDifference == 0:
        arcpy.AddMessage("Number of features in staging area Non Legal Planning Objectives (Line) dataset: " + str(nonlegalLineStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_NON_LEGAL_LINE dataset: " + str(nonlegalLineBCGWCount))
        arcpy.AddMessage("There are the same number of Non Legal Planning Objectives (Line) features in both the staging and RMP_PLAN_NON_LEGAL_LINE datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalLineDifference > 0:
        arcpy.AddError("Number of features in staging area Non Legal Planning Objectives (Line) dataset: " + str(nonlegalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_LINE dataset: " + str(nonlegalLineBCGWCount))
        arcpy.AddError("There are " + str(nonlegalLineDifference) + " more Non Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_LINE dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalLineDifference < 0:
        arcpy.AddError("Number of features in staging area Non Legal Planning Objectives (Line) dataset: " + str(nonlegalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_LINE dataset: " + str(nonlegalLineBCGWCount))
        arcpy.AddError("There are " + str(nonlegalLineDifference) + " less Non Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_LINE dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_NON_LEGAL_LINE_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_LINE_SVW")
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_CAR, "nonlegalLineCAR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineCARStagingCount = int(arcpy.GetCount_management("nonlegalLineCAR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_FSJ, "nonlegalLineFSJ_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineFSJStagingCount = int(arcpy.GetCount_management("nonlegalLineFSJ_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_KAM, "nonlegalLineKAM_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineKAMStagingCount = int(arcpy.GetCount_management("nonlegalLineKAM_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_KOR, "nonlegalLineKOR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineKORStagingCount = int(arcpy.GetCount_management("nonlegalLineKOR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_NAN, "nonlegalLineNAN_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineNANStagingCount = int(arcpy.GetCount_management("nonlegalLineNAN_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_PRG, "nonlegalLinePRG_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLinePRGStagingCount = int(arcpy.GetCount_management("nonlegalLinePRG_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_SKE, "nonlegalLineSKE_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineSKEStagingCount = int(arcpy.GetCount_management("nonlegalLineSKE_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalLine_staging_SUR, "nonlegalLineSUR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalLineSURStagingCount = int(arcpy.GetCount_management("nonlegalLineSUR_staging_current_lyr").getOutput(0))

    nonlegalLineStagingCountTotal = nonlegalLineCARStagingCount + nonlegalLineFSJStagingCount + nonlegalLineKAMStagingCount + nonlegalLineKORStagingCount + nonlegalLineNANStagingCount + nonlegalLinePRGStagingCount + nonlegalLineSKEStagingCount + nonlegalLineSURStagingCount
    nonlegalLineBCGWCount = arcpy.GetCount_management(nonlegalLine_BCGW_SVW)
    nonlegalLineDifference = nonlegalLineStagingCountTotal - int(nonlegalLineBCGWCount.getOutput(0))
    if nonlegalLineDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Non Legal Planning Objectives (Line) dataset: " + str(nonlegalLineStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_NON_LEGAL_LINE_SVW dataset: " + str(nonlegalLineBCGWCount))
        arcpy.AddMessage("There are the same number of current Non Legal Planning Objectives (Line) features in both the staging and RMP_PLAN_NON_LEGAL_LINE_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalLineDifference > 0:
        arcpy.AddError("Number of current features in staging area Non Legal Planning Objectives (Line) dataset: " + str(nonlegalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_LINE_SVW dataset: " + str(nonlegalLineBCGWCount))
        arcpy.AddError("There are " + str(nonlegalLineDifference) + " more current Non Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_LINE_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalLineDifference < 0:
        arcpy.AddError("Number of current features in staging area Non Legal Planning Objectives (Line) dataset: " + str(nonlegalLineStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_LINE_SVW dataset: " + str(nonlegalLineBCGWCount))
        arcpy.AddError("There are " + str(nonlegalLineDifference) + " less current Non Legal Planning Objectives (Line) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_LINE_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_NON_LEGAL_POINT
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POINT")
    nonlegalPointCARStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_CAR).getOutput(0))
    nonlegalPointFSJStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_FSJ).getOutput(0))
    nonlegalPointKAMStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_KAM).getOutput(0))
    nonlegalPointKORStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_KOR).getOutput(0))
    nonlegalPointNANStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_NAN).getOutput(0))
    nonlegalPointPRGStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_PRG).getOutput(0))
    nonlegalPointSKEStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_SKE).getOutput(0))
    nonlegalPointSURStagingCount = int(arcpy.GetCount_management(nonlegalPoint_staging_SUR).getOutput(0))

    nonlegalPointStagingCountTotal = nonlegalPointCARStagingCount + nonlegalPointFSJStagingCount + nonlegalPointKAMStagingCount + nonlegalPointKORStagingCount + nonlegalPointNANStagingCount + nonlegalPointPRGStagingCount + nonlegalPointSKEStagingCount + nonlegalPointSURStagingCount
    nonlegalPointBCGWCount = arcpy.GetCount_management(nonlegalPoint_BCGW)
    nonlegalPointDifference = nonlegalPointStagingCountTotal - int(nonlegalPointBCGWCount.getOutput(0))
    if nonlegalPointDifference == 0:
        arcpy.AddMessage("Number of features in staging area Non Legal Planning Objectives (Point) dataset: " + str(nonlegalPointStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_NON_LEGAL_POINT dataset: " + str(nonlegalPointBCGWCount))
        arcpy.AddMessage("There are the same number of Non Legal Planning Objectives (Point) features in both the staging and RMP_PLAN_NON_LEGAL_POINT datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPointDifference > 0:
        arcpy.AddError("Number of features in staging area Non Legal Planning Objectives (Point) dataset: " + str(nonlegalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POINT dataset: " + str(nonlegalPointBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPointDifference) + " more Non Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POINT dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPointDifference < 0:
        arcpy.AddError("Number of features in staging area Non Legal Planning Objectives (Point) dataset: " + str(nonlegalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POINT dataset: " + str(nonlegalPointBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPointDifference) + " less Non Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POINT dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")

    #Check RMP_PLAN_NON_LEGAL_POINT_SVW
    arcpy.AddMessage("")
    arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POINT_SVW")
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_CAR, "nonlegalPointCAR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointCARStagingCount = int(arcpy.GetCount_management("nonlegalPointCAR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_FSJ, "nonlegalPointFSJ_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointFSJStagingCount = int(arcpy.GetCount_management("nonlegalPointFSJ_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_KAM, "nonlegalPointKAM_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointKAMStagingCount = int(arcpy.GetCount_management("nonlegalPointKAM_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_KOR, "nonlegalPointKOR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointKORStagingCount = int(arcpy.GetCount_management("nonlegalPointKOR_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_NAN, "nonlegalPointNAN_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointNANStagingCount = int(arcpy.GetCount_management("nonlegalPointNAN_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_PRG, "nonlegalPointPRG_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointPRGStagingCount = int(arcpy.GetCount_management("nonlegalPointPRG_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_SKE, "nonlegalPointSKE_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointSKEStagingCount = int(arcpy.GetCount_management("nonlegalPointSKE_staging_current_lyr").getOutput(0))
    arcpy.MakeFeatureLayer_management(nonlegalPoint_staging_SUR, "nonlegalPointSUR_staging_current_lyr", "\"STATUS\" = 0")
    nonlegalPointSURStagingCount = int(arcpy.GetCount_management("nonlegalPointSUR_staging_current_lyr").getOutput(0))

    nonlegalPointStagingCountTotal = nonlegalPointCARStagingCount + nonlegalPointFSJStagingCount + nonlegalPointKAMStagingCount + nonlegalPointKORStagingCount + nonlegalPointNANStagingCount + nonlegalPointPRGStagingCount + nonlegalPointSKEStagingCount + nonlegalPointSURStagingCount
    nonlegalPointBCGWCount = arcpy.GetCount_management(nonlegalPoint_BCGW_SVW)
    nonlegalPointDifference = nonlegalPointStagingCountTotal - int(nonlegalPointBCGWCount.getOutput(0))
    if nonlegalPointDifference == 0:
        arcpy.AddMessage("Number of current features in staging area Non Legal Planning Objectives (Point) dataset: " + str(nonlegalPointStagingCountTotal))
        arcpy.AddMessage("Number of features in BCGW RMP_PLAN_NON_LEGAL_POINT_SVW dataset: " + str(nonlegalPointBCGWCount))
        arcpy.AddMessage("There are the same number of current Non Legal Planning Objectives (Point) features in both the staging and RMP_PLAN_NON_LEGAL_POINT_SVW datasets")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPointDifference > 0:
        arcpy.AddError("Number of current features in staging area Non Legal Planning Objectives (Point) dataset: " + str(nonlegalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POINT_SVW dataset: " + str(nonlegalPointBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPointDifference) + " more current Non Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POINT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")
    if nonlegalPointDifference < 0:
        arcpy.AddError("Number of current features in staging area Non Legal Planning Objectives (Point) dataset: " + str(nonlegalPointStagingCountTotal))
        arcpy.AddError("Number of features in BCGW RMP_PLAN_NON_LEGAL_POINT_SVW dataset: " + str(nonlegalPointBCGWCount))
        arcpy.AddError("There are " + str(nonlegalPointDifference) + " less current Non Legal Planning Objectives (Point) features in the staging dataset than in the RMP_PLAN_NON_LEGAL_POINT_SVW dataset")
        arcpy.AddMessage(" ")
        arcpy.AddMessage(" ")


arcpy.AddMessage("....tool has finished running")
