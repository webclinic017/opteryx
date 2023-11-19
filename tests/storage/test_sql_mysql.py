"""
Test we can read from Sqlite - this is a basic exercise of the SQL Connector
"""
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))

import opteryx
from opteryx.connectors import SqlConnector

MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_USER = os.environ.get("MYSQL_USER")
CONNECTION = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@mysql-3c28af34-joocer-9765.a.aivencloud.com:10067/defaultdb?charset=utf8mb4"


def test_mysql_storage():
    opteryx.register_store("mysql", SqlConnector, remove_prefix=True, connection=CONNECTION)

    results = opteryx.query("SELECT * FROM mysql.planets")
    assert results.rowcount == 9, results.rowcount
    assert results.columncount == 20

    # PROCESS THE DATA IN SOME WAY
    results = opteryx.query("SELECT COUNT(*) FROM mysql.planets;")
    assert results.rowcount == 1, results.rowcount
    assert results.columncount == 1

    # PUSH A PROJECTION
    results = opteryx.query("SELECT name FROM mysql.planets;")
    assert results.rowcount == 9, results.rowcount
    assert results.columncount == 1


if __name__ == "__main__":  # pragma: no cover
    from tests.tools import run_tests

    _mysql_create_tables()

    run_tests()
