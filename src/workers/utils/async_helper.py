"""
Async Helper Utilities for Celery Tasks

This module provides utilities to safely run async code in Celery tasks
on macOS where asyncio.run() causes SIGSEGV in forked workers.

The solution creates a new event loop for each task execution, which is
safe in forked processes.
"""

import asyncio
import logging
from typing import Coroutine, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def run_async_task(coro: Coroutine[Any, Any, T]) -> T:
    """
    Safely run an async coroutine in a Celery task.

    This function creates a new event loop for each execution, which is
    safe in forked worker processes on macOS. It avoids the SIGSEGV issue
    caused by asyncio.run() in forked processes.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Example:
        @celery_app.task
        def my_task():
            async def do_work():
                return await some_async_function()

            result = run_async_task(do_work())
            return result
    """
    # Create a new event loop for this task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run the coroutine
        result = loop.run_until_complete(coro)
        return result
    finally:
        # Clean up the loop
        try:
            # Cancel any remaining tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Run the loop one more time to process cancellations
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception as e:
            logger.warning(f"Error cleaning up event loop: {e}")
        finally:
            loop.close()


def celery_async_task(func):
    """
    Decorator to automatically wrap async functions for Celery tasks.

    This decorator allows you to write Celery tasks as async functions
    while ensuring they work properly in forked worker processes.

    Example:
        @celery_app.task
        @celery_async_task
        async def my_async_task():
            result = await some_async_function()
            return result
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return run_async_task(coro)

    return wrapper
