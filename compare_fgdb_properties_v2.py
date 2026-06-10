#===========================================================================
# Script name: compare_fgdb_properties_v2.py
# Original Author: Sasha Lees, February 5, 2010 (Python 2 / ArcGIS 9.3)
# Original Script: Compare_FGDB_Properties_v1b_100628.py
# Migrated to: Python 3 / ArcGIS Pro 3
# Migration notes:
#   - arcgisscripting.create(9.3) / win32com replaced with arcpy
#   - print statements replaced with arcpy.AddMessage()
#   - gp.* calls replaced with arcpy.*
#   - .iteritems() / .has_key() replaced with Python 3 equivalents
#   - <> replaced with !=
#   - eval('obj.'+prop) replaced with getattr(obj, prop, None)
#   - Children.Reset()/Next() enumeration replaced with direct list iteration
#   - in_memory workspace replaced with memory workspace (Pro)
#   - time.clock() replaced with time.perf_counter()
#   - All file writes use open(..., encoding='utf-8')
#
# Entry point: run(master_fgdb, returned_fgdb)
# Output:      compareFGDBLogFile  (module-level variable; read by .pyt wrapper)
#===========================================================================

import os
import time
import datetime
import arcpy

# Module-level variable - set by run(); read by the .pyt toolbox wrapper after calling run()
compareFGDBLogFile = None


def run(master_fgdb, returned_fgdb):
    """
    Compare properties of returned_fgdb against master_fgdb.

    Checks:
      - Domain names and coded values / descriptions
      - Feature dataset coordinate systems, tolerances, resolutions, extents
      - Feature class properties, fields, and field indexes
      - Topology elements (cluster tolerance, participating feature classes)

    Writes a text log file to the parent folder of returned_fgdb.
    Sets the module-level compareFGDBLogFile to the output path on completion.
    """
    global compareFGDBLogFile

    # --- Set up log file ---
    # ORIGINAL: gdbPath = os.path.dirname(returnedFGDB); open(LogFile, 'w')
    # CHANGE: open(..., encoding='utf-8') added; os.path.join() for cross-platform path safety
    # RISK: If returned_fgdb parent folder is read-only, open() raises PermissionError
    # DOWNSTREAM: fh used by _log() for all file output throughout the function
    now = time.localtime()
    t1 = str(now.tm_hour) + str(now.tm_min) + str(now.tm_sec)
    gdb_path = os.path.dirname(returned_fgdb)
    log_file = os.path.join(
        gdb_path,
        f"DataPropertiesCheck_Log_{datetime.date.today()}_{t1}.txt"
    )
    fh = open(log_file, 'w', encoding='utf-8')

    # -----------------------------------------------------------------------
    # Internal helpers (closures over fh, master_fgdb, returned_fgdb)
    # -----------------------------------------------------------------------

    def _log(msg):
        # ORIGINAL: __printMsg — print msg (Python 2); conditional gp.AddMessage if toolFlag='YES'
        # CHANGE: arcpy.AddMessage() always (toolbox context); write to file unconditionally
        # RISK: None; toolbox tools always use arcpy.AddMessage()
        # DOWNSTREAM: Every output line in domain_properties, dataset_properties, topology_check
        arcpy.AddMessage(msg)
        fh.write(msg + '\n')

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

    compareFGDBLogFile = log_file
