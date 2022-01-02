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
Tokenizer -> Lexer -> Planner

Tokenizer deconstructs a string into it's parts
Lexer Interprets the tokens
Planner creates a naive plan for the query


"""
import re
from opteryx.utils.dates import parse_iso
from opteryx.engine.functions import FUNCTIONS
from opteryx.engine.sql.parser.constants import SQL_TOKENS, OPERATORS, SQL_KEYWORDS
from opteryx.engine.aggregators.aggregators import AGGREGATORS


def interpret_value(value):
    if not isinstance(value, str):
        return value
    if value.upper() in ("TRUE", "FALSE"):
        return value.upper() == "TRUE"
    try:
        # there appears to be a race condition with this library
        # so wrap in a SystemError
        num = fastnumbers.fast_real(value)
        if isinstance(num, (int, float)):
            return num
    except SystemError:
        pass
    value = value[1:-1]
    return parse_iso(value) or value


def case_correction(token, part_of_query):
    if part_of_query in (
        SQL_TOKENS.LITERAL,
        SQL_TOKENS.VARIABLE,
        SQL_TOKENS.SUBQUERY,
    ):
        return token
    return token.upper()

def is_int(value):
    try:
        int_value = int(value)
        return True
    except ValueError:
        return False

def is_float(value):
    try:
        int_value = float(value)
        return True
    except ValueError:
        return False

def get_token_type(token):
    """
    Determine the token type.
    """
    token = str(token).strip()
    token_upper = token.upper()
    if len(token) == 0:
        return SQL_TOKENS.EMPTY
    if token[0] == token[-1] == "`":
        # tokens in ` quotes are variables, this is how we supersede all other
        # checks, e.g. if it looks like a keyword but is a variable.
        return SQL_TOKENS.VARIABLE
    if token in list(SQL_KEYWORDS):
        return SQL_TOKENS.KEYWORD
    if token == "*":  # nosec - not a password
        return SQL_TOKENS.EVERYTHING
    if token_upper in FUNCTIONS:
        return SQL_TOKENS.FUNCTION
    if token_upper in OPERATORS:
        return SQL_TOKENS.OPERATOR
    if token_upper in AGGREGATORS:
        return SQL_TOKENS.AGGREGATOR
    if token[0] == token[-1] == '"' or token[0] == token[-1] == "'":
        # tokens in quotes are either dates or string literals, if we can
        # parse to a date, it's a date
        if parse_iso(token[1:-1]):
            return SQL_TOKENS.TIMESTAMP
        else:
            return SQL_TOKENS.LITERAL
    if is_int(token):
        return SQL_TOKENS.INTEGER
    if is_float(token):
        return SQL_TOKENS.DOUBLE
    if token in ("(", "["):
        return SQL_TOKENS.LEFTPARENTHESES
    if token in (")", "]"):
        return SQL_TOKENS.RIGHTPARENTHESES
    if re.search(r"^[^\d\W][\w\-\.]*", token):
        if token_upper in ("TRUE", "FALSE"):
            # 'true' and 'false' without quotes are booleans
            return SQL_TOKENS.BOOLEAN
        if token_upper in ("NULL", "NONE"):
            # 'null' or 'none' without quotes are nulls
            return SQL_TOKENS.NULL
        if token_upper == "AND":  # nosec - not a password
            return SQL_TOKENS.AND
        if token_upper == "OR":  # nosec - not a password
            return SQL_TOKENS.OR
        if token_upper == "NOT":  # nosec - not a password
            return SQL_TOKENS.NOT
        if token_upper == "AS":  # nosec - not a password
            return SQL_TOKENS.AS
        # tokens starting with a letter, is made up of letters, numbers,
        # hyphens, underscores and dots are probably variables. We do this
        # last so we don't miss assign other items to be a variable
        return SQL_TOKENS.VARIABLE
    # at this point, we don't know what it is
    return SQL_TOKENS.UNKNOWN

def analyze_tokens(tokens):
    """
    Go through a set of tokens:
        1) Determine the Part of Query (Part of Speach) to each
        2) Perform normalization, such as making keywords uppercase
    """

    def _inner_analysis(tokens):
        for token in tokens:
            poq = get_token_type(token)
            token = case_correction(token, poq)
            yield (token, poq)

    # find lists and structs

    return list(_inner_analysis(tokens))