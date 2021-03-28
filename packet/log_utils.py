"""
General utilities for logging metadata
"""

from functools import wraps
from datetime import datetime
from typing import Any, Callable, TypeVar, cast

from packet import app, ldap
from packet.context_processors import get_rit_name
from packet.utils import is_freshman_on_floor

F = TypeVar('F', bound=Callable)

def log_time(func: F) -> F:
    """
    Decorator for logging the execution time of a function
    """
    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        start = datetime.now()

        result = func(*args, **kwargs)

        seconds = (datetime.now() - start).total_seconds()
        app.logger.info('{}.{}() returned after {} seconds'.format(func.__module__, func.__name__, seconds))

        return result

    return cast(F, wrapped_function)


def _format_cache(func: Any) -> str:
    """
    :return: The output of func.cache_info() as a compactly formatted string
    """
    info = func.cache_info()
    return '{}[hits={}, misses={}, size={}/{}]'.format(func.__name__, info.hits, info.misses, info.currsize,
                                                       info.maxsize)


# Tuple of lru_cache functions to log stats from
_caches = (get_rit_name, ldap.get_member, is_freshman_on_floor)


def log_cache(func: F) -> F:
    """
    Decorator for logging cache info
    """

    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        result = func(*args, **kwargs)

        app.logger.info('Cache stats: ' + ', '.join(map(_format_cache, _caches)))

        return result

    return cast(F, wrapped_function)
