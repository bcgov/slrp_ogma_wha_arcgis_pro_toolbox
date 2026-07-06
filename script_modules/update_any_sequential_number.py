'''
Author: Mark McGirr (June 2009)

Purpose: This script updates the values of a field with the next highest sequential number.
        If it is a string field you can enter a string prefix, and it will start adding numbers to the
        new prefix at 1, or to the existing prefix at it's highest value.

History:
----------------------------------------------------------------------------------------------
Date: April 2026
Author: Sean Parsons
Modification: Updated script to be compatible with SLRP OGMA ArcGIS Pro toolbox and Python 3.
----------------------------------------------------------------------------------------------
Date: June 2026
Modification: Converted to importable module with run() function. Fixed SearchCursor indentation
              bug (if selected_field_values block was outside for loop - only the last record
              was processed). Replaced print() with arcpy.AddMessage(). Added arcpy progressor.
-----------------------------------------------------------------------------------------------
'''
import arcpy


def run(selected_featureclass, selected_field, prefix, is_new_prefix, just_display_dont_update):
    """Update a field with the next highest sequential number.

    For string fields, scans all records to build a prefix-to-highest-suffix dictionary,
    validates the prefix, and fills blank records with the next sequential value.
    For numeric fields, finds the highest existing value and fills zero/null records.

    Parameters
    ----------
    selected_featureclass : str
        Full path or layer name of the feature class to update.
    selected_field : str
        Name of the field to update.
    prefix : str
        Prefix string for text fields (e.g. "CAR_RCA_"). Pass "" for numeric fields.
    is_new_prefix : bool
        True if this prefix has never been used before (text fields only).
    just_display_dont_update : bool
        True to report the next value without writing any changes.
    """
    arcpy.SetProgressor("step", "Checking field...", 0, 4, 1)

    arcpy.AddMessage(f"Feature Class  : {selected_featureclass}")
    arcpy.AddMessage(f"Field          : {selected_field}")
    arcpy.AddMessage(f"Prefix         : {prefix if prefix else '(none - numeric field)'}")
    arcpy.AddMessage(f"Is new prefix? : {is_new_prefix}")
    arcpy.AddMessage(f"Display only?  : {just_display_dont_update}")

    ############################################################################################
    # Step 1: Check to see if the selected field exists and whether its a string field
    ############################################################################################
    arcpy.SetProgressorLabel("Step 1 of 4: Checking that the selected field exists...")
    arcpy.SetProgressorPosition()

    selected_field_exists = 'no'
    for fldObj in arcpy.ListFields(selected_featureclass):
        this_field_name = fldObj.name
        this_field_type = fldObj.type
        if this_field_name.upper() == selected_field.upper():
            selected_field_exists = 'yes'
            selected_field_type = this_field_type

    if selected_field_exists == 'no':
        arcpy.AddError(f"Field '{selected_field}' was not found in the feature class. Check the field name and try again.")
        return

    arcpy.AddMessage(f"Field '{selected_field}' found. Field type: {selected_field_type}")

    #######################################################################################################
    #######################################################################################################
    # STRING FIELD SECTION
    # Only relevant for string fields.
    #######################################################################################################
    #######################################################################################################

    if selected_field_type in ('TEXT', 'String'):

        #######################################################################################################
        # Step 2: Scan all records and build a dict of {prefix: highest_suffix_number}
        #
        # Each field value is split into a text prefix and a numeric suffix (the trailing digits).
        # For example "CAR_RCA_135" -> prefix="CAR_RCA_", suffix=135
        # The dict tracks the highest suffix seen for each prefix across ALL records.
        #######################################################################################################
        arcpy.SetProgressorLabel("Step 2 of 4: Scanning all records to find existing prefix/suffix values...")
        arcpy.SetProgressorPosition()

        selected_field_values = []

        #create a cursor and read all records for selected field into a list
        number_suffix_list= []
        field_prefix_list = []
        prefix_suffix = {}
        with arcpy.da.SearchCursor(selected_featureclass, [selected_field]) as cursor:
            for row in cursor:
                field_value = row[0]
                selected_field_values.append(row[0])

                # ORIGINAL: if selected_field_values block was at this indent level (inside with, outside for)
                # CHANGE: Moved inside the for loop so every record is processed, not just the last one.
                # RISK: Leaving outside the for loop causes only the last record to feed prefix_suffix,
                #       which can result in duplicate sequential numbers being assigned.
                # DOWNSTREAM: prefix_suffix -> current_highest_sequence_number -> new_numbers_start_at
                if field_value:
                    pig = field_value
                    numbers_start_at = 0
                    hit_the_end_of_suffix_numbers = 'no'
                    digits_found = 'no'
                    has_suffix = 'yes'  #mmm
                    if len(pig) > 0 :
                        x = len(pig)
                        if pig[(x-1)].isdigit() is False: #mmm
                            hit_the_end_of_suffix_numbers == 'yes-'#mmm
                            has_suffix = 'no'
                        while    hit_the_end_of_suffix_numbers == 'no' and x > 0:
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
                        if this_prefix not in prefix_suffix:
                            prefix_suffix[this_prefix] = 0
                        if prefix_suffix[this_prefix]< this_suffix :
                            prefix_suffix[this_prefix] = this_suffix

        arcpy.AddMessage(f"\nExisting prefixes and highest values found in '{selected_field}':")
        for x , y  in prefix_suffix.items():
            arcpy.AddMessage(f"  {x}  ->  highest value: {y}  (next would be: {x}{y + 1})")

        #######################################################################################################
        # Step 3: Validate the entered prefix and determine the next sequential number
        #######################################################################################################
        arcpy.SetProgressorLabel("Step 3 of 4: Validating prefix and determining next value...")
        arcpy.SetProgressorPosition()

        prefix_error_message = ""
        if is_new_prefix == True:
            current_highest_sequence_number = 0
            if prefix in prefix_suffix:
                  prefix_error_message =  "the prefix already exists"

        if is_new_prefix == False:
            if prefix not in prefix_suffix:
                  prefix_error_message =  "the prefix does not already exist"
            if prefix in prefix_suffix:
                arcpy.AddMessage(f"Prefix '{prefix}' found. Highest existing value: {prefix}{prefix_suffix[prefix]}")
                current_highest_sequence_number = prefix_suffix[prefix]

        if prefix_error_message != "":
            arcpy.AddError(prefix_error_message)
            return

        # end of finding all the prefix and suffix values

        #######################################################################################################
        # Step 4: Update the blank fields with the new prefix and incremented suffix values
        #######################################################################################################

        new_numbers_start_at = current_highest_sequence_number + 1
        arcpy.AddWarning(f"Next sequential value for prefix '{prefix}': {prefix}{new_numbers_start_at}")

        if just_display_dont_update is True:
            arcpy.SetProgressorLabel("Step 4 of 4: Display only - no edits will be made.")
            arcpy.SetProgressorPosition()
            arcpy.AddWarning("'Just display' is checked - the data was NOT updated.")
            return

        arcpy.SetProgressorLabel(f"Step 4 of 4: Updating blank '{selected_field}' records, starting at {prefix}{new_numbers_start_at}...")
        arcpy.SetProgressorPosition()
        arcpy.AddMessage(f"\nUpdating blank records in '{selected_field}', starting at {prefix}{new_numbers_start_at}:")

        if prefix_error_message == ""  and just_display_dont_update is False :
            update_count = 0
            with arcpy.da.UpdateCursor(selected_featureclass, [selected_field]) as cursor:
                for row in cursor:
                    origional_value = row[0]
                    modified_value = (origional_value or "").strip()
                    if modified_value == "" :
                        modified_value = prefix + str(new_numbers_start_at)
                        new_numbers_start_at = new_numbers_start_at + 1
                        row[0] = modified_value
                        cursor.updateRow(row)
                        arcpy.AddMessage(f"    Updated -> {modified_value}")
                        update_count += 1

            arcpy.AddMessage(f"\nDone. {update_count} record(s) updated.")

    #######################################################################################################
    #######################################################################################################
    # NUMERIC FIELD SECTION
    # Only relevant for numeric fields. Just increment to the highest number found.
    #######################################################################################################
    #######################################################################################################

    if selected_field_type not in ('TEXT', 'String'):

        #######################################################################################################
        # Step 2: Scan all records to find the current highest value
        #######################################################################################################
        arcpy.SetProgressorLabel("Step 2 of 4: Scanning all records to find the highest existing value...")
        arcpy.SetProgressorPosition()

        selected_field_values = []

        #create a cursor and read all records for selected field into a list
        number_suffix_list= []
        highest_number = 0
        with arcpy.da.SearchCursor(selected_featureclass, [selected_field]) as cursor:
            for row in cursor:
                field_value = row[0]
                selected_field_values.append(row[0])

                # ORIGINAL: if selected_field_values block was at this indent level (inside with, outside for)
                # CHANGE: Moved inside the for loop so every record is evaluated for the highest value.
                # RISK: Leaving outside causes only the last record to determine highest_number, which
                #       can result in duplicate sequential numbers being assigned.
                # DOWNSTREAM: highest_number feeds new_numbers_start_at for the UpdateCursor below.
                if selected_field_values:
                    if field_value is not None:
                        pig = int(field_value)
                        if pig > highest_number:
                            highest_number = pig

        arcpy.AddMessage(f"Highest existing value in '{selected_field}': {highest_number}")

        #######################################################################################################
        # Step 3: Report the next value that will be assigned
        #######################################################################################################
        arcpy.SetProgressorLabel("Step 3 of 4: Determining next sequential value...")
        arcpy.SetProgressorPosition()

        arcpy.AddWarning(f"Next sequential value for '{selected_field}': {highest_number + 1}")

        ############################################################################################
        # Step 4: Loop through again and replace the zeros / nulls
        ############################################################################################
        if just_display_dont_update is True:
            arcpy.SetProgressorLabel("Step 4 of 4: Display only - no edits will be made.")
            arcpy.SetProgressorPosition()
            arcpy.AddWarning("'Just display' is checked - the data was NOT updated.")
            return

        arcpy.SetProgressorLabel(f"Step 4 of 4: Updating zero/null '{selected_field}' records, starting at {highest_number + 1}...")
        arcpy.SetProgressorPosition()
        arcpy.AddMessage(f"\nUpdating zero/null records in '{selected_field}', starting at {highest_number + 1}:")

        if  just_display_dont_update is False :
            update_count = 0
            with arcpy.da.UpdateCursor(selected_featureclass, [selected_field]) as cursor:
                for row in cursor:
                    origional_value = row[0]
                    if origional_value == 0 or origional_value is None:
                        highest_number  = highest_number + 1
                        row[0] = highest_number
                        arcpy.AddMessage(f"    {selected_field} = {highest_number}")
                        cursor.updateRow(row)
                        update_count += 1

            arcpy.AddMessage(f"\nDone. {update_count} record(s) updated.")