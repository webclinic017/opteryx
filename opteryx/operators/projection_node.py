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
Projection Node

This is a SQL Query Execution Plan Node.

This Node eliminates columns that are not needed in a Relation. This is also the Node
that performs column renames.
"""
import time
from typing import Iterable

from opteryx.exceptions import SqlError
from opteryx.managers.expression import evaluate_and_append
from opteryx.models import QueryProperties
from opteryx.operators import BasePlanNode


class ProjectionNode(BasePlanNode):
    def __init__(self, properties: QueryProperties, **config):
        """
        Attribute Projection, remove unwanted columns and performs column renames.
        """
        super().__init__(properties=properties)
        self.projection = config["projection"]

    @property
    def config(self):  # pragma: no cover
        return str(self._projection)

    @property
    def name(self):  # pragma: no cover
        return "Projection"

    def execute(self) -> Iterable:
        if len(self._producers) != 1:  # pragma: no cover
            raise SqlError(f"{self.name} expects a single producer")

        morsels = self._producers[0]  # type:ignore

        projection = []
        for column in self.projection:
            projection.append(str(column.source_column))

        for morsel in morsels.execute():
            # If any of the columns are FUNCTIONs, we need to evaluate them
            #            start_time = time.time_ns()
            #            morsel = evaluate_and_append(self._expressions, morsel)
            #            self.statistics.time_evaluating += time.time_ns() - start_time

            morsel = morsel.select(projection)

            yield morsel
