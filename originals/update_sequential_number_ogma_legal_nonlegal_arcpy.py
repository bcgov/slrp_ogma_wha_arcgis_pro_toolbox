'''
Author: Carole Mahood - based on original gp script written by Mark McGirr   
Purpose: To find the highest sequential PROVID number across both legal and
         non-legal OGMA feature classes for a given prefix, then update
         empty/null records in the non-legal feature class with the next
         sequential values.
         
Date: January 8, 2017

Arguments:  
            
Dependencies: 
              
----------------------------------------------------------------------------------------------
Date: 
Author:    
Modification:   
-----------------------------------------------------------------------------------------------
'''

import sys, arcpy, datetime, os, shutil
from arcpy import env

arcpy.env.overwriteOutput = True

def main():
    set_global_variables()
    update_data()
    
def set_global_variables():
    global fc_1
    fc_1 = sys.argv[1]
      
    global field_1
    field_1 = sys.argv[2]
      
    global fc_2
    fc_2 = sys.argv[3]
      
    global field_2
    field_2 = sys.argv[4]
      
    global prefix
    prefix = sys.argv[5]
 
    global is_new_prefix
    is_new_prefix = sys.argv[6]
    
    global just_display_dont_update
    just_display_dont_update = sys.argv[7]
    
    
    
#     global fc_1
#     fc_1 = r"\\spatialfiles.bcgov\work\srm\wml\Workarea\camahood\Data_Management\data_issues\slrp\fresh_old_growth_management_area_bc_Update_20181218_1.gdb\old_growth_management_area_albers\old_growth_management_area_non_legal_bc_poly"
#      
#     global field_1
#     field_1 = "NON_LEGAL_OGMA_PROVID"
#      
#     global fc_2
#     fc_2 = r"\\spatialfiles.bcgov\work\srm\wml\Workarea\camahood\Data_Management\data_issues\slrp\fresh_old_growth_management_area_bc_Update_20181218_1.gdb\old_growth_management_area_albers\old_growth_management_area_legal_bc_poly"
#      
#     global field_2
#     field_2 = "LEGAL_OGMA_PROVID"
#      
#     global prefix
#     prefix = "CAR_RCA_"
#      
#     global is_new_prefix
#     is_new_prefix = False
#      
#     global just_display_dont_update
#     just_display_dont_update = False
    
    arcpy.AddMessage(fc_1)
    arcpy.AddMessage(field_1)
    arcpy.AddMessage(fc_2)
    arcpy.AddMessage(field_2)
    arcpy.AddMessage(prefix)
    arcpy.AddMessage('Is a new prefix? ' + is_new_prefix)
    arcpy.AddMessage('Just display value, dont update? ' + just_display_dont_update)
    arcpy.AddMessage("\n")
    
     
    
            

def update_data():

    #check if prefix exists
    arcpy.MakeFeatureLayer_management(fc_1, 'fc_1_lyr', "\"" + field_1 + "\" like '" + prefix + "%'")
    count_1 = int(str(arcpy.GetCount_management('fc_1_lyr')))
        
    arcpy.MakeFeatureLayer_management(fc_2, 'fc_2_lyr', "\"" + field_2 + "\" like '" + prefix + "%'")
    count_2 = int(str(arcpy.GetCount_management('fc_2_lyr')))
    
    total_prefix_count = count_1 + count_2
    
    keep_going = True
    
    if total_prefix_count == 0:
        arcpy.AddWarning(prefix + ' is a new prefix.')
        
        if is_new_prefix != 'true':
            keep_going = False
            arcpy.AddError('Please rerun the tool with the "This will be a new prefix" box checked')
            sys.exit()
            
            
    else:
        arcpy.AddWarning(prefix + ' already exists in one of the feature classes.\n')
        if is_new_prefix == 'true': 
            keep_going = False           
            arcpy.AddError('If you are sure you want to proceed using this prefix, rerun the tool with the "This will be a new prefix" box unchecked.')
            sys.exit()
        
    
    if keep_going == True:
    
        if is_new_prefix == True:
            arcpy.AddWarning(prefix + ' is a new prefix. Numbering will start at ' + prefix + '1.')
            
            next_value = 1
        
        else:
    
            arcpy.AddWarning('Searching through ' + str(count_1) + ' features with prefix of ' + prefix + ' in ' + os.path.basename(fc_1))
            arcpy.AddWarning('Searching through ' + str(count_2) + ' features with prefix of ' + prefix + ' in ' + os.path.basename(fc_2) + "\n")


            #find highest number for each prefix
            the_list = []
                
                #look in fc_1
            fields = [field_1]
            search_cur_1 = arcpy.da.SearchCursor('fc_1_lyr', fields)
            
            
            for row in search_cur_1:
                split_list = row[0].split('_')
                if len(split_list) == 3:
                    prefix_1 = split_list[0] + "_" + split_list[1] + "_"
                    number_suffix = split_list[2]
                elif len(split_list) == 4:
                    prefix_1 = split_list[0] + "_" + split_list[1] + "_" + split_list[2] + "_"
                    number_suffix = split_list[3]
                else:
                    prefix_1 = 0
                    number_suffix = 0
                
                
                try:
                    number_suffix_int = int(number_suffix)
        
                    if [prefix_1, number_suffix_int] not in the_list:
                        the_list.append([prefix_1, number_suffix_int])
                except:
                    arcpy.AddWarning('            ' +  row[0] + ' does not have an integer as a suffix...skipping.')
            
                #look in fc_2
            fields = [field_2]
            search_cur_2 = arcpy.da.SearchCursor('fc_2_lyr', fields)
            
            for row in search_cur_2:
                split_list = row[0].split('_')
                if len(split_list) == 3:
                    prefix_2 = split_list[0] + "_" + split_list[1] + "_"
                    number_suffix = split_list[2]
                elif len(split_list) == 4:
                    prefix_2 = split_list[0] + "_" + split_list[1] + "_" + split_list[2] + "_"
                    number_suffix = split_list[3]
                else:
                    prefix_2 = 0
                    number_suffix = 0
                
                
                try:
                    number_suffix_int = int(number_suffix)
        
                    if [prefix_2, number_suffix_int] not in the_list:
                        the_list.append([prefix_2, number_suffix_int])
                except:
                    arcpy.AddWarning('            ' +  row[0] + ' does not have an integer as a suffix...skipping.')
                
            the_list.sort()
            highest_value_in_the_list = max(the_list)
            highest_suffix = highest_value_in_the_list[1]
            
            next_value = highest_suffix + 1
            
            
            arcpy.AddWarning('The highest value in either dataset is ' + prefix + str(highest_suffix) + '. Numbering for new features will start at ' + prefix + str(next_value) + ".")
                
            
        if just_display_dont_update != 'true':
            arcpy.AddMessage('Updating ' + field_1 + ", starting with " + prefix + str(next_value) + ":")
            
            fds = os.path.dirname(fc_1)
            x = os.path.dirname(fds)
            arcpy.AddWarning('fds ' + fds)
            arcpy.AddWarning('x ' + x)
            arcpy.AddMessage('workspace: ' +  fds)
            
            edit = arcpy.da.Editor(x)
            edit.startEditing(True)
            edit.startOperation()
            
                
            
            arcpy.MakeFeatureLayer_management(fc_1, 'fc_1_lyr', "\"" + field_1 + "\" = '' OR \"" + field_1 + "\" is null")
            fields = [field_1]
            update_cur = arcpy.da.UpdateCursor('fc_1_lyr', fields)
            
            for row in update_cur:
                arcpy.AddMessage('    ' + prefix + str(next_value)) 
                row[0] = prefix + str(next_value)
                update_cur.updateRow(row)
                next_value +=1
            
            edit.stopOperation()
            edit.stopEditing(True)
            
        else:
            arcpy.AddWarning('Display only box checked - data was not updated.')           
        
   

        
        
        
             
            
            
        
    
main()