"""
Dealing with timestamps for the phenoscoring project.
"""

from datetime import datetime

timestamp_format = '%Y-%m-%d %H:%M'


def now_timestamp(format=timestamp_format):
    """get a timestamp string, less resolution than standard str()."""
    
    return datetime.now().strftime(format)
