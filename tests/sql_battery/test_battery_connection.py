"""
The best way to test a SQL engine is to throw queries at it.

This tests substitutions passed to the connection
"""
from datetime import datetime
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))
import pytest

import opteryx
from opteryx.connectors import DiskConnector


# fmt:off
STATEMENTS = [
        ("SELECT * FROM $planets WHERE name = ?", ["Earth"], 1, 20),
        ("SELECT * FROM $planets WHERE id = ?", [4], 1, 20),
        ("SELECT * FROM $planets WHERE id > ?", [4], 5, 20),
        ("SELECT * FROM $planets WHERE name LIKE ?", ['%t%'], 5, 20),
        ("SELECT * FROM $planets WHERE name LIKE ? AND id > ?", ['%t%', 4], 4, 20),
        ("SELECT * FROM $planets WHERE id > ? AND name LIKE ?", [4, '%t%'], 4, 20),
        ("SELECT * FROM $planets WHERE 9 <> ?", [None], 0, 20),
        ("SELECT * FROM $planets WHERE 9 != ?", [None], 0, 20),
        ("SELECT * FROM $planets WHERE BOOLEAN(id) = ?", [True], 9, 20),
        ("SELECT * FROM $planets WHERE \"'\" = ?", ["'"], 9, 20),
        ("SELECT * FROM $astronauts WHERE birth_date = ?", [datetime(year=1967, month=5, day=17)], 1, 19),

        # parameterized query batches
        ("SET @id = ?; SELECT * FROM $planets WHERE id >= @id AND id <= @id;", [1], 1, 20),
        ("SET @id = ?; SELECT * FROM $planets WHERE id <> @id AND name = ?;", [1, "Earth"], 1, 20),
        ("SET @id = 1; SELECT * FROM $planets WHERE id <> @id AND name = ?;", ["Earth"], 1, 20),
    ]
# fmt:on


@pytest.mark.parametrize("statement, subs, rows, columns", STATEMENTS)
def test_sql_battery(statement, subs, rows, columns):
    """
    Test an battery of statements
    """
    conn = opteryx.connect(reader=DiskConnector(prefix=""), partition_scheme=None)
    cursor = conn.cursor()
    cursor.execute(statement, subs)
    actual_rows, actual_columns = cursor.shape

    assert (
        rows == actual_rows
    ), f"Query returned {actual_rows} rows but {rows} were expected, {statement}\n{cursor.head(10)}"
    assert (
        columns == actual_columns
    ), f"Query returned {actual_columns} cols but {columns} were expected, {statement}\n{cursor.head(10)}"


if __name__ == "__main__":  # pragma: no cover
    print(f"RUNNING BATTERY OF {len(STATEMENTS)} CONNECTION TESTS")
    for statement, subs, rows, cols in STATEMENTS:
        print(statement)
        test_sql_battery(statement, subs, rows, cols)

    print("✅ okay")
