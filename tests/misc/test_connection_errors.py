"""
Test the connection example from the documentation
"""
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))

import pytest


def test_connection_invalid_state():

    import opteryx
    from opteryx.exceptions import CursorInvalidStateError

    conn = opteryx.connect()
    cur = conn.cursor()

    with pytest.raises(CursorInvalidStateError):
        cur.fetchone()

    with pytest.raises(CursorInvalidStateError):
        cur.fetchmany()

    with pytest.raises(CursorInvalidStateError):
        cur.fetchall()

    with pytest.raises(CursorInvalidStateError):
        cur.shape()


#def test_connection_warnings():
#
#    import opteryx
#
#    conn = opteryx.connect()
#    cur = conn.cursor()
#    cur.execute("SELECT * FROM $planets WITH(_NO_CACHE)")
#    cur.fetchone()
#
#    assert cur.has_warnings


def test_connection_parameter_mismatch():
    """test substitution binding errors"""

    import opteryx
    from opteryx.exceptions import ProgrammingError

    conn = opteryx.connect()
    cur = conn.cursor()
    with pytest.raises(ProgrammingError):
        cur.execute("SELECT * FROM $planets WHERE id = ?", experimental=True)
    with pytest.raises(ProgrammingError):
        cur.execute(
            "SELECT * FROM $planets WHERE id = ? AND name = ?", [1], experimental=True
        )
    with pytest.raises(ProgrammingError):
        cur.execute(
            "SELECT * FROM $planets WHERE id = ? AND name = ?", (1,), experimental=True
        )
    with pytest.raises(ProgrammingError):
        cur.execute("SELECT * FROM $planets WHERE id = ?", (1, 2), experimental=True)


if __name__ == "__main__":  # pragma: no cover

    test_connection_invalid_state()
#    test_connection_warnings()
    test_connection_parameter_mismatch()

    print("✅ okay")
