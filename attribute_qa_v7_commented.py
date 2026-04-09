'''
Author: Carole Bjorkman
Purpose: 
         
Date: January 27, 2009

Arguments: argv[1] = dataset to check
           argv[2] = is DRM running tool? (boolean - checked = yes)
           argv[3] = corresponding "Master" dataset

Outputs: excel spreadsheet listing errors

Dependencies: 


History:
----------------------------------------------------------------------------------------------
Date: March 22, 2010
Author: C. Bjorkman
Modification: Adding in checks for 0 in featID/provID fields
              Adding in more LU checks
              Some changes to output text file formatting

Date: April 7, 2010
Author: C. Bjorkman
Modification: Adding in check for "<NULL>" as a string in any field
              Adding in modification type check: if mod type = permanent retirement, there should
                  not be a matching provID with a modification type of new, modified, or retired
              Adding in a check for duplicate provIDs within a single modification type
              
Date: May 12, 2010
Author: C. Bjorkman
Modification: Adding in limiter for checking SLRP boundary names against SLRP Boundary dataset - restrict
                 to features with "Current" status only to avoid picking up features that have been 
                 corrected.
                 
Date: May 20, 2010
Author: C. Bjorkman
Modification: Fixing "Check for Duplicates in FeatID" module - it wasn't picking up duplicates

Date: June 1, 2010
Author: C. Bjorkman
Modification: Adding in piece to compare # of records in pre & post update feature classes with boolean
                to toggle on & off for DRM vs Region, plus cleaning up formatting of output text file to make
                it more user friendly
                
Date: Jan 8, 2011
Author: C. Bjorkman
Modification: Updated section 7 to hit both legal & non legal ogma datasets when checking for duplicate 
                provid/provid part numbers.  Updated incorrect output statement in section 2.

Date: May 2015
Author: C. Mahood (fka Bjorkman)
Modification: Rewrote script to hit arcpy, added in references to new fields (Act/OGC stuff)

Date: Sept 2015
Author: C. Mahood (fka Bjorkman)
Modification: Added in exceptions for gaps due to mass Skeena non-legal poly deletions

ate: Feb 13 2017
Author: C. Mahood (fka Bjorkman)
Modification: Rewrote section 9 to process WAY WAY WAY faster

Date: Feb 13 2017
Author: C. Mahood (fka Bjorkman)
Modification: Added in check for URL fields (is a valid URL) (****UNDER DEVELOPMENT***)

Date: Aug 23 2018
Author: C. Mahood
Modification: Removed 'drmRunningTool' variable - all users will now check against Master (if DRM)
                or the FC they recieved for updating (should have an untouched copy in their workarea)
                
Date: Jan 12 2022
Author: C. Mahood
Modification: removed "No errors" messages in tool interface as they were being shown even if errors
                existed and users were then not checking the output text file. Will hopefully 
                avoid error-filled check-ins coming back to DRMs in the future & reduce confusion.
-----------------------------------------------------------------------------------------------
'''

# Import standard libraries, arcpy GIS library, and urllib2 for URL validation (Section 13).
import sys, string, os, os.path, datetime, arcpy, urllib2
from arcpy import env

# Allow arcpy to overwrite existing outputs without raising errors.
env.overwriteOutput = True

#arguments
# Parse command-line arguments: argv[1] = post-update dataset path, argv[2] = master/pre-update dataset path.
try:
    argScriptName = sys.argv[0]
    
    inDataset = sys.argv[1]
    
# #    drmRunningTool = False 
# #     argDRMRunningTool = sys.argv[2]
# #     if argDRMRunningTool =='true':
# #         drmRunningTool = True 
        
    masterDataset = sys.argv[2]
except:
    print "no arguments"

####################################################################
##TESTING BLOCK
# inDataset = r"\\spatialfiles.bcgov\work\srm\wml\workarea\camahood\Data_Management\slrp_issues\strategic_land_resource_plan_bc_Update_20211208_returned_20211214.gdb\slrp_planning_feature_legal_PRG_poly"
# masterDataset = r"\\spatialfiles.bcgov\work\srm\wml\workarea\camahood\Data_Management\slrp_issues\strategic_land_resource_plan_bc.gdb\slrp_planning_feature_legal_PRG_poly"

# inDataset = r"\\friday\slrp\UpdateWorkarea\Tools\test_wksp\updates\old_growth_management_area_bc_1.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"
# masterDataset = r"\\friday\slrp\UpdateWorkarea\Tools\test_wksp\masters\old_growth_management_area_bc_1.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"
# 
#drmRunningTool = True
####################################################################

# Entry point: runs all QA sections in sequence then compacts the geodatabase.
def main():
    set_global_variables()
    start_text_file()
    section_0_DRM_checks()
    section_1_check_for_false_nulls()
    section_2_check_change_attribute_fields()
    section_3_check_legalization_and_approval_attributes()
    section_4_check_for_0_or_null_in_FEATID_and_PROVID()
    section_5_check_for_gaps_in_PROVID()
    section_6_check_for_gaps_in_feature_id()
    section_7_check_for_duplicate_provid_provid_part_number_in_current_records()
    section_8_check_for_duplicates_in_featID()
    section_9_check_for_provid_pairs_based_on_mod_type()
    section_10_check_for_provID_provIDpartnumber_duplication_by_mod_type()
    section_11_check_lo_nlpf_boundary_specific_dependancies()
    section_11_check_lu_beo_dependancies()
    section_12_check_domains()
    ##section_13_check_url_fields()
    compact_gdb()

# Derive all global path variables and dataset-specific field names from the input dataset path.
def set_global_variables():
    global featClassName
    featClassName = os.path.basename(inDataset)
    
        # Map feature class name to its unique ID field, provincial ID field, and part-number field.
        #determine name of unique id and prov id field, depending on what dataset is loaded:
    global uniqueIDField
    global provIDField
    global provIDPartNum
    
    if featClassName == 'landscape_unit_poly':
        uniqueIDField = "LANDSCAPE_UNIT_ID"
        provIDField = "LANDSCAPE_UNIT_PROVID"
        provIDPartNum = "PROVID_PART_NUMBER"
    if featClassName == 'old_growth_management_area_legal_bc_poly':
        uniqueIDField = "LEGAL_OGMA_INTERNAL_ID"
        provIDField = "LEGAL_OGMA_PROVID"
        provIDPartNum = "PROVID_PART_NUMBER"
    if featClassName == 'old_growth_management_area_non_legal_bc_poly':
        uniqueIDField = "NON_LEGAL_OGMA_INTERNAL_ID"
        provIDField = "NON_LEGAL_OGMA_PROVID"
        provIDPartNum = "PROVID_PART_NUMBER"
    if featClassName == 'slrp_planning_boundary_bc_poly':
        uniqueIDField = "STRGC_LAND_RSRCE_PLAN_ID"
        provIDField = "STRGC_LAND_RSRCE_PLAN_PROVID"
        provIDPartNum = "PROVID_PART_NUMBER"
    if featClassName[:27] == 'slrp_planning_feature_legal':
        uniqueIDField = "LEGAL_FEAT_ID"
        provIDField = "LEGAL_FEAT_PROVID"
        provIDPartNum = "PROVID_PART_NUMBER"
    if featClassName[:31] == 'slrp_planning_feature_non_legal':
        uniqueIDField = "NON_LEGAL_FEAT_ID"
        provIDField = "NON_LEGAL_FEAT_PROVID"
        provIDPartNum = "PROVID_PART_NUMBER"
        
    # Derive the feature dataset path, GDB path, update folder path, and dataset folder path from the input path.
    global fdsPath
    fdsPath = os.path.dirname(inDataset)
    
    global fdsName
    fdsName = os.path.basename(fdsPath)
    
    global gdbPath
    gdbPath = os.path.dirname(fdsPath)
    
    global gdbName
    gdbName = os.path.basename(gdbPath)
    
    global updateFolderPath
    updateFolderPath = os.path.dirname(gdbPath)
    
    global updateFolderName
    updateFolderName = os.path.basename(updateFolderPath)
    
    global datasetFolderPath
    datasetFolderPath = os.path.dirname(updateFolderPath)
    
    global datasetFolderName
    datasetFolderName = os.path.basename(datasetFolderPath)
    
    global masterFeatClassName
    masterFeatClassName = os.path.basename(masterDataset)
    
    # Build the output report file path: saved in the update folder, named with feature class and today's date.
    global attributeQAReportFile
    attributeQAReportFile = updateFolderPath + "\\" + featClassName + "_attribute_check_"  + str(datetime.date.today())+ ".txt"
    
    # Standard "no errors" message string reused across all sections.
    global noErrorsMessage
    noErrorsMessage = '    - No errors found'

# Create (overwrite) the output text report file and write the header block.
def start_text_file():
    fh = open(attributeQAReportFile, 'w') 
    fh.write("\n")
    fh.write('ATTRIBUTE VERIFICATION FOR:  ' + featClassName + '\n')
    fh.write('======================================================================================================\n')
    fh.write('\n')
    fh.write('Dataset Path:  ' + inDataset + '\n')
    fh.write('\n')
    fh.write('\n')
    fh.close()
 
# SECTION 0: Compare pre-update (master) and post-update feature counts.
def section_0_DRM_checks():
    '''
    Section 0 — Record count comparison (pre vs post): Compares the count of features between master and update.
    Checks that the number of NEW + MODIFIED features equals the count difference, and that retirements are at least equal to modifications.
    '''
    fh = open(attributeQAReportFile, 'a')

    fh.write('\n')
    
    arcpy.AddMessage('')
    section = '------------Section 0------------'
    arcpy.AddMessage(section)
    fh.write(section + '\n')
   
    fh.write('PRE & POST UPDATE FEATURE CLASS RECORD COUNT COMPARISON:\n')
    fh.write("--------------------------------------------------------\n")
    fh.write("\n")
    
    # Create feature layers from both master and update datasets for selection operations.
    arcpy.MakeFeatureLayer_management(masterDataset, 'master_fc_lyr')
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    
    # Get record counts from both datasets and calculate the net difference.
    masterCount = str(arcpy.GetCount_management("master_fc_lyr"))
    updateCount = str(arcpy.GetCount_management("fc_lyr"))
    masterUpdateDifference = int(updateCount) - int(masterCount)
    
    
    fh.write("    # of Features in Pre-Update Feature Class:                         " + str(masterCount) + "\n")
    fh.write("    # of Features in Post-Update Feature Class:                        " + str(updateCount) + "\n")         
    fh.write("                                                                      ----\n")
    fh.write("    Difference (Post - Pre):                                           " + str(masterUpdateDifference)+ "\n")
    fh.write("\n")
    
    # Count features by MODIFICATION_TYPE to cross-check against the net record difference.
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\"  = 'MODIFIED'")
    modifiedCount = str(arcpy.GetCount_management("fc_lyr"))
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\"  = 'NEW'")
    newCount = str(arcpy.GetCount_management("fc_lyr"))
    
    fh.write("\n")
    fh.write("    # of MODIFIED Features in Post Update Feature Class:               " + str(modifiedCount) + "\n")
    fh.write("    # of NEW Features in Post Update Feature Class:                    " + str(newCount) + "\n")
    fh.write("                                                                      -----\n")
    fh.write("    Total NEW + MODIFIED:                                              " + str(int(modifiedCount) + int(newCount)) +       "\n")
    fh.write("\n")
    
    # Validate: the count difference (post minus pre) should equal NEW + MODIFIED count.
    if masterUpdateDifference <> int(modifiedCount) + int(newCount):
        fh.write("***ERROR --> " + str(masterUpdateDifference) + " feature(s) added to post-update feature class.\n")
        fh.write("            " + str(int(modifiedCount) + int(newCount)) + " feature(s) flagged as NEW or MODIFIED.\n")
        fh.write("             These numbers should match.\n")
        fh.write("\n")
    
    # Count RETIREMENT and PERMANENT RETIREMENT features.
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\"  = 'PERMANENT RETIREMENT'")
    permRetireCount = str(arcpy.GetCount_management("fc_lyr"))
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\"  = 'RETIREMENT'")
    retireCount = str(arcpy.GetCount_management("fc_lyr"))
    
    fh.write("\n")
    fh.write("    # of PERMANENT RETIREMENT Features in Post Update Feature Class:   " + str(permRetireCount) + "\n")
    fh.write("    # of RETIREMENT Features in Post Update Feature Class:             " + str(retireCount) + "\n")
    fh.write("                                                                      -----\n")
    fh.write("    Total RETIRED + PERMANENTLY RETIRED:                               " + str(int(permRetireCount) + int(retireCount)) + "\n")
    fh.write("\n")
    # Validate: total retirements should be >= total modified (each MODIFIED needs a paired RETIREMENT).
    if int(permRetireCount) + int(retireCount) < int(modifiedCount):
        fh.write("***ERROR --> " + str(int(permRetireCount) + int(retireCount)) + " feature(s) flagged as RETIREMENT and PERMANENT RETIREMENT.\n")
        fh.write("            " + str(modifiedCount) + " feature(s) flagged as MODIFIED.\n")
        fh.write("            The number of RETIREMENT and PERMANENT RETIREMENT features should be\n")
        fh.write("            greater than or equal to the number of MODIFIED features.\n")

    fh.write("\n")
    fh.write("\n")
    fh.write("\n")
    fh.close()
    
    arcpy.AddMessage('    - complete')
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 1: Check all string and numeric fields for false or invalid null values.
def section_1_check_for_false_nulls():

    '''
    Section 1 — False nulls: Scans every string field for text values like <Null>, NULL, null etc.
      that were accidentally typed instead of a true database null. Also checks numeric fields for unexpected nulls.
    '''
    fh = open(attributeQAReportFile, 'a')  
    
    
    section = '----------Section 1----------'
    arcpy.AddMessage(section)
    fh.write(section + '\n')
    
    fh.write('FALSE & INVALID NULL VALUES CHECKS:\n')
    fh.write("--------------------------------------------------------\n")
    fh.write("\n")
    
    ruleMessage = r"RULE TO CHECK: False nulls (<Null>, <NULL>, Null, NULL, null, or <null> as a text string) in any string field is invalid."
    fh.write(ruleMessage + "\n")
    arcpy.AddMessage(ruleMessage)
    
    # Build a list of all string field names and query each for text representations of null.
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    
    okTest = 0
    stringFieldNameList = [f.name for f in arcpy.ListFields('fc_lyr', "", "String")]
    for field in stringFieldNameList:
        selectionString = "\"" + field + "\" in ('<Null>', '<NULL>', 'Null', 'NULL', 'null', '<null>')"
        arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", selectionString)
        
        badNullCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if badNullCount > 0:
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            nullErrorList = []
            while row:
                if row.getValue(uniqueIDField) not in nullErrorList:
                    nullErrorList.append(row.getValue(uniqueIDField))
                row = rows.next()
            fh.write('***ERROR --> [' + str(uniqueIDField) + '] has ' + str(arcpy.GetCount_management("fc_lyr")) + ' features with <NULL>, <Null>, NULL, or Null as a string instead of a true NULL value: \n')
            for uniqueID in nullErrorList:
                fh.write('     ' + uniqueIDField + ' ' + str(uniqueID) + ": False Null in " + str(field) + '\n')
            okTest = okTest + 1
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
    
    fh.write('\n') 
    arcpy.AddMessage('')
    
    # Build a list of all integer field names and check each for unexpected true null values.
    message = r"RULE TO CHECK: <NULL> in numeric fields is invalid."
    arcpy.AddMessage(message)
    fh.write(message + "\n")
       
    okTest = 0
    numberFieldNameList = [f.name for f in arcpy.ListFields('fc_lyr', "", "Integer")]
    for field in numberFieldNameList:
        selectionString = "\"" + str(field) + "\" is NULL"
        arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", selectionString)
        
        badNullCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if badNullCount > 0:
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            nullErrorList = []
            while row:
                if row.getValue(uniqueIDField) not in nullErrorList:
                    nullErrorList.append(str(row.getValue(uniqueIDField)))
                row = rows.next()
            fh.write('***ERROR --> [' + str(field) + '] has ' + str(arcpy.GetCount_management("fc_lyr")) + ' features with <Null> in a numeric field: \n')
            
            for uniqueID in nullErrorList:
                fh.write('     ' + uniqueIDField + ' ' + str(uniqueID) + ": Null in " + str(field) + '\n')
            okTest = okTest + 1

    if okTest == 0:
        fh.write(noErrorsMessage + '\n')

    fh.write('\n')
    fh.write('\n')  
    fh.write('\n')
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 2: Validate all change management attributes for correctness and consistency.
def section_2_check_change_attribute_fields():
    '''
    Section 2 — Change management attributes: This is the most complex section. Validates the 8 change management fields documented in the Change_Management_Attributes.pdf. 
    Checks that: STATUS matches MODIFICATION_TYPE, GIS_CHANGE_DATE and RETIREMENT_DATE are filled in correctly per modification scenario, date comparisons are logical (no retirement before 1900, no future dates), 
    and that all IDIR usernames are uppercase.'''
    fh = open(attributeQAReportFile, 'a')  
    
    section = '----------Section 2----------'
    
    arcpy.AddMessage(section)
    fh.write(section + '\n')
    
    fh.write('CHANGE MANAGEMENT ATTRIBUTES VERIFICATION:\n')
    fh.write("--------------------------------------------------------\n")
    fh.write("\n")
    
    # Set STATUS query strings: Landscape Units use values 0/1 for current and 2/3 for retired; all others use 0/1.
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    #set status query variable - different for landscape units than other feature classes
    if featClassName == 'landscape_unit_poly':
        statusQueryCurrent = "\"STATUS\" in (0,1)"
        statusQueryRetired = "\"STATUS\" in (2,3)"
    else: 
        statusQueryCurrent = "\"STATUS\" = 0"
        statusQueryRetired = "\"STATUS\" = 1"
        
    # Check: features flagged NEW, MODIFIED, or MODIFIED_NOREPLACE must not have a retired STATUS.
    ruleMessage = 'RULE TO CHECK: Features with a [MODIFICATION TYPE] of NEW, MODIFIED, or MODIFIED_NOREPLACE must not have [STATUS] set to Retired.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n")
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"MODIFICATION_TYPE\" IN ('NEW', 'MODIFIED', 'MODIFIED_NOREPLACE')")
    arcpy.SelectLayerByAttribute_management('fc_lyr', "SUBSET_SELECTION", statusQueryRetired)
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
    #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " features flagged as NEW, MODIFIED, or MODIFIED_NOREPLACE have status\n")
        fh.write("             set as RETIRED: \n")
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else:
        fh.write(noErrorsMessage + '\n')

    fh.write('\n') 
    arcpy.AddMessage('') 

    # Check: features flagged RETIREMENT or PERMANENT RETIREMENT must not have a current STATUS.
    ruleMessage = 'RULE TO CHECK: Features with a [MODIFICATION TYPE] of RETIREMENT or PERMANENT RETIREMENT must not have [STATUS] set to Current.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n")
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"MODIFICATION_TYPE\" IN ('RETIREMENT', 'PERMANENT RETIREMENT')")
    arcpy.SelectLayerByAttribute_management('fc_lyr', "SUBSET_SELECTION", statusQueryCurrent)
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
    #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " features flagged as RETIREMENT or PERMANENT RETIREMENT have status\n")
        fh.write("             set as CURRENT: \n")
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else:
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    # Check: current features must have all four active change management fields populated.
    ruleMessage = 'RULE TO CHECK: Features with a [STATUS] set to Current must have [GIS_CHANGE_DATE],[GIS_CHANGE_PERSON],[CHANGE_REASON], and [INITIATOR OF CHANGE] filled out.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n")
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", statusQueryCurrent)
    arcpy.SelectLayerByAttribute_management('fc_lyr', "SUBSET_SELECTION", "\"GIS_CHANGE_DATE\" is null OR (\"GIS_CHANGE_PERSON\" is null OR \"GIS_CHANGE_PERSON\" = '') OR (\"CHANGE_REASON\" is null OR \"CHANGE_REASON\" = '') OR (\"INITIATOR_OF_CHANGE\" is null OR \"INITIATOR_OF_CHANGE\" = '')")
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
        #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " CURRENT features missing one or more of the following CURRENT change\n")
        fh.write("             management attributes:\n")
        fh.write("             [GIS_CHANGE_DATE],[GIS_CHANGE_PERSON],[CHANGE_REASON],\n")
        fh.write("             [INITIATOR_OF_CHANGE]\n")      
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    else:
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    # Check: current features must NOT have any retirement change management fields populated.
    ruleMessage = 'RULE TO CHECK: Features with a [STATUS] set to Current must NOT have [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],[RETIREMENT_REASON], or [RETIREMENT_INITIATOR_OF_CHANGE] filled out.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n")
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", statusQueryCurrent)
    arcpy.SelectLayerByAttribute_management('fc_lyr', "SUBSET_SELECTION", "(\"RETIREMENT_DATE\" is not null OR \"RETIREMENT_GIS_CHANGE_PERSON\" is not null OR \"RETIREMENT_REASON\" is not null OR \"RETIREMENT_INITIATOR_OF_CHANGE\" is not null OR \"RETIREMENT_GIS_CHANGE_PERSON\" <> '' OR \"RETIREMENT_REASON\" <> '' OR \"RETIREMENT_INITIATOR_OF_CHANGE\" <> '')")
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
        #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " CURRENT features have one or more of the following RETIREMENT change\n")
        fh.write("             management attributes filled in:\n")
        fh.write("             [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],\n")
        fh.write("             [RETIREMENT_REASON],[RETIREMENT_INITIATOR_OF_CHANGE]\n")
        
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else: 
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    # Check: retired features must have all four retirement change management fields populated.
    ruleMessage = 'RULE TO CHECK: Features with a [STATUS] set to Retired must have [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],[RETIREMENT_REASON], or [RETIREMENT_INITIATOR_OF_CHANGE] filled out.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n") 
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", statusQueryRetired)
    arcpy.SelectLayerByAttribute_management('fc_lyr', "SUBSET_SELECTION", "(\"RETIREMENT_DATE\" is null OR \"RETIREMENT_GIS_CHANGE_PERSON\" is null OR \"RETIREMENT_REASON\" is null OR \"RETIREMENT_INITIATOR_OF_CHANGE\" is null OR \"RETIREMENT_GIS_CHANGE_PERSON\" ='' OR \"RETIREMENT_REASON\" = '' OR \"RETIREMENT_INITIATOR_OF_CHANGE\" ='')")
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
        #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " RETIRED features missing one or more of the following RETIREMENT\n")
        fh.write("             change management attributes:\n")
        fh.write("             [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],\n")
        fh.write("             [RETIREMENT_REASON],[RETIREMENT_INITIATOR_OF_CHANGE]\n")
    
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else:
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    # Check: NEW or MODIFIED features must have all four active change management fields populated.
    ruleMessage = 'RULE TO CHECK: Features with [MODIFICATION_TYPE] flagged as NEW or MODIFIED must have [GIS_CHANGE_DATE],[GIS_CHANGE_PERSON],[CHANGE_REASON], and [INITIATOR OF CHANGE] filled out.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n") 
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"MODIFICATION_TYPE\" IN ('NEW', 'MODIFIED') AND ((\"GIS_CHANGE_DATE\" is null) OR (\"GIS_CHANGE_PERSON\" is null OR \"GIS_CHANGE_PERSON\" = '') OR (\"CHANGE_REASON\" is null OR \"CHANGE_REASON\" = '') OR (\"INITIATOR_OF_CHANGE\" is null OR \"INITIATOR_OF_CHANGE\" = ''))")
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
        #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " features flagged as NEW or MODIFIED missing one or more of the following\n")
        fh.write("             CURRENT change management attributes:\n")
        fh.write("             [GIS_CHANGE_DATE],[GIS_CHANGE_PERSON],[CHANGE_REASON],\n")
        fh.write("             [INITIATOR_OF_CHANGE]\n")
        
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else:
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    # Check: NEW or MODIFIED features must NOT have any retirement change management fields populated.
    ruleMessage = 'RULE TO CHECK: Features with [MODIFICATION_TYPE] flagged as NEW or MODIFIED must NOT have [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],[RETIREMENT_REASON], or [RETIREMENT_INITIATOR_OF_CHANGE] filled out.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n") 
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"MODIFICATION_TYPE\" IN ('NEW', 'MODIFIED') AND (\"RETIREMENT_DATE\" is not null OR \"RETIREMENT_GIS_CHANGE_PERSON\" is not null OR \"RETIREMENT_REASON\" is not null OR \"RETIREMENT_INITIATOR_OF_CHANGE\" is not null OR \"RETIREMENT_GIS_CHANGE_PERSON\" <> '' OR \"RETIREMENT_REASON\" <>'' OR \"RETIREMENT_INITIATOR_OF_CHANGE\" <> '')")
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
        #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " features flagged as NEW or MODIFIED features have one or more of the\n")
        fh.write("             following RETIREMENT change management attributes filled in:\n")
        fh.write("             [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],\n")
        fh.write("             [RETIREMENT_REASON],[RETIREMENT_INITIATOR_OF_CHANGE]\n")
        
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else:
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    
# Check: RETIREMENT or PERMANENT RETIREMENT features must have all retirement fields populated.
    
    ruleMessage = 'RULE TO CHECK: Features with [MODIFICATION_TYPE] flagged as RETIREMENT or PERMANENT_RETIREMENT must have [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],[RETIREMENT_REASON], or [RETIREMENT_INITIATOR_OF_CHANGE] filled out.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n") 
    #BUG - High: Query uses 'PERMANENT_RETIREMENT' (underscore) but the actual GDB domain value is
    #BUG - High: 'PERMANENT RETIREMENT' (space). This IN() clause matches ZERO features — the entire
    #BUG - High: check is silently skipped for permanently retired features with missing retirement attributes.
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" IN ('RETIREMENT', 'PERMANENT_RETIREMENT') AND (\"RETIREMENT_DATE\" is null OR \"RETIREMENT_GIS_CHANGE_PERSON\" is null OR \"RETIREMENT_REASON\" is null OR \"RETIREMENT_INITIATOR_OF_CHANGE\" is null OR \"RETIREMENT_GIS_CHANGE_PERSON\" = '' OR \"RETIREMENT_REASON\" = '' OR \"RETIREMENT_INITIATOR_OF_CHANGE\" = '')")
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    
        #if there are any mismatches, get the # and report out on all unique IDs
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " features flagged as RETIREMENT or PERMANENT RETIREMENT missing one\n")
        fh.write("             or more of the following RETIREMENT change management attributes:\n")
        fh.write("             [RETIREMENT_DATE],[RETIREMENT_GIS_CHANGE_PERSON],\n")
        fh.write("             [RETIREMENT_REASON],[RETIREMENT_INITIATOR_OF_CHANGE]\n")    
        rows = arcpy.SearchCursor('fc_lyr')
        row = rows.next()
        uniqueList = []
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
        
        for uniqueID in uniqueList:
            fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
        fh.write('\n')
    
    else:
        fh.write(noErrorsMessage + '\n')
        

    fh.write('\n') 
    arcpy.AddMessage('') 

    
    # Check: IDIR usernames in all four change management person fields must be uppercase.
    ruleMessage = 'RULE TO CHECK: IDIR values in change management attributes must be uppercase.'    
    arcpy.AddMessage(ruleMessage)
    fh.write(ruleMessage + "\n") 
    arcpy.SelectLayerByAttribute_management("fc_lyr", "CLEAR_SELECTION")
    okCount = 0
    gisChangePersonList = []
    initiatorOfChangeList = []
    retirementGISChangePersonList = []
    retirementInitiatorOfChangeList = []
    rows = arcpy.SearchCursor('fc_lyr')
    row = rows.next()
    while row:
        if row.getValue("GIS_CHANGE_PERSON") not in gisChangePersonList:
            if row.getValue("GIS_CHANGE_PERSON")<> None:
                gisChangePersonList.append(row.getValue("GIS_CHANGE_PERSON"))  
        if row.getValue("INITIATOR_OF_CHANGE") not in initiatorOfChangeList:
            if row.getValue("INITIATOR_OF_CHANGE")<> None:
                initiatorOfChangeList.append(row.getValue("INITIATOR_OF_CHANGE"))
        if row.getValue("RETIREMENT_GIS_CHANGE_PERSON") not in retirementGISChangePersonList:
            if row.getValue("RETIREMENT_GIS_CHANGE_PERSON")<> None:
                retirementGISChangePersonList.append(row.getValue("RETIREMENT_GIS_CHANGE_PERSON"))
        if row.getValue("RETIREMENT_INITIATOR_OF_CHANGE") not in retirementInitiatorOfChangeList:
            if row.getValue("RETIREMENT_INITIATOR_OF_CHANGE")<> None:
                retirementInitiatorOfChangeList.append(row.getValue("RETIREMENT_INITIATOR_OF_CHANGE"))
        row = rows.next()
    
    # Collect unique values from all four person fields for uppercase validation.
    #Checking for uppercase in GIS_CHANGE_PERSON
    # Check GIS_CHANGE_PERSON values for lowercase characters; select and report offending feature IDs.
    tempList = []
    for x in gisChangePersonList:
        if x.isupper() <> True:
            tempList.append(str(x))
    uniqueList = []
    for x in tempList:
        selectionString = "\"GIS_CHANGE_PERSON\" = " + "'" + x + "'"
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
    if len(uniqueList)>0:
        fh.write("***ERROR --> " + str(arcpy.GetCount_management("fc_lyr")) + " features have lowercase text in GIS_CHANGE_PERSON field: \n")
        for uniqueID in uniqueList:
            fh.write('        ' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            okCount = okCount + 1
        fh.write('\n')
    
    # Check INITIATOR_OF_CHANGE values for lowercase characters.
    #Checking for uppercase in INITIATOR_OF_CHANGE
    tempList = []
    for x in initiatorOfChangeList:
        if x.isupper() <> True:
            tempList.append(str(x))
    uniqueList = []
    for x in tempList:
        selectionString = "\"INITIATOR_OF_CHANGE\" = " + "'" + x + "'"
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
    if len(uniqueList)>0:
        fh.write("***ERROR --> " + str(arcpy.GetCount_management("fc_lyr")) + " features have lowercase text in INITIATOR_OF_CHANGE field: \n")
        for uniqueID in uniqueList:
            fh.write('                ' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            okCount = okCount + 1
        fh.write('\n')
        
    # Check RETIREMENT_GIS_CHANGE_PERSON values for lowercase characters.
    #Checking for uppercase in RETIREMENT_GIS_CHANGE_PERSON
    tempList = []
    for x in retirementGISChangePersonList:
        if x.isupper() <> True:
            if x.isspace <> True:
                tempList.append(str(x))
    uniqueList = []
    for x in tempList:
        selectionString = "\"RETIREMENT_GIS_CHANGE_PERSON\" = " + "'" + x + "'"
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
    if len(uniqueList)>0:
        fh.write("***ERROR --> " + str(arcpy.GetCount_management("fc_lyr")) + " features have lowercase text in RETIREMENT_GIS_CHANGE_PERSON field: \n")
        for uniqueID in uniqueList:
            fh.write('                ' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            okCount = okCount + 1
        fh.write('\n')
    
        #Checking for uppercase in RETIREMENT_INITIATOR_OF_CHANGE
    # Check RETIREMENT_INITIATOR_OF_CHANGE values for lowercase characters.
    tempList = []
    for x in retirementInitiatorOfChangeList:
        if x.isupper() <> True:
            tempList.append(str(x))
    uniqueList = []
    for x in tempList:
        selectionString = "\"RETIREMENT_INITIATOR_OF_CHANGE\" = " + "'" + x + "'"
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        while row:
            if row.getValue(uniqueIDField) not in uniqueList:
                uniqueList.append(row.getValue(uniqueIDField))
            row = rows.next()
        uniqueList.sort()
    if len(uniqueList)>0:
        fh.write("***ERROR --> " + str(arcpy.GetCount_management("fc_lyr")) + " features have lowercase text in RETIREMENT_INITIATOR_OF_CHANGE field: \n")
        for uniqueID in uniqueList:
            fh.write('                ' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            okCount = okCount + 1
        fh.write('\n')
    
    if okCount == 0: 
        fh.write(noErrorsMessage + '\n')
          
  
    
    fh.write('\n')
    fh.write('\n')
    fh.write('\n')
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 3: Validate legalization and approval dates against feature class type and associated legislation.
def section_3_check_legalization_and_approval_attributes():
    section = '----------Section 3----------'
    arcpy.AddMessage(section)
    
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + '\n')
    
    fh.write("CHECK APPROVAL & LEGALIZATION ATTRIBUTES: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n')
    
    # Branch on feature class name to set the correct date field and query for each dataset type.
    #set up variables based on feature class name:
    if featClassName == 'landscape_unit_poly':
        arcpy.AddMessage('    Not applicable for Landscape Units...')
        fh.write('Not applicable for Landscape Units... \n')
    
    if featClassName[:31] == 'slrp_planning_feature_non_legal':
        arcpy.AddMessage('    Not applicable for Non-Legal Planning Features...')
        fh.write('Not applicable for Non-Legal Planning Features... \n')
    
    
    # SLRP legal planning features: LEGALIZATION_DATE must be present and after 1900-01-01.
    if featClassName[:27] == 'slrp_planning_feature_legal':
        ruleMessage = "RULE TO CHECK: Legal features must have [LEGALIZATION_DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        
        selectQuery = "\"LEGALIZATION_DATE\" IS NULL or \"LEGALIZATION_DATE\" < date'1900-01-01'"
        fieldName = "[LEGALIZATION_DATE]"
 
    # Legal OGMAs: LEGALIZATION_DATE must be present and after 1900-01-01.
    if featClassName == 'old_growth_management_area_legal_bc_poly':
        ruleMessage = "RULE TO CHECK: Legal features must have [LEGALIZATION_DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        
        selectQuery = "\"LEGALIZATION_DATE\" IS NULL or \"LEGALIZATION_DATE\" < date'1900-01-01'"
        fieldName = "[LEGALIZATION_DATE]"
    
    
    # SLRP planning boundaries: approved boundaries must have APPROVAL_DATE filled in.
    if featClassName == 'slrp_planning_boundary_bc_poly': 
        ruleMessage = "RULE TO CHECK: Approved features must have [APPROVAL_DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")

        #BUG - High: SQL operator precedence error. AND binds tighter than OR, so the query evaluates as:
        #BUG - High: (PLAN_STATUS='Approved' AND APPROVAL_DATE is null) OR (APPROVAL_DATE < date'1900-01-01').
        #BUG - High: The second condition has no PLAN_STATUS guard — non-Approved features with pre-1900 dates
        #BUG - High: produce false positives. Fix: wrap the OR in parentheses.
        selectQuery = "\"PLAN_STATUS\" = 'Approved' AND \"APPROVAL_DATE\" is null or \"APPROVAL_DATE\" < date'1900-01-01'"
        fieldName = "[APPROVAL_DATE]"
       
    
    # Run the date-presence query for all applicable feature classes and report affected feature IDs.
    if featClassName not in ('landscape_unit_poly', 'old_growth_management_area_legal_bc_poly', 'old_growth_management_area_non_legal_bc_poly'):
        if featClassName[:31] <>  'slrp_planning_feature_non_legal':
            #get list of errors & report out
            arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
            arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", selectQuery)
            errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
            if errorCount > 0:
                fh.write("***ERROR --> " + str(errorCount) + " features have " + fieldName + " missing:\n")
                rows = arcpy.SearchCursor('fc_lyr')
                row = rows.next()
                uniqueList = []
                while row:
                    if row.getValue(uniqueIDField) not in uniqueList:
                        uniqueList.append(row.getValue(uniqueIDField))
                    row = rows.next()
                uniqueList.sort()
                for uniqueID in uniqueList:
                    fh.write('                ' + uniqueIDField + ' ' + str(uniqueID) + '\n')
                fh.write('\n')
                fh.write('\n')
        
            else:
                fh.write(noErrorsMessage + '\n')
                
    
    
    
    
    # Legal OGMAs only: validate that Act-specific date fields match the value in ASSOCIATED_ACT_NAME.
    #Legal OGMAs only:
    # Check: features with ASSOCIATED_ACT_NAME = 'FRPA and OGAA' must have BOTH date fields populated.
    if featClassName == 'old_growth_management_area_legal_bc_poly':
        ruleMessage = "RULE TO CHECK: Features with [ASSOCIATED_ACT_NAME] = 'FRPA and OGAA' must have [LEGALIZATION_FRPA_DATE] AND [LEGALIZATION_OGAA_DATE] filled in."   
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"ASSOCIATED_ACT_NAME\" = 'FRPA and OGAA' AND (\"LEGALIZATION_FRPA_DATE\" is null OR \"LEGALIZATION_OGAA_DATE\" is null OR \"LEGALIZATION_FRPA_DATE\" < date'1920-01-01' OR \"LEGALIZATION_OGAA_DATE\" < date'1920-01-01')")
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        #BUG - Low: Debug print statement left in production code. Python 3 syntax error if script is ported.
        print 'cow', errorCount
        
            #if there are any mismatches, get the # and report out on all unique IDs
        if errorCount > 0:
            fh.write("***ERROR --> " + str(errorCount) + " features with [ASSOCIATED_ACT_NAME] = FRPA and OGAA is missing either [LEGALIZATION_FRPA_DATE] or [LEGALIZATION_OGAA_DATE].\n")  
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
            uniqueList.sort()
            
            for uniqueID in uniqueList:
                fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            fh.write('\n')
        
        else:
            fh.write(noErrorsMessage + '\n')
            
            
        fh.write('\n')  
        arcpy.AddMessage('') 
        
        
        # Check: features with ASSOCIATED_ACT_NAME = 'OGAA' must have LEGALIZATION_OGAA_DATE filled in.
        ruleMessage = "RULE TO CHECK: Features with [ASSOCIATED_ACT_NAME] = 'OGAA' must have [LEGALIZATION_OGAA_DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"ASSOCIATED_ACT_NAME\" = 'OGAA' AND (\"LEGALIZATION_OGAA_DATE\" is null OR \"LEGALIZATION_OGAA_DATE\" < date'1920-01-01')")
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        
            #if there are any mismatches, get the # and report out on all unique IDs
        if errorCount > 0:
            fh.write("***ERROR --> " + str(errorCount) + " features with [ASSOCIATED_ACT_NAME] = OGAA are missing [LEGALIZATION_OGAA_DATE].\n")  
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
            uniqueList.sort()
            
            for uniqueID in uniqueList:
                 fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            fh.write('\n')
        
        else: 
            fh.write(noErrorsMessage + '\n')
            
            
        fh.write('\n')  
        arcpy.AddMessage('') 
        
        
        # Check: features with ASSOCIATED_ACT_NAME = 'OGAA' must NOT have LEGALIZATION_FRPA_DATE filled in.
        ruleMessage = "RULE TO CHECK: Features with [ASSOCIATED_ACT_NAME] = 'OGAA' must have [LEGALIZATION_OGAA DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        #BUG - High: Logic error — IS NOT NULL OR > should be IS NOT NULL AND >.
        #BUG - High: A null FRPA_DATE satisfies neither sub-condition but OR means a null value
        #BUG - High: with date < 1920 may still pass. FRPA contamination on OGAA-only features may be missed.
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"ASSOCIATED_ACT_NAME\" = 'OGAA' AND (\"LEGALIZATION_FRPA_DATE\" is not null OR \"LEGALIZATION_FRPA_DATE\" > date'1920-01-01')")
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        
            #if there are any mismatches, get the # and report out on all unique IDs
        if errorCount > 0:
            fh.write("***ERROR --> " + str(errorCount) + " features with [ASSOCIATED_ACT_NAME] = OGAA have [LEGALIZATION_FRPA_DATE] filled in.\n")  
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
            uniqueList.sort()
            
            for uniqueID in uniqueList:
                 fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            fh.write('\n')
        
        else: 
            fh.write(noErrorsMessage + '\n')
            
            
        fh.write('\n')  
        arcpy.AddMessage('') 
        
        
        # Check: features with ASSOCIATED_ACT_NAME = 'FRPA' must have LEGALIZATION_FRPA_DATE filled in.
        ruleMessage = "RULE TO CHECK: Features with [ASSOCIATED_ACT_NAME] = 'FRPA' must have [LEGALIZATION_FRPA_DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"ASSOCIATED_ACT_NAME\" = 'FRPA' AND (\"LEGALIZATION_FRPA_DATE\" is null OR \"LEGALIZATION_FRPA_DATE\" < date'1920-01-01')")
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        
            #if there are any mismatches, get the # and report out on all unique IDs
        if errorCount > 0:
            fh.write("***ERROR --> " + str(errorCount) + " features with [ASSOCIATED_ACT_NAME] = FRPA are missing [LEGALIZATION_FRPA_DATE].\n")  
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
            uniqueList.sort()
            
            for uniqueID in uniqueList:
                 fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            fh.write('\n')
        
        else: 
            fh.write(noErrorsMessage + '\n')
            
            
        fh.write('\n')  
        arcpy.AddMessage('') 
        
        
        # Check: features with ASSOCIATED_ACT_NAME = 'FRPA' must NOT have LEGALIZATION_OGAA_DATE filled in.
        ruleMessage = "RULE TO CHECK: Features with [ASSOCIATED_ACT_NAME] = 'FRPA' must not have [LEGALIZATION_OGAA DATE] filled in."
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        #BUG - High: Same IS NOT NULL OR > logic error as line 919, but for OGAA date on FRPA-only features.
        #BUG - High: OGAA date contamination on FRPA-only features may not be caught.
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"ASSOCIATED_ACT_NAME\" = 'FRPA' AND (\"LEGALIZATION_OGAA_DATE\" is not null OR \"LEGALIZATION_OGAA_DATE\" > date'1920-01-01')")
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        
            #if there are any mismatches, get the # and report out on all unique IDs
        if errorCount > 0:
            fh.write("***ERROR --> " + str(errorCount) + " features with [ASSOCIATED_ACT_NAME] = FRPA have [LEGALIZATION_OGAA_DATE] filled in.\n")  
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
            uniqueList.sort()
            
            for uniqueID in uniqueList:
                 fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            fh.write('\n')
        
        else:
            fh.write(noErrorsMessage + '\n')
            
            
        fh.write('\n')  
        arcpy.AddMessage('') 
        
    # Both legal and non-legal OGMAs: ASSOCIATED_ACT_NAME must not be null, blank, or a false null string.
    #legal & non-legal ogmas
    if featClassName[:3] == 'old':
        ruleMessage = "RULE TO CHECK: [ASSOCIATED_ACT_NAME] must not be null"
        arcpy.AddMessage(ruleMessage)
        fh.write(ruleMessage + "\n")
        
        arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"ASSOCIATED_ACT_NAME\" in ('', ' ', 'NULL','Null','null','<NULL>','<Null>','<null>') OR \"ASSOCIATED_ACT_NAME\" is null")
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        
            #if there are any mismatches, get the # and report out on all unique IDs
        if errorCount > 0:
            fh.write("***ERROR --> " + str(errorCount) + " features have a blank, null, or false null [ASSOCIATED_ACT_NAME]\n")  
            rows = arcpy.SearchCursor('fc_lyr')
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    #BUG - High: uniqueList.append(uniqueIDField) appends the field NAME string (e.g. 'NON_LEGAL_OGMA_INTERNAL_ID')
                    #BUG - High: instead of row.getValue(uniqueIDField). Fix: uniqueList.append(row.getValue(uniqueIDField)).
                    #BUG - High: The error count is correct but affected feature IDs cannot be identified from the report.
                    uniqueList.append(uniqueIDField)
                row = rows.next()
            uniqueList.sort()
            
            for uniqueID in uniqueList:
                 fh.write('                *' + uniqueIDField + ' ' + str(uniqueID) + '\n')
            fh.write('\n')
        
        else:
            fh.write(noErrorsMessage + '\n')
            
    
    


    fh.write('\n') 
    fh.write('\n')  
    fh.write('\n')      
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 4: Ensure no feature has a zero or null value in its unique ID or provincial ID fields.
def section_4_check_for_0_or_null_in_FEATID_and_PROVID():
    section = '----------Section 4----------'
    arcpy.AddMessage(section)
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    fh.write('\n')
    
    fh.write("CHECK FOR ZEROES,BLANKS,NULLS IN FEATID AND PROVID FIELDS: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n')
    
    # Check the unique feature ID field for zero or null values.
    #Check featID for 0's
    checkMessage = 'RULE TO CHECK: Feature ID field must not have any zeroes, blanks, or NULLs.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    selectionString = "\"" + uniqueIDField + "\" = 0 OR \"" + uniqueIDField + "\" IS NULL"
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    if errorCount > 0:
        fh.write("***ERROR --> " + str(errorCount) + " features have FEATID that is 0, blank, or NULL.\n")
    else:
        fh.write(noErrorsMessage + '\n')
        
    
    fh.write('\n')
    arcpy.AddMessage('')
    
    
    # Check the provincial ID field for zero or null values.
    #check provID for 0's
    checkMessage = 'RULE TO CHECK: ProvID field must not have any zeroes, blanks, or NULLs.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    if featClassName in ('landscape_unit_poly', 'slrp_planning_boundary_bc_poly'): 
        selectionString = "\"" + provIDField + "\" = 0 OR \"" + provIDField + "\" IS NULL"
    else:
        selectionString = "\"" + provIDField + "\" is NULL OR \"" + provIDField + "\" = '' OR \"" + provIDField + "\" = '0'"  
    arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", selectionString)
    errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
    if errorCount:
        fh.write("***ERROR --> " + str(errorCount) + " features have PROVID that is 0, blank, or NULL.\n")
    # SECTION 5: Check for gaps in the sequential PROV_ID numbering across the dataset.
    else: 
        fh.write(noErrorsMessage + '\n')
        


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    # OGMA datasets: collect all PROV_IDs, find the range min/max, and flag any missing integers.
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')
            
def section_5_check_for_gaps_in_PROVID():
    section = '----------Section 5----------'
    arcpy.AddMessage(section)
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    
    fh.write("CHECK FOR GAPS IN PROVID: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n')
    
    checkMessage = 'RULE TO CHECK: ProvID field must not have gaps in sequential numbering.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    #OGMAS are not checked for PROVID gaps
    okTest = 0
    if featClassName in ('old_growth_management_area_legal_bc_poly','old_growth_management_area_non_legal_bc_poly'):
        textString = '***OGMAs are not checked for gaps in PROV ID at this time***'
        arcpy.AddMessage('        ' + textString)
        fh.write('        ' + textString + '\n')
        fh.write("\n")
    
        #slrp planning features (legal & non legal, point/line/poly)
    # SLRP planning features: parse compound PROV_IDs (e.g. CAR_20_123) grouped by SLRP ID segment.
    if featClassName[:21] == 'slrp_planning_feature':
        arcpy.SelectLayerByAttribute_management('fc_lyr', "CLEAR_SELECTION")
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
    
        fcProvIDList = []    
        while row:
            if row.getValue(provIDField) not in fcProvIDList:
                fcProvIDList.append(row.getValue(provIDField))
            row = rows.next()
    
        fcSLRPIDList = []
        for fcProvID in fcProvIDList:
            slrpID = fcProvID.split('_')
            if len(slrpID) < 3:
                fh.write('***ERROR --> MISSING PROVID: One or more features has a missing or incomplete value in PROVID\n')
                okTest = okTest + 1
            else:
                if slrpID[1] not in fcSLRPIDList:
                    fcSLRPIDList.append(slrpID[1])
          
        fcProvIDDict = {}
        specialFCProvIDDict = {}
        for fcSLRPID in fcSLRPIDList:
            selectionString = provIDField + " like " + "'%$_" + fcSLRPID + "$_%' ESCAPE '$'"
            arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            
            subsetProvIDList = [] 
            # Skeena special case: features with SKE_17, SKE_20, SKE_23 prefixes have known mass-deletion gaps;
            specialSubsetProvIDList = []  ##### dealing with special case due to Skeena mass deletions (Sept 2015) #####
            # route them to a separate list with hardcoded minimum values to avoid false gap errors.
            while row:
                if row.getValue(provIDField)[0:6] == 'SKE_17':  ##### dealing with special case due to Skeena mass deletions (Sept 2015) #####
                    specialSubsetProvIDList.append(row.getValue(provIDField))
                elif row.getValue(provIDField)[0:6] == 'SKE_20':  ##### dealing with special case due to Skeena mass deletions (Sept 2015) #####
                    specialSubsetProvIDList.append(row.getValue(provIDField))
                elif row.getValue(provIDField)[0:6] == 'SKE_23':  ##### dealing with special case due to Skeena mass deletions (Sept 2015) #####
                    specialSubsetProvIDList.append(row.getValue(provIDField))
                elif row.getValue(provIDField) not in subsetProvIDList:
                    subsetProvIDList.append(row.getValue(provIDField))
                row = rows.next()
    
            # Extract the numeric suffix from each PROV_ID and build a dictionary keyed by SLRP ID segment.
            provIDSuffixList = []
            for subsetProvID in subsetProvIDList:
                provIDEndBit = subsetProvID.split('_')
                if provIDEndBit[2] not in provIDSuffixList:
                    provIDSuffixList.append(provIDEndBit[2])
            
            specialProvIDSuffixList = []
            for subsetProvID in specialSubsetProvIDList:
                provIDEndBit = subsetProvID.split('_')
                if provIDEndBit[2] not in provIDSuffixList:
                    specialProvIDSuffixList.append(provIDEndBit[2])
                  
            fcProvIDDict[fcSLRPID] = provIDSuffixList
              
        # Walk each SLRP segment's suffix list and flag any integer gaps between min and max.
        for fcProvID in fcProvIDDict:
            maxfcProvID = -99999999999999
            minfcProvID = 99999999999999
            for fcSLRPID in fcProvIDDict[fcProvID]:
                if int(fcSLRPID) < minfcProvID:
                    minfcProvID = int(fcSLRPID)
                if int(fcSLRPID) > maxfcProvID:
                    maxfcProvID = int(fcSLRPID)
            
            tempList = []
            for d in fcProvIDDict[fcProvID]:
                tempList.append(int(d))
            
            
    
            for fcSLRPID in range(minfcProvID, maxfcProvID):
                c = tempList.count(fcSLRPID)
                if c < 1 == True:
                    fh.write('***ERROR --> PROV_ID Gap: XXX_' + str(fcProvID) + "_" + str(fcSLRPID) + ' is missing \n')
                    okTest = okTest + 1
        
        for fcProvID in specialFCProvIDDict:
            maxfcProvID = -99999999999999
            minfcProvID = 99999999999999
            for fcSLRPID in specialFCProvIDDict[fcProvID]:
                if int(fcSLRPID) == 17:
                    minfcProvID = 30069
                if int(fcSLRPID) == 20:
                    minfcProvID = 12552
                if int(fcSLRPID) == 23:
                    minfcProvID = 143
                    
# #                 if int(fcSLRPID) < minfcProvID:
# #                     minfcProvID = int(fcSLRPID)
# #                 if int(fcSLRPID) > maxfcProvID:
# #                     maxfcProvID = int(fcSLRPID)
            
            tempList = []
            for d in specialFCProvIDDict[fcProvID]:
                tempList.append(int(d))
            
            
    
            for fcSLRPID in range(minfcProvID, maxfcProvID):
                c = tempList.count(fcSLRPID)
                if c < 1 == True:
                    fh.write('***ERROR --> PROV_ID Gap: XXX_' + str(fcProvID) + "_" + str(fcSLRPID) + ' is missing \n')
                    okTest = okTest + 1

    

    # SLRP boundaries and Landscape Units: check for gaps in the flat integer PROV_ID sequence.
    #slrp boundaries or lu
    if featClassName in ('slrp_planning_boundary_bc_poly', 'landscape_unit_poly'):
        
        arcpy.SelectLayerByAttribute_management("fc_lyr", "CLEAR_SELECTION")
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
    
        fcProvIDList = []  
        
        while row:
            if row.getValue(provIDField) not in fcProvIDList:
                fcProvIDList.append(row.getValue(provIDField))
            row = rows.next()
        
        for fcProvID in fcProvIDList:
            maxfcProvID = -99999999999999
            if int(fcProvID) > maxfcProvID:
                maxfcProvID = int(fcProvID)
            
        tempList = []
        for d in fcProvIDList:
            tempList.append(int(d))
        
        # Hardcoded starting values for gap checks: LU starts at 2164, SLRP boundary starts at 93.
        if featClassName == 'landscape_unit_poly':
            a = 2164
        if featClassName == 'slrp_planning_boundary_bc_poly':
            a = 93
        for y in range(a, maxfcProvID):
            c = tempList.count(y)
            if c < 1 == True:
                fh.write('***ERROR --> PROV_ID Gap: ' +  str(y) + ' is missing \n')   
                okTest = okTest + 1
        
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 6: Check for gaps in the sequential unique feature ID (FEAT_ID / INTERNAL_ID) numbering.
def section_6_check_for_gaps_in_feature_id():   
    section = '----------Section 6----------'
    arcpy.AddMessage(section)        
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    
    fh.write("CHECK FOR GAPS IN FEATURE ID FIELD: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n')
    
    
    okTest = 0
        # SLRP planning features: collect FEAT_IDs from ALL feature classes of the same type in the FDS.
        #lo/nlpf
    if featClassName[:21] == 'slrp_planning_feature':
        checkMessage = 'RULE TO CHECK: Feature ID field must not have any gaps in sequential numbering.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 
        
        env.workspace = fdsPath
        fcList = arcpy.ListFeatureClasses()
        fcList2 = []        
        for x in fcList:
            if featClassName[:27] == 'slrp_planning_feature_legal':
                if featClassName[:27] == x[:27]:
                    if featClassName[-4:] == x[-4:]:
                        fcList2.append(x)
            if featClassName[:31] == 'slrp_planning_feature_non_legal':
                if featClassName[:31] == x[:31]:
                    if featClassName[-4:] == x[-4:]:
                        fcList2.append(x)
              

        # Build a combined FEAT_ID list across all matching feature classes for cross-FC gap detection.
        featIDList = []    
        for x in fcList2: 
            arcpy.MakeFeatureLayer_management(x, "featClass_lyr", "", "")    
            rows = arcpy.SearchCursor("featClass_lyr")
            row = rows.next()
            while row:
                if row.getValue(uniqueIDField) not in featIDList:
                    featIDList.append(row.getValue(uniqueIDField))
                featIDList.sort()
                row = rows.next()
        
        # Hardcoded start value of 500000: skips IDs voided by historical mass deletions.
        maxX = max(featIDList)
                        
                 
        for y in range(500000, maxX): ############### Starts at 237247 because of mass deletion of Skeena non-legal records in 2015! ##############
            c = featIDList.count(y)
            if c < 1 == True:
                fh.write('***ERROR --> FEAT_ID Gap: ' +  str(y) + ' is missing \n') 
                okTest = okTest + 1
            
                          
        # SLRP boundaries and Landscape Units: collect IDs from single FC and check for gaps.
        #slrp boundaries / lu's
    elif featClassName in ('landscape_unit_poly', 'slrp_planning_boundary_bc_poly'):        
        if featClassName == 'landscape_unit_poly':
            checkMessage = 'RULE TO CHECK: [LANDSCAPE_UNIT_ID] field must not have any gaps in sequential numbering.'
            arcpy.AddMessage(checkMessage)
            fh.write(checkMessage + "\n") 
        else:
            checkMessage = 'RULE TO CHECK: [STRGC_LAND_RSRCE_PLAN_ID] field must not have any gaps in sequential numbering.'
            arcpy.AddMessage(checkMessage)
            fh.write(checkMessage + "\n") 

            
        arcpy.SelectLayerByAttribute_management("fc_lyr", "CLEAR_SELECTION")
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        featIDList = []
        while row:
            if row.getValue(uniqueIDField) not in featIDList:
                featIDList.append(row.getValue(uniqueIDField))
            featIDList.sort()
            row = rows.next()
           
        for x in featIDList:
            maxX = -9999999999999999999
            if int(x) > maxX:
                maxX = int(x)
            
        tempList = []
        for d in featIDList:
            tempList.append(int(d))
        
        # Hardcoded start values: SLRP boundary starts at 123, Landscape Unit starts at 1919.
        if featClassName == 'slrp_planning_boundary_bc_poly':
            a = 123
        if featClassName == 'landscape_unit_poly':
            a = 1919
        
        for y in range(a, maxX):
            c = tempList.count(y)
            if c < 1 == True:
                if featClassName == 'landscape_unit_poly':
                    fh.write('***ERROR --> LANDSCAPE_UNIT_ID Gap: ' +  str(y) + ' is missing \n')
                    okTest = okTest + 1 
                else:
                    fh.write('***ERROR --> STRGC_LAND_RSRCE_PLAN_ID Gap: ' +  str(y) + ' is missing \n') 
                    okTest = okTest + 1
                
    
        # OGMAs: collect OGMA_INTERNAL_IDs and check for gaps from hardcoded start value.
        #ogmas
    else:
        checkMessage = 'RULE TO CHECK: OGMA_INTERNAL_ID field must not have any gaps in sequential numbering.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n")
        arcpy.SelectLayerByAttribute_management("fc_lyr", "CLEAR_SELECTION", "")
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        featIDList = []
        while row:
            if row.getValue(uniqueIDField) not in featIDList:
                featIDList.append(row.getValue(uniqueIDField))
            row = rows.next()
            
        for x in featIDList:
            maxX = -9999999999999999999
            if int(x) > maxX:
                maxX = int(x)
            
        tempList = []
        for d in featIDList:
            tempList.append(int(d))
    
        # Hardcoded start value of 500000 for both legal and non-legal OGMAs.
        if featClassName == 'old_growth_management_area_legal_bc_poly':
            a = 500000 #changes occasionally when mistakes are made - just grab the highest FEAT_ID number and put it in here to skip any gaps prior to this number
        if featClassName == 'old_growth_management_area_non_legal_bc_poly':
            a = 500000 #changes occasionally when mistakes are made - just grab the highest FEAT_ID number and put it in here to skip any gaps prior to this number
        arcpy.AddMessage('a is ' + str(a))
        for y in range(a, maxX):
            c = tempList.count(y)
            if c < 1 == True:
                fh.write('***ERROR --> OGMA_INTERNAL_ID Gap: ' +  str(y) + ' is missing \n')
                okTest = okTest + 1
    
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 7: Check for duplicate PROV_ID / PROV_ID_PART_NUMBER combinations among current features.
def section_7_check_for_duplicate_provid_provid_part_number_in_current_records():
    section = '----------Section 7----------'
    arcpy.AddMessage(section)     
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + '\n')
    
    fh.write("CHECK FOR DUPLICATE PROVID/PROVID PART NUMBER COMIBINATIONS: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n')
    
    checkMessage = 'RULE TO CHECK: Features with a [STATUS] of CURRENT should have unique [PROVID]/[PROVID_PART_NUMBER] combinations.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    okTest = 0
    
# Set STATUS query: LU uses values 0 and 1 for current; all others use value 0 only.
    
    env.workspace = fdsPath
    arcpy.MakeFeatureLayer_management(featClassName, 'fc_lyr')
    
    #set query variables:
    if featClassName == 'landscape_unit_poly':
        statusQuery = "\"STATUS\" in (0,1)"
    else: 
        statusQuery = "\"STATUS\" = 0"
        
    # Non-OGMA feature classes: concatenate PROV_ID and PART_NUMBER with separator and check for duplicates.
    #non-ogma feature classes
    if featClassName [:3] <> 'old':
            #check that provid/provid part number are not duplicated in current features
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", statusQuery)
        fcProvIDList = []
        currentCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if currentCount > 0:
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()             
            while row:
                 a = row.getValue(provIDField)
                 b = row.getValue(provIDPartNum)
                 provID_with_part = str(a) + 'xxxxx' + str(b)
                 fcProvIDList.append(provID_with_part)
                 row = rows.next() 
        
        dupProvIDList = []
        for x in fcProvIDList:
            if fcProvIDList.count(x)> 1:
                if x not in dupProvIDList: 
                    dupProvIDList.append(x)
        
        if len(dupProvIDList) > 0:
            for x in dupProvIDList:
                y = x.split('xxxxx')
                provID = y[0]
                fh.write('***ERROR --> PROVID/PROVID_PART_NUMBER Duplicate: PROVID ' +  str(provID) + ' with CURRENT\n')
                fh.write('             status has duplicates in [PROVID_PART_NUMBER] field.\n')
                okTest = okTest + 1
    

    # OGMAs: check for duplicate PROV_ID/PART_NUMBER combinations across BOTH legal and non-legal datasets.
    #OGMAS - will look at duplicates in provid/part number in both legal & non legal datasets
    if featClassName == 'old_growth_management_area_legal_bc_poly':
        otherOGMAfc = 'old_growth_management_area_non_legal_bc_poly'
        otherPROVID = "NON_LEGAL_OGMA_PROVID"
    if featClassName == 'old_growth_management_area_non_legal_bc_poly':
        otherOGMAfc = 'old_growth_management_area_legal_bc_poly'
        otherPROVID = "LEGAL_OGMA_PROVID"
    
    
        arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", statusQuery)
        fcProvIDList = []
        currentCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if currentCount> 0:
             rows = arcpy.SearchCursor("fc_lyr")
             row = rows.next()             
             while row:
                 a = row.getValue(provIDField)
                 b = row.getValue(provIDPartNum)
                 provID_with_part = str(a) + 'xxxxx' + str(b)
                 fcProvIDList.append(provID_with_part)
                 row = rows.next() 
                 
        # Append PROV_ID/PART_NUMBER combinations from the other OGMA dataset into the same list.
        #now read the other ogma feature class (legal or non legal) provid/part #'s into the same list
        arcpy.MakeFeatureLayer_management(otherOGMAfc, "other_ogma_lyr")
        arcpy.SelectLayerByAttribute_management("other_ogma_lyr", "NEW_SELECTION", statusQuery)
        #BUG - High: arcpy.GetCount_management('fc_lyr') checks the PRIMARY layer count, not 'other_ogma_lyr'.
        #BUG - High: If the primary layer has zero current features, the other OGMA layer is never read.
        #BUG - High: Fix: change 'fc_lyr' to 'other_ogma_lyr' to guard the correct layer.
        currentCount = int(str(arcpy.GetCount_management('fc_lyr')))
        
        if currentCount > 0:
            rows = arcpy.SearchCursor("other_ogma_lyr")
            row = rows.next()             
            while row:
                 a = row.getValue(otherPROVID)
                 b = row.getValue("PROVID_PART_NUMBER")
                 provID_with_part = str(a) + 'xxxxx' + str(b)
                 fcProvIDList.append(provID_with_part)
                 row = rows.next() 
            fcProvIDList.sort()
        
        # Find and report any PROV_ID/PART_NUMBER combinations that appear more than once.
        dupProvIDList = []
        for x in fcProvIDList:
            if fcProvIDList.count(x)> 1:
                if x not in dupProvIDList: 
                    dupProvIDList.append(x)
        
        if len(dupProvIDList) > 0:
            for x in dupProvIDList:
                y = x.split('xxxxx')
                provID = y[0]
                fh.write('***ERROR --> PROVID/PROVID_PART_NUMBER Duplicate: PROVID ' +  str(provID) + ' with CURRENT\n')
                fh.write('             status has duplicates in [PROVID_PART_NUMBER] field. NOTE: This\n')
                fh.write('             duplicate may occur in either the legal or non legal ogma feature class.\n')
                okTest = okTest + 1
                
                        
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 8: Check for duplicate values in the unique feature ID field.
def section_8_check_for_duplicates_in_featID():
    section = '----------Section 8----------'
    arcpy.AddMessage(section)
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    
    fh.write("CHECK FOR DUPLICATES IN FEATURE ID FIELD: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n')
   
    checkMessage = 'RULE TO CHECK: Values in Feature ID field must be unique.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    env.workspace = fdsPath
    arcpy.MakeFeatureLayer_management(featClassName, 'fc_lyr')  

    
# SLRP planning features: collect FEAT_IDs from all matching FCs in the feature dataset.
    
    fcList2 = []        
    if featClassName[:21] == 'slrp_planning_feature':
        fcList = arcpy.ListFeatureClasses()
        for x in fcList:
            if featClassName[:27] == 'slrp_planning_feature_legal':
                if featClassName[:27] == x[:27]:
                    if featClassName[-4:] == x[-4:]:
                        fcList2.append(x)
            if featClassName[:31] == 'slrp_planning_feature_non_legal':
                if featClassName[:31] == x[:31]:
                    if featClassName[-4:] == x[-4:]:
                        fcList2.append(x)
                     
    # All other datasets: check for duplicates within the single feature class.
    #slrp boundaries / lu's/ ogmas
    else:
        fcList2 = [featClassName]         
        
    # Build the full ID list across all relevant feature classes.
    featIDList = [] 
    
    for x in fcList2: 
        arcpy.MakeFeatureLayer_management(x, "featClass_lyr", "", "")    
        rows = arcpy.SearchCursor("featClass_lyr")
        row = rows.next()
        while row:
            featIDList.append(row.getValue(uniqueIDField))
            featIDList.sort()
            row = rows.next()
    
    # Walk the ID list and flag any value that appears more than once.
    okTest = 0        
    for y in featIDList:
        c = featIDList.count(y)
        #BUG - Low: Chained comparison "c > 1 == True" evaluates as (c > 1) and (1 == True).
        #BUG - Low: Works in Python 2/3 because 1 == True, but is misleading. Should be: if c > 1:
        if c > 1 == True:
            if featClassName[:3] == 'old':
                fh.write('***ERROR --> OGMA_INTERNAL_ID Duplicate: ' +  str(y) + ' is a duplicate \n') 
            else:
                fh.write('***ERROR --> FEAT_ID Duplicate: ' +  str(y) + ' is a duplicate \n') 
            okTest = okTest + 1

    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    
    
# SECTION 9: Validate PROV_ID pairing rules based on MODIFICATION_TYPE.
def section_9_check_for_provid_pairs_based_on_mod_type():
    section = '----------Section 9----------'
    arcpy.AddMessage(section)
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    
    fh.write("CHECK FOR PROVID PAIRS BASED ON MODIFICATION TYPE: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n') 
      
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')    
        
        # Collect unique PROV_IDs for each MODIFICATION_TYPE into separate lists for comparison.
        #get list of provIDs where MODIFICATION_TYPE = 'MODIFIED'
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" = 'MODIFIED'")   
    field = provIDField
    values = [row[0] for row in arcpy.da.SearchCursor("fc_lyr", field)]
    modifiedProvIDList = list(set(values))
    modifiedProvIDList.sort()
        
        #get list of provIDs where MODIFICATION_TYPE = 'RETIREMENT'
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" = 'RETIREMENT'")
    field = provIDField
    retirement_values = [row[0] for row in arcpy.da.SearchCursor("fc_lyr", field)]
    retiredProvIDList = list(set(retirement_values))
    retiredProvIDList.sort()
    
        #get list of provIDs where MODIFICATION_TYPE = 'PERMANENT RETIREMENT'
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" = 'PERMANENT RETIREMENT'")
    field = provIDField
    perm_retirement_values = [row[0] for row in arcpy.da.SearchCursor("fc_lyr", field)]
    perm_retiredProvIDList = list(set(perm_retirement_values))
    perm_retiredProvIDList.sort()
    
        #get list of provIDs where MODIFICATION_TYPE = 'MODIFIED_NOREPLACE'
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" = 'MODIFIED_NOREPLACE'")
    field = provIDField
    mod_noreplace_values = [row[0] for row in arcpy.da.SearchCursor("fc_lyr", field)]
    mod_noreplaceProvIDList = list(set(mod_noreplace_values))
    mod_noreplaceProvIDList.sort()
    
        #get list of provIDs where MODIFICATION_TYPE = 'NEW'
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" = 'NEW'")
    field = provIDField
    new_values = [row[0] for row in arcpy.da.SearchCursor("fc_lyr", field)]
    newProvIDList = list(set(new_values))
    newProvIDList.sort()
    
    
    #Now compare the lists & get errors if any
    
    # MODIFIED check: every MODIFIED PROV_ID must have a matching RETIREMENT PROV_ID.
    #modified checks
    checkMessage = 'RULE TO CHECK: If a feature is flagged with a [MODIFICATION_TYPE] of MODIFIED, there must be another feature with the same PROVID and the [MODIFICATION_TYPE] flagged as RETIREMENT.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
        #comparing the lists - if modified, must have matching retired feature
    okTest = 0
    errorProvIDList = [i for i in modifiedProvIDList if not i in retiredProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        
    else:
        arcpy.AddWarning('        - errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] = MODIFIED \n')
        fh.write('              without matching PROVID with [MODIFICATION_TYPE] = RETIREMENT: \n')
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')

    fh.write('\n')
    arcpy.AddMessage('')

   
   # RETIREMENT check: every RETIREMENT PROV_ID must have a matching MODIFIED PROV_ID.
   #retirement checks
    checkMessage = 'RULE TO CHECK: If a feature is flagged with a [MODIFICATION_TYPE] of RETIREMENT, there must be another feature with the same PROVID and the [MODIFICATION_TYPE] flagged as MODIFIED.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n")
    
        #comparing the lists - if retired, must have matching modified feature
    okTest = 0
    errorProvIDList = [i for i in retiredProvIDList if not i in modifiedProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] = RETIREMENT\n')
        fh.write('              without matching PROVID with [MODIFICATION_TYPE] = MODIFICATION:\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')

    fh.write('\n')
    arcpy.AddMessage('')
    
     
    # PERMANENT RETIREMENT checks: PERM RETIRED PROV_IDs must NOT appear under any other mod type.
    #permanent retirement checks
    checkMessage = 'RULE TO CHECK: If a feature is flagged with a [MODIFICATION_TYPE] of PERMANENT RETIREMENT, there must NOT be another feature with the same PROVID and the [MODIFICATION_TYPE] flagged as anything else.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n")
     
        #comparing the lists - if permanently retired not have the same provid flagged with another modification type
            # Sub-check: PERMANENT RETIREMENT vs MODIFIED.
            #perm retirement vs modified
    okTest = 0
    errorProvIDList = [i for i in perm_retiredProvIDList if i in modifiedProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             PERMANENT RETIREMENT with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = MODIFICATION\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        # Sub-check: PERMANENT RETIREMENT vs NEW.
        #perm retirement vs new
    okTest = 0
    errorProvIDList = [i for i in perm_retiredProvIDList if i in newProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of NEW\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of NEW')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             PERMANENT RETIREMENT with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = NEW\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        # Sub-check: PERMANENT RETIREMENT vs RETIREMENT.
        #perm retirement vs retirement
    okTest = 0
    errorProvIDList = [i for i in perm_retiredProvIDList if i in retiredProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of RETIRED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of RETIRED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             PERMANENT RETIREMENT with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = RETIREMENT\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        # Sub-check: PERMANENT RETIREMENT vs MODIFIED_NOREPLACE.
        #perm retirement vs modify no replace
    okTest = 0
    errorProvIDList = [i for i in perm_retiredProvIDList if i in mod_noreplaceProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED_NOREPLACE\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED_NOREPLACE')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             PERMANENT RETIREMENT with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = MODIFIED_NOREPLACE\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')

    fh.write('\n')
    fh.write('\n')
     
     
    # NEW checks: NEW PROV_IDs must NOT appear under any other modification type.
    #new checks
    checkMessage = 'RULE TO CHECK: If a feature is flagged with a [MODIFICATION_TYPE] of NEW, there must NOT be another feature with the same PROVID and the [MODIFICATION_TYPE] flagged as anything else.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
   
        #comparing the lists - if new, must not have the same provid flagged as something else
            # Sub-check: NEW vs MODIFIED.
            #new vs modified
    okTest = 0
    errorProvIDList = [i for i in newProvIDList if i in modifiedProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             NEW with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = MODIFICATION\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        #new vs perm retirement
    okTest = 0
    errorProvIDList = [i for i in newProvIDList if i in perm_retiredProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of PERMANENTLY RETIRED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of PERMANENTLY RETIRED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             NEW with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = PERMANENT RETIREMENT\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        #new vs retirement
    okTest = 0
    errorProvIDList = [i for i in newProvIDList if i in retiredProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of RETIRED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of RETIRED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             NEW with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = RETIREMENT\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        #new vs modify no replace
    okTest = 0
    errorProvIDList = [i for i in newProvIDList if i in mod_noreplaceProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        #BUG - Low: "no errors" label says [MODIFICATION_TYPE] of NEW but this sub-check is NEW vs MODIFIED_NOREPLACE.
        #BUG - Low: The label should read MODIFIED_NOREPLACE. Misleads the reviewer reading the report.
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of NEW\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of NEW')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             NEW with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = MODIFIED_NOREPLACE\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')

    fh.write('\n')
    fh.write('\n')
        
    
    # MODIFIED_NOREPLACE checks: MODIFIED_NOREPLACE PROV_IDs must NOT appear under any other mod type.
    #modify no replace checks
    checkMessage = 'RULE TO CHECK: If a feature is flagged with a [MODIFICATION_TYPE] of MODIFIED_NOREPLACE, there must NOT be another feature with the same PROVID and a [MODIFICATION_TYPE] flagged as anything else.'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
            #comparing the lists - if modify no replace, must not have the same provid flagged as something else
            # Sub-check: MODIFIED_NOREPLACE vs MODIFIED.
            #modify no replace vs modified
    okTest = 0
    errorProvIDList = [i for i in mod_noreplaceProvIDList if i in modifiedProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of MODIFIED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             MODIFIED_NOREPLACE with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = MODIFICATION\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        # Sub-check: MODIFIED_NOREPLACE vs PERMANENT RETIREMENT.
        #mod_noreplace vs perm retirement
    okTest = 0
    errorProvIDList = [i for i in mod_noreplaceProvIDList if i in perm_retiredProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of PERMANENTLY RETIRED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of PERMANENTLY RETIRED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             MODIFIED_NOREPLACE with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = PERMANENT RETIREMENT\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        # Sub-check: MODIFIED_NOREPLACE vs RETIREMENT.
        #MODIFIED_NOREPLACE vs retirement
    okTest = 0
    errorProvIDList = [i for i in mod_noreplaceProvIDList if i in retiredProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of RETIRED\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of RETIRED')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             MODIFIED_NOREPLACE with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = RETIREMENT\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')
    
        # Sub-check: MODIFIED_NOREPLACE vs NEW.
        #modify no replace vs new 
    okTest = 0
    errorProvIDList = [i for i in mod_noreplaceProvIDList if i in newProvIDList]
    if len(errorProvIDList) > 0:
        okTest = okTest + 1
    if okTest == 0:
        fh.write('  Checking for matching features with [MODIFICATION_TYPE] of NEW\n')
        fh.write(noErrorsMessage + '\n')
        arcpy.AddMessage('  Checking for matching features with [MODIFICATION_TYPE] of NEW')
        
    
    else:
        arcpy.AddWarning('        - Errors found.')
        fh.write('***ERROR --> The following PROVIDs have features with [MODIFICATION_TYPE] =\n')
        fh.write('             MODIFIED_NOREPLACE with a matching PROVID with [MODIFICATION_TYPE]\n')
        fh.write('             = NEW\n')
 
        for x in errorProvIDList:
                fh.write('                ' + provIDField + ' ' + str(x) + '\n')
    
    fh.write('\n')
    arcpy.AddMessage('')

    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')


# SECTION 10: Check for duplicate PROV_ID/PROV_ID_PART_NUMBER combinations within each MODIFICATION_TYPE.
def section_10_check_for_provID_provIDpartnumber_duplication_by_mod_type():

    #BUG - Medium: File handle opened here on line 2037 is immediately orphaned by a second open() on line 2041.
    #BUG - Medium: The first handle is never closed, holding a file lock until the process ends.
    fh = open(attributeQAReportFile, 'a')  
    
    section = '-------Section 10-------'
    arcpy.AddMessage(section)
    # Open report file for appending (note: redundant open — see BUG above).
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n") 
    
    fh.write("CHECK FOR PROVID/PROVID PART NUMBER DUPLICATION BASED ON MODIFICATION TYPE: \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n') 
   
    checkMessage = 'RULE TO CHECK: There must be no duplication of [PROVID]/[PROVID_PART_NUMBER] for features flagged with the same [MODIFICATION_TYPE].'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 

    env.workspace = fdsPath
    arcpy.MakeFeatureLayer_management(featClassName, 'fc_lyr')
    
    okTest = 0
    # Collect all distinct MODIFICATION_TYPE values present in the dataset.
    arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"MODIFICATION_TYPE\" is not NULL")
    rows = arcpy.SearchCursor("fc_lyr")
    row = rows.next()
    modificationTypeList = []
    while row:
        if row.getValue("MODIFICATION_TYPE") not in modificationTypeList:
            modificationTypeList.append(row.getValue("MODIFICATION_TYPE"))
        row = rows.next()
    modificationTypeList.sort()
    
    # For each modification type, select matching features and collect PROV_ID/PART_NUMBER pairs.
    for x in modificationTypeList:
        selectionString = "\"MODIFICATION_TYPE\" = '" + x + "'"
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if errorCount >0:
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            provIDList = []
            while row:
                provID = row.getValue(provIDField)
                partNum = row.getValue("PROVID_PART_NUMBER")
                concatenation = str(provID) + "   PROVID_PART_NUMBER " + str(partNum)
                provIDList.append(concatenation)
                row = rows.next()
            provIDList.sort()
            # Build a deduplicated list of any PROV_ID/PART_NUMBER pairs that appear more than once.
            uniqueList = []
            for y in provIDList:
                if provIDList.count(y)> 1:  
                    if y not in uniqueList:           
                        uniqueList.append(y)
                uniqueList.sort()
            if len(uniqueList)>0:
                fh.write('***ERROR --> There is duplication of [PROVID]/[PROVID_PART_NUMBER] for fields with\n')
                fh.write('             [MODIFICATION_TYPE] flagged as ' + x + ": \n")            
                for z in uniqueList:
                    fh.write('                ' + provIDField + ' ' + str(z) + '\n')
                okTest = okTest + 1
    
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')

# SECTION 11 (SLRP planning features): Check PROV_ID integrity and cross-reference against SLRP boundary dataset.
def section_11_check_lo_nlpf_boundary_specific_dependancies():
    #BUG - Medium: File handle opened unconditionally here (line 2109) and again on line 2111 and line 2115.
    #BUG - Medium: The first two handles are orphaned. Three opens, only one close. Fix: single open() after the if-check.
    fh = open(attributeQAReportFile, 'a')
    if featClassName[:21] == 'slrp_planning_feature':
        fh = open(attributeQAReportFile, 'a')  
        
        section = '-------Section 11-------'
        arcpy.AddMessage(section)
        fh = open(attributeQAReportFile, 'a')  
        fh.write(section + "\n") 
        
        fh.write("CHECK FOR SLRP ID MISMATCHES: \n")
        fh.write("-------------------------------------------------------\n")
        fh.write('\n') 
       
        #For legal & non features, check to see if PROVID [xxx_##_xxx] and SLRP Name are actually in SLRP boundary dataset 
 
        env.workspace = fdsPath
        arcpy.MakeFeatureLayer_management(featClassName, 'fc_lyr')
        arcpy.MakeFeatureLayer_management('slrp_planning_boundary_bc_poly', "slrp_lyr", "","")
    
    
    okTest = 0
    # Check that no PROV_ID is blank or has fewer than 3 underscore-delimited segments.
    if featClassName[:21] == 'slrp_planning_feature':
        checkMessage = 'RULE TO CHECK: PROVID must not be blank or incomplete.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n")         
        
        # Collect all unique PROV_IDs from the update dataset.
        arcpy.SelectLayerByAttribute_management("fc_lyr", "CLEAR_SELECTION")
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
    
        fcProvIDList = []    
        while row:
            if row.getValue(provIDField) not in fcProvIDList:
                fcProvIDList.append(row.getValue(provIDField))
            row = rows.next()
        
        # Parse the middle segment (SLRP ID) from each compound PROV_ID for boundary cross-reference.
        fcSLRPIDList = []
        for x in fcProvIDList:
            slrpID = x.split('_')
            if len(slrpID) < 3: 
                #BUG - Low: Typo in error message — "is has" should be "has". No functional impact.
                fh.write("***ERROR --> One or more features is has a blank or incomplete PROVID.\n")
                fh.write("\n")
                okTest = okTest + 1
            else: 
                if slrpID[1] not in fcSLRPIDList:
                    fcSLRPIDList.append(slrpID[1])
       
       
        # For each SLRP ID segment found in PROV_IDs, verify it exists in the SLRP boundary dataset.
        checkMessage = 'RULE TO CHECK: SLRP ID within ProvID field (i.e. SLRP ID for CAR_20_123 = 20) must exist in SLRP Boundary dataset(slrp_planning_boundary_bc_poly - [STRGC_LAND_RSRCE_PLAN_PROVID].'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 
        
        for x in fcSLRPIDList:
            y = str(x)
            selectionString = "\"STRGC_LAND_RSRCE_PLAN_PROVID\" = " + y
            arcpy.SelectLayerByAttribute_management("slrp_lyr", "NEW_SELECTION", selectionString)
            slrpProvIDCount = int(str(arcpy.GetCount_management('slrp_lyr')))
            if slrpProvIDCount == 0:
                selectionString = provIDField + " like " + "'%$_" + y + "$_%' ESCAPE '$'"
                arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
                fh.write("***ERROR --> " + str(arcpy.GetCount_management('fc_lyr')) + " features have a PROVID with SLRP ID prefix " + y + " that does not occur in the SLRP boundary dataset: \n")
                
                rows = arcpy.SearchCursor("fc_lyr")
                row = rows.next()
                uniqueList = []
                while row:
                    if row.getValue(uniqueIDField) not in uniqueList:
                        uniqueList.append(row.getValue(uniqueIDField))
                    row = rows.next()
          
                    uniqueList.sort()
            
                for x in uniqueList:
                    fh.write('                ' + uniqueIDField + ' ' + str(x) + '\n')
                fh.write('\n')
                okTest = okTest + 1
    
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            


    # Build a dictionary of current SLRP boundary PROV_IDs mapped to their SLRP plan names.
    if featClassName[:21] == 'slrp_planning_feature':
        arcpy.SelectLayerByAttribute_management("slrp_lyr", "NEW_SELECTION", "\"STATUS\" = 0")
        #read slrp boundary names and PROVID's into a dictionary
        rows = arcpy.SearchCursor("slrp_lyr")
        row = rows.next()
        slrpBoundaryDict = {}
        while row:
            slrpProvID = row.getValue("STRGC_LAND_RSRCE_PLAN_PROVID")
            slrpName = row.getValue("STRGC_LAND_RSRCE_PLAN_NAME")
            slrpBoundaryDict[slrpProvID] = slrpName
            row = rows.next()
        
        fh.write('\n')
        
        #For legal & non features, check to see if PROVID [xxx_##_xxx] matches a)region name, b)SLRP number 
    # For each current SLRP boundary, check that planning features using its SLRP ID have the correct plan name.
    if featClassName[:21] == 'slrp_planning_feature':
        checkMessage = 'RULE TO CHECK: [STRGC_LAND_RSRCE_PLAN_NAME] and [STRGC_LAND_RSRCE_PLAN_PROVID] from slrp_planning_boundary_bc_poly must match what is being put into ProvID and [STRGC_LAND_RSRCE_PLAN_NAME] fields of legal/non-legal planning features dataset being checked.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 
        
        okTest = 0   
        for x in slrpBoundaryDict:
            y = str(x)
            #BUG - Medium: SUBSET_SELECTION on line 2216 uses selectionString1 — the same string used on line 2215
            #BUG - Medium: for NEW_SELECTION. Subsetting a selection with the same query changes nothing.
            #BUG - Medium: Line 2216 should apply selectionString2 or be removed entirely.
            selectionString1 = provIDField + " like " + "'%$_" + y + "$_%' ESCAPE '$' AND STATUS = 0"
            arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString1)
            arcpy.SelectLayerByAttribute_management("fc_lyr", "SUBSET_SELECTION", selectionString1)
            selectionString2 = "\"STRGC_LAND_RSRCE_PLAN_NAME\" <> " + "'" + slrpBoundaryDict[x] + "'"
            arcpy.SelectLayerByAttribute_management("fc_lyr", "SUBSET_SELECTION", selectionString2)
            errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
            if errorCount > 0:
                fh.write("***ERROR --> " + str(errorCount) + " features have SLRP Name and PROVID prefix mismatch:\n")
                rows = arcpy.SearchCursor("fc_lyr")
                row = rows.next()
                uniqueList = []
                while row:
                    if row.getValue(uniqueIDField) not in uniqueList:
                        uniqueList.append(row.getValue(uniqueIDField))
                    row = rows.next()
          
                uniqueList.sort()
                for x in uniqueList:
                    fh.write('     ' + uniqueIDField + ' ' + str(x) + '\n')
                fh.write('\n') 
                okTest = okTest + 1
                
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
    
    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')
      
        
# SECTION 11 (Landscape Units): Validate BEO, status, and multi-part LU consistency rules.
def section_11_check_lu_beo_dependancies():
    if featClassName == 'landscape_unit_poly':
        #BUG - Medium: File handle opened on line 2252 is orphaned by a second open() on line 2256.
        #BUG - Medium: First handle is never closed. Fix: remove the duplicate open() on line 2256.
        fh = open(attributeQAReportFile, 'a')  
        
        section = '-------Section 11-------'
        arcpy.AddMessage(section)
        fh = open(attributeQAReportFile, 'a')  
        fh.write(section + "\n") 
        
        fh.write("CHECK LANDSCAPE UNIT SPECIFIC DEPENDANCIES: \n")
        fh.write("-------------------------------------------------------\n")
        fh.write('\n') 
       
        # Check: features with PROVID_PART_NUMBER = 0 must have External (not Internal) STATUS.
        #For legal & non features, check to see if PROVID [xxx_##_xxx] and SLRP Name are actually in SLRP boundary dataset 
        checkMessage = 'RULE TO CHECK: Features with [PROVID_PART_NUMBER] = 0 must have [STATUS] set to External-Current or External-Retired.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 

        #Check that where provid part number = 0, status <> internal (current or retired) 
        env.workspace = fdsPath
        arcpy.MakeFeatureLayer_management(featClassName, 'fc_lyr')
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"PROVID_PART_NUMBER\" = 0 and \"STATUS\" in (1,3)")
        okTest = 0
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if errorCount>0:
            fh.write("***ERROR --> " + str(errorCount) + " features have status set to INTERNAL that should be EXTERNAL:\n")
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
          
            uniqueList.sort()
          
            for x in uniqueList:
                fh.write('                ' + uniqueIDField + ' ' + str(x) + '\n')
            fh.write('\n')
            okTest = okTest + 1
    
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
        
        # Check: External features with BEO_SUB_TYPE_APPLICABLE = Yes must have BIODIVERSITY_EMPHASIS_OPTION = Multiple.
        #Check that where status = external, if beo subtype = yes then beo value = multiple
        checkMessage = 'RULE TO CHECK: Features with [STATUS] set to External-Current or External-Retired AND [BEO_SUB_TYPE_APPLICABLE] = Yes must also have [BIODIVERSITY_EMPHASIS_OPTION] set to Multiple'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 

        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"STATUS\" in (0,2) and \"BEO_SUB_TYPE_APPLICABLE\" = 'Y' AND \"BIODIVERSITY_EMPHASIS_OPTION\" <> 'Multiple'")
        okTest = 0
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if errorCount>0:
            fh.write("***ERROR --> " + str(errorCount) + " features have [BIODIVERSITY_EMPHASIS_OPTION] other than Multiple:\n")
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
          
            uniqueList.sort()
          
            for x in uniqueList:
                fh.write('                ' + uniqueIDField + ' ' + str(x) + '\n')
            fh.write('\n')
            okTest = okTest + 1
         
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
        
        # Check: External features with BEO_SUB_TYPE_APPLICABLE = No must have PROVID_PART_NUMBER = 0.
        #Check that where status = external, if beo subtype = no then provID part number = 0
        checkMessage = 'RULE TO CHECK: Features with [STATUS] set to External-Current or External-Retired AND [BEO_SUB_TYPE_APPLICABLE] = No must have [PROVID_PART_NUMBER] = 0.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 

        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"STATUS\" in (0,2) and \"BEO_SUB_TYPE_APPLICABLE\" = 'N' AND \"PROVID_PART_NUMBER\" <> 0")
        okTest = 0
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if errorCount>0:
            fh.write("***ERROR --> " + str(errorCount) + " features have PROVID_PART_NUMBER other than 0:\n")
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
          
            uniqueList.sort()
          
            for x in uniqueList:
                fh.write('                ' + uniqueIDField + ' ' + str(x) + '\n')
            fh.write('\n')
            okTest = okTest + 1
            fh.write('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')
            fh.write("NOTE --> If the above [LANDSCAPE_UNIT_ID] is one of 1021, 1022, 1027, 1028, 1031, 1811, 1813, 1816, 1819 the above ERROR may not be applicable due to known anomalies.  Please contact the Data Resource Manager for further clarification.\n")
            fh.write('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')
         
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
        
        # Check: Internal features (STATUS 1 or 3) must have BEO_SUB_TYPE_APPLICABLE = Yes.
        #Check that where status = internal, beo subtype = yes
        checkMessage = 'RULE TO CHECK: Features with [STATUS] set to Internal-Current or Internal-Retired must have [BEO_SUB_TYPE_APPLICABLE] = Yes.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 
       
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"STATUS\" in (1,3) and \"BEO_SUB_TYPE_APPLICABLE\" = 'N'")
        okTest = 0
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if errorCount>0:
            fh.write("***ERROR --> " + str(errorCount) + " Internal features have BEO_SUB_TYPE_APPLICABLE set to No:\n")
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
          
            uniqueList.sort()
          
            for x in uniqueList:
                fh.write('                ' + uniqueIDField + ' ' + str(x) + '\n')
            fh.write('\n')
            okTest = okTest + 1
         
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
        
        # Check: Internal features with BEO_SUB_TYPE_APPLICABLE = Yes must NOT have BIODIVERSITY_EMPHASIS_OPTION = Multiple.
        #Check that where status = internal and beo subtype = yes, then beo value is not set to multiple
        checkMessage = 'RULE TO CHECK: Features with [STATUS] set to Internal-Current or Internal-Retired AND [BEO_SUB_TYPE_APPLICABLE] = Yes must not have [BIODIVERSITY_EMPHASIS_OPTION] = Multiple.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 
    
        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"STATUS\" in (1,3) and \"BEO_SUB_TYPE_APPLICABLE\" = 'Y' and \"BIODIVERSITY_EMPHASIS_OPTION\" = 'Multiple'")
        okTest = 0
        errorCount = int(str(arcpy.GetCount_management('fc_lyr')))
        if errorCount>0:
            #BUG - High: Raw string literal r"...\n" — the \n is NOT a newline; it is the two characters \ and n.
            #BUG - High: The error message will appear without a line break in the report. Remove the r prefix.
            fh.write("***ERROR --> " + str(errorCount) + r" Internal features have BIODIVERSITY_EMPHASIS_OPTION set to Multiple:\n")
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            uniqueList = []
            while row:
                if row.getValue(uniqueIDField) not in uniqueList:
                    uniqueList.append(row.getValue(uniqueIDField))
                row = rows.next()
          
            uniqueList.sort()
          
            for x in uniqueList:
                fh.write('                ' + uniqueIDField + ' ' + str(x) + '\n')
            fh.write('\n')
            okTest = okTest + 1
         
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
        
        # Check: if a landscape unit has multiple parts (PROVID_PART_NUMBER > 0), all current parts must share
        #check if lu has more than one part, all CURRENT parts have same lu number, and lu name
        # the same LANDSCAPE_UNIT_NUMBER and LANDSCAPE_UNIT_NAME.
        checkMessage = 'RULE TO CHECK: If a landscape unit has more than one part, all Current parts must have the same [LANDSCAPE_UNIT_NUMBER] and [LANDSCAPE_UNIT_NAME]'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 

        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"PROVID_PART_NUMBER\" > 0 AND \"STATUS\" in (0,1)")
        #BUG - High: okTest is incremented unconditionally here, before any error check.
        #BUG - High: This means if okTest == 0: at line 2463 is NEVER true — "no errors" is never written
        #BUG - High: for this check regardless of actual data state. Move increment inside the error block.
        okTest = okTest + 1
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        provIDList = []
        while row:
            if row.getValue(provIDField) not in provIDList:
                provIDList.append(row.getValue(provIDField))
            row = rows.next()
        provIDList.sort()
         
        # For each multi-part PROV_ID, compare LU number and name values across all current parts.
        for provID in provIDList:
            y = str(provID)
            selectString = provIDField + " = " + y 
            arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectString)
            if int(str(arcpy.GetCount_management("fc_lyr"))) > 1:
                rows = arcpy.SearchCursor("fc_lyr")
                row = rows.next()
                luNumberList = []
                while row:
                    if row.getValue("LANDSCAPE_UNIT_NUMBER") not in luNumberList:
                        luNumberList.append(row.getValue("LANDSCAPE_UNIT_NUMBER"))
                    row = rows.next()
                luNumberList.sort()
                
                rows = arcpy.SearchCursor("fc_lyr")
                row = rows.next()
                luNameList = []
                while row:
                    if row.getValue("LANDSCAPE_UNIT_NAME") not in luNameList:
                        luNameList.append(row.getValue("LANDSCAPE_UNIT_NAME"))
                    row = rows.next()
                luNameList.sort()
                
                if len(luNumberList) > 1:
                    fh.write("***ERROR --> CURRENT Landscape Units with [PROVID] " + y + " have multiple values in\n")
                    fh.write("             [LANDSCAPE_UNIT_NUMBER]\n")
                    okTest = okTest + 1
                
                if len(luNameList) > 1:
                    fh.write("***ERROR --> CURRENT Landscape Units with [PROVID] " + y + " have multiple values in\n")
                    #BUG - Critical: NameError — 'fileHandlw' is undefined. Should be 'fh'.
                    #BUG - Critical: Script CRASHES here whenever a landscape unit name mismatch is detected.
                    #BUG - Critical: Fix: replace fileHandlw with fh.
                    fileHandlw.write("             [LANDSCAPE_UNIT_NAME]\n")
                    okTest = okTest + 1
        
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            
        
        # Check: features with STATUS = Internal-Current must have a matching PROV_ID with STATUS = External-Current.
        #Check that features with a STATUS of Internal-Current have a matching feature with the same PROVID and a STATUS of External-Current
        checkMessage = 'RULE TO CHECK: Features with [STATUS] = Internal-Current must have a matching feeature with the same [LANDSCAPE_UNIT_PROVID] that has a [STATUS] = External-Current.'
        arcpy.AddMessage(checkMessage)
        fh.write(checkMessage + "\n") 

        arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", "\"Status\" = 1")
        okTest = 0
        # Collect all Internal-Current PROV_IDs and check each has a matching External-Current (STATUS=0) partner.
        #read internal-current prov ids into a list & sort
        internalCurrentProvIDList = []
        rows = arcpy.SearchCursor("fc_lyr")
        row = rows.next()
        retirementProvIDList = []
        while row:
            if row.getValue(provIDField) not in internalCurrentProvIDList:
                internalCurrentProvIDList.append(row.getValue(provIDField))
            row = rows.next()
        internalCurrentProvIDList.sort()
        
        for x in internalCurrentProvIDList:
            selectionString = "\"" + provIDField + "\" = " + str(x)
            arcpy.SelectLayerByAttribute_management("fc_lyr", "NEW_SELECTION", selectionString)
            
            rows = arcpy.SearchCursor("fc_lyr")
            row = rows.next()
            statusList = []
            while row:
                if row.getValue("STATUS") not in statusList:
                    statusList.append(row.getValue("STATUS"))
                row = rows.next()
            statusList.sort()
            
            if 0 not in statusList:
                fh.write('***ERROR --> PROVID ' + str(x) + ' has features with [STATUS] = Internal-Current without\n')
                fh.write('             matching PROVID with [STATUS] = External-Current \n')  
                okTest = okTest + 1
    
        if okTest == 0:
            fh.write(noErrorsMessage + '\n')
            


        fh.write('\n') 
        fh.write('\n')     
        fh.write('\n')   
        fh.close()
        
        arcpy.AddMessage('')
        arcpy.AddMessage('')
        arcpy.AddMessage('')


# SECTION 12: Validate all field values against their assigned GDB coded-value domains.
def section_12_check_domains():
    import arcpy.da
    
    section = '----------Section 12----------'
    arcpy.AddMessage(section)
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    
    fh.write("CHECK FIELD VALUES AGAINST DOMAIN VALUES \n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n') 
      
    checkMessage = 'RULE TO CHECK: For fields with assigned domains, values within the fields must be part of the domain list'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    # Create a feature layer for attribute selection.
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    okTest = 0
    #Get domain values
    # Retrieve all coded-value domains defined in the geodatabase.
    domains = arcpy.da.ListDomains(gdbPath)
    # For each domain, build a list of valid coded values.
    for domain in domains:
        domainValLists = []
        codedValueList = []
        if domain.domainType == 'CodedValue':
            coded_values = domain.codedValues
            #BUG - Medium: .iteritems() is Python 2 only. Python 3 / ArcGIS Pro requires .items().
            #BUG - Medium: This will raise AttributeError immediately on any Python 3 environment.
            for val in coded_values.iteritems():
                domainValLists.append(val)
            for domainValList in domainValLists:
                codedValueList.append(domainValList[0])
            
            # Allow None as a valid value for domains that permit null (ModificationType, OGMAType).
            #add "None" to domain value lists for those fields that allow null values
        if domain.name in ('ModificationType', 'OGMAType'):
            codedValueList.append(None)


        # For each field that references this domain, collect distinct field values from the dataset.
        #get fields that have domains applied & check that all field values are within domain
        fieldList = arcpy.ListFields(inDataset)
        for field in fieldList: 
            if field.domain == domain.name:
                valueList = []
                #BUG - Medium: Old-style SearchCursor opened with no del rows. Multiple cursors accumulate
                #BUG - Medium: across the nested domain/field loop, holding schema locks on the feature class.
                rows = arcpy.SearchCursor("fc_lyr")
                row = rows.next()
                while row:
                    if row.getValue(field.name) not in valueList:
                        valueList.append(row.getValue(field.name))
                    row = rows.next()
                  
                # Compare each field value against the domain list; select and report any out-of-domain values.
                for value in valueList:
                    if value not in codedValueList:
                        #BUG - Medium: Domain value concatenated directly into SQL string without escaping.
                        #BUG - Medium: If a domain code contains a single quote (e.g. O'Neil), the query is malformed
                        #BUG - Medium: and arcpy raises an exception, skipping all remaining domain checks in this loop.
                        selectQuery = "\"" + str(field.name) + "\" = '" + str(value) + "'"
                        arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", selectQuery)
                        rows = arcpy.SearchCursor("fc_lyr")
                        row = rows.next()
                        errorList = []
                        while row:
                            if row.getValue("OBJECTID") not in errorList:
                                errorList.append(row.getValue("OBJECTID"))
                            row = rows.next()
                        errorList.sort()

                        for objectID in errorList:
                            fh.write('***ERROR --> OBJECTID ' + str(objectID) + ' has a non-domain value in [' + field.name + '] \n')
                            okTest = okTest + 1
                    fh.write('\n')
     
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        
    


    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')


# SECTION 13 (DISABLED): Validate URL fields contain reachable HTTP endpoints.
# This section is commented out in main() — under development since 2017.
def section_13_check_url_fields():
    import arcpy.da
    
    section = '----------Section 13----------'
    arcpy.AddMessage(section)
    fh = open(attributeQAReportFile, 'a')  
    fh.write(section + "\n")
    
    fh.write("CHECK URL FIELDS FOR VALID URLS\n")
    fh.write("-------------------------------------------------------\n")
    fh.write('\n') 
      
    checkMessage = 'RULE TO CHECK: [ENABLING_DOCUMENT_URL] must contain a valid metadata URL'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    
    # Collect all unique ENABLING_DOCUMENT_URL values; treat None as empty string.
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    okTest = 0
    
    urlList = []
    rows = arcpy.SearchCursor('fc_lyr')
    for row in rows:
        if row.getValue("ENABLING_DOCUMENT_URL") not in urlList:
            if row.getValue("ENABLING_DOCUMENT_URL") is None:
                if "" not in urlList:
                    urlList.append("")
            else:
                urlList.append(row.getValue("ENABLING_DOCUMENT_URL"))
    # Attempt to open each URL; flag any that raise an exception (unreachable or malformed).
    for url in urlList:
        try:
            urllib2.urlopen(url)
        except:
            okTest = okTest + 1
            arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"ENABLING_DOCUMENT_URL\" = '" + url + "'")
            rows2 = arcpy.SearchCursor('fc_lyr')
            errorList = []
            for row2 in rows2:
                #BUG - High: row.getValue("OBJECTID") uses the OUTER cursor variable 'row' (already exhausted),
                #BUG - High: not the INNER cursor variable 'row2'. Every error entry gets the same wrong OBJECTID.
                #BUG - High: Fix: change row.getValue("OBJECTID") to row2.getValue("OBJECTID").
                errorList.append(row.getValue("OBJECTID"))
            del rows2
            
            for objectID in errorList:
                fh.write('***ERROR --> OBJECTID ' + str(objectID) + ' does not have a valid URL in [ENABLING_DOCUMENT_URL] \n')
                okTest = okTest + 1
                fh.write('\n')
     
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        
    
    del rows
    
    
    
    # Collect all unique RSRCE_PLAN_METADATA_LINK values and validate each URL is reachable.
    checkMessage = 'RULE TO CHECK: [RSRCE_PLAN_METADATA_LINK] must contain a valid metadata URL'
    arcpy.AddMessage(checkMessage)
    fh.write(checkMessage + "\n") 
    
    arcpy.MakeFeatureLayer_management(inDataset, 'fc_lyr')
    okTest = 0
    
    urlList = []
    rows = arcpy.SearchCursor('fc_lyr')
    for row in rows:
        if row.getValue("RSRCE_PLAN_METADATA_LINK") not in urlList:
            urlList.append(row.getValue("RSRCE_PLAN_METADATA_LINK"))
    for url in urlList:
        try:
            urllib2.urlopen(url)
        except:
            okTest = okTest + 1
            arcpy.SelectLayerByAttribute_management('fc_lyr', "NEW_SELECTION", "\"RSRCE_PLAN_METADATA_LINK\" = '" + url + "'")
            rows2 = arcpy.SearchCursor('fc_lyr')
            errorList = []
            for row2 in rows2:
                errorList.append(row.getValue("OBJECTID"))
            del rows2
            
            for objectID in errorList:
                fh.write('***ERROR --> OBJECTID ' + str(objectID) + ' does not have a valid URL in [RSRCE_PLAN_METADATA_LINK] \n')
                okTest = okTest + 1
                fh.write('\n')
     
    if okTest == 0:
        fh.write(noErrorsMessage + '\n')
        
    
    del rows
            
            
            
    
            
    
    
    
    
    
    
    
    
    fh.write('\n') 
    fh.write('\n')     
    fh.write('\n')   
    fh.close()
    
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    arcpy.AddMessage('')
    

# Final step: compact the geodatabase to reclaim space and optimise performance after edits.
def compact_gdb():
    arcpy.AddMessage('Final step: compacting geodatabase')
    arcpy.Compact_management(gdbPath)

# Run the tool.
main()

# Print completion messages to the ArcGIS tool dialog.
arcpy.AddMessage('')
arcpy.AddMessage('----------------------- Tool has finished running ----------------------')
arcpy.AddWarning('')
arcpy.AddWarning('----------- Review attribute check text file for any errors ------------')


