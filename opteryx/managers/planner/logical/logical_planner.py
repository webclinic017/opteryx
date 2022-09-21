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
import datetime

import numpy
import pyarrow

from opteryx import operators, functions
from opteryx.connectors import connector_factory
from opteryx.exceptions import SqlError, UnsupportedSyntaxError
from opteryx.functions.binary_operators import BINARY_OPERATORS
from opteryx.managers.expression import ExpressionTreeNode
from opteryx.managers.expression import get_all_nodes_of_type
from opteryx.managers.expression import NodeType


from opteryx.managers.planner.logical import queries

from opteryx.models import Columns
from opteryx.utils import fuzzy_search


def create_plan(ast, properties):

    last_query = None
    for query in ast:
        query_type = next(iter(query))
        builder = queries.QUERY_BUILDER.get(query_type)
        if builder is None:
            raise UnsupportedSyntaxError(f"Statement not supported `{query_type}`")
        last_query = builder(query, properties)
    return last_query


def _check_hints(self, hints):

    from opteryx.third_party.mbleven import compare

    well_known_hints = (
        "NO_CACHE",
        "NO_PARTITION",
        "NO_PUSH_PROJECTION",
        "PARALLEL_READ",
    )

    for hint in hints:
        if hint not in well_known_hints:
            best_match_hint = None
            best_match_score = 100

            for known_hint in well_known_hints:
                my_dist = compare(hint, known_hint)
                if my_dist > 0 and my_dist < best_match_score:
                    best_match_score = my_dist
                    best_match_hint = known_hint

            if best_match_hint:
                self._statistics.warn(
                    f"Hint `{hint}` is not recognized, did you mean `{best_match_hint}`?"
                )
            else:
                self._statistics.warn(f"Hint `{hint}` is not recognized.")


def _extract_relations(self, ast, default_path: bool = True):
    """ """
    relations = ast
    if default_path:
        try:
            relations = ast["Query"]["body"]["Select"]["from"]
        except IndexError:
            return "$no_table"

    for relation in relations:
        if "Table" in relation["relation"]:
            # is the relation a builder function
            if relation["relation"]["Table"]["args"]:
                function = relation["relation"]["Table"]["name"][0]["value"].lower()
                alias = function
                if relation["relation"]["Table"]["alias"] is not None:
                    alias = relation["relation"]["Table"]["alias"]["name"]["value"]
                args = [
                    self._filter_extract(a["Unnamed"])
                    for a in relation["relation"]["Table"]["args"]
                ]
                yield (alias, {"function": function, "args": args}, "Function", [])
            else:
                alias = None
                if relation["relation"]["Table"]["alias"] is not None:
                    alias = relation["relation"]["Table"]["alias"]["name"]["value"]
                hints = []
                if relation["relation"]["Table"]["with_hints"] is not None:
                    hints = [
                        hint["Identifier"]["value"]
                        for hint in relation["relation"]["Table"]["with_hints"]
                    ]
                    # hint checks
                    self._check_hints(hints)
                dataset = ".".join(
                    [part["value"] for part in relation["relation"]["Table"]["name"]]
                )
                if dataset[0:1] == "$":
                    yield (alias, dataset, "Internal", hints)
                else:
                    yield (alias, dataset, "External", hints)

        if "Derived" in relation["relation"]:
            subquery = relation["relation"]["Derived"]["subquery"]["body"]
            try:
                alias = relation["relation"]["Derived"]["alias"]["name"]["value"]
            except (KeyError, TypeError):
                alias = None
            if "Select" in subquery:
                ast = {}
                ast["Query"] = relation["relation"]["Derived"]["subquery"]
                subquery_plan = self.copy()
                subquery_plan.create_plan(ast=[ast])

                yield (alias, subquery_plan, "SubQuery", [])
            if "Values" in subquery:
                body = []
                headers = [
                    h["value"]
                    for h in relation["relation"]["Derived"]["alias"]["columns"]
                ]
                for value_set in subquery["Values"]:
                    values = [
                        self._build_literal_node(v["Value"]).value for v in value_set
                    ]
                    body.append(dict(zip(headers, values)))
                yield (alias, {"function": "values", "args": body}, "Function", [])


def _extract_joins(self, ast):
    try:
        joins = ast["Query"]["body"]["Select"]["from"][0]["joins"]
    except IndexError:
        return None

    for join in joins:
        join_using = None
        join_on = None
        join_mode = join["join_operator"]
        if isinstance(join_mode, dict):
            join_mode = list(join["join_operator"].keys())[0]
            if "Using" in join["join_operator"][join_mode]:
                join_using = [
                    v["value"]
                    for v in join["join_operator"][join_mode].get("Using", [])
                ]
            if "On" in join["join_operator"][join_mode]:
                join_on = self._filter_extract(join["join_operator"][join_mode]["On"])

        right = next(self._extract_relations([join], default_path=False))
        yield (join_mode, right, join_on, join_using)


def _filter_extract(self, function):
    alias = []

    if function is None:
        return None

    if function == "Wildcard":
        return ExpressionTreeNode(NodeType.WILDCARD)

    # get any alias information for a field (usually means we're in a SELECT clause)
    if "UnnamedExpr" in function:
        return self._filter_extract(function["UnnamedExpr"])
    if "ExprWithAlias" in function:
        alias = [function["ExprWithAlias"]["alias"]["value"]]
        function = function["ExprWithAlias"]["expr"]
    if "QualifiedWildcard" in function:
        return ExpressionTreeNode(
            NodeType.WILDCARD, value=function["QualifiedWildcard"][0]["value"]
        )
    if "Unnamed" in function:
        return self._filter_extract(function["Unnamed"])
    if "Expr" in function:
        return self._filter_extract(function["Expr"])

    if "Identifier" in function:
        token_name = function["Identifier"]["value"]
        if token_name[0] == "@":
            if token_name not in self.properties.variables:  # pragma: no cover
                raise SqlError(f"Undefined variable found in query `{token_name}`.")
            return self.properties.variables.get(token_name)
        else:
            return ExpressionTreeNode(
                token_type=NodeType.IDENTIFIER,
                value=token_name,
                alias=alias,
            )
    if "CompoundIdentifier" in function:
        return ExpressionTreeNode(
            token_type=NodeType.IDENTIFIER,
            value=".".join(p["value"] for p in function["CompoundIdentifier"]),
            alias=".".join(p["value"] for p in function["CompoundIdentifier"]),
        )
    if "Function" in function:
        func = function["Function"]["name"][0]["value"].upper()
        args = [self._filter_extract(a) for a in function["Function"]["args"]]
        if functions.is_function(func):
            node_type = NodeType.FUNCTION
        elif operators.is_aggregator(func):
            node_type = NodeType.AGGREGATOR
        else:
            likely_match = fuzzy_search(
                func, operators.aggregators() + functions.functions()
            )
            if likely_match is None:
                raise SqlError(f"Unknown function or aggregate '{func}'")
            raise SqlError(
                f"Unknown function or aggregate '{func}'. Did you mean '{likely_match}'?"
            )

        return ExpressionTreeNode(
            token_type=node_type, value=func, parameters=args, alias=alias
        )
    if "BinaryOp" in function:
        left = self._filter_extract(function["BinaryOp"]["left"])
        operator = function["BinaryOp"]["op"]
        right = self._filter_extract(function["BinaryOp"]["right"])

        operator_type = NodeType.COMPARISON_OPERATOR
        if operator in BINARY_OPERATORS:
            operator_type = NodeType.BINARY_OPERATOR
        if operator == "And":
            operator_type = NodeType.AND
        if operator == "Or":
            operator_type = NodeType.OR
        if operator == "Xor":
            operator_type = NodeType.XOR

        return ExpressionTreeNode(
            operator_type,
            value=operator,
            left_node=left,
            right_node=right,
            alias=alias,
        )
    if "Cast" in function:
        # CAST(<var> AS <type>) - convert to the form <type>(var), e.g. BOOLEAN(on)
        args = [self._filter_extract(function["Cast"]["expr"])]
        data_type = function["Cast"]["data_type"]
        if data_type == "Timestamp":
            data_type = "TIMESTAMP"
        elif "Varchar" in data_type:
            data_type = "VARCHAR"
        elif "Decimal" in data_type:
            data_type = "NUMERIC"
        elif "Boolean" in data_type:
            data_type = "BOOLEAN"
        else:
            raise SqlError(f"Unsupported type for CAST  - '{data_type}'")

        alias.append(f"CAST({args[0].value} AS {data_type})")

        return ExpressionTreeNode(
            NodeType.FUNCTION,
            value=data_type.upper(),
            parameters=args,
            alias=alias,
        )

    try_caster = list(function.keys())[0]
    if try_caster in ("TryCast", "SafeCast"):
        # CAST(<var> AS <type>) - convert to the form <type>(var), e.g. BOOLEAN(on)
        args = [self._filter_extract(function[try_caster]["expr"])]
        data_type = function[try_caster]["data_type"]
        try_caster = try_caster.replace("Cast", "_Cast").upper()
        if data_type == "Timestamp":
            data_type = "TIMESTAMP"
        elif "Varchar" in data_type:
            data_type = "VARCHAR"
        elif "Decimal" in data_type:
            data_type = "NUMERIC"
        elif "Boolean" in data_type:
            data_type = "BOOLEAN"
        else:
            raise SqlError(f"Unsupported type for {try_caster}  - '{data_type}'")

        alias.append(f"{try_caster}({args[0].value} AS {data_type})")

        return ExpressionTreeNode(
            NodeType.FUNCTION,
            value=f"TRY_{data_type.upper()}",
            parameters=args,
            alias=alias,
        )

    if "Extract" in function:
        # EXTRACT(part FROM timestamp)
        datepart = ExpressionTreeNode(
            NodeType.LITERAL_VARCHAR, value=function["Extract"]["field"]
        )
        value = self._filter_extract(function["Extract"]["expr"])

        alias.append(f"EXTRACT({datepart.value} FROM {value.value})")
        alias.append(f"DATEPART({datepart.value}, {value.value}")

        return ExpressionTreeNode(
            NodeType.FUNCTION,
            value="DATEPART",
            parameters=[datepart, value],
            alias=alias,
        )

    if "MapAccess" in function:
        # Identifier[key] -> GET(Identifier, key) -> alias of I[k] or alias
        identifier = function["MapAccess"]["column"]["Identifier"]["value"]
        key_dict = function["MapAccess"]["keys"][0]["Value"]
        if "SingleQuotedString" in key_dict:
            key = key_dict["SingleQuotedString"]
            key_node = ExpressionTreeNode(NodeType.LITERAL_VARCHAR, value=key)
        if "Number" in key_dict:
            key = key_dict["Number"][0]
            key_node = ExpressionTreeNode(NodeType.LITERAL_NUMERIC, value=key)
        alias.append(f"{identifier}[{key}]")

        identifier_node = ExpressionTreeNode(NodeType.IDENTIFIER, value=identifier)
        return ExpressionTreeNode(
            NodeType.FUNCTION,
            value="GET",
            parameters=[identifier_node, key_node],
            alias=alias,
        )
    if "Value" in function:
        return self._build_literal_node(function["Value"], alias)

    if "UnaryOp" in function:
        if function["UnaryOp"]["op"] == "Not":
            right = self._filter_extract(function["UnaryOp"]["expr"])
            return ExpressionTreeNode(token_type=NodeType.NOT, centre_node=right)
        if function["UnaryOp"]["op"] == "Minus":
            number = 0 - numpy.float64(
                function["UnaryOp"]["expr"]["Value"]["Number"][0]
            )
            return ExpressionTreeNode(
                NodeType.LITERAL_NUMERIC, value=number, alias=alias
            )
    if "Between" in function:
        expr = self._filter_extract(function["Between"]["expr"])
        low = self._filter_extract(function["Between"]["low"])
        high = self._filter_extract(function["Between"]["high"])
        inverted = function["Between"]["negated"]

        if inverted:
            # LEFT <= LOW AND LEFT >= HIGH (not between)
            left_node = ExpressionTreeNode(
                NodeType.COMPARISON_OPERATOR,
                value="Lt",
                left_node=expr,
                right_node=low,
            )
            right_node = ExpressionTreeNode(
                NodeType.COMPARISON_OPERATOR,
                value="Gt",
                left_node=expr,
                right_node=high,
            )

            return ExpressionTreeNode(
                NodeType.OR, left_node=left_node, right_node=right_node
            )
        else:
            # LEFT > LOW and LEFT < HIGH (between)
            left_node = ExpressionTreeNode(
                NodeType.COMPARISON_OPERATOR,
                value="GtEq",
                left_node=expr,
                right_node=low,
            )
            right_node = ExpressionTreeNode(
                NodeType.COMPARISON_OPERATOR,
                value="LtEq",
                left_node=expr,
                right_node=high,
            )

            return ExpressionTreeNode(
                NodeType.AND, left_node=left_node, right_node=right_node
            )

    if "InSubquery" in function:
        # if it's a sub-query we create a plan for it
        left = self._filter_extract(function["InSubquery"]["expr"])
        ast = {}
        ast["Query"] = function["InSubquery"]["subquery"]
        subquery_plan = self.copy()
        subquery_plan.create_plan(ast=[ast])
        operator = "NotInList" if function["InSubquery"]["negated"] else "InList"

        sub_query = ExpressionTreeNode(NodeType.SUBQUERY, value=subquery_plan)
        return ExpressionTreeNode(
            NodeType.COMPARISON_OPERATOR,
            value=operator,
            left_node=left,
            right_node=sub_query,
        )
    try_filter = list(function.keys())[0]
    if try_filter in ("IsTrue", "IsFalse", "IsNull", "IsNotNull"):
        centre = self._filter_extract(function[try_filter])
        return ExpressionTreeNode(
            NodeType.UNARY_OPERATOR, value=try_filter, centre_node=centre
        )
    if try_filter in ("Like", "SimilarTo", "ILike"):
        negated = function[try_filter]["negated"]
        left = self._filter_extract(function[try_filter]["expr"])
        right = self._filter_extract(function[try_filter]["pattern"])
        if negated:
            try_filter = f"Not{try_filter}"
        return ExpressionTreeNode(
            NodeType.COMPARISON_OPERATOR,
            value=try_filter,
            left_node=left,
            right_node=right,
        )
    if "InList" in function:
        left_node = self._filter_extract(function["InList"]["expr"])
        list_values = {
            self._filter_extract(v).value for v in function["InList"]["list"]
        }
        operator = "NotInList" if function["InList"]["negated"] else "InList"
        right_node = ExpressionTreeNode(
            token_type=NodeType.LITERAL_LIST, value=list_values
        )
        return ExpressionTreeNode(
            token_type=NodeType.COMPARISON_OPERATOR,
            value=operator,
            left_node=left_node,
            right_node=right_node,
        )
    if "InUnnest" in function:
        left_node = self._filter_extract(function["InUnnest"]["expr"])
        operator = "NotContains" if function["InUnnest"]["negated"] else "Contains"
        right_node = self._filter_extract(function["InUnnest"]["array_expr"])
        return ExpressionTreeNode(
            token_type=NodeType.COMPARISON_OPERATOR,
            value=operator,
            left_node=left_node,
            right_node=right_node,
        )

    if "Nested" in function:
        return ExpressionTreeNode(
            token_type=NodeType.NESTED,
            centre_node=self._filter_extract(function["Nested"]),
        )

    if "Tuple" in function:
        return ExpressionTreeNode(
            NodeType.LITERAL_LIST,
            value=[
                self._build_literal_node(t["Value"]).value for t in function["Tuple"]
            ],
            alias=alias,
        )

    raise SqlError(
        f"Unknown or unsupported clauses in statement `{list(function.keys())}`"
    )


def _extract_field_list(self, projection):
    """
    Projections are lists of attributes, the most obvious one is in the SELECT
    statement but they can exist elsewhere to limit the amount of data
    processed at each step.
    """
    if projection == ["Wildcard"]:
        return [ExpressionTreeNode(token_type=NodeType.WILDCARD)]

    projection = [self._filter_extract(attribute) for attribute in projection]
    return projection


def _extract_selection(self, ast):
    """
    Although there is a SELECT statement in a SQL Query, Selection refers to the
    filter or WHERE statement.
    """
    selections = ast["Query"]["body"]["Select"]["selection"]
    return self._filter_extract(selections)


def _extract_filter(self, ast):
    """filters are used in SHOW queries"""
    filters = ast["filter"]
    if filters is None:
        return None
    if "Where" in filters:
        return self._filter_extract(filters["Where"])
    if "Like" in filters:
        left = ExpressionTreeNode(NodeType.IDENTIFIER, value="name")
        right = ExpressionTreeNode(NodeType.LITERAL_VARCHAR, value=filters["Like"])
        root = ExpressionTreeNode(
            NodeType.COMPARISON_OPERATOR,
            value="Like",
            left_node=left,
            right_node=right,
        )
        return root


def _extract_distinct(self, ast):
    return ast["Query"]["body"]["Select"]["distinct"]


def _extract_limit(self, ast):
    limit = ast["Query"].get("limit")
    if limit is not None:
        return int(limit["Value"]["Number"][0])
    return None


def _extract_offset(self, ast):
    offset = ast["Query"].get("offset")
    if offset is not None:
        return int(offset["value"]["Value"]["Number"][0])
    return None


def _extract_order(self, ast):
    order = ast["Query"].get("order_by")
    if order is not None:
        orders = []
        for col in order:
            column = self._extract_field_list([col["expr"]])
            orders.append(
                (
                    column,
                    "descending" if str(col["asc"]) == "False" else "ascending",
                ),
            )
        return orders


def _extract_having(self, ast):
    having = ast["Query"]["body"]["Select"]["having"]
    return self._filter_extract(having)


def _explain_planner(self, ast, statistics):
    explain_plan = self.copy()
    explain_plan.create_plan(ast=[ast["Explain"]["statement"]])
    explain_node = operators.ExplainNode(
        self.properties, statistics, query_plan=explain_plan
    )
    self.add_operator("explain", explain_node)


def _show_columns_planner(self, ast, statistics):

    dataset = ".".join([part["value"] for part in ast["ShowColumns"]["table_name"]])

    if dataset[0:1] == "$":
        mode = "Internal"
        reader = None
    else:
        reader = connector_factory(dataset)
        mode = reader.__mode__

    self.add_operator(
        "reader",
        operators.reader_factory(mode)(
            properties=self.properties,
            statistics=statistics,
            dataset=dataset,
            alias=None,
            reader=reader,
            cache=None,  # never read from cache
            start_date=self.start_date,
            end_date=self.end_date,
        ),
    )
    last_node = "reader"

    filters = self._extract_filter(ast["ShowColumns"])
    if filters:
        self.add_operator(
            "filter",
            operators.ColumnFilterNode(
                properties=self.properties, statistics=statistics, filter=filters
            ),
        )
        self.link_operators(last_node, "filter")
        last_node = "filter"

    self.add_operator(
        "columns",
        operators.ShowColumnsNode(
            properties=self.properties,
            statistics=statistics,
            full=ast["ShowColumns"]["full"],
            extended=ast["ShowColumns"]["extended"],
        ),
    )
    self.link_operators(last_node, "columns")
    last_node = "columns"


def _show_create_planner(self, ast, statistics):

    if ast["ShowCreate"]["obj_type"] != "Table":
        raise SqlError("SHOW CREATE only supports tables")

    dataset = ".".join([part["value"] for part in ast["ShowCreate"]["obj_name"]])

    if dataset[0:1] == "$":
        mode = "Internal"
        reader = None
    else:
        reader = connector_factory(dataset)
        mode = reader.__mode__

    self.add_operator(
        "reader",
        operators.reader_factory(mode)(
            properties=self.properties,
            statistics=statistics,
            dataset=dataset,
            alias=None,
            reader=reader,
            cache=None,  # never read from cache
            start_date=self.start_date,
            end_date=self.end_date,
        ),
    )
    last_node = "reader"

    self.add_operator(
        "show_create",
        operators.ShowCreateNode(
            properties=self.properties, statistics=statistics, table=dataset
        ),
    )
    self.link_operators(last_node, "show_create")
    last_node = "show_create"


def _extract_identifiers(self, ast):
    identifiers = []
    if isinstance(ast, dict):
        for key, value in ast.items():
            if key in ("Identifier",):
                identifiers.append(value["value"])
            if key in ("Using",):
                for item in ast["Using"]:
                    identifiers.append(item["value"])
            if key in ("QualifiedWildcard",):
                identifiers.append("*")
            identifiers.extend(self._extract_identifiers(value))
    if isinstance(ast, list):
        for item in ast:
            if item in ("Wildcard",):
                identifiers.append("*")
            identifiers.extend(self._extract_identifiers(item))

    return list(set(identifiers))


def _show_variable_planner(self, ast, statistics):
    """
    SHOW <variable> only really has a single node.

    All of the keywords should up as a 'values' list in the variable in the ast.

    The last word is the variable, preceeding words are modifiers.
    """

    keywords = [value["value"].upper() for value in ast["ShowVariable"]["variable"]]
    if keywords[0] == "FUNCTIONS":
        show_node = "show_functions"
        node = operators.ShowFunctionsNode(
            properties=self.properties,
            statistics=statistics,
        )
        self.add_operator(show_node, operator=node)
    elif keywords[0] == "PARAMETER":
        if len(keywords) != 2:
            raise SqlError("`SHOW PARAMETER` expects a single parameter name.")
        key = keywords[1].lower()
        if not hasattr(self.properties, key) or key == "variables":
            raise SqlError(f"Unknown parameter '{key}'.")
        value = getattr(self.properties, key)

        show_node = "show_parameter"
        node = operators.ShowValueNode(
            properties=self.properties, statistics=statistics, key=key, value=value
        )
        self.add_operator(show_node, operator=node)
    else:  # pragma: no cover
        raise SqlError(f"SHOW statement type not supported for `{keywords[0]}`.")

    name_column = ExpressionTreeNode(NodeType.IDENTIFIER, value="name")

    order_by_node = operators.SortNode(
        properties=self.properties,
        statistics=statistics,
        order=[([name_column], "ascending")],
    )
    self.add_operator("order", operator=order_by_node)
    self.link_operators(show_node, "order")


def _naive_select_planner(self, ast, statistics):
    """
    The planner creates the naive query plan.

    The goal here is to create a plan to respond to the user, it creates has
    no clever tricks to improve performance.
    """
    all_identifiers = self._extract_identifiers(ast)

    _relations = [r for r in self._extract_relations(ast)]
    if len(_relations) == 0:
        _relations = [(None, "$no_table", "Internal", [])]

    # We always have a data source - even if it's 'no table'
    alias, dataset, mode, hints = _relations[0]

    # external comes in different flavours
    reader = None
    if mode == "External":
        reader = connector_factory(dataset)
        mode = reader.__mode__

    self.add_operator(
        "from",
        operators.reader_factory(mode)(
            properties=self.properties,
            statistics=statistics,
            alias=alias,
            dataset=dataset,
            reader=reader,
            cache=self._cache,
            start_date=self.start_date,
            end_date=self.end_date,
            hints=hints,
            selection=all_identifiers,
        ),
    )
    last_node = "from"

    _joins = list(self._extract_joins(ast))
    if len(_joins) == 0 and len(_relations) == 2:
        # If there's no explicit JOIN but the query has two relations, we
        # use a CROSS JOIN
        _joins = [("CrossJoin", _relations[1], None, None)]
    for join_id, _join in enumerate(_joins):
        if _join:
            join_type, right, join_on, join_using = _join
            if join_type == "CrossJoin" and right[2] == "Function":
                join_type = "CrossJoinUnnest"
            else:

                dataset = right[1]
                if isinstance(dataset, QueryPlanner):
                    mode = "Blob"  # this is still here until it's moved
                    reader = None
                elif isinstance(dataset, dict) and dataset.get("function") is not None:
                    mode = "Function"
                    reader = None
                elif dataset[0:1] == "$":
                    mode = "Internal"
                    reader = None
                else:
                    reader = connector_factory(dataset)
                    mode = reader.__mode__

                # Otherwise, the right table needs to come from the Reader
                right = operators.reader_factory(mode)(
                    properties=self.properties,
                    statistics=statistics,
                    dataset=dataset,
                    alias=right[0],
                    reader=reader,
                    cache=self._cache,
                    start_date=self.start_date,
                    end_date=self.end_date,
                    hints=right[3],
                )

            join_node = operators.join_factory(join_type)
            if join_node is None:
                raise SqlError(f"Join type not supported - `{_join[0]}`")

            self.add_operator(
                f"join-{join_id}",
                join_node(
                    properties=self.properties,
                    statistics=statistics,
                    join_type=join_type,
                    join_on=join_on,
                    join_using=join_using,
                ),
            )
            self.link_operators(last_node, f"join-{join_id}")

            self.add_operator(f"join-{join_id}-right", right)
            self.link_operators(f"join-{join_id}-right", f"join-{join_id}", "right")

            last_node = f"join-{join_id}"

    _selection = self._extract_selection(ast)
    if _selection:
        self.add_operator(
            "where",
            operators.SelectionNode(self.properties, statistics, filter=_selection),
        )
        self.link_operators(last_node, "where")
        last_node = "where"

    _projection = self._extract_field_list(ast["Query"]["body"]["Select"]["projection"])
    _groups = self._extract_field_list(ast["Query"]["body"]["Select"]["group_by"])
    if _groups or get_all_nodes_of_type(
        _projection, select_nodes=(NodeType.AGGREGATOR,)
    ):
        _aggregates = _projection.copy()
        if isinstance(_aggregates, dict):
            raise SqlError("GROUP BY cannot be used with SELECT *")
        if not any(
            a.token_type == NodeType.AGGREGATOR
            for a in _aggregates
            if isinstance(a, ExpressionTreeNode)
        ):
            wildcard = ExpressionTreeNode(NodeType.WILDCARD)
            _aggregates.append(
                ExpressionTreeNode(
                    NodeType.AGGREGATOR, value="COUNT", parameters=[wildcard]
                )
            )
        self.add_operator(
            "agg",
            operators.AggregateNode(
                self.properties, statistics, aggregates=_aggregates, groups=_groups
            ),
        )
        self.link_operators(last_node, "agg")
        last_node = "agg"

    _having = self._extract_having(ast)
    if _having:
        self.add_operator(
            "having",
            operators.SelectionNode(self.properties, statistics, filter=_having),
        )
        self.link_operators(last_node, "having")
        last_node = "having"

    _projection = self._extract_field_list(ast["Query"]["body"]["Select"]["projection"])
    # qualified wildcards have the qualifer in the value
    # e.g. SELECT table.* -> node.value = table
    if (_projection[0].token_type != NodeType.WILDCARD) or (
        _projection[0].value is not None
    ):
        self.add_operator(
            "select",
            operators.ProjectionNode(
                self.properties, statistics, projection=_projection
            ),
        )
        self.link_operators(last_node, "select")
        last_node = "select"

    _distinct = self._extract_distinct(ast)
    if _distinct:
        self.add_operator(
            "distinct", operators.DistinctNode(self.properties, statistics)
        )
        self.link_operators(last_node, "distinct")
        last_node = "distinct"

    _order = self._extract_order(ast)
    if _order:
        self.add_operator(
            "order", operators.SortNode(self.properties, statistics, order=_order)
        )
        self.link_operators(last_node, "order")
        last_node = "order"

    _offset = self._extract_offset(ast)
    if _offset:
        self.add_operator(
            "offset",
            operators.OffsetNode(self.properties, statistics, offset=_offset),
        )
        self.link_operators(last_node, "offset")
        last_node = "offset"

    _limit = self._extract_limit(ast)
    # 0 limit is valid
    if _limit is not None:
        self.add_operator(
            "limit", operators.LimitNode(self.properties, statistics, limit=_limit)
        )
        self.link_operators(last_node, "limit")
        last_node = "limit"


def explain(self):
    def _inner_explain(node, depth):
        if depth == 1:
            operator = self.get_operator(node)
            yield {
                "operator": operator.name,
                "config": operator.config,
                "depth": depth - 1,
            }
        incoming_operators = self.get_incoming_links(node)
        for operator_name in incoming_operators:
            operator = self.get_operator(operator_name[0])
            if isinstance(operator, operators.BasePlanNode):
                yield {
                    "operator": operator.name,
                    "config": operator.config,
                    "depth": depth,
                }
            yield from _inner_explain(operator_name[0], depth + 1)

    head = list(set(self.get_exit_points()))
    # print(head, self._edges)
    if len(head) != 1:
        raise SqlError(f"Problem with the plan - it has {len(head)} heads.")
    plan = list(_inner_explain(head[0], 1))

    table = pyarrow.Table.from_pylist(plan)
    table = Columns.create_table_metadata(table, table.num_rows, "plan", None)
    yield table
