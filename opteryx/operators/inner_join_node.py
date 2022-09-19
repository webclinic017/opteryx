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
Inner Join Node

This is a SQL Query Execution Plan Node.

This performs a INNER JOIN
"""
import time
from typing import Iterable

import numpy
import pyarrow

from opteryx import config
from opteryx.operators import BasePlanNode
from opteryx.models import Columns, QueryProperties, QueryStatistics
from opteryx.exceptions import SqlError
from opteryx.third_party import pyarrow_ops
from opteryx.utils import arrow

INTERNAL_BATCH_SIZE = 500


def calculate_batch_size(cardinality):
    """dynamically work out the processing batch size for the USING JOIN"""
    # - HIGH_CARDINALITY_BATCH_SIZE (over 90% unique) = INTERNAL_BATCH_SIZE
    # - MEDIUM_CARDINALITY_BATCH_SIZE (5% > n < 90%) = INTERNAL_BATCH_SIZE * n
    # - LOW_CARDINALITY_BATCH_SIZE (less than 5% unique) = 5
    # These numbers have had very little science put into them, they are unlikely
    # to be optimal
    if cardinality < 0.05:
        return 5
    if cardinality > 0.9:
        return INTERNAL_BATCH_SIZE
    return INTERNAL_BATCH_SIZE * cardinality


class InnerJoinNode(BasePlanNode):
    def __init__(
        self, properties: QueryProperties, statistics: QueryStatistics, **config
    ):
        super().__init__(properties=properties, statistics=statistics)
        self._right_table = config.get("right_table")
        self._join_type = config.get("join_type", "CrossJoin")
        self._on = config.get("join_on")
        self._using = config.get("join_using")

    @property
    def name(self):  # pragma: no cover
        return "Inner Join"

    @property
    def config(self):  # pragma: no cover
        return ""

    def execute(self) -> Iterable:

        if len(self._producers) != 2:
            raise SqlError(f"{self.name} expects two producers")

        left_node = self._producers[0]  # type:ignore
        right_node = self._producers[1]  # type:ignore

        self._right_table = pyarrow.concat_tables(
            right_node.execute(), promote=True
        )  # type:ignore

        if self._using:

            right_columns = Columns(self._right_table)
            left_columns = None
            right_join_columns = [
                right_columns.get_column_from_alias(col, only_one=True)
                for col in self._using
            ]

            for page in arrow.consolidate_pages(left_node.execute(), self._statistics):

                if left_columns is None:
                    left_columns = Columns(page)
                    left_join_columns = [
                        left_columns.get_column_from_alias(col, only_one=True)
                        for col in self._using
                    ]
                    new_metadata = left_columns + right_columns

                    # we estimate the cardinality of the left table to inform the
                    # batch size for the joins. Cardinality here is the ratio of
                    # unique values in the set. Although we're working it out, we'll
                    # refer to this as an estimate because it may be different per
                    # page of data - we're assuming it's not very different.
                    cols = pyarrow_ops.columns_to_array_denulled(
                        page, left_join_columns
                    )
                    if page.num_rows > 0:
                        card = len(numpy.unique(cols)) / page.num_rows
                    else:
                        card = 0
                    batch_size = calculate_batch_size(card)

                # we break this into small chunks otherwise we very quickly run into memory issues
                for batch in page.to_batches(max_chunksize=batch_size):

                    # blocks don't have column_names, so we need to wrap in a table
                    batch = pyarrow.Table.from_batches([batch], schema=page.schema)

                    new_page = pyarrow_ops.inner_join(
                        self._right_table, batch, right_join_columns, left_join_columns
                    )
                    new_page = new_metadata.apply(new_page)
                    yield new_page

        elif self._on:

            right_columns = Columns(self._right_table)

            right_null_columns, self._right_table = Columns.remove_null_columns(
                self._right_table
            )

            left_columns = None

            for page in arrow.consolidate_pages(left_node.execute(), self._statistics):

                if left_columns is None:
                    left_columns = Columns(page)
                    try:
                        right_join_column = right_columns.get_column_from_alias(
                            self._on.right.value, only_one=True
                        )
                        left_join_column = left_columns.get_column_from_alias(
                            self._on.left.value, only_one=True
                        )
                    except SqlError:
                        # the ON condition may not always be in the order of the tables
                        # purposefully reference the values the wrong way around
                        right_join_column = right_columns.get_column_from_alias(
                            self._on.left.value, only_one=True
                        )
                        left_join_column = left_columns.get_column_from_alias(
                            self._on.right.value, only_one=True
                        )

                    left_null_columns, page = Columns.remove_null_columns(page)
                    new_metadata = right_columns + left_columns

                    # ensure the types are compatible for joining by coercing numerics
                    self._right_table = arrow.coerce_column(
                        self._right_table, right_join_column
                    )

                page = arrow.coerce_column(page, left_join_column)

                # do the join
                # This uses the cjoin / HASH JOIN / legacy join
                new_page = page.join(
                    self._right_table,
                    keys=[left_join_column],
                    right_keys=[right_join_column],
                    join_type="inner",
                    coalesce_keys=False,
                )

                # update the metadata
                new_page = Columns.restore_null_columns(
                    left_null_columns + right_null_columns, new_page
                )

                new_page = new_metadata.apply(new_page)
                yield new_page
