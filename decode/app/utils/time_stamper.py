from datetime import datetime


def get_current_time_stamp_formated():
    """return YYYY/MM/DD, HH:MM:SS"""
    return datetime.now().strftime("%Y/%m/%d, %H:%M:%S")
