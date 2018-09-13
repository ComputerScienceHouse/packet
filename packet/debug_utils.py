"""
General utilities for use when debugging
"""

from functools import wraps
from datetime import datetime

from packet import context_processors


def log_time(func):
    """
    Decorator for logging the execution time of a function
    """
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        start = datetime.now()

        result = func(*args, **kwargs)

        seconds = (datetime.now() - start).total_seconds()
        print("{}.{}() returned after {} seconds".format(func.__module__, func.__name__, seconds))

        return result

    return wrapped_function


def log_cache():
    """
    Utility call for logging cache info
    """
    print("get_csh_name():", context_processors.get_csh_name.cache_info())
    print("get_rit_name():", context_processors.get_rit_name.cache_info())
