# utils.py
"""
Utility functions for HelpIT application.

This module contains common helper functions used across the application.
"""

import sys


def is_compiled() -> bool:
    """
    Detect if the application is compiled with PyInstaller.

    Returns:
        True if running as a compiled executable, False otherwise.
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def debug_print(*args, **kwargs) -> None:
    """
    Print debug messages only when running in development mode.

    Messages are suppressed when the application is compiled with PyInstaller.

    Args:
        *args: Positional arguments passed to print().
        **kwargs: Keyword arguments passed to print().
    """
    if not is_compiled():
        print(*args, **kwargs)