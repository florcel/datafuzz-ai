"""Application constants and configuration values.

Centralizes magic numbers and strings for easier maintenance.
"""

# Request/Response configuration
DEFAULT_TIMEOUT = 5.0
DEFAULT_RETRIES = 2
DEFAULT_CONCURRENCY = 5

# Payload generation
LONG_STRING_LENGTH = 5000
UNICODE_TEST_STRING = "🤖漢字\u200b"  # Emoji + CJK + zero-width space

# Performance thresholds
DEFAULT_SLOW_THRESHOLD_MS = 900
FAST_THRESHOLD_MS = 100
ACCEPTABLE_THRESHOLD_MS = 500

# Database
DEFAULT_DATABASE_URL = "sqlite:///datafuzz.db"

# File paths
DEFAULT_REPORTS_DIR = "reports/samples"
DEFAULT_REPORT_FILE = "report.html"
DEFAULT_PAYLOADS_FILE = "payloads.json"

# HTTP methods
HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Status code ranges
SUCCESS_STATUS_RANGE = (200, 300)
CLIENT_ERROR_RANGE = (400, 500)
SERVER_ERROR_RANGE = (500, 600)
