"""
General utilities for logging metadata
"""

from functools import wraps
from datetime import datetime
from typing import Any, Callable, TypeVar, cast

from packet import app, ldap
from packet.context_processors import get_rit_name
from packet.utils import is_freshman_on_floor

WrappedFunc = TypeVar("WrappedFunc", bound=Callable)


def log_time(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator for logging the execution time of a function

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.
    """

    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        """
        Wrap the function to log its execution time.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            Any: The result of the wrapped function.
        """

        start: datetime = datetime.now()

        result = func(*args, **kwargs)

        seconds: float = (datetime.now() - start).total_seconds()
        app.logger.info(
            "{}.{}() returned after {} seconds".format(
                func.__module__, func.__name__, seconds
            )
        )

        return result

    return cast(WrappedFunc, wrapped_function)


def _format_cache(func: Any) -> str:
    """
    Format the cache info of a function

    Args:
        func (Any): The function to get cache info from.

    Returns:
        str: A formatted string with cache hits, misses, and size.
    """

    info = func.cache_info()

    return "{}[hits={}, misses={}, size={}/{}]".format(
        func.__name__, info.hits, info.misses, info.currsize, info.maxsize
    )


# Tuple of lru_cache functions to log stats from
_caches = (get_rit_name, ldap.get_member, is_freshman_on_floor)


def log_cache(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator for logging cache info

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.
    """

    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        """
        Wrap the function to log its cache info.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            Any: The result of the wrapped function.
        """

        result = func(*args, **kwargs)

        app.logger.info("Cache stats: " + ", ".join(map(_format_cache, _caches)))

        return result

    return cast(WrappedFunc, wrapped_function)
