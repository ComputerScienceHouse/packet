"""
General utilities for logging metadata
"""

from functools import wraps
from datetime import datetime

from packet import app, ldap
from packet.context_processors import get_rit_name
from packet.utils import is_freshman_on_floor


def log_time(func):
    """
    Decorator for logging the execution time of a function
    """
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        start = datetime.now()

        result = func(*args, **kwargs)

        seconds = (datetime.now() - start).total_seconds()
        app.logger.info('{}.{}() returned after {} seconds'.format(func.__module__, func.__name__, seconds))

        return result

    return wrapped_function


def _format_cache(func):
    """
    :return: The output of func.cache_info() as a compactly formatted string
    """
    info = func.cache_info()
    return '{}[hits={}, misses={}, size={}/{}]'.format(func.__name__, info.hits, info.misses, info.currsize,
                                                       info.maxsize)


# Tuple of lru_cache functions to log stats from
_caches = (get_rit_name, ldap.get_member, is_freshman_on_floor)


def log_cache(func):
    """
    Decorator for logging cache info
    """

    @wraps(func)
    def wrapped_function(*args, **kwargs):
        result = func(*args, **kwargs)

        app.logger.info('Cache stats: ' + ', '.join(map(_format_cache, _caches)))

        return result

    return wrapped_function
