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
"""

import io
from functools import lru_cache


@lru_cache(1)
def _memcached_server(**kwargs):
    import os

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
    except ImportError:
        return None

    # wait 1 second to try to connect, it's not worthwhile as a cache if it's slow
    return base.Client(
        (
            memcached_config[0],
            memcached_config[1],
        ),
        connect_timeout=1,
        timeout=1,
    )


from opteryx.storage import BaseBufferCache


class MemcachedCache(BaseBufferCache):
    def __init__(self, **kwargs):
        self._server = _memcached_server(**kwargs)

    def get(self, key):
        if self._server:
            response = self._server.get(key)
            if response:
                return io.BytesIO(response)

    def set(self, key, value):
        if self._server:
            self._server.set(key, value.read())
            value.seek(0)
