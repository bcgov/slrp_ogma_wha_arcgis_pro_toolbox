'''
Author: Mark McGirr
Purpose: This script checks to see if there are duplicate values in a selected field.
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
    process_current_only = sys.argv[3]
    gp.addmessage(process_current_only)
    if process_current_only =='true' :
        process_current_only = True
    else:
        process_current_only = False
    gp.addmessage(process_current_only)
    selected_featureclass2 = sys.argv[4]
    gp.addmessage(selected_featureclass2)
    selected_field2 = sys.argv[5]
    gp.addmessage(selected_field2)
        
except:
    print "no arguments"




##############################################################################################
 # for testing in eclipse
 
''' 
#selected_featureclass =  r'W:\srm\wml\Workarea\jnbowman\temp\planning_test\slrp.gdb\lu3'
selected_featureclass = r"\\srmapps\slrp\UpdateWorkarea\Tools\test_wksp\mark\old_growth_management_area_bc.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc"
selected_featureclass2 = r"\\srmapps\slrp\UpdateWorkarea\Tools\test_wksp\mark\old_growth_management_area_bc.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc"
selected_featureclass2 = r"w:\srm\wml\Workarea\cbjorkman\zTemp\testtesttest.gdb\test2"
selected_featureclass = r"w:\srm\wml\Workarea\cbjorkman\zTemp\testtesttest.gdb\test1"


selected_field = "LEGAL_OGMA_PROVID;OGMA_TYPE;junksection"
selected_field2 = "NON_LEGAL_OGMA_PROVID;OGMA_TYPE;junksection"
selected_field = "field1;OGMA_TYPE;junksection"
selected_field2 = "field1;OGMA_TYPE;junksection"
process_current_only = True

'''


############################################################################################




############################################################################################
# split list of fields into individual parts 
temp_field_list = selected_field.split(';')
temp_field_list.append("") # add a blank just so we can evaluate if there is no second field passed in

selected_field = temp_field_list[0]
selected_field_part2 = temp_field_list[1]
                            
print selected_field
print selected_field_part2 


temp_field_list2 = selected_field2.split(';')
temp_field_list2.append("") # add a blank just so we can evaluate if there is no second field passed in

selected_field2 = temp_field_list2[0]
selected_field2_part2 = temp_field_list2[1]
                            
print selected_field2
print selected_field2_part2 


############################################################################################
#check to see if the selected field exists

'''

enumObj = gp.listfields(selected_featureclass)
fldobj = enumObj.next()

#Get all the field names in the featureclass
#Use the ListFields to create an enumeration object
enumObj = gp.ListFields(selected_featureclass, '*')
enumObj.reset()
fldObj = enumObj.next()

selected_field_exists = 'no'
while fldObj:
        #print 'The field name is', fldObj.Name, 'has been loaded'
        this_field_name = fldObj.Name
        this_field_name.upper()
        if this_field_name == selected_field.upper():
            selected_field_exists = 'yes'           
    
        fldObj = enumObj.next()

'''

############################################################################################









############################################################################################
#check for duplicates

#if selected_field_exists == 'yes':

selected_field_values = []

#create a cursor and read all records for selected field into a list    
rowsObj = gp.searchcursor(selected_featureclass)
row = rowsObj.next()
while row:
        execute_string = "row." + selected_field
        print execute_string, "  execute_string"
        origional_value_part1 = str(eval(execute_string))
        origional_value_part2 = ""
        origional_value = origional_value_part1
        execute_retirement_string = "row." + "RETIREMENT_DATE"
        retirement_string = str(eval(execute_retirement_string))
        print "retirement_string   " , retirement_string
        #if retirement_string  == ""  or retirement_string  == "None":
        #    gp.addmessage( "this is not retired yet")
        #else:
        #    gp.addmessage("retired")



        if selected_field_part2 <> "" :
            execute_string_part2 = "row." + selected_field_part2
            origional_value_part2 = str(eval(execute_string_part2))
            origional_value = origional_value_part1 + " -> " + origional_value_part2

        #if float(origional_value_part1) < 0 or float(origional_value_part2) < 0:
        #    print 'skipping this record because its a negative'
        #else:
        #    print "process these positive records"
        
        #if float(origional_value_part1) < 0:
        #    print "this one less than zero"
             
        
        try:
            number_from_string = float(origional_value_part1)
        except:
            number_from_string = 0
            
#            if process_current_only == False and float(origional_value_part1) >= 0 :
        if process_current_only == False and number_from_string >= 0 :
            selected_field_values.append (origional_value)
            #row=rowsObj.next()
 
#            if process_current_only == True and float(origional_value_part1) >= 0  and (retirement_string  == ""  or retirement_string  == "None"):
        if process_current_only == True and number_from_string >= 0  and (retirement_string  == ""  or retirement_string  == "None"):
            selected_field_values.append (origional_value)
            #row=rowsObj.next()
    
        row=rowsObj.next()
        







#selected_field_values2 = []

#create a cursor and read all records for selected field into a list    
rowsObj = gp.searchcursor(selected_featureclass2)
row = rowsObj.next()
while row:
        execute_string = "row." + selected_field2
        origional_value_part1 = str(eval(execute_string))
        origional_value_part2 = ""
        origional_value = origional_value_part1
        execute_retirement_string = "row." + "RETIREMENT_DATE"
        retirement_string = str(eval(execute_retirement_string))
        print "retirement_string   " , retirement_string
        #if retirement_string  == ""  or retirement_string  == "None":
        #    gp.addmessage( "this is not retired yet")
        #else:
        #    gp.addmessage("retired")



        if selected_field2_part2 <> "" :
            execute_string_part2 = "row." + selected_field2_part2
            origional_value_part2 = str(eval(execute_string_part2))
            origional_value = origional_value_part1 + " -> " + origional_value_part2

        #if float(origional_value_part1) < 0 or float(origional_value_part2) < 0:
        #    print 'skipping this record because its a negative'
        #else:
        #    print "process these positive records"
        
        #if float(origional_value_part1) < 0:
        #    print "this one less than zero"
             
        
        try:
            number_from_string = float(origional_value_part1)
        except:
            number_from_string = 0
            
#            if process_current_only == False and float(origional_value_part1) >= 0 :
        if process_current_only == False and number_from_string >= 0 :
            selected_field_values.append (origional_value)
            #row=rowsObj.next()
 
#            if process_current_only == True and float(origional_value_part1) >= 0  and (retirement_string  == ""  or retirement_string  == "None"):
        if process_current_only == True and number_from_string >= 0  and (retirement_string  == ""  or retirement_string  == "None"):
            selected_field_values.append (origional_value)
            #row=rowsObj.next()
    
        row=rowsObj.next()



















        
#check for duplicates and print warning message if there are duplicates
duplicates_found = 'no'
gp.addwarning(" ")
gp.addwarning(" ")

if selected_field_values:
    selected_field_values.sort()
    last = selected_field_values[-1]
    for i in range(len(selected_field_values)-2, -1, -1):
        if last == selected_field_values[i]:
            notify_message = selected_field + "   " + str(selected_field_values[i]) + "   has duplicate values."
            duplicates_found = 'yes'
            gp.addwarning(notify_message)
        else:
            last = selected_field_values[i]

gp.addwarning(" ")
gp.addwarning(" ")

if duplicates_found == 'no':

    gp.addwarning("No Duplicates Have Been Found")
    gp.addwarning(" ")
    gp.addwarning(" ")

#else:
#    gp.adderror(selected_field + " does not exist.")
    
