# isort: skip_file
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module sets up various parts of the Engine - we do somethings in a specific order
to ensure they load correctly.

- If a .env file is present and 'dotEnv' is installed, we load the .env file
- If OPTERYX_DEBUG is set, we put the engine in DEBUG mode which means additional
  logging and validation
- Initialize the CacheManager
- Define functions for user access

"""

import os
import datetime
from pathlib import Path

# python-dotenv allows us to create an environment file to store secrets. If
# there is no .env it will fail gracefully.
try:
    import dotenv  # type:ignore
except ImportError:  # pragma: no cover
    dotenv = None  # type:ignore

_env_path = Path(".") / ".env"

#  deepcode ignore PythonSameEvalBinaryExpressiontrue: false +ve, values can be different
if _env_path.exists() and (dotenv is None):  # pragma: no cover  # nosemgrep
    # using a logger here will tie us in knots
    print(f"{datetime.datetime.now()} [LOADER] `.env` file exists but `dotEnv` not installed.")
elif dotenv is not None:  # pragma: no cover variables from `.env`")
    dotenv.load_dotenv(dotenv_path=_env_path)
    print(f"{datetime.datetime.now()} [LOADER] Loading `.env` file.")

if os.environ.get("OPTERYX_DEBUG") is not None:
    from opteryx.debugging import OpteryxOrsoImportFinder

from orso.logging import get_logger
from orso.logging import set_log_name

from opteryx import config
from opteryx.managers.cache.cache_manager import CacheManager  # isort:skip

cache_manager = CacheManager(cache_backend=None)

from opteryx.connection import Connection
from opteryx.connectors import register_arrow
from opteryx.connectors import register_df
from opteryx.connectors import register_store


__all__ = [
    "apilevel",
    "threadsafety",
    "paramstyle",
    "connect",
    "query",
    "Connection",
    "register_arrow",
    "register_df",
    "register_store",
]

# PEP-249 specifies these attributes for a Python Database API 2.0 compliant interface
# For more details, see: https://www.python.org/dev/peps/pep-0249/
apilevel: str = "1.0"  # Compliance level with DB API 2.0
threadsafety: int = 0  # Thread safety level, 0 means not thread-safe
paramstyle: str = "qmark"  # Parameter placeholder style, qmark means '?' for placeholders


def connect(*args, **kwargs):
    """
    Establish a new database connection and return a Connection object.

    Note: This function is designed to comply with the 'connect' method
    described in PEP0249 for Python Database API Specification v2.0.
    """
    # Check for deprecated 'cache' parameter
    if "cache" in kwargs:
        # Import the warnings module here to minimize dependencies
        import warnings

        # Emit a deprecation warning
        warnings.warn(
            "'cache' is no longer set via a parameter on connect, use opteryx.cache_manager instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    # Create and return a Connection object
    return Connection(*args, **kwargs)


def query(operation, params: list = None, **kwargs):
    """
    Helper function to execute a query and return a cursor.

    This function is designed to be similar to the DuckDB function of the same name.
    It simplifies the process of executing queries by abstracting away the connection
    and cursor creation steps.

    Parameters:
        operation: SQL query string
        params: list of parameters to bind into the SQL query
        kwargs: additional arguments for creating the Connection

    Returns:
        Executed cursor
    """
    # Create a new database connection
    conn = Connection(**kwargs)

    # Create a new cursor object using the connection
    curr = conn.cursor()

    # Execute the SQL query using the cursor
    curr.execute(operation=operation, params=params)

    # Return the executed cursor
    return curr


# Try to increase the priority of the application
if not config.DISABLE_HIGH_PRIORITY and hasattr(os, "nice"):  # pragma: no cover
    nice_value = os.nice(0)
    try:
        os.nice(-20 + nice_value)
        print(f"{datetime.datetime.now()} [LOADER] Process priority set to {os.nice(0)}.")
    except PermissionError:
        display_nice = str(nice_value)
        if nice_value == 0:
            display_nice = "0 (normal)"
        print(
            f"{datetime.datetime.now()} [LOADER] Cannot update process priority. Currently set to {display_nice}."
        )

# Log resource usage
if config.ENABLE_RESOURCE_LOGGING:  # pragma: no cover
    from opteryx.utils.resource_monitor import ResourceMonitor
