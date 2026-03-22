# constants.py
"""
Application-wide constants for HelpIT.

"""

# Window dimensions
MAIN_WINDOW_SIZE = "520x320"
PROCESS_MANAGER_SIZE = "600x500"
SERVICE_MANAGER_SIZE = "750x600"
SCRIPT_MANAGER_SIZE = "450x350"
FILE_EXPLORER_SIZE = "1200x700"
PROGRESS_WINDOW_SIZE = "450x180"

# Network settings
DEFAULT_PING_TIMEOUT = 2  # seconds
DEFAULT_PSEXEC_TIMEOUT = 30  # seconds
DEFAULT_SCRIPT_TIMEOUT = 120  # seconds

# File copy settings
COPY_BUFFER_SIZE = 64 * 1024  # 64 KB

# UI Colors
COLOR_SUCCESS = "#4CAF50"  # Green
COLOR_ERROR = "#F44336"    # Red
COLOR_WARNING = "#FF9800"  # Orange
COLOR_INFO = "#2196F3"     # Blue
COLOR_PAUSED = "#FFC107"   # Amber

# Database settings
DEFAULT_DB_NAME = "config.sqlite"
MAC_RETENTION_DAYS = 30