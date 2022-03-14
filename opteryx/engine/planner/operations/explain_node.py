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
Explain Node

This is a SQL Query Execution Plan Node.

This writes out a query plan
"""
from typing import Iterable
from pyarrow import concat_tables
from opteryx.engine.query_statistics import QueryStatistics
from opteryx.engine.planner.operations.base_plan_node import BasePlanNode


class SortNode(BasePlanNode):
    def __init__(self, statistics: QueryStatistics, **config):
        self._order = config.get("order")

    def greedy(self):
        return True

    @property
    def name(self):
        return "Explain"

    def execute(self, data_pages: Iterable) -> Iterable:

        pass
