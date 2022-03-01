"""
This compensates for missing temporal table support in the SQL parser.

For information on temporal tables see: 
https://blog.devgenius.io/a-query-in-time-introduction-to-sql-server-temporal-tables-145ddb1355d9

This supports the following syntaxes

- FOR TODAY
- FOR YESTERDAY
- FOR DATES AS OF <timestamp>
- FOR DATES BETWEEN <timestamp> AND <timestamp>

"""
import re
from mabel.utils import dates
import datetime

SQL_PARTS = [
    r"SELECT",
    r"FROM",
    r"FOR",
    r"WHERE",
    r"GROUP BY",
    r"HAVING",
    r"ORDER BY",
    r"LIMIT",
    r"OFFSET"
]


def clean_statement(string):
    """
    Remove carriage returns and all whitespace to single spaces
    """
    _RE_COMBINE_WHITESPACE = re.compile(r"\s+")
    return _RE_COMBINE_WHITESPACE.sub(" ", string).strip().upper()

def sql_parts(string):
    """
    Split a SQL statement into clauses
    """
    reg = re.compile(
        r"(\(|\)|,|"
        + r"|".join([r"\b" + i.replace(r" ", r"\s") + r"\b" for i in SQL_PARTS])
        + r")",
        re.IGNORECASE,
    )
    parts = reg.split(string)
    return [part.strip() for part in parts if part.strip() != ""]

def remove_comments(string):
    """
    Remove comments from the string
    """
    pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|--[^\r\n]*$)"
    # first group captures quoted strings (double or single)
    # second group captures comments (//single-line or /* multi-line */)
    regex = re.compile(pattern, re.MULTILINE | re.DOTALL)

    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return ""  # so we will return empty to remove the comment
        else:  # otherwise, we will return the 1st group
            return match.group(1)  # captured quoted-string

    return regex.sub(_replacer, string)


def extract_temporal_filters(sql):

    # prep the statement, by normalizing it
    clean_sql = remove_comments(sql)
    clean_sql = clean_statement(clean_sql)
    parts = sql_parts(clean_sql)

    TODAY = datetime.date.today()
    clearing_regex = None
    start_date = None
    end_date = None

    try:
        pos = parts.index("FOR")
        for_dates = parts[pos + 1]
        if for_dates == "TODAY":
            start_date = TODAY
            end_date = TODAY
            clearing_regex = r"(\bFOR\sTODAY\b)"
        elif for_dates == "YESTERDAY":
            start_date = TODAY - datetime.timedelta(days=1)
            end_date = TODAY - datetime.timedelta(days=1)
            clearing_regex = r"(\bFOR\sYESTERDAY\b)"
        # previous_month
        # previous_cycle
        # this_cycle
        elif for_dates.startswith("DATES AS OF"):
            date_string = for_dates[12:]
            start_date = dates.parse_iso(date_string[1:-1])
            end_date = start_date
            clearing_regex = r"(FOR\sDATES\sAS\sOF\s" + date_string + r")"
        elif for_dates.startswith("DATES BETWEEN "):
            between = for_dates.split(' ')
            start_date = dates.parse_iso(between[2][1:-1])
            end_date = dates.parse_iso(between[4][1:-1])
            clearing_regex = r"(FOR\sDATES\sBETWEEN\s" + between[2] + r"\sAND\s" + between[4] + r")"

        if clearing_regex:
            regex = re.compile(clearing_regex, re.MULTILINE | re.DOTALL)
            sql = regex.sub("-- FOR STATEMENT\n", sql)

        # swap the order if we need to
        if start_date > end_date:
            start_date, end_date = end_date, start_date
    except:
        pass

    return start_date, end_date, sql
