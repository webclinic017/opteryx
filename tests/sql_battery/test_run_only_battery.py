"""
The best way to test a SQL Engine is to throw queries at it.

This is part of a suite of tests which are based on running many SQL statements.

 >  Run Only
    Shape Checking
    Results Checking
    Compare to DuckDB

This is the lightest of the battery tests, it only ensures a query executes.

This may seem pointless as a test if that is all it is doing, but this has it's uses,
particularly in testing SQL parsing based problems/features - we don't care if the
result is right, if the engine can't parse the statements.

However, this is the lowest value of the SQL battery tests, all we know after running
this set is that the statements parse and the resulting query executes without error.
We don't know if the query parsed correctly or if the result is correct.

It currently takes less than a second to run the whole set, and it gives us some
confidence in the function of the engine.
"""
import glob
import os
import sys
import pytest

sys.path.insert(1, os.path.join(sys.path[0], "../.."))

import opteryx


def get_tests(test_type):
    suites = glob.glob(f"**/**.{test_type}", recursive=True)
    for suite in suites:
        with open(suite, mode="r") as test_file:
            yield from [
                line
                for line in test_file.read().splitlines()
                if len(line) > 0 and line[0] != "#"
            ]


RUN_ONLY_TESTS = list(get_tests("run_tests"))


@pytest.mark.parametrize("statement", RUN_ONLY_TESTS)
def test_run_only_tests(statement):
    """
    These tests are only run, the result is not checked.
    This is useful for parsing checks
    """
    conn = opteryx.connect()
    cursor = conn.cursor()

    cursor.execute(statement)
    # row count doesn't fail if there are no records
    cursor.rowcount


if __name__ == "__main__":  # pragma: no cover
    import shutil
    import time

    width = shutil.get_terminal_size((80, 20))[0] - 15

    nl = "\n"

    print(f"RUNNING BATTERY OF {len(RUN_ONLY_TESTS)} RUN_ONLY TESTS")
    for index, statement in enumerate(RUN_ONLY_TESTS):
        start = time.monotonic_ns()
        print(
            f"\033[0;36m{(index + 1):04}\033[0m {statement[0:width - 1].ljust(width)}",
            end="",
        )

        test_run_only_tests(statement)

        print(
            f"\033[0;32m{str(int((time.monotonic_ns() - start)/1000000)).rjust(4)}ms\033[0m ✅"
        )

    print("--- ✅ \033[0;32mdone\033[0m")
