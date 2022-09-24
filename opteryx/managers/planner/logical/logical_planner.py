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
This builds a logical plan can resolve the query from the user.

This doesn't attempt to do optimization, this just build a convenient plan which will
respond to the query correctly.

The effective order of operations must be:

    01. FROM
    02. JOIN
    03. WHERE
    04. GROUP BY
    05. HAVING
    06. SELECT
    07. DISTINCT
    08. ORDER BY
    09. OFFSET
    10. LIMIT

So we just build it in that order.
"""
import pyarrow

from opteryx import operators
from opteryx.exceptions import SqlError, UnsupportedSyntaxError


from opteryx.managers.planner.logical import builders, queries

from opteryx.models import Columns


def create_plan(ast, properties):

    last_query = None
    for query in ast:
        query_type = next(iter(query))
        builder = queries.QUERY_BUILDER.get(query_type)
        if builder is None:
            raise UnsupportedSyntaxError(f"Statement not supported `{query_type}`")
        last_query = builder(query, properties)
    return last_query


def _explain_planner(ast, statistics):
    explain_plan = copy()
    explain_plan.create_plan(ast=[ast["Explain"]["statement"]])
    explain_node = operators.ExplainNode(properties, query_plan=explain_plan)
    add_operator("explain", explain_node)


def explain(self):
    def _inner_explain(node, depth):
        if depth == 1:
            operator = get_operator(node)
            yield {
                "operator": operator.name,
                "config": operator.config,
                "depth": depth - 1,
            }
        incoming_operators = get_incoming_links(node)
        for operator_name in incoming_operators:
            operator = get_operator(operator_name[0])
            if isinstance(operator, operators.BasePlanNode):
                yield {
                    "operator": operator.name,
                    "config": operator.config,
                    "depth": depth,
                }
            yield from _inner_explain(operator_name[0], depth + 1)

    head = list(set(get_exit_points()))
    # print(head, _edges)
    if len(head) != 1:
        raise SqlError(f"Problem with the plan - it has {len(head)} heads.")
    plan = list(_inner_explain(head[0], 1))

    table = pyarrow.Table.from_pylist(plan)
    table = Columns.create_table_metadata(table, table.num_rows, "plan", None)
    yield table
