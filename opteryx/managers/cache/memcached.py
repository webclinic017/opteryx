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
This implements an interface to Memcached

If we have 10 failures in a row, stop trying to use the cache.
"""

import os
from typing import Union

from orso.tools import single_item_cache

from opteryx.exceptions import MissingDependencyError
from opteryx.managers.kvstores import BaseKeyValueStore

MAXIMUM_CONSECUTIVE_FAILURES: int = 10


@single_item_cache
def _memcached_server(**kwargs):
    """
    Handling connecting to Memcached
    """
    # the server must be set in the environment
    memcached_config = kwargs.get("server", os.environ.get("MEMCACHED_SERVER"))
    if memcached_config is None:
        return None

    # expect either SERVER or SERVER:PORT entries
    memcached_config = memcached_config.split(":")
    if len(memcached_config) == 1:
        # the default memcached port
        memcached_config.append(11211)

    # we need the server and the port
    if len(memcached_config) != 2:
        return None

    try:
        from pymemcache.client import base
    except ImportError as err:
        raise MissingDependencyError(err.name) from err

    # wait 1 second to try to connect, it's not worthwhile as a cache if it's slow
    return base.Client(
        (
            memcached_config[0],
            memcached_config[1],
        ),
        connect_timeout=1,
        timeout=1,
    )


class MemcachedCache(BaseKeyValueStore):
    """
    Cache object
    """

    def __init__(self, **kwargs):
        """
        Parameters:
            server: string (optional)
                Sets the memcached server and port (server:port). If not provided
                the value will be obtained from the OS environment.
        """
        self._server = _memcached_server(**kwargs)
        self._consecutive_failures: int = 0

    def get(self, key: str) -> Union[bytes, None]:
        if self._consecutive_failures >= MAXIMUM_CONSECUTIVE_FAILURES:
            return None
        try:
            response = self._server.get(key)
            self._consecutive_failures = 0
            if response:
                return bytes(response)
        except Exception as err:
            self._consecutive_failures += 1
            if self._consecutive_failures >= MAXIMUM_CONSECUTIVE_FAILURES:
                import datetime

                print(
                    f"{datetime.datetime.now()} [CACHE] Disabling remote Memcached cache due to persistent errors ({err})."
                )

    def set(self, key: str, value: bytes) -> None:
        if self._consecutive_failures < MAXIMUM_CONSECUTIVE_FAILURES:
            self._server.set(key, value)
