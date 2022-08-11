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
Grouping Node

This is a SQL Query Execution Plan Node.

This performs aggregations, both of grouped and non-grouped data. 

This is a greedy operator - it consumes all the data before responding.

This algorithm is a balance of performance, it is much slower than a groupby based on
the pyarrow_ops library for datasets with a high number of duplicate values (e.g.
grouping by a boolean column) - on a 10m record set, timings are 10:1 (removing raw
read time - e.g. 30s:21s where 20s is the read time).

But, on high cardinality data (nearly unique columns), the performance is much faster,
on a 10m record set, timings are 1:400 (50s:1220s where 20s is the read time).
"""
from typing import Iterable, List

import numpy as np
import pyarrow.json

from opteryx.engine.attribute_types import TOKEN_TYPES
from opteryx.engine import QueryDirectives, QueryStatistics
from opteryx.engine.planner.expression import NodeType, get_all_identifiers
from opteryx.engine.planner.operations import BasePlanNode
from opteryx.exceptions import SqlError
from opteryx.utils.columns import Columns

COUNT_STAR: str = "COUNT(*)"

# use the aggregators from pyarrow
AGGREGATORS = {
    "ALL": "hash_all",
    "ANY": "hash_any",
    "APPROXIMATE_MEDIAN": "hash_approximate_median",
    "COUNT": "hash_count",  # counts only non nulls
    "COUNT_DISTINCT": "hash_count_distinct",
    "CUMULATIVE_SUM": "cumulative_sum",
    "DISTINCT": "hash_distinct",
    "LIST": "hash_list",
    "MAX": "hash_max",
    "MAXIMUM": "hash_max",  # alias
    "MEAN": "hash_mean",
    "AVG": "hash_mean",  # alias
    "AVERAGE": "hash_mean",  # alias
    "MIN": "hash_min",
    "MINIMUM": "hash_min",  # alias
    "MIN_MAX": "hash_min_max",
    "ONE": "hash_one",
    "PRODUCT": "hash_product",
    "STDDEV": "hash_stddev",
    "SUM": "sum",
    "QUANTILES": "hash_tdigest",
    "VARIANCE": "hash_variance",
}


class AggregateNode(BasePlanNode):
    def __init__(
        self, directives: QueryDirectives, statistics: QueryStatistics, **config
    ):
        super().__init__(directives=directives, statistics=statistics)

        self._aggregates = config.get("aggregates", [])
        self._groups = config.get("groups", [])

    @property
    def config(self):  # pragma: no cover
        return str(self._aggregates)

    def greedy(self):  # pragma: no cover
        return True

    @property
    def name(self):  # pragma: no cover
        return "Aggregation"

    def _is_count_star(self, aggregates, groups):
        """
        Is the SELECT clause `SELECT COUNT(*)` with no GROUP BY
        """
        if len(groups) != 0:
            return False
        if len(aggregates) != 1:
            return False
        if aggregates[0].value != "COUNT":
            return False
        if aggregates[0].parameters[0].token_type != NodeType.WILDCARD:
            return False
        return True

    def _count_star(self, data_pages):
        count = 0
        for page in data_pages.execute():
            count += page.num_rows
        table = pyarrow.Table.from_pylist([{COUNT_STAR: count}])
        table = Columns.create_table_metadata(
            table=table,
            expected_rows=1,
            name="groupby",
            table_aliases=[],
        )
        yield table

    def _project(self, tables, fields):
        fields = set(fields)
        for table in tables:
            columns = Columns(table)
            column_names = [
                columns.get_column_from_alias(field, only_one=True) for field in fields
            ]
            yield table.select(set(column_names))
            

    def execute(self) -> Iterable:

        if len(self._producers) != 1:
            raise SqlError(f"{self.name} on expects a single producer")

        data_pages = self._producers[0]  # type:ignore
        if isinstance(data_pages, pyarrow.Table):
            data_pages = (data_pages,)

        if self._is_count_star(self._aggregates, self._groups):
            yield from self._count_star(data_pages)
            return

        from collections import defaultdict

        collector: dict = defaultdict(dict)

        # get all the columns anywhere in the groups or aggregates
        all_identifiers = get_all_identifiers(self._groups + self._aggregates)
        # join all the pages together, selecting only the columns we found above
        table = pyarrow.concat_tables(
            self._project(data_pages.execute(), all_identifiers), promote=True
        )

        print("GROUPS", self._groups)
        print("AGGREGATES", self._aggregates)
        print("EVERYTHING", all_identifiers)

        # get the column metadata
        columns = Columns(table)

        # to allow grouping by functions not in the SELECT clause, we should execute
        # any functions in self._groups and add the column here
        groups = table.group_by(columns.get_column_from_alias(group.value, only_one=True) for group in self._groups)

        # TODO: deal with WILDCARD
        # TODO: build a map for the result columns to the alias and preferred names (e.g. MAX(name))
        aggs = [
            (agg.parameters[0].value, AGGREGATORS.get(agg.value))
            for agg in self._aggregates
            if agg.token_type == NodeType.AGGREGATOR
        ]
        print(aggs)

        groups = groups.aggregate(aggs)
        print(groups.column_names)
        groups = Columns.create_table_metadata(
            table=groups,
            expected_rows=len(collector),
            name=columns.table_name,
            table_aliases=[],
        )
        columns = Columns(groups)
        # TODO: rename the columns before doing the metadata step
        columns.set_preferred_name(
            columns.get_column_from_alias("name_max", only_one=True), "MAX(name)"
        )
        groups = columns.apply(groups)
        yield groups
