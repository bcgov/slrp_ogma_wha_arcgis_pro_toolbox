'''
Author: Mark McGirr
Purpose: This script updates the values of a field with the next highest sequential number.
        If it is a string field you can enter a string prefix, and it will start adding numbers to the
        new prefix at 1, or to the existing prefix at it's highest value.
         `
Date: June 2009

Arguments: argv0 = script name (does not need to be passed).  argv1 = enire path to featureclass
           argv2 = field to check for duplicates in
           
Outputs:
Dependencies:


History:
----------------------------------------------------------------------------------------------
Date:
Author:
Modification:
-----------------------------------------------------------------------------------------------
'''
import sys, string, os, os.path, win32com.client
import win32com.client    #arcgisscripting
gp=win32com.client.Dispatch("esriGeoprocessing.GpDispatch.1")
    
    
############################################################################################
#read passed in arguments
try:
    argThisDataSet = ""
    argScriptName = sys.argv[0]
    selected_featureclass = sys.argv[1]
    gp.addmessage(selected_featureclass)
    selected_field = sys.argv[2]
    gp.addmessage(selected_field)
    prefix = sys.argv[3]
    gp.addmessage(prefix)
except:
    print "no arguments"
    
try:
    is_new_prefix = True
    is_new_prefix_arg = sys.argv[4]
    gp.addmessage(is_new_prefix_arg)
    if is_new_prefix_arg == 'true':
        #gp.addmessage( "Of course its true")
        is_new_prefix = True
    if is_new_prefix_arg == 'false':
        #gp.addmessage( "Of course its false")
        is_new_prefix = False 
except:
    print "no arguments"
          
try:
    just_display_dont_update = True
    just_display_dont_update_arg  = sys.argv[5]
    gp.addmessage(just_display_dont_update_arg)
    if just_display_dont_update_arg == 'true':
        #gp.addmessage( "Of course its true")
        just_display_dont_update = True
    if just_display_dont_update_arg == 'false':
        #gp.addmessage( "Of course its false")
        just_display_dont_update = False             
        
except:
    print "no arguments"



# these below statements are for testing so you con't have to pass the arguments in.
'''
#selected_featureclass =  r"w:\srm\kam\Workarea\ksc_proj\p09\p09_0009A_FSP_FIA_data_prep_phase2\wrk\data\prov\strategic_land_resource_plan_bc_Mark_test.gdb\slrp_albers\slrp_planning_feature_non_legal_bc_point_dup"
#selected_field = "NON_LEGAL_FEAT_PROVID"
selected_featureclass =  r"V:\old_growth_management_area_bc_tooltest.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc_poly_provid"

selected_field = "LEGAL_OGMA_PROVID"
#selected_field = "NON_LEGAL_FEAT_ID"
prefix = "SKE_KIS_"
is_new_prefix = False
just_display_dont_update = False  
'''


#selected_featureclass = r"\\Walnut\slrp\UpdateWorkarea\Tools\test_wksp\mark\old_growth_management_area_bc.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc"
#selected_field = "OBJECTID"
############################################################################################










############################################################################################
#check to see if the selected field exists and whether its a string field

enumObj = gp.ListFields(selected_featureclass, '*')
enumObj.reset()
fldObj = enumObj.next()

selected_field_exists = 'no'
while fldObj:
        #print 'The field name is', fldObj.Name, 'has been loaded'
        this_field_name = fldObj.Name
        this_field_type = fldObj.type
        this_field_name.upper()
        if this_field_name == selected_field.upper():
            selected_field_exists = 'yes'
            selected_field_type = this_field_type           
    
        fldObj = enumObj.next()
############################################################################################






#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################
'''
This section is only relavent for string fields.
'''

if  selected_field_type == 'String':
    print "starting into string section"





    #######################################################################################################
    #get highest suffix number                     variable  "new_numbers_start_at"    will hold value
    '''
    This section is only relevent for string fields.
    
    The value of every record for the field you selected is broken down into a suffix which contains the
    right most numbers of the string, and a prefix which contains all the leading characters.
    A dictionary is built that contains the unique prefix's and the highest number that exists in the suffix.
    i.e.
    
    CAR_RCA_   135
    KAM_21_    144
    SM_DL_     1300
    
    '''
        
    selected_field_values = []
    
    #create a cursor and read all records for selected field into a list    
    rowsObj = gp.searchcursor(selected_featureclass)
    row = rowsObj.next()
    number_suffix_list= []
    field_prefix_list = []
    prefix_suffix = {}
    while row:  # read each row of the featureclass
        execute_string = "row." + selected_field
        field_value = eval(execute_string)
        selected_field_values.append ( eval(execute_string))
        row=rowsObj.next()
    
        if selected_field_values:
            pig = field_value
            print "pig   is   " , pig
            numbers_start_at = 0
            hit_the_end_of_suffix_numbers = 'no'
            digits_found = 'no'
            has_suffix = 'yes'  #mmm
            print len(pig), "length", " hit_the_end_of_suffix_numbers  " ,  hit_the_end_of_suffix_numbers
            if len(pig) > 0 : 
                x = len(pig)
                print "x is " , x
                if pig[(x-1)].isdigit() is False: #mmm
                    hit_the_end_of_suffix_numbers == 'yes-'#mmm
                    has_suffix = 'no'
                while    hit_the_end_of_suffix_numbers == 'no' and x > 0:
                    print pig[(x-1)], x
                    x = x - 1
                    if pig[(x-1)].isdigit():
                        numbers_start_at = x
                    else:
                             hit_the_end_of_suffix_numbers = 'yes'
    
                if has_suffix == 'yes':  #mmm
                    this_prefix =  pig[:(numbers_start_at -1)]
                    this_suffix = int(pig[(numbers_start_at -1):])
                else:  #mmm
                    this_suffix = 0  #mmm
                    this_prefix = pig
                print "thisprefix    " , this_prefix  # mmm
                if prefix_suffix.has_key(this_prefix) == False:
                    print "adding the prefix   " , this_prefix , "==============================================="
                    prefix_suffix[this_prefix] = 0
                if prefix_suffix[this_prefix]< this_suffix :
                    prefix_suffix[this_prefix] = this_suffix
    
    
    #sa = set(field_prefix_list)
    #print sa
    
    for x , y  in prefix_suffix.iteritems():
        gp.addmessage(str(x) + " has a highest value of   " + str(y) )
        print x, " has a highest value of   " , y 
    
    prefix_error_message = ""
    if is_new_prefix == True:
        print "is_new_prefix is checked on"
        current_highest_sequence_number = 0
        if prefix_suffix.has_key(prefix) is True:
              prefix_error_message =  "the prefix already exists"
       
    if is_new_prefix == False:
        print "is_new_prefix is not checked on"
        if prefix_suffix.has_key(prefix) is False:
              prefix_error_message =  "the prefix does not already exists"
        if prefix_suffix.has_key(prefix) is True:
            print "prefix " , prefix
            print prefix_suffix[prefix]
            
            current_highest_sequence_number = prefix_suffix[prefix]
            print "current_highest_sequence_number" , current_highest_sequence_number

    del row
    del rowsObj
    
    
    if prefix_error_message <> "":
        gp.adderror(prefix_error_message)
        gp.addmessage(" ")
        gp.addmessage(" ")
        stop
  
    
    # end of finding all the prefix and suffix values
    #######################################################################################################
    #######################################################################################################
      

    #stop


    #######################################################################################################
    #######################################################################################################
    # update the blank fields with the new prefix and incremented suffix values









    new_numbers_start_at =    current_highest_sequence_number + 1 
    gp.addmessage(" ")
    gp.addmessage(" ")
    gp.addwarning( "new_numbers_start_at   "  + str(new_numbers_start_at) + "     for  prefix  " + prefix  )
    gp.addmessage(" ")
    gp.addmessage(" ")













    
    if prefix_error_message == ""  and just_display_dont_update is False :
#    if prefix_error_message == "" :
    

        
        print "new_numbers_start_at   " ,    new_numbers_start_at 
        
        
        rowsObj = gp.updatecursor(selected_featureclass)
        row = rowsObj.next()
        while row:
            
            #create a cursor and read all records for selected field into a list    
        
            execute_string = "row." + selected_field
            origional_value = eval(execute_string)
            modified_value = origional_value.strip()
            if modified_value == "" :
                modified_value = prefix + str(new_numbers_start_at)
                new_numbers_start_at = new_numbers_start_at + 1
                execute_string = str("row." + selected_field + " = " + '"' +  modified_value + '"')
                exec execute_string
                print "updated " , modified_value
                rowsObj.UpdateRow(row)
                
            row=rowsObj.next()
        
        del row
        del rowsObj
        
    
#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################













#######################################################################################################
#######################################################################################################
#######################################################################################################
#######################################################################################################
'''
This section is only relavent for numeric fields.  Just increment to the highest number found.
'''
    
    
 
    


#########  Get the highest value    ########

if  selected_field_type <> 'String':
    print "starting into non_string section"
    selected_field_values = []

    #create a cursor and read all records for selected field into a list    
    rowsObj = gp.searchcursor(selected_featureclass)
    row = rowsObj.next()
    number_suffix_list= []
    highest_number = 0
    while row:  # read each row of the featureclass
        execute_string = "row." + selected_field
        field_value = eval(execute_string)
        selected_field_values.append ( eval(execute_string))
        row=rowsObj.next()
    
        if selected_field_values:
            pig = int(field_value)
            if pig > highest_number:
                highest_number = pig
            
            
    
    printstring  = "new_numbers_start_at   " + str(highest_number + 1)
    gp.addmessage(printstring) 
    
    del row
    del rowsObj
    
    ############################################################################################
    # Loop through again and replace the zeros
    if  just_display_dont_update is False :
            
                
        rowsObj = gp.updatecursor(selected_featureclass)
        row = rowsObj.next()
        while row:
            
            #create a cursor and read all records for selected field into a list    
        
            execute_string = "row." + selected_field
            origional_value = eval(execute_string)
            if origional_value == 0:
                highest_number  = highest_number + 1
                execute_string = str("row." + selected_field + " = " + '"' +  str(highest_number) + '"')
                print execute_string
                exec execute_string
                rowsObj.UpdateRow(row)
                
            row=rowsObj.next()
            
        
    #del row
    #del rowsObj
        