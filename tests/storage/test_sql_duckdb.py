"""
Test we can read from DuckDB - this is a basic exercise of the SQL Connector
"""
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))

import opteryx
from opteryx.connectors import SqlConnector
from tests.tools import create_duck_db


def test_duckdb_storage():
    create_duck_db()

    opteryx.register_store(
        "duckdb",
        SqlConnector,
        remove_prefix=True,
        connection="duckdb:///planets.duckdb",
    )

    results = opteryx.query("SELECT * FROM duckdb.planets")
    assert results.rowcount == 9, results.rowcount
    assert results.columncount == 20

    # PROCESS THE DATA IN SOME WAY
    results = opteryx.query("SELECT COUNT(*) FROM duckdb.planets;")
    assert results.rowcount == 1, results.rowcount
    assert results.columncount == 1

    # PUSH A PROJECTION
    results = opteryx.query("SELECT name FROM duckdb.planets;")
    assert results.rowcount == 9, results.rowcount
    assert results.columncount == 1


if __name__ == "__main__":  # pragma: no cover
    from tests.tools import run_tests

    run_tests()
