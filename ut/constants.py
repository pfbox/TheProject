from django.core.cache import caches

#using memory for now
memory_cache = caches['memory']

# This is using for queries to wrap tables and fields
Default_Identifier = '"'
Current_Identifier = '"'  # {'MySQL','`','PostgreSQL':'"','SQLite':'"','MS SQL':'"'}

# Constants
Default_Attribute = -1
Default_Class = -1
Default_Filter = -1
Default_Project = -1

# Input Types
IT_Default = -1
IT_Select2 = 1
IT_TextBox = 2
IT_RadioButton=3
IT_InlineRadioButton=4

# Datatype Constants
DT_Integer = 1
DT_Float = 2
DT_String = 3
DT_Text = 4
DT_Date = 5
DT_Instance = 6
DT_Datetime = 7
DT_External = 8
DT_Boolean = 9
DT_Table = 10
DT_Currency = 11
DT_Email = 12
DT_Time = 13
DT_Calculated = 14
DT_Lookup = 15
DT_ManyToMany = 16
DT_Hyperlink = 17
DT_File = 18
DT_Image = 19
DT_ActionItem = 20

DT_NUMBERS = [DT_Integer, DT_Float, DT_Date, DT_Instance, DT_Datetime, DT_Boolean, DT_Currency]
DT_LETTERS = [DT_String, DT_Text, DT_External, DT_Email, DT_Lookup, DT_Calculated, DT_Time, DT_Hyperlink]

DTG_Int = [DT_Integer, DT_Boolean]  # 1
DTG_Float = [DT_Float, DT_Currency]  # 2
DTG_String = [DT_String, DT_Email, DT_Lookup, DT_Time, DT_Hyperlink]  # 3
DTG_Text = [DT_Text]  # 4
DTG_Instance = [DT_Instance]  # 5
DTG_Date = [DT_Date, DT_Datetime]  # 5
DTG_ManyToMany = [DT_ManyToMany]  # 6

FT_Exact = 1
FT_MinMax = 2
FT_Contains = 3
FT_Like = 4
