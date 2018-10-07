"""
General utilities for logging metadata
"""

from functools import wraps
from datetime import datetime

from packet import context_processors, app


def log_time(func):
    """
    Decorator for logging the execution time of a function
    """
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        start = datetime.now()

        result = func(*args, **kwargs)

        seconds = (datetime.now() - start).total_seconds()
        app.logger.info("{}.{}() returned after {} seconds".format(func.__module__, func.__name__, seconds))

        return result

    return wrapped_function


def log_cache(func):
    """
    Decorator for logging cache info
    """
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        result = func(*args, **kwargs)

        app.logger.info("get_csh_name(): {}, get_rit_name(): {}".format(context_processors.get_csh_name.cache_info(),
                                                                        context_processors.get_rit_name.cache_info()))

        return result

    return wrapped_function
