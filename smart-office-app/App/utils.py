# utils.py
import datetime

def parse_time(timestr):
    """
    Parses a time string into a datetime object.
    Supports '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', and '%Y-%m-%d %H:%M:%S.%f' formats.
    """
    if timestr is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"): # Added .%f for isoformat
        try:
            return datetime.datetime.strptime(timestr, fmt)
        except ValueError:
            continue
    return None

def datetime_to_string(dt_obj):
    """
    Converts a datetime or date object to a string format suitable for JSON storage (ISO format for datetime, YYYY-MM-DD for date).
    """
    if dt_obj is None:
        return None
    if isinstance(dt_obj, datetime.datetime):
        return dt_obj.isoformat()
    if isinstance(dt_obj, datetime.date):
        return dt_obj.strftime('%Y-%m-%d')
    return str(dt_obj) # Fallback for other types