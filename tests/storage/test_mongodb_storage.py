"""
Test we can read from MinIO
"""
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../.."))

import orjson
import pymongo  # type:ignore

import opteryx

from opteryx.connectors import MongoDbConnector


COLLECTION_NAME = "mongo"
MONGO_CONNECTION = os.environ.get("MONGO_CONNECTION")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE")


def populate_mongo():

    myclient = pymongo.MongoClient(MONGO_CONNECTION)
    mydb = myclient[MONGO_DATABASE]
    collection = mydb[COLLECTION_NAME]

    collection.drop()

    for i in range(25):
        data = open("testdata/tweets/tweets-0000.jsonl", mode="rb").read()
        collection.insert_many(map(orjson.loads, data.split(b"\n")[:-1]))


def test_mongo_storage():

    opteryx.register_store(COLLECTION_NAME, MongoDbConnector)

    populate_mongo()

    conn = opteryx.connect()

    # SELECT EVERYTHING
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {COLLECTION_NAME}.data.tweets;")
    rows = cur.arrow()
    assert rows.num_rows == 25 * 25, rows.num_rows

    # PROCESS THE DATA IN SOME WAY
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {COLLECTION_NAME}.data.tweets GROUP BY userid;")
    rows = list(cur.fetchall())
    assert len(rows) == 2

    conn.close()


if __name__ == "__main__":  # pragma: no cover
    test_mongo_storage()
    print("✅ okay")
