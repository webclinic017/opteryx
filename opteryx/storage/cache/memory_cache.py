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
This implements an in-memory cache.

We use an LRU to maintain the size of the cache, this is simple and only
tracks number of items in the cache.

We're using a dictionary and moving items to the top of the dictionary
when it's accessed. This relies on Python dictionaries being ordered.
"""

from .base_buffer_cache import BaseBufferCache


class InMemoryCache(BaseBufferCache):
    def __init__(self, **kwargs):
        """
        Parameters:
            cache_size: int (optional)
                The maximim number of items maintained in the cache.
        """
        self._cache_size = int(kwargs.get("cache_size", 50))
        self._cache = {}

    def get(self, key):
        # pop() will remove the item if it's in the dict, we will return it to the
        # cache which will put it at the end of the list, that means the unused items
        # will slowly creep to the end of the list.
        value = self._cache.pop(key, None)
        if value:
            self._cache[key] = value
        return value

    def set(self, key, value):
        # add the new item to the top of the dict
        self._cache[key] = value

        # if we're  full, we want to remove the oldest item from the cache
        if len(self._cache) == self.size:
            # we want to remove the first item in the dict, we could convert to a list,
            # but then we need to create a list, this is faster and uses less memory
            self._cache.pop(next(iter(self._cache)))
