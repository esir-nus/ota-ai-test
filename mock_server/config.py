"""
Configuration for mock update server
"""

# Server port
UPDATE_SERVER_PORT = 5000

# Package settings
DEFAULT_PACKAGE_SIZE = 1024 * 1024  # 1MB
PACKAGE_DIRECTORY = "packages"

# Authentication settings
AUTH_ENABLED = True
AUTH_TOKEN_EXPIRY = 3600  # 1 hour in seconds
DEFAULT_AUTH_TOKEN = "mock_auth_token_123"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
UPDATE_SERVER_LOG = "mock_server.log"

# Server endpoint
UPDATE_SERVER_BASE_URL = f"http://localhost:{UPDATE_SERVER_PORT}" 