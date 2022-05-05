"""
Performance tests are not intended to be ran as part of the regression set.

This tests the relative performance of different storage formats.

60 cycles of arrow took 57.517561689 seconds
60 cycles of jsonl took 60.022933532 seconds
60 cycles of orc took 54.458555462 seconds
60 cycles of parquet took 58.751262451 seconds
60 cycles of zstd took 67.272617175 seconds
"""
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))

import opteryx
from opteryx.storage.adapters.local import DiskStorage
from opteryx.storage.cache.memory_cache import InMemoryCache

import time


class Timer(object):
    def __init__(self, name="test"):
        self.name = name

    def __enter__(self):
        self.start = time.time_ns()

    def __exit__(self, type, value, traceback):
        print(
            "{} took {} seconds".format(self.name, (time.time_ns() - self.start) / 1e9)
        )


FORMATS = ("arrow", "jsonl", "orc", "parquet", "zstd")
cache = InMemoryCache(size=100)

if __name__ == "__main__":

    CYCLES = 60

    conn = opteryx.connect(reader=DiskStorage(), partition_scheme=None, cache=cache)

    for format in FORMATS:
        with Timer(f"{CYCLES} cycles of {format}"):
            for round in range(CYCLES):
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM tests.data.formats.{format};")
                [a for a in cur.fetchall()]
