'''
Author: Carole Bjorkman
Purpose: Post-load QA tool that compares record counts between staging area File GDBs and
            their corresponding published BCGW datasets for three dataset groups (each optional):
            OGMAs (legal and non-legal) — base SP table, ALL_SVW, and CURRENT_SVW (STATUS=0);
            Landscape Units — base SP table and SVW (STATUS in 0,1);
            SLRP — planning boundaries and six geometry types (legal/non-legal × poly/line/point),
            where staging counts are summed across 8 regional FCs before comparing to the
            consolidated BCGW SP table and SVW.
            Mismatches are reported via arcpy.AddError(); matches via arcpy.AddMessage().

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
Date: May 22, 2026
Author: C. Sostad
Modification: Updated from Python 2 / ArcGIS 10.8 standalone script to Python 3 / ArcGIS Pro 3
              modular form for import by slrp_ogma_arcpro_toolbox.pyt.
              Key changes:
              - Removed sys.argv argument parsing; staging_path and bcgw_path are now run() parameters
              - Two bare print str() calls replaced with arcpy.AddMessage()
              - arcpy.MakeFeatureLayer_management replaced with arcpy.management.MakeFeatureLayer
                per ArcGIS Pro 3 convention
              - Temporary layer names given UUID suffix to prevent collisions on repeated runs
              - arcpy.env.overwriteOutput replaces arcpy.overwriteOutput (legacy attribute)
              - All comparison logic wrapped in run() for toolbox import pattern

-----------------------------------------------------------------------------------------------
'''

# ORIGINAL: Imported sys, string, os, os.path, arcpy with duplicates
# CHANGE: Removed unused 'string' import, removed duplicate 'sys' import, added uuid for layer name uniqueness
# RISK: None - only removing unused and duplicate imports
# DOWNSTREAM: No impact on comparison logic
import os
import arcpy
import uuid

# ORIGINAL: staging_path and bcgw_path were passed by the caller (toolbox .pyt)
#           which had the staging path hardcoded as its default parameter value,
#           and all ~100 dataset sub-paths were constructed inline in run().
# CHANGE: Dataset sub-paths are now read from .env via config_loader so that
#         GDB names/structures can be updated in one place without touching
#         source code. staging_base and bcgw_path are still accepted as run()
#         parameters so the toolbox dialog values take precedence (the toolbox
#         pre-fills them from .env too, but the user can override them).
# RISK: If .env is absent or a key is missing, config_loader raises
#       before any arcpy work begins.
# DOWNSTREAM: Only the dataset path construction block inside run() is affected;
#             all comparison logic below is unchanged.
import config_loader


def _get_count(dataset):
    """Wrapper around arcpy.GetCount_management that intercepts ERROR 000229 (Cannot open)
    and adds a plain-English message pointing the user to the data custodian."""
    try:
        return arcpy.GetCount_management(dataset)
    except arcpy.ExecuteError as e:
        if "000229" in str(e):
            arcpy.AddError(
                f"Cannot open dataset:\n  {dataset}\n"
                "This is usually a read-access/permissions problem.\n"
                "If this is a BCGW dataset, contact the data custodian to request access:\n"
                "  GeoBC / DataBC: data@gov.bc.ca\n"
                "  Or submit a request through the BC Data Catalogue: "
                "https://catalogue.data.gov.bc.ca"
            )
        raise


def run(ogma_compare, lu_compare, slrp_compare, staging_path, bcgw_path):
    """Compare record counts between staging area datasets and BCGW published datasets.

    Parameters
    ----------
    ogma_compare  : bool  - run OGMA count comparison
    lu_compare    : bool  - run Landscape Unit count comparison
    slrp_compare  : bool  - run SLRP count comparison
    staging_path  : str   - base path to the staging area folder
                            (e.g. \\\\data.bcgov\\data_staging_bcgw\\land_use_plans_secure\\slrp)
    bcgw_path     : str   - path to the BCGW SDE connection file
                            (e.g. Database Connections\\BCGW.sde)
    """

    # ORIGINAL: arcpy.overwriteOutput = True  (legacy module-level attribute, Python 2 era)
    # CHANGE: arcpy.env.overwriteOutput = True  (correct ArcGIS Pro 3 form)
    # RISK: None - functionally equivalent; env form is the supported API in Pro 3
    # DOWNSTREAM: Affects all arcpy operations in this run() call only
    arcpy.env.overwriteOutput = True

    # Unique suffix appended to every temporary layer name to prevent collisions
    # if the tool is run more than once in the same ArcGIS Pro session.
    uid = uuid.uuid4().hex[:8]

    # Pre-flight: validate staging_path before constructing any dataset paths.
    # Catches the common mistake of browsing into the GDB rather than its parent folder,
    # which causes ERROR 000732 with the GDB name duplicated in the path.
    if staging_path.lower().endswith('.gdb'):
        arcpy.AddError(
            "Staging Area Base Path must be the folder that CONTAINS the GDB(s), "
            "not the GDB itself.\n"
            f"  You entered:  {staging_path}\n"
            f"  Try instead:  {os.path.dirname(staging_path)}\n"
            "In the tool dialog, browse to the parent folder (e.g. ...\\slrp), "
            "not into old_growth_management_area_bc.gdb."
        )
        return
    if not os.path.isdir(staging_path):
        arcpy.AddError(
            "Staging Area Base Path does not exist or is not accessible:\n"
            f"  {staging_path}\n"
            "Check that the network drive is mapped and the path is correct."
        )
        return

    ##############################################################
    # Datasets to compare — sub-paths loaded from .env
    ##############################################################

    def _sp(key):
        """Build a full staging dataset path from a .env variable name."""
        return os.path.join(staging_path, getattr(config_loader, key))

    ogmaLegal_staging         = _sp("DATASET_OGMA_LEGAL")
    ogmaLegal_BCGW            = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_SP"
    ogmaLegal_BCGW_current_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_CURRENT_SVW"
    ogmaLegal_BCGW_all_SVW    = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_ALL_SVW"

    ogmaNonLegal_staging      = _sp("DATASET_OGMA_NON_LEGAL")
    ogmaNonLegal_BCGW         = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_SP"
    ogmaNonLegal_BCGW_current_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_CURRENT_SVW"
    ogmaNonLegal_BCGW_all_SVW = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_OGMA_NON_LEGAL_ALL_SVW"

    lu_staging                = _sp("DATASET_LU")
    lu_BCGW                   = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_LANDSCAPE_UNIT_SP"
    lu_BCGW_SVW               = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_LANDSCAPE_UNIT_SVW"

    slrpBoundary_staging      = _sp("DATASET_SLRP_BOUNDARY")
    slrpBoundary_BCGW         = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_STRGC_LAND_RSRCE_PLAN_SP"
    slrpBoundary_BCGW_SVW     = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_STRGC_LAND_RSRCE_PLAN_SVW"

    legalPoly_staging_CAR     = _sp("DATASET_SLRP_LEGAL_POLY_CAR")
    legalPoly_staging_FSJ     = _sp("DATASET_SLRP_LEGAL_POLY_FSJ")
    legalPoly_staging_KAM     = _sp("DATASET_SLRP_LEGAL_POLY_KAM")
    legalPoly_staging_KOR     = _sp("DATASET_SLRP_LEGAL_POLY_KOR")
    legalPoly_staging_NAN     = _sp("DATASET_SLRP_LEGAL_POLY_NAN")
    legalPoly_staging_PRG     = _sp("DATASET_SLRP_LEGAL_POLY_PRG")
    legalPoly_staging_SKE     = _sp("DATASET_SLRP_LEGAL_POLY_SKE")
    legalPoly_staging_SUR     = _sp("DATASET_SLRP_LEGAL_POLY_SUR")
    legalPoly_BCGW            = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POLY"
    legalPoly_BCGW_SVW        = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POLY_SVW"

    legalLine_staging_CAR     = _sp("DATASET_SLRP_LEGAL_LINE_CAR")
    legalLine_staging_FSJ     = _sp("DATASET_SLRP_LEGAL_LINE_FSJ")
    legalLine_staging_KAM     = _sp("DATASET_SLRP_LEGAL_LINE_KAM")
    legalLine_staging_KOR     = _sp("DATASET_SLRP_LEGAL_LINE_KOR")
    legalLine_staging_NAN     = _sp("DATASET_SLRP_LEGAL_LINE_NAN")
    legalLine_staging_PRG     = _sp("DATASET_SLRP_LEGAL_LINE_PRG")
    legalLine_staging_SKE     = _sp("DATASET_SLRP_LEGAL_LINE_SKE")
    legalLine_staging_SUR     = _sp("DATASET_SLRP_LEGAL_LINE_SUR")
    legalLine_BCGW            = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_LINE"
    legalLine_BCGW_SVW        = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_LINE_SVW"

    legalPoint_staging_CAR    = _sp("DATASET_SLRP_LEGAL_POINT_CAR")
    legalPoint_staging_FSJ    = _sp("DATASET_SLRP_LEGAL_POINT_FSJ")
    legalPoint_staging_KAM    = _sp("DATASET_SLRP_LEGAL_POINT_KAM")
    legalPoint_staging_KOR    = _sp("DATASET_SLRP_LEGAL_POINT_KOR")
    legalPoint_staging_NAN    = _sp("DATASET_SLRP_LEGAL_POINT_NAN")
    legalPoint_staging_PRG    = _sp("DATASET_SLRP_LEGAL_POINT_PRG")
    legalPoint_staging_SKE    = _sp("DATASET_SLRP_LEGAL_POINT_SKE")
    legalPoint_staging_SUR    = _sp("DATASET_SLRP_LEGAL_POINT_SUR")
    legalPoint_BCGW           = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POINT"
    legalPoint_BCGW_SVW       = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_LEGAL_POINT_SVW"

    nonlegalPoly_staging_CAR  = _sp("DATASET_SLRP_NON_LEGAL_POLY_CAR")
    nonlegalPoly_staging_FSJ  = _sp("DATASET_SLRP_NON_LEGAL_POLY_FSJ")
    nonlegalPoly_staging_KAM  = _sp("DATASET_SLRP_NON_LEGAL_POLY_KAM")
    nonlegalPoly_staging_KOR  = _sp("DATASET_SLRP_NON_LEGAL_POLY_KOR")
    nonlegalPoly_staging_NAN  = _sp("DATASET_SLRP_NON_LEGAL_POLY_NAN")
    nonlegalPoly_staging_PRG  = _sp("DATASET_SLRP_NON_LEGAL_POLY_PRG")
    nonlegalPoly_staging_SKE  = _sp("DATASET_SLRP_NON_LEGAL_POLY_SKE")
    nonlegalPoly_staging_SUR  = _sp("DATASET_SLRP_NON_LEGAL_POLY_SUR")
    nonlegalPoly_BCGW         = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POLY"
    nonlegalPoly_BCGW_SVW     = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POLY_SVW"

    nonlegalLine_staging_CAR  = _sp("DATASET_SLRP_NON_LEGAL_LINE_CAR")
    nonlegalLine_staging_FSJ  = _sp("DATASET_SLRP_NON_LEGAL_LINE_FSJ")
    nonlegalLine_staging_KAM  = _sp("DATASET_SLRP_NON_LEGAL_LINE_KAM")
    nonlegalLine_staging_KOR  = _sp("DATASET_SLRP_NON_LEGAL_LINE_KOR")
    nonlegalLine_staging_NAN  = _sp("DATASET_SLRP_NON_LEGAL_LINE_NAN")
    nonlegalLine_staging_PRG  = _sp("DATASET_SLRP_NON_LEGAL_LINE_PRG")
    nonlegalLine_staging_SKE  = _sp("DATASET_SLRP_NON_LEGAL_LINE_SKE")
    nonlegalLine_staging_SUR  = _sp("DATASET_SLRP_NON_LEGAL_LINE_SUR")
    nonlegalLine_BCGW         = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_LINE"
    nonlegalLine_BCGW_SVW     = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_LINE_SVW"

    nonlegalPoint_staging_CAR = _sp("DATASET_SLRP_NON_LEGAL_POINT_CAR")
    nonlegalPoint_staging_FSJ = _sp("DATASET_SLRP_NON_LEGAL_POINT_FSJ")
    nonlegalPoint_staging_KAM = _sp("DATASET_SLRP_NON_LEGAL_POINT_KAM")
    nonlegalPoint_staging_KOR = _sp("DATASET_SLRP_NON_LEGAL_POINT_KOR")
    nonlegalPoint_staging_NAN = _sp("DATASET_SLRP_NON_LEGAL_POINT_NAN")
    nonlegalPoint_staging_PRG = _sp("DATASET_SLRP_NON_LEGAL_POINT_PRG")
    nonlegalPoint_staging_SKE = _sp("DATASET_SLRP_NON_LEGAL_POINT_SKE")
    nonlegalPoint_staging_SUR = _sp("DATASET_SLRP_NON_LEGAL_POINT_SUR")
    nonlegalPoint_BCGW        = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POINT"
    nonlegalPoint_BCGW_SVW    = bcgw_path + "\\WHSE_LAND_USE_PLANNING.RMP_PLAN_NON_LEGAL_POINT_SVW"

    ################################################################
    # Pre-flight: verify access to RMP_OGMA_LEGAL_SP
    # This dataset is restricted. General BCGW access does not guarantee
    # access to this specific layer — it requires a separate data-sharing
    # agreement or explicit grant from the data custodian.
    ################################################################
    if ogma_compare:
        try:
            arcpy.GetCount_management(ogmaLegal_BCGW)
        except arcpy.ExecuteError as e:
            if "000229" in str(e):
                arcpy.AddError(
                    "Cannot open WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_SP.\n"
                    "Access to this layer is restricted and must be granted separately,\n"
                    "even if you have a general BCGW connection.\n"
                    "To request access, contact the data custodian:\n"
                    "  GeoBC / DataBC: data@gov.bc.ca\n"
                    "  Reference dataset: WHSE_LAND_USE_PLANNING.RMP_OGMA_LEGAL_SP\n"
                    "  BC Data Catalogue: https://catalogue.data.gov.bc.ca"
                )
                return
            raise

    ################################################################
    # Start dataset count comparison if comparison is set to True
    ################################################################
    _step_count = sum([bool(ogma_compare), bool(lu_compare), bool(slrp_compare)])
    arcpy.SetProgressor("step", "Starting record count comparison...", 0, max(_step_count, 1), 1)

    # OGMAs
    if ogma_compare is False:
        arcpy.AddMessage("OGMA geodatabase not selected for comparison...")

    if ogma_compare is True:
        arcpy.SetProgressorLabel("Comparing OGMA record counts...")
        arcpy.SetProgressorPosition()
        # check RMP_OGMA_LEGAL_SP
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_OGMA_LEGAL_SP")
        ogmaLegalStagingCount = _get_count(ogmaLegal_staging)
        ogmaLegalBCGWCount = _get_count(ogmaLegal_BCGW)
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

        # check RMP_OGMA_LEGAL_ALL_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_OGMA_LEGAL_ALL_SVW")
        ogmaLegalStagingCount = _get_count(ogmaLegal_staging)
        ogmaLegalBCGWCount = _get_count(ogmaLegal_BCGW_all_SVW)
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

        # check RMP_OGMA_LEGAL_CURRENT_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_OGMA_LEGAL_CURRENT_SVW")
        # ORIGINAL: arcpy.MakeFeatureLayer_management(...)
        # CHANGE: arcpy.management.MakeFeatureLayer(...) per ArcGIS Pro 3 convention; uid suffix for session uniqueness
        # RISK: None - functionally identical; layer name uniqueness prevents collision on repeated runs
        # DOWNSTREAM: GetCount call immediately follows; uses same uid-suffixed name
        arcpy.management.MakeFeatureLayer(ogmaLegal_staging, f"ogmaLegal_current_lyr_{uid}", '"STATUS" = 0')
        ogmaLegalStagingCount = _get_count(f"ogmaLegal_current_lyr_{uid}")
        ogmaLegalBCGWCount = _get_count(ogmaLegal_BCGW_current_SVW)
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

        # check RMP_OGMA_NON_LEGAL_SP
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_OGMA_NON_LEGAL_SP")
        ogmaNonLegalStagingCount = _get_count(ogmaNonLegal_staging)
        ogmaNonLegalBCGWCount = _get_count(ogmaNonLegal_BCGW)
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

        # check RMP_OGMA_NON_LEGAL_ALL_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_OGMA_NON_LEGAL_ALL_SVW")
        ogmaNonLegalStagingCount = _get_count(ogmaNonLegal_staging)
        ogmaNonLegalBCGWCount = _get_count(ogmaNonLegal_BCGW_all_SVW)
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

        # check RMP_OGMA_NON_LEGAL_CURRENT_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_OGMA_NON_LEGAL_CURRENT_SVW")
        arcpy.management.MakeFeatureLayer(ogmaNonLegal_staging, f"ogmaNonLegal_current_lyr_{uid}", '"STATUS" = 0')
        ogmaNonLegalStagingCount = _get_count(f"ogmaNonLegal_current_lyr_{uid}")
        ogmaNonLegalBCGWCount = _get_count(ogmaNonLegal_BCGW_current_SVW)
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


    # Landscape Units
    if lu_compare is False:
        arcpy.AddMessage("Landscape Unit geodatabase not selected for comparison...")

    if lu_compare is True:
        arcpy.SetProgressorLabel("Comparing Landscape Unit record counts...")
        arcpy.SetProgressorPosition()
        # Check RMP_LANDSCAPE_UNIT_SP
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_LANDSCAPE_UNIT_SP")
        luStagingCount = _get_count(lu_staging)
        luBCGWCount = _get_count(lu_BCGW)
        luDifference = int(luStagingCount.getOutput(0)) - int(luBCGWCount.getOutput(0))
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

        # Check RMP_LANDSCAPE_UNIT_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_LANDSCAPE_UNIT_SVW")
        arcpy.management.MakeFeatureLayer(lu_staging, f"lu_current_lyr_{uid}", '"STATUS" in (0,1)')
        luStagingCount = _get_count(f"lu_current_lyr_{uid}")
        luBCGWCount = _get_count(lu_BCGW_SVW)
        luDifference = int(luStagingCount.getOutput(0)) - int(luBCGWCount.getOutput(0))
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


    # SLRP Boundaries
    if slrp_compare is False:
        arcpy.AddMessage("Strategic Land Resource Plan geodatabase not selected for comparison...")

    if slrp_compare is True:
        arcpy.SetProgressorLabel("Comparing SLRP record counts...")
        arcpy.SetProgressorPosition()
        # check RMP_STRGC_LAND_RSRCE_PLAN_SP
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_STRGC_LAND_RSRCE_PLAN_SP")
        slrpStagingCount = _get_count(slrpBoundary_staging)
        slrpBCGWCount = _get_count(slrpBoundary_BCGW)
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

        # check RMP_STRGC_LAND_RSRCE_PLAN_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_STRGC_LAND_RSRCE_PLAN_SVW")
        arcpy.management.MakeFeatureLayer(slrpBoundary_staging, f"slrpBoundary_current_lyr_{uid}", '"STATUS" = 0')
        slrpStagingCount = _get_count(f"slrpBoundary_current_lyr_{uid}")
        slrpBCGWCount = _get_count(slrpBoundary_BCGW_SVW)
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

        # Check RMP_PLAN_LEGAL_POLY
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POLY")
        legalPolyCARStagingCount = int(_get_count(legalPoly_staging_CAR).getOutput(0))
        legalPolyFSJStagingCount = int(_get_count(legalPoly_staging_FSJ).getOutput(0))
        legalPolyKAMStagingCount = int(_get_count(legalPoly_staging_KAM).getOutput(0))
        legalPolyKORStagingCount = int(_get_count(legalPoly_staging_KOR).getOutput(0))
        legalPolyNANStagingCount = int(_get_count(legalPoly_staging_NAN).getOutput(0))
        legalPolyPRGStagingCount = int(_get_count(legalPoly_staging_PRG).getOutput(0))
        legalPolySKEStagingCount = int(_get_count(legalPoly_staging_SKE).getOutput(0))
        legalPolySURStagingCount = int(_get_count(legalPoly_staging_SUR).getOutput(0))
        legalPolyStagingCountTotal = legalPolyCARStagingCount + legalPolyFSJStagingCount + legalPolyKAMStagingCount + legalPolyKORStagingCount + legalPolyNANStagingCount + legalPolyPRGStagingCount + legalPolySKEStagingCount + legalPolySURStagingCount
        legalPolyBCGWCount = _get_count(legalPoly_BCGW)
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

        # Check RMP_PLAN_LEGAL_POLY_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POLY_SVW")
        arcpy.management.MakeFeatureLayer(legalPoly_staging_CAR, f"legalPolyCAR_{uid}", '"STATUS" = 0')
        legalPolyCARStagingCount = int(_get_count(f"legalPolyCAR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_FSJ, f"legalPolyFSJ_{uid}", '"STATUS" = 0')
        legalPolyFSJStagingCount = int(_get_count(f"legalPolyFSJ_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_KAM, f"legalPolyKAM_{uid}", '"STATUS" = 0')
        legalPolyKAMStagingCount = int(_get_count(f"legalPolyKAM_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_KOR, f"legalPolyKOR_{uid}", '"STATUS" = 0')
        legalPolyKORStagingCount = int(_get_count(f"legalPolyKOR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_NAN, f"legalPolyNAN_{uid}", '"STATUS" = 0')
        legalPolyNANStagingCount = int(_get_count(f"legalPolyNAN_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_PRG, f"legalPolyPRG_{uid}", '"STATUS" = 0')
        legalPolyPRGStagingCount = int(_get_count(f"legalPolyPRG_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_SKE, f"legalPolySKE_{uid}", '"STATUS" = 0')
        legalPolySKEStagingCount = int(_get_count(f"legalPolySKE_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoly_staging_SUR, f"legalPolySUR_{uid}", '"STATUS" = 0')
        legalPolySURStagingCount = int(_get_count(f"legalPolySUR_{uid}").getOutput(0))
        legalPolyStagingCountTotal = legalPolyCARStagingCount + legalPolyFSJStagingCount + legalPolyKAMStagingCount + legalPolyKORStagingCount + legalPolyNANStagingCount + legalPolyPRGStagingCount + legalPolySKEStagingCount + legalPolySURStagingCount
        legalPolyBCGWCount = _get_count(legalPoly_BCGW_SVW)
        legalPolyDifference = legalPolyStagingCountTotal - int(legalPolyBCGWCount.getOutput(0))
        if legalPolyDifference == 0:
            arcpy.AddMessage("Number of current features in staging area Legal Planning Objectives (Polygon) dataset: " + str(legalPolyStagingCountTotal))
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

        # Check RMP_PLAN_LEGAL_LINE
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_LEGAL_LINE")
        legalLineCARStagingCount = int(_get_count(legalLine_staging_CAR).getOutput(0))
        legalLineFSJStagingCount = int(_get_count(legalLine_staging_FSJ).getOutput(0))
        legalLineKAMStagingCount = int(_get_count(legalLine_staging_KAM).getOutput(0))
        legalLineKORStagingCount = int(_get_count(legalLine_staging_KOR).getOutput(0))
        legalLineNANStagingCount = int(_get_count(legalLine_staging_NAN).getOutput(0))
        legalLinePRGStagingCount = int(_get_count(legalLine_staging_PRG).getOutput(0))
        legalLineSKEStagingCount = int(_get_count(legalLine_staging_SKE).getOutput(0))
        legalLineSURStagingCount = int(_get_count(legalLine_staging_SUR).getOutput(0))
        legalLineStagingCountTotal = legalLineCARStagingCount + legalLineFSJStagingCount + legalLineKAMStagingCount + legalLineKORStagingCount + legalLineNANStagingCount + legalLinePRGStagingCount + legalLineSKEStagingCount + legalLineSURStagingCount
        legalLineBCGWCount = _get_count(legalLine_BCGW)
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

        # Check RMP_PLAN_LEGAL_LINE_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_LEGAL_LINE_SVW")
        arcpy.management.MakeFeatureLayer(legalLine_staging_CAR, f"legalLineCAR_{uid}", '"STATUS" = 0')
        legalLineCARStagingCount = int(_get_count(f"legalLineCAR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_FSJ, f"legalLineFSJ_{uid}", '"STATUS" = 0')
        legalLineFSJStagingCount = int(_get_count(f"legalLineFSJ_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_KAM, f"legalLineKAM_{uid}", '"STATUS" = 0')
        legalLineKAMStagingCount = int(_get_count(f"legalLineKAM_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_KOR, f"legalLineKOR_{uid}", '"STATUS" = 0')
        legalLineKORStagingCount = int(_get_count(f"legalLineKOR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_NAN, f"legalLineNAN_{uid}", '"STATUS" = 0')
        legalLineNANStagingCount = int(_get_count(f"legalLineNAN_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_PRG, f"legalLinePRG_{uid}", '"STATUS" = 0')
        legalLinePRGStagingCount = int(_get_count(f"legalLinePRG_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_SKE, f"legalLineSKE_{uid}", '"STATUS" = 0')
        legalLineSKEStagingCount = int(_get_count(f"legalLineSKE_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalLine_staging_SUR, f"legalLineSUR_{uid}", '"STATUS" = 0')
        legalLineSURStagingCount = int(_get_count(f"legalLineSUR_{uid}").getOutput(0))
        legalLineStagingCountTotal = legalLineCARStagingCount + legalLineFSJStagingCount + legalLineKAMStagingCount + legalLineKORStagingCount + legalLineNANStagingCount + legalLinePRGStagingCount + legalLineSKEStagingCount + legalLineSURStagingCount
        legalLineBCGWCount = _get_count(legalLine_BCGW_SVW)
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

        # Check RMP_PLAN_LEGAL_POINT
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POINT")
        legalPointCARStagingCount = int(_get_count(legalPoint_staging_CAR).getOutput(0))
        legalPointFSJStagingCount = int(_get_count(legalPoint_staging_FSJ).getOutput(0))
        legalPointKAMStagingCount = int(_get_count(legalPoint_staging_KAM).getOutput(0))
        legalPointKORStagingCount = int(_get_count(legalPoint_staging_KOR).getOutput(0))
        legalPointNANStagingCount = int(_get_count(legalPoint_staging_NAN).getOutput(0))
        legalPointPRGStagingCount = int(_get_count(legalPoint_staging_PRG).getOutput(0))
        legalPointSKEStagingCount = int(_get_count(legalPoint_staging_SKE).getOutput(0))
        legalPointSURStagingCount = int(_get_count(legalPoint_staging_SUR).getOutput(0))
        legalPointStagingCountTotal = legalPointCARStagingCount + legalPointFSJStagingCount + legalPointKAMStagingCount + legalPointKORStagingCount + legalPointNANStagingCount + legalPointPRGStagingCount + legalPointSKEStagingCount + legalPointSURStagingCount
        # ORIGINAL: print str(legalPointStagingCountTotal)   (Python 2 bare print statement)
        # CHANGE: arcpy.AddMessage(str(...))  per Python 3 / ArcGIS Pro 3 toolbox convention
        # RISK: None - output only; no logic change
        # DOWNSTREAM: No impact
        arcpy.AddMessage(str(legalPointStagingCountTotal))
        legalPointBCGWCount = _get_count(legalPoint_BCGW)
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

        # Check RMP_PLAN_LEGAL_POINT_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_LEGAL_POINT_SVW")
        arcpy.management.MakeFeatureLayer(legalPoint_staging_CAR, f"legalPointCAR_{uid}", '"STATUS" = 0')
        legalPointCARStagingCount = int(_get_count(f"legalPointCAR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_FSJ, f"legalPointFSJ_{uid}", '"STATUS" = 0')
        legalPointFSJStagingCount = int(_get_count(f"legalPointFSJ_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_KAM, f"legalPointKAM_{uid}", '"STATUS" = 0')
        legalPointKAMStagingCount = int(_get_count(f"legalPointKAM_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_KOR, f"legalPointKOR_{uid}", '"STATUS" = 0')
        legalPointKORStagingCount = int(_get_count(f"legalPointKOR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_NAN, f"legalPointNAN_{uid}", '"STATUS" = 0')
        legalPointNANStagingCount = int(_get_count(f"legalPointNAN_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_PRG, f"legalPointPRG_{uid}", '"STATUS" = 0')
        legalPointPRGStagingCount = int(_get_count(f"legalPointPRG_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_SKE, f"legalPointSKE_{uid}", '"STATUS" = 0')
        legalPointSKEStagingCount = int(_get_count(f"legalPointSKE_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(legalPoint_staging_SUR, f"legalPointSUR_{uid}", '"STATUS" = 0')
        legalPointSURStagingCount = int(_get_count(f"legalPointSUR_{uid}").getOutput(0))
        legalPointStagingCountTotal = legalPointCARStagingCount + legalPointFSJStagingCount + legalPointKAMStagingCount + legalPointKORStagingCount + legalPointNANStagingCount + legalPointPRGStagingCount + legalPointSKEStagingCount + legalPointSURStagingCount
        # ORIGINAL: print str(legalPointStagingCountTotal)   (Python 2 bare print statement)
        # CHANGE: arcpy.AddMessage(str(...))  per Python 3 / ArcGIS Pro 3 toolbox convention
        # RISK: None - output only; no logic change
        # DOWNSTREAM: No impact
        arcpy.AddMessage(str(legalPointStagingCountTotal))
        legalPointBCGWCount = _get_count(legalPoint_BCGW_SVW)
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

        # Check RMP_PLAN_NON_LEGAL_POLY
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POLY")
        nonlegalPolyCARStagingCount = int(_get_count(nonlegalPoly_staging_CAR).getOutput(0))
        nonlegalPolyFSJStagingCount = int(_get_count(nonlegalPoly_staging_FSJ).getOutput(0))
        nonlegalPolyKAMStagingCount = int(_get_count(nonlegalPoly_staging_KAM).getOutput(0))
        nonlegalPolyKORStagingCount = int(_get_count(nonlegalPoly_staging_KOR).getOutput(0))
        nonlegalPolyNANStagingCount = int(_get_count(nonlegalPoly_staging_NAN).getOutput(0))
        nonlegalPolyPRGStagingCount = int(_get_count(nonlegalPoly_staging_PRG).getOutput(0))
        nonlegalPolySKEStagingCount = int(_get_count(nonlegalPoly_staging_SKE).getOutput(0))
        nonlegalPolySURStagingCount = int(_get_count(nonlegalPoly_staging_SUR).getOutput(0))
        nonlegalPolyStagingCountTotal = nonlegalPolyCARStagingCount + nonlegalPolyFSJStagingCount + nonlegalPolyKAMStagingCount + nonlegalPolyKORStagingCount + nonlegalPolyNANStagingCount + nonlegalPolyPRGStagingCount + nonlegalPolySKEStagingCount + nonlegalPolySURStagingCount
        nonlegalPolyBCGWCount = _get_count(nonlegalPoly_BCGW)
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

        # Check RMP_PLAN_NON_LEGAL_POLY_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POLY_SVW")
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_CAR, f"nonlegalPolyCAR_{uid}", '"STATUS" = 0')
        nonlegalPolyCARStagingCount = int(_get_count(f"nonlegalPolyCAR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_FSJ, f"nonlegalPolyFSJ_{uid}", '"STATUS" = 0')
        nonlegalPolyFSJStagingCount = int(_get_count(f"nonlegalPolyFSJ_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_KAM, f"nonlegalPolyKAM_{uid}", '"STATUS" = 0')
        nonlegalPolyKAMStagingCount = int(_get_count(f"nonlegalPolyKAM_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_KOR, f"nonlegalPolyKOR_{uid}", '"STATUS" = 0')
        nonlegalPolyKORStagingCount = int(_get_count(f"nonlegalPolyKOR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_NAN, f"nonlegalPolyNAN_{uid}", '"STATUS" = 0')
        nonlegalPolyNANStagingCount = int(_get_count(f"nonlegalPolyNAN_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_PRG, f"nonlegalPolyPRG_{uid}", '"STATUS" = 0')
        nonlegalPolyPRGStagingCount = int(_get_count(f"nonlegalPolyPRG_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_SKE, f"nonlegalPolySKE_{uid}", '"STATUS" = 0')
        nonlegalPolySKEStagingCount = int(_get_count(f"nonlegalPolySKE_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoly_staging_SUR, f"nonlegalPolySUR_{uid}", '"STATUS" = 0')
        nonlegalPolySURStagingCount = int(_get_count(f"nonlegalPolySUR_{uid}").getOutput(0))
        nonlegalPolyStagingCountTotal = nonlegalPolyCARStagingCount + nonlegalPolyFSJStagingCount + nonlegalPolyKAMStagingCount + nonlegalPolyKORStagingCount + nonlegalPolyNANStagingCount + nonlegalPolyPRGStagingCount + nonlegalPolySKEStagingCount + nonlegalPolySURStagingCount
        nonlegalPolyBCGWCount = _get_count(nonlegalPoly_BCGW_SVW)
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

        # Check RMP_PLAN_NON_LEGAL_LINE
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_LINE")
        nonlegalLineCARStagingCount = int(_get_count(nonlegalLine_staging_CAR).getOutput(0))
        nonlegalLineFSJStagingCount = int(_get_count(nonlegalLine_staging_FSJ).getOutput(0))
        nonlegalLineKAMStagingCount = int(_get_count(nonlegalLine_staging_KAM).getOutput(0))
        nonlegalLineKORStagingCount = int(_get_count(nonlegalLine_staging_KOR).getOutput(0))
        nonlegalLineNANStagingCount = int(_get_count(nonlegalLine_staging_NAN).getOutput(0))
        nonlegalLinePRGStagingCount = int(_get_count(nonlegalLine_staging_PRG).getOutput(0))
        nonlegalLineSKEStagingCount = int(_get_count(nonlegalLine_staging_SKE).getOutput(0))
        nonlegalLineSURStagingCount = int(_get_count(nonlegalLine_staging_SUR).getOutput(0))
        nonlegalLineStagingCountTotal = nonlegalLineCARStagingCount + nonlegalLineFSJStagingCount + nonlegalLineKAMStagingCount + nonlegalLineKORStagingCount + nonlegalLineNANStagingCount + nonlegalLinePRGStagingCount + nonlegalLineSKEStagingCount + nonlegalLineSURStagingCount
        nonlegalLineBCGWCount = _get_count(nonlegalLine_BCGW)
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

        # Check RMP_PLAN_NON_LEGAL_LINE_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_LINE_SVW")
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_CAR, f"nonlegalLineCAR_{uid}", '"STATUS" = 0')
        nonlegalLineCARStagingCount = int(_get_count(f"nonlegalLineCAR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_FSJ, f"nonlegalLineFSJ_{uid}", '"STATUS" = 0')
        nonlegalLineFSJStagingCount = int(_get_count(f"nonlegalLineFSJ_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_KAM, f"nonlegalLineKAM_{uid}", '"STATUS" = 0')
        nonlegalLineKAMStagingCount = int(_get_count(f"nonlegalLineKAM_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_KOR, f"nonlegalLineKOR_{uid}", '"STATUS" = 0')
        nonlegalLineKORStagingCount = int(_get_count(f"nonlegalLineKOR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_NAN, f"nonlegalLineNAN_{uid}", '"STATUS" = 0')
        nonlegalLineNANStagingCount = int(_get_count(f"nonlegalLineNAN_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_PRG, f"nonlegalLinePRG_{uid}", '"STATUS" = 0')
        nonlegalLinePRGStagingCount = int(_get_count(f"nonlegalLinePRG_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_SKE, f"nonlegalLineSKE_{uid}", '"STATUS" = 0')
        nonlegalLineSKEStagingCount = int(_get_count(f"nonlegalLineSKE_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalLine_staging_SUR, f"nonlegalLineSUR_{uid}", '"STATUS" = 0')
        nonlegalLineSURStagingCount = int(_get_count(f"nonlegalLineSUR_{uid}").getOutput(0))
        nonlegalLineStagingCountTotal = nonlegalLineCARStagingCount + nonlegalLineFSJStagingCount + nonlegalLineKAMStagingCount + nonlegalLineKORStagingCount + nonlegalLineNANStagingCount + nonlegalLinePRGStagingCount + nonlegalLineSKEStagingCount + nonlegalLineSURStagingCount
        nonlegalLineBCGWCount = _get_count(nonlegalLine_BCGW_SVW)
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

        # Check RMP_PLAN_NON_LEGAL_POINT
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POINT")
        nonlegalPointCARStagingCount = int(_get_count(nonlegalPoint_staging_CAR).getOutput(0))
        nonlegalPointFSJStagingCount = int(_get_count(nonlegalPoint_staging_FSJ).getOutput(0))
        nonlegalPointKAMStagingCount = int(_get_count(nonlegalPoint_staging_KAM).getOutput(0))
        nonlegalPointKORStagingCount = int(_get_count(nonlegalPoint_staging_KOR).getOutput(0))
        nonlegalPointNANStagingCount = int(_get_count(nonlegalPoint_staging_NAN).getOutput(0))
        nonlegalPointPRGStagingCount = int(_get_count(nonlegalPoint_staging_PRG).getOutput(0))
        nonlegalPointSKEStagingCount = int(_get_count(nonlegalPoint_staging_SKE).getOutput(0))
        nonlegalPointSURStagingCount = int(_get_count(nonlegalPoint_staging_SUR).getOutput(0))
        nonlegalPointStagingCountTotal = nonlegalPointCARStagingCount + nonlegalPointFSJStagingCount + nonlegalPointKAMStagingCount + nonlegalPointKORStagingCount + nonlegalPointNANStagingCount + nonlegalPointPRGStagingCount + nonlegalPointSKEStagingCount + nonlegalPointSURStagingCount
        nonlegalPointBCGWCount = _get_count(nonlegalPoint_BCGW)
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

        # Check RMP_PLAN_NON_LEGAL_POINT_SVW
        arcpy.AddMessage("")
        arcpy.AddMessage("Checking RMP_PLAN_NON_LEGAL_POINT_SVW")
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_CAR, f"nonlegalPointCAR_{uid}", '"STATUS" = 0')
        nonlegalPointCARStagingCount = int(_get_count(f"nonlegalPointCAR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_FSJ, f"nonlegalPointFSJ_{uid}", '"STATUS" = 0')
        nonlegalPointFSJStagingCount = int(_get_count(f"nonlegalPointFSJ_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_KAM, f"nonlegalPointKAM_{uid}", '"STATUS" = 0')
        nonlegalPointKAMStagingCount = int(_get_count(f"nonlegalPointKAM_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_KOR, f"nonlegalPointKOR_{uid}", '"STATUS" = 0')
        nonlegalPointKORStagingCount = int(_get_count(f"nonlegalPointKOR_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_NAN, f"nonlegalPointNAN_{uid}", '"STATUS" = 0')
        nonlegalPointNANStagingCount = int(_get_count(f"nonlegalPointNAN_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_PRG, f"nonlegalPointPRG_{uid}", '"STATUS" = 0')
        nonlegalPointPRGStagingCount = int(_get_count(f"nonlegalPointPRG_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_SKE, f"nonlegalPointSKE_{uid}", '"STATUS" = 0')
        nonlegalPointSKEStagingCount = int(_get_count(f"nonlegalPointSKE_{uid}").getOutput(0))
        arcpy.management.MakeFeatureLayer(nonlegalPoint_staging_SUR, f"nonlegalPointSUR_{uid}", '"STATUS" = 0')
        nonlegalPointSURStagingCount = int(_get_count(f"nonlegalPointSUR_{uid}").getOutput(0))
        nonlegalPointStagingCountTotal = nonlegalPointCARStagingCount + nonlegalPointFSJStagingCount + nonlegalPointKAMStagingCount + nonlegalPointKORStagingCount + nonlegalPointNANStagingCount + nonlegalPointPRGStagingCount + nonlegalPointSKEStagingCount + nonlegalPointSURStagingCount
        nonlegalPointBCGWCount = _get_count(nonlegalPoint_BCGW_SVW)
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


if __name__ == "__main__":
    # ORIGINAL: _staging_path and _bcgw_path were hardcoded UNC literals.
    # CHANGE: Loaded from .env via config_loader.
    # RISK: If .env is absent, config_loader raises with a clear message.
    # DOWNSTREAM: Only the standalone test invocation is affected.
    _staging_path = config_loader.STAGING_BASE
    _bcgw_path    = config_loader.BCGW_SDE
    run(True, True, True, _staging_path, _bcgw_path)
