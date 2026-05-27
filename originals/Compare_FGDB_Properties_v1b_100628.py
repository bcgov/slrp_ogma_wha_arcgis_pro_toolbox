'''

    Author:        Sasha Lees
    Purpose:       Compares the dataset properties of a  returned dataset (FGDB) with a Master dataset (FGDB).  Checks for matching domains,
                   domain code values, coordinate system, tolerances, spatial domain/extent, fields and field properties.
                   Also checks the topology rule properties. 
    Date:         February 5, 2010 
    Arguments:     masterFGDB - Master File Geodatabase path and name.  returnedFGDB - returned or updated FGDB path and name.
    Outputs:      Text file report in the same folder as the Returned FGDB, named by date and time
    Dependencies:   Built with 9.3 Scripting Object.  9.2 does not have all of the functionality available in 9.3
    
    Assumptions:    Assumes Master FGDB properties are correct, and uses these as a baseline for comparing the Returned features
                    Assumes all domains use coded values (not ranges)
                  
    History:        Published to SLRP DRM Toolbox April 21, 2010.
                    June 28, 2010  (salees)  added a check for a valid FGDB.  
                        Updated domain table name export to be the full length of the domain name, not just 6 chars, and to temporarily overwrite output for temporary domain tables
                        
    --------------------------------------------------------------
'''

# Import modules and initialise geoprocessor object variable
import sys, string, os, os.path, datetime, time

##SEE BOTTOM OF SCRIPT, AFTER DEF's, FOR SETUP ....

#START OF DEF Modules
# ---------------------------------------------------------------------------
#    Compare FGDB Properties:  Domain Name and Coded Values/Descriptions. 
#    NOTE:  Cannot access Domain properties such as field type, domain type, split policy, merge policy, 
#    and Domain description in Python.
#    Also, Sub-type Properties may have to be compared using VB or ArcObjects, 
#    as it does not appear possible in Python/Geoprocessing Module
# ---------------------------------------------------------------------------

def DomainProperties(): 
    __printMsg ('----------------------------------------------------------------------------\n')
    __printMsg('STARTING Checking FGDB Domains...\n')
    domCheckErrorCount = 0
    
    #Get list of domains for each FGDB/Workspace
    domains1 = desc1.Domains       #Master Domains
    domains2 = desc2.Domains       #Returned Domains
    
    #Sort each list alphabetically (optional)
    domains1.sort()
    domains2.sort()
    
    #strip unicode 'u' from domains lists, for printing
    #NOTE: using just str(domains1) does not work - must act on each individual item in list
    doms1 = [str(item) for item in domains1]
    doms2 = [str(item) for item in domains2]
    
    __printMsg('Master Domains:  \t'+ str(doms1))
    __printMsg('Returned Domains: \t'+ str(doms2)+ '\n')
    #print '-----------------------------------------\n'
    
    #Series of if loops to check for No Domains
    if not domains1 and not domains2:
        __printMsg('OK \t Neither the Master nor the Returned FGDB have any domains.')
        #OK Done - skip comparison of domains
        
    if domains1 and not domains2:
        __printMsg('ERROR \t The Returned FGDB has no domains, but the Master has the following domains:')
        __printMsg('\t'+ str(domains1))
        domCheckErrorCount = domCheckErrorCount+1
        #ERROR Done - skip comparison of domains
        
    if not domains1 and domains2:
        __printMsg('ERROR \t The Master FGDB has no domains, but the Returned FGDB does have domains')
        __printMsg('Extra domains from Returned FGDB:  '+ str(domains2))
        domCheckErrorCount = domCheckErrorCount+1
        # ERROR - skip comparison of domains

    #Start major loop to compare values if domains exist in both FGDBs
    #NOTE: Domain names are case sensitive, and must match the master.  By default, the comparison is also case sensitive
    if len(domains1) > 0 and len(domains2) > 0:
        #Compare  - Check for missing domain NAMES in Returned FGDB   
        for dom in domains1:
            if not domains2.count(dom):           #tests if a value is not in the list.  
                #print 'OK    ',dom, 'from Master also exists in Returned FGDB...'
            #else:
                __printMsg('ERROR    '+ dom + 'is not present in Returned FGDB...')
                domCheckErrorCount = domCheckErrorCount+1
                
        __printMsg('-----------------------------------------\n')
        
        #As we cannot directly access Domain coded values/descriptions using Python (that I know of), here is a workaround:
        #Export Domains to a table, in order to work with it, and check values and descriptions
        #Use the temporary in_memory workspace.  Tables will only exist while the script is running.
        ##Or try using a scratchworkspace or T: Local Disk
        
        __printMsg('Preparing to check Domain Values...\n')
        gp.overwriteoutput=1
       
        
        #Create temporary Master domain tables (One table of codes/descriptions  per domain)
        __printMsg('\t Exporting MASTER Domains to temporary tables...')
        for dom1 in domains1:
            __printMsg('\t\t ...'+ dom1)
            tabName = dom1  #[0:6]   #take the first 6 characters, to use in the output table name 
            gp.Workspace = "in_memory"
            gp.DomainToTable_management(masterFGDB,dom1,tabName+'_dom1',"CODE","DESCRIPT")
            #print 'Done exporting Master Domain table for ', dom1
        #print '\n-----------------------------------------\n'
        __printMsg('\n')
        
        #Create temporary Returned domain tables (One table of codes/descriptions per domain)
        #print gp.getMessages()
        __printMsg('\t Exporting RETURNED Domains to temporary tables...')
        for dom2 in domains2:
            __printMsg('\t\t ... '+ dom2)
            tabName = dom2  #[0:6]   #take the first 6 characters, to use in the output table name 
            gp.Workspace = "in_memory"
            gp.DomainToTable_management(returnedFGDB,dom2,tabName+'_dom2',"CODE","DESCRIPT")
            #print 'Done exporting Master Domain table for ', dom2
        #print '\n-----------------------------------------\n'
        
        #Now compare individual items in Returned domain tables to Master domain tables
        for dom in domains2:
            __printMsg('\n-----------------------------------------\n')
            __printMsg('Checking CODES and DESCRIPTIONS in Returned FGDB for domain:   ' + dom + '\n')
            if domains1.count(dom):           #tests if domain NAME from Returned is in/equal to the Master list of domains
                #print '     ', dom, 'exists in the Returned FGDB...'
                #Create Dictionary of domain code values/descriptions
                tabName = dom  #[0:6]
                d1 = __buildDict(tabName+'_dom1')    #Calls __BuildDict method (below)
                d2 = __buildDict(tabName+'_dom2')
                
                __printMsg('Master Domain - ' + dom + ' - has ' + str(len(d1)) + ' values:')
                for vcode, desc in d1.iteritems():
                    __printMsg('\t' + vcode + '\t' + str(desc).strip('[u]'))

                __printMsg('\n')
                __printMsg('Returned Domain - ' + dom + ' - has ' + str(len(d2)) + ' values:')
                for vcode, desc in d2.iteritems():
                    __printMsg('\t' + vcode + '\t' + str(desc).strip('[u]'))
                
                #print '\n-----------------------------------------\n'
                __printMsg('\n')
                
                if len(d1)==0 and len(d2)==0:  #This should never be true, as this should have been weeded out earlier
                    __printMsg('Both Master and Returned FGDB have no domains.')
                else:
                    #Compare Returned Domain values to Master Domain values
                    for key in d1.keys():
                        if key in d2.keys():
                            #print 'Comparing Master', key, d1[key], 'with Returned', key, d2[key]
                            if d1[key] != d2[key]:
                                __printMsg('ERROR    Description or case for '+ dom + ' ' + key + ' does not match: '+ str(d1[key]).strip('[u]') +'vs'+ str(d2[key]).strip('[u]'))
                                domCheckErrorCount = domCheckErrorCount+1
                            #elif d1[key] == d2[key]:
                                #print 'OK     Descriptions match...'
                        
                        else:
                            __printMsg('ERROR    No Domain value for: ' + key +  'or case mismatch.')
                            domCheckErrorCount = domCheckErrorCount+1
                        
                    #print '-----------------------------------------\n'
                            
                    #Check for any additional domain values that may have been added to the Returned Features
                    outList2 = [key for key in d2.keys() if key not in d1.keys()]
                    if len(outList2)!= 0:
                        __printMsg('ERROR    The following coded values are extra in the Returned domain ' + dom +':')
                        outlist3 = [str(item) for item in outList2]
                        #outlist3.sort()
                        __printMsg('\t' + str(outlist3))
                        domCheckErrorCount = domCheckErrorCount+1
                        
                        #print '-----------------------------------------\n'
                    #else:
                        #print 'OK     The Returned FGDB has no extra values for domain', dom
                    
                    #print '-----------------------------------------\n'
                

            # NOT domains1.count(dom)   - domain2 not in master domain list
            else:
                __printMsg('ERROR    Domain: ' + dom + 'does not exist in the Master FGDB ... Returned FGDB has an extra domain.')
                domCheckErrorCount = domCheckErrorCount+1
                #print '-----------------------------------------\n'

    
    __printMsg('\n')
    gp.overwriteoutput=0
        
    #print '\n----------------------------------------------------------------------------'
    #__printMsg('DONE CHECKING FGDB DOMAINS:')
    #if domCheckErrorCount > 1:
     #   __printMsg('\t There are ' + str(domCheckErrorCount) + ' errors with the Returned FGDB domains.  Please see the log file for details.')
    #elif domCheckErrorCount ==1:
      #  __printMsg('\t There is an error with the Returned FGDB domains.  Please see the log file for details.')
    #else:
       # __printMsg('\t No domain errors found.')
    #print '----------------------------------------------------------------------------\n'
    
# ---------------------------------------------------------------------------
# Build Dictionary for Domain CODES and DESCRIPTION
# called from def DomainProperties()
# --------------------------------------------------------------------------- 
def __buildDict(inputFC): #-----BEWARE OF HARDCODED PRIMARY KEY AND ATTRIBUTES BELOW!!!!!
    '''Build a dictionary of the primary key, and it's fields'''
    d = {}
    cur = gp.SearchCursor(inputFC)
    row = cur.Next()
    while row:
        d[row.CODE] = [row.DESCRIPT]
        row = cur.Next()
    del cur
    return d


# ---------------------------------------------------------------------------
#  Compare FEATURE DATASET  Properties: Dataset Name, XY Coordinate System, Resolution Tolerance, Spatial Domain
#  For each matching dataset, loop through the feature classes to compare feature class (FC) properties, including fields.
#  Uses __FCprops function to loop through FCs.
# __FCprops uses __dictCompare function to compare index and field objects
# ---------------------------------------------------------------------------

def DatasetProperties(): 

    __printMsg('\n----------------------------------------------------------------------------')
    __printMsg('STARTING checking Dataset, Feature Class, and Field properties...')
    __printMsg('\nNOTE: While this script can detect if a Default Subtype Code is applied to a FC, (which implies that Subtypes exist),')
    __printMsg('it DOES NOT detect what the actual values of the Subtype are, or if the values match.')
    __printMsg('The script also CAN NOT detect if Domains are applied to any individual Subtypes.')
    __printMsg('The script CAN detect if a domain is applied to a field, which then applies to all records in the table, regardless of Subtype.')
    __printMsg('-----------------------------------------')
    
    __printMsg('\nGetting Dataset Lists ... ')  #and Feature classes....'
    
    #Get list of Feature Datasets
    gp.workspace = masterFGDB
    if not gp.ListDatasets():
        __printMsg('\t\tWARNING   Master has no Datasets...')
    dsets1 = gp.ListDatasets()
    dsets1s = [str(item) for item in dsets1]   #strips out the unicode specifier from the list
    __printMsg('\tMaster Feature Datasets:  \t' + str(dsets1s))
    
    gp.workspace = returnedFGDB
    if not gp.ListDatasets():
        __printMsg('\t\tWARNING   Returned has no Datasets...')
    dsets2 = gp.ListDatasets()
    dsets2s = [str(item) for item in dsets2]
    __printMsg('\tReturned Feature Datasets:  \t' + str(dsets2s) + '\n')
    
    #First, check if a FD does not exist in returnedFGDB
    for dataset in dsets1:
        if not gp.exists(os.path.join(returnedFGDB,dataset)):
            __printMsg('\tERROR    There is no matching feature dataset name in the Returned FGDB for: ' + dataset)
            
    #Second, check for any extra Datasets that the Returned FGDB may have (and not in Master).
    for dataset in dsets2:
        if not gp.exists(os.path.join(masterFGDB,dataset)):
            __printMsg('\tERROR    The Returned FGDB has an addition feature dataset for: '+ dataset)
    
    #Third, for matching datasets, compare properties of each       
    for dataset in dsets1:
        if gp.exists(os.path.join(returnedFGDB,dataset)):
            __printMsg('\n-----------------------------------------\n')
            __printMsg('Now Comparing FD properties for...\n')
            __printMsg('  DATASET: ' + dataset)
            
            __printMsg('\n\tDescribing FDs...')
            fdDesc1 = gp.describe(os.path.join(masterFGDB,dataset))
            fdDesc2 = gp.describe(os.path.join(returnedFGDB,dataset))
            
            #print '\t Now Comparing FD properties...'
            if fdDesc1.DatasetType == fdDesc2.DatasetType:
                #print 'Dataset Types match:', fdDesc1.DatasetType
                pass
            else:
                __printMsg('\t\tERROR    Dataset Type Mismatch.') 
                
            if fdDesc1.SpatialReference.IsHighPrecision == fdDesc2.SpatialReference.IsHighPrecision:
                #print 'High Precision:', fdDesc1.SpatialReference.IsHighPrecision
                pass
            else:
                __printMsg('\t\tERROR     Precision Mismatch.')
            
            
            #print '\n-----------------------------------------\n'
            __printMsg('\n\tComparing Coordinate System details for FDs....')
            
            srPropList = ['Type', 'Name','ProjectionName','FalseEasting','FalseNorthing','CentralMeridian','StandardParallel1','StandardParallel2','LinearUnitName']
            for srProp in srPropList:
                if eval('fdDesc1.SpatialReference.'+srProp) == eval('fdDesc2.SpatialReference.'+srProp):
                    #print 'Matching ',srProp,':',eval('fdDesc1.SpatialReference.'+srProp)
                    pass
                else:
                    __printMsg('\t\tERROR     Mismatching '+ srProp + ': ' +str(eval('fdDesc1.SpatialReference.'+srProp))+' vs ' + str(eval('fdDesc2.SpatialReference.'+srProp)))
                    if srProp == 'Name':
                        break      #break out of loop if Coordinate System names are not the same. End of comparison.
                  
            #print '\n-----------------------------------------\n'
            __printMsg('\n\tChecking Tolerance Properties for FD....')
            srPropList = ['XYTolerance', 'ZTolerance', 'MTolerance']
            #print ' Getting XY and Z Coordinate System Properties for FD....\n'
            for srProp in srPropList:
                if eval('fdDesc1.SpatialReference.'+srProp) == eval('fdDesc2.SpatialReference.'+srProp):
                    #print 'Matching ',srProp,':',eval('fdDesc1.SpatialReference.'+srProp)
                    pass
                else:
                    __printMsg('\t\tERROR     Mismatching ' + srProp+ ': ' + str(eval('fdDesc1.SpatialReference.'+srProp))+' vs ' + str(eval('fdDesc2.SpatialReference.'+srProp)))
            
            
            #print '\n-----------------------------------------\n'
            __printMsg('\n\tChecking Resolution Properties for FD....')
            srPropList = ['XYResolution', 'ZResolution', 'MResolution']
            #print ' Getting XY and Z Coordinate System Properties for FD....\n'
            for srProp in srPropList:
                if eval('fdDesc1.SpatialReference.'+srProp) == eval('fdDesc2.SpatialReference.'+srProp):
                    #print 'Matching ',srProp,':',eval('fdDesc1.SpatialReference.'+srProp)
                    pass
                else:
                    __printMsg('\t\tERROR     Mismatching ' + srProp +': ' + str(eval('fdDesc1.SpatialReference.'+srProp))+' vs '+ str(eval('fdDesc2.SpatialReference.'+srProp)))
            
            
            #print '\n-----------------------------------------\n'
            __printMsg('\n\tChecking Spatial Domain Properties for FD....')
            srPropList = ['Domain', 'ZDomain', 'MDomain']
            #print ' Getting XY and Z Coordinate System Properties for FD....\n'
            for srProp in srPropList:
                if eval('fdDesc1.SpatialReference.'+srProp) == eval('fdDesc2.SpatialReference.'+srProp):
                    #print 'Matching ',srProp,':',eval('fdDesc1.SpatialReference.'+srProp)
                    pass
                else:
                    __printMsg('\t\tERROR     Mismatching ' + srProp + ': ' + str(eval('fdDesc1.SpatialReference.'+srProp))+' vs '+ str(eval('fdDesc2.SpatialReference.'+srProp)))
            
            

            #print '\n-----------------------------------------\n'
            __printMsg('\n\tChecking Spatial Extents for FD....')
            #print 'Extents (XMin, YMin, XMax, YMax):', fdDesc1.Extent.XMin, fdDesc1.Extent.YMin, fdDesc1.Extent.XMax, fdDesc1.Extent.YMax
            srPropList = ['XMin', 'YMin', 'XMax', 'YMax']
            for srProp in srPropList:
                #pstring = eval('fdDesc1.SpatialReference.'+srProp)
                #print pstring
                #print srProp,':',pstring
                #print srProp,':',eval('fdDesc1.Extent.'+srProp)
                if eval('fdDesc1.Extent.'+srProp) == eval('fdDesc2.Extent.'+srProp):
                    #print 'Matching ',srProp,':',eval('fdDesc1.Extent.'+srProp)
                    pass
                else:
                    __printMsg('\t\tWARNING     Mismatching ' + srProp + ': ' + str(eval('fdDesc1.Extent.'+srProp))+' vs ' + str(eval('fdDesc2.Extent.'+srProp)))
            
            #Finally, compare feature class properties of each feature class in the dataset
            __FCprops(dataset)   #Calls module to compare Feature Class Properties
            
# ---------------------------------------------------------------------------
#    Compare FEATURE CLASS Properties:  FC Name, Field Names, Non-Nullable Fields Set, Subtypes exist and Domains applied
#     Called by def DatasetProperties()
# ---------------------------------------------------------------------------
#def __FCprops():
def __FCprops(dataset):
    
    __printMsg('\n-----------------------------------------\n')
    __printMsg('Checking Feature Classes for...')
    __printMsg('  DATASET:  '+ dataset)
    
    dataset1 = os.path.join(masterFGDB,dataset)
    dataset2 = os.path.join(returnedFGDB,dataset)
    
    #Get List of Feature Classes
    gp.workspace = dataset1
    fcList1 = gp.ListFeatureClasses()
    __printMsg('\nMaster Feature Classes in '+ dataset+ ':')
    for item in fcList1:
        __printMsg('\t'+ item)
    
    gp.workspace = dataset2
    fcList2 = gp.ListFeatureClasses()
    __printMsg('\nReturned Feature Classes in '+ dataset+ ':')
    for item in fcList2:
        __printMsg('\t'+ item)
    
    #print '\n-----------------------------------------\n'
    __printMsg('\n\tComparing FCs...')
    
    #First, check for missing feature classes in returned dataset
    for fc in fcList1:
        if not gp.exists(os.path.join(dataset2,fc)):
            __printMsg('\tERROR     '+ fc+ ' name DOES NOT EXIST in Returned FGDB.  Cannot check FC or field properties.')
            
    #Second, check for additional feature classes in returned dataset
    #print '\n-----------------------------------------\n'    
    for fc in fcList2:
        if not gp.exists(os.path.join(dataset1,fc)):
            __printMsg('\tERROR    The Returned FGDB has an ADDITIONAL feature class for: '+ fc + 'in Dataset ' + dataset)
    
    #Third, compare existing feature classes
    __printMsg('\n-----------------------------------------\n')
    for fc in fcList1:
        if gp.exists(os.path.join(dataset2,fc)):
            #print'\t', fc, ' EXISTS in Returned FGDB'
            
            __printMsg('Describing Feature Classes...')
            __printMsg('  FEATURE CLASS:  '+ fc)
            fc1 = os.path.join(dataset1,fc)
            fc2 = os.path.join(dataset2,fc)
                                 
            fcDesc1 = gp.describe(fc1)
            fcDesc2 = gp.describe(fc2)
            
            #-------------------------------------------------
            #Checking General Field Properties
            __printMsg('\nPreliminary check of Feature Class (FC) properties...')
            
            fcPropList = ['HasSpatialIndex','FeatureType','ShapeFieldName','ShapeType','AreaFieldName','LengthFieldName','DefaultSubtypeCode']
            cnt = 0
            for property in fcPropList:
                val1 = eval('fcDesc1.'+property)
                val2 = eval('fcDesc2.'+property)
                #print '\tComparing Feature Class', property, '...\t', val1, val2
                if val2 == val1:
                    #print '\t\t',property, 'is the same ...'
                    pass
                else:
                    __printMsg('\tERROR     '+property+ ' is NOT the same in the Returned feature class ' + fcDesc2.Name)
                    cnt += 1
            
            #if cnt == 0:  #no errors
             #   print '\t...OK'
                       
            #-------------------------------------------------
            #Checking Field order and field properties
            #Assume there will always be some fields (fldObj list is never empty), therefore don't need to check for empty field list
            __printMsg('\nChecking Fields...')
            fldObj1 = gp.ListFields(fc1)
            fldObj2 = gp.ListFields(fc2)
            
            __printMsg('\n\tChecking Number of fields, field order, and field properties ...\n')
            #print 'Field Objects length:', len(fldObj1), len(fldObj2)
            if len(fldObj2) != len(fldObj1):
                __printMsg('\t\tERROR     The number of fields in '+ fc2+ ' are NOT equal: '+ str(len(fldObj1))+ ' vs '+  str(len(fldObj2)))
                #pass
            else:
                __printMsg('\t\tThe number of fields match! Now checking field order....\n')
            
                #Compare field order - the listField Object should be in the same order as in the FC
                #Build field order dictionaries - field order, field name - ignore Shape field name, Area and Length attributes, as these are sometimes
                #arbitrarily placed at the start or at the end.  Handle these separately, to advise if there is a difference in order.
                
                #--------------------------Build field order DICTIONARY 1 - from fldObj1
                cnt = 0     #used for object count - all fields
                order = 1   #used to track main fields (ignore shape, area, length fields)
                df1 = {}     #initialise dictionary of main field order, field name
                dicttemp1 = {}  #initialise dictionary of shape, area, length and count (internal fields)
                
                while cnt < len(fldObj1):   #length of both object list will be the same, otherwise, would not be doing this comparison
                    if fldObj1[cnt].Name in [fcDesc1.ShapeFieldName, fcDesc1.AreaFieldName,fcDesc1.LengthFieldName]:
                        #add to dictionary
                        dicttemp1[fldObj1[cnt].Name] = cnt
                    else:
                        #print 'adding to dict...', cnt
                        df1[order] = fldObj1[cnt].Name
                        order += 1
                        
                    cnt += 1
            
                #--------------------------Build field order DICTIONARY 2 - from fldObj2
                cnt = 0
                order = 1
                df2 = {}     #initialise dictionary of fields
                dicttemp2 = {}  #initialise dictionary of shape, area, length order
                while cnt < len(fldObj2):
                    if fldObj2[cnt].Name in [fcDesc2.ShapeFieldName, fcDesc2.AreaFieldName,fcDesc2.LengthFieldName]:
                        dicttemp2[fldObj2[cnt].Name] = cnt
                    else:
                        #print 'adding to dict...', cnt
                        df2[order] = fldObj2[cnt].Name
                        order += 1
                        
                    cnt += 1
                
                #---------------------------------------------
                #Now Comparing Dictionary order for main fields
                cnt = 0
                for key in df1.keys():
                    if df1[key] != df2[key]:
                        __printMsg('\t\tWARNING   Fields are out of Order at '+ df2[key]+ ' in the returned features.   Quitting field order comparison...')
                        cnt += 1
                        break  #break out of order checking loop - if one field is out of order, subsequent fields will be too.
                
                if cnt ==0:  #if no error are found/nothing out of order
                    __printMsg('\t\tOK    The main fields (not including Shape, Area, and Length fields) are in the same order.\n')
                
                #---------------------------------------------
                # Comparing the order of internal Shape, Area, and Length fields.  These can sometimes be arbitrarily at the start
                # or the end of the field list. 
                for key in dicttemp1.keys():
                    try:
                        if dicttemp1[key] != dicttemp2[key]:
                            __printMsg('\t\tWARNING    Internal field '+ key+ 'is not in the same order as the master Feature Class.')
                    except LookupError:   #Exception if key does not exist in dicttemp2
                        __printMsg('\t\tERROR     Internal field '+ key + 'does not exist in the returned features.')
                
            #print '\n\t...done checking field order....\n'
            
            #call dictCompare function below to compare field properties
            #print '\n\tComparing Field Properties...'
            propList = ['Domain','IsNullable','Type','Length']
            msg = '     ...in Returned FC '+fcDesc2.Name
            __dictCompare(fldObj1, fldObj2,propList,'Field',msg)   
        
            #-------------------------------------
            __printMsg('\n\tChecking Field Indexes...')
            
            IndexObj1 = gp.ListIndexes(fc1)
            IndexObj2 = gp.ListIndexes(fc2)
            
            #Series of if loops to check for No Indexes
            #NOTE:  it may be that all feature classes automatically have an index on the OBJECTID, so this step may be unnecessary
            if not IndexObj1 and not IndexObj2:
                __printMsg('\t\tOK \t Neither the Master nor the Returned FC have any Field Indexes.')
                #OK Done - skip comparison of Field Indexes
                
            if IndexObj1 and not IndexObj2:
                __printMsg('\t\tERROR \t The Returned FC has no Field Indexes, but the Master FC does.')
                #ERROR - now check the details
                
            if not IndexObj1 and IndexObj2:
                __printMsg('\t\tERROR \t The Master FC has no Field Indexes, but the Returned FC does have Field Indexes')
                # ERROR - now check the details
            
            #If either FC has any indexes, check the details
            if len(IndexObj1) > 0 or len(IndexObj2) > 0:
                #call dictCompare function below to compare indexes
                propList= ['Name','IsAscending','IsUnique']
                msg = '     ...in Returned FC '+fcDesc2.Name
                __dictCompare(IndexObj1,IndexObj2,propList,'Field Index',msg)   #call dictCompare function below
         
            #DONE with Field Index Checking
       #Done with   loop - if FC exists
       
        
# --------------------------------------------------------------------------- 
#Build Dictionaries for field Name and property for two feature classes , based on a property list.
 
# Accepts two Object lists, for comparison.  For example a field list object, or an index list object (ObjList1, ObjList2)
# propList - also accepts a list of Properties (describe properties) to compare  (propList)
# dType - the type of properties/Objects being compared  eg. Index, Field, etc.  Used for reporting any errors
# msg - message to be used if there is an error - specifies Feature Class name
# --------------------------------------------------------------------------- 
def __dictCompare(ObjList1, ObjList2,propList,dType,msg):
    
    #Create a dictionary from the Object lists
    #First create empty dictionary 
    Dict1 = {}
    Dict2 = {}
    
    #print 'Building  dictionary 1...'
    for item in ObjList1:
        Dict1[item.Name] = item
    
    #print 'Building  dictionary 2\n'     
    for item in ObjList2:
        Dict2[item.Name] = item
    
    ''' comparing the two dictionaries'''
    for key in Dict1:
        if key != 'FDO_Shape':    #FDO_Shape appears to be an internal attribute index, therefore ignore
            if Dict2.has_key(key): 
                #print 'Checking',dType, key, '...' 
                Obj1 = Dict1[key]     #what if value is null?
                Obj2 = Dict2[key]
                for property in propList:
                    val1 = eval('Obj1.'+property)
                    val2 = eval('Obj2.'+property)
                    #print '\tComparing', property, '...\t', val1, val2
                    if val2 == val1:
                        #print '\t\t',property, 'is the same ...'
                        pass   #OK - do nothing.
                    else:
                        if not val1:
                            val1 = '<not defined>'
                        if not val2:
                            val2 = '<not defined>'
                        __printMsg('\t\tWARNING     '+ dType + ' '+ key +' '+ property + ' is NOT the same: ' + val1 + ' vs '+ val2 + ' '  + msg)
            else:
                __printMsg('\t\tERROR     '+dType+ ' ' + key+ ' is missing!!' + msg)   #eg. Field or Index is missing
            
    for key in Dict2:
        if not Dict1.has_key(key):
            __printMsg('\t\tERROR     '+ dType+ ' ' + key+ ' is extra!!' + msg)   #eg. Field or Index is missing
            
# ---------------------------------------------------------------------------
#    Check TOPOLOGY element: Name, Cluster Tolerance, Participating Feature Classes, Rules
# ---------------------------------------------------------------------------
def TopologyCheck():
    
    gp.workspace = masterFGDB

    __printMsg('\n----------------------------------------------------------------------------\n')
    __printMsg('STARTING Topology check...')
    __printMsg('\nNOTE:  While this script DOES find which feature classes participate in a topology (if any)')
    __printMsg('it CAN NOT detect which rules are applied to the feature classes.')
    __printMsg('-----------------------------------------')
    __printMsg('\nLooking for matching Topology Elements....')
    
    #Get list of Feature Datasets
    dsets1 = gp.ListDatasets()
    for dataset1 in dsets1:
        __printMsg('\n\tDataset: '+ dataset1+'\n')
        
        gp.workspace = masterFGDB
        dsDescribe1 = gp.Describe(dataset1)
        
        children1 = dsDescribe1.Children
        #print 'Children expanded:', dsDescribe1.ChildrenExpanded
        children1.Reset()
        child1 = children1.Next()
        topCount = 0
        while child1:
            if child1.Datatype == 'Topology':
                __printMsg("\t\t%s: %s" % (child1.Datatype, child1.Name))
                topCount += 1
                gp.workspace = dataset1
                topoDesc1 = gp.Describe(child1.Name)
                topCtol1 = topoDesc1.ClusterTolerance
                topfclass1 = topoDesc1.FeatureClassNames
                topfclass1str = [str(item) for item in topfclass1]
                __printMsg('\n\t\tTopology Cluster Tolerance: '+ str(topoDesc1.ClusterTolerance))
                __printMsg('\t\tTopology FeatureClasses: '+ str(topfclass1str))
                
                #Look for equivalent topology name in Returned FGDB datase
                # NOTE: dataset name and topology name must be equal!!
                comparePath = returnedFGDB + "\\" + dataset1 + "\\" + child1.Name
                #print comparePath
                if gp.exists(comparePath):
                    __printMsg('\n\tMatching Topology EXISTS in the Returned FGDB')
                    topoDesc2 = gp.Describe(comparePath)
                    topCtol2 = topoDesc2.ClusterTolerance
                    topfclass2 = topoDesc2.FeatureClassNames
                    topfclass2str = [str(item) for item in topfclass2]
                    
                    if topCtol2==topCtol1:
                        __printMsg('\t\tTolerance is equal: '+ str(topCtol1))
                    else:
                        __printMsg('\t\tERROR    Returned tolerance setting is not equal: '+str(topCtol1)+' vs '+ str(topCtol2))
                    
                    if topfclass2str==topfclass1str:
                        __printMsg('\t\tParticipating feature classes are equal: '+ str(topfclass1str))
                    else:
                        __printMsg('\t\tERROR    Returned participating feature classes are not equal: '+str(topfclass1str)+' vs '+ str(topfclass2str))
                        
                        
                else:
                    __printMsg('\n\tERROR    Dataset and/or Topology '+ comparePath+ ' does not exist!')
                
            child1 = children1.Next()
            
        #if no topology elements - based on count tracking
        if topCount == 0:
            __printMsg('\nNOTE     No topology elements exist in the Master FGDB for dataset '+ dataset1)
        elif topCount > 0:
            __printMsg('\nNOTE     There is ' + str(topCount)+ ' Topology element(s) in the Master FGDB for dataset '+ dataset1)
            
    
    #------------------
    #Look for extra Topology Elements in Returned data
    gp.workspace = returnedFGDB
    
    __printMsg('\n\nLooking for extra Topology Elements in the returned FGDB datasets....')
    
    #Get list of Feature Datasets
    dsets2 = gp.ListDatasets()
    topCount2 = 0
    for dataset2 in dsets2:
        gp.workspace = returnedFGDB
        dsDescribe2 = gp.Describe(dataset2)
        
        # Print out any children with their datatype
        children2 = dsDescribe2.Children
        children2.Reset()
        child2 = children2.Next()
        while child2:
            #print "\t%s: %s" % (child2.Name, child2.Datatype)
            if child2.Datatype == 'Topology':
                #Look for equivalent topology name in Master FGDB datase
                # NOTE: dataset name and topology name must be equal!!
                comparePath2 = masterFGDB + "\\" + dataset2 + "\\" + child2.Name
                #print comparePath2
                if not gp.exists(comparePath2):
                    __printMsg('\tERROR    Extra TOPOLOGY exists in the Returned Dataset: '+ dataset2 + "\\" + child2.Name)
                    topCount2 += 1
            child2 = children2.Next()
    
    if topCount2 == 0:
            __printMsg('\t...None found...OK.')

# ---------------------------------------------------------------------------
#    Prints message to standard output (python window), log file, and tool (Add Messages)
#     Adds a Message to the geoprocessor (in case this is run as a tool)
#     and also prints the message to the screen
# ---------------------------------------------------------------------------
def __printMsg(msg):
    
    #Print to standard output
    print msg
    
    msg = '\n' + msg
    
    #Print to file
    if fileStat == 'open':
        fileHandle.write(msg)
    
    #Print to tool window
    if toolFlag == 'YES':
        gp.AddMessage(msg)
    


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
#    Initial Set Up
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

#Import the Geoprocessing Object.  If 9.3 is not available, invokes the next available version
# NOTE: 9.3 accepts and returns common Python structures such as lists and Booleans - earlier versions of ArcGIS
# will get an error when trying to deal with/list describe objects.  9.2 will return an enumeration instead of a Python List.
    
try:
    import arcgisscripting
    gp = arcgisscripting.create(9.3)
    print 'Created 9.3 Scripting Object....'
except:
    try:
        gp = arcgisscripting.create()
        print 'Created a 9.2 Scripting object'
        print 'NOTE: this script requires ArcGIS 9.3 functionality to fully run.\n Errors may occur if using 9.2'
    except:
        gp = win32com.client.Dispatch("esriGeoprocessing.GpDispatch.1")   #This would be for pre 9.2 


# Set OverWriteOutput to False
gp.overwriteoutput=0

#----------------------------------------
##Script arguments...
# We also want to know how the arguments were supplied, which sets a flag to indicate how messages will be given...
#---------------------------------------

#First, check for arguments supplied by a tool  NOTE: parameters will just be blank if not set in a tool.
masterFGDB = gp.GetParameterAsText(0)
returnedFGDB = gp.GetParameterAsText(1)


if masterFGDB and returnedFGDB:    #if parameters are not null/blank/empty  (indicates that parameters are set from a tool)
    toolFlag = 'YES'        # Flags if the parameters are set from running a tool - then 'AddMessages' will be used...
else:
     #Then check for arguments supplied from command line 
    try:
        #argScriptName = sys.argv[0]   #optional 
        masterFGDB = sys.argv[1]
        returnedFGDB = sys.argv[2]
        toolFlag = 'NO'    # Flags if the parameters are set from running from command line - don't need 'AddMessages'

    #Then, if still no argument...  (may be set directly in the script)
    except:
        print 'No arguments provided - will check script for hard-coded values'
        print '-----------------------------------------\n'
        toolFlag = 'NO'      #don't need 'AddMessages'


###TEST DATASETS
#masterFGDB = r'Z:\Tools\test_wksp\salees\StrategicLandAndResourcePlans\CurrentUpdate\strategic_land_resource_plan_bc.gdb'
#returnedFGDB = r'Z:\Tools\test_wksp\salees\StrategicLandAndResourcePlans\CurrentUpdate\strategic_land_resource_plan_bc_Update_20100525_returned.gdb'

#----------------------------------------
# Test for existence of input and output
#----------------------------------------

fileStat = 'init'

if not gp.exists(masterFGDB):
    __printMsg('QUITTING - Master file does not exist')
    sys.exit()
    
if not gp.exists(returnedFGDB):
    __printMsg('QUITTING - Returned file does not exist')
    sys.exit()
    
#----------------------------------------
# Set up log file
#----------------------------------------

now = time.localtime()
t1 = str(now.tm_hour)+str(now.tm_min)+str(now.tm_sec)
gdbPath = os.path.dirname(returnedFGDB)

LogFile = gdbPath + "\\" + "DataPropertiesCheck_Log_"  + str(datetime.date.today())+ '_' + t1 + ".txt"
fileHandle = open(LogFile, 'w')
fileStat = 'open'

__printMsg(' Writing to Log File '+LogFile+' ...\n')

startTime = time.clock()

START_TIME = time.ctime(time.time())
__printMsg('   Starting : '+START_TIME)
__printMsg('\n----------------------------------------------------------------------------\n')


# ---------------------------------------------------------------------------
#    Describe FGDB and set up Describe Variable
#    Test that parameter supplied is actually a FGDB  - FUTURE - alternatively, if not a FGDB, then go to appropriate test
# ---------------------------------------------------------------------------

__printMsg('Master FGDB: '+ masterFGDB)
__printMsg('Returned FGDB: '+ returnedFGDB)
__printMsg('\n Describing Master and Returned GeoDatabases...\n')

desc1 = gp.describe(masterFGDB)
desc2 = gp.describe(returnedFGDB)


#Test that they are a FGDB and that they exist
if not desc1.datatype == 'Workspace' and not desc1.extension == 'gdb' :
    __printMsg('QUITTING - Master is not a File Geodatabase.  Must be a File GDB...')
    sys.exit()
    
if not desc2.datatype == 'Workspace' and not desc2.extension == 'gdb':
    __printMsg('QUITTING - Returned is not a File Geodatabase.  Must be a File GDB...')
    sys.exit()

#Check that master and returned are the same data type
if desc1.WorkspaceType <> desc2.WorkspaceType:
    __printMsg('\t\tERROR    Workspace Type Mismatch: '+ desc1.WorkspaceType+ ' vs '+ desc2.WorkspaceType)
    __printMsg('QUITTING - One of the databases is not a true File geodatabase ... Cannot proceed.')
    sys.exit()

#Check that FGDB contains some Feature Datasets
gp.workspace = masterFGDB
if not gp.ListDatasets():
    __printMsg('\t\tWARNING   Master has no Datasets...')
gp.workspace = returnedFGDB
if not gp.ListDatasets():
    __printMsg('\t\tWARNING   Returned has no Datasets...')


# ---------------------------------------------------------------------------
#    Call Modules
# ---------------------------------------------------------------------------

DomainProperties()
DatasetProperties()       #Compares Feature Dataset Properties and Feature Class Properties.  Loops each feature class within a feature dataset.
TopologyCheck()

stopTime = time.clock()
elapsedTime = stopTime - startTime

__printMsg('\n----------------------------------------------------------------------------')
print "\n...SCRIPT COMPLETE...   elapsed time = " + str(round(elapsedTime / 60, 1)) + " minutes"
fileHandle.write('\n')
fileHandle.write("\n...SCRIPT COMPLETE...   elapsed time = " + str(round(elapsedTime / 60, 1)) + " minutes")

#Close Log File
fileHandle.close()

