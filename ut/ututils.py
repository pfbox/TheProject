from django.utils.html import escape
from pandas import isnull

def get_json_safe_value(x):
    if type(x)==str:
        res=escape(x)
    elif isnull(x):
        res=None
    else:
        res=str(x)
    return res