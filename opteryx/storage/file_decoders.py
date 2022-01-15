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
Decompressors for the Readers.

These yield a tuple of the schema and a tuple of the values for a row
"""

from opteryx.exceptions import MissingDependencyError
import simdjson
from typing import Tuple, Any

json_parser = simdjson.Parser()

class PartitionFormatMismatch(Exception):
    pass

def _json_to_tuples(line, projection) -> Tuple[Any]:
    """
    Parse each line in the file to a dictionary.

    We do some juggling so we can delete the object which is faster than creating a
    new Parser for each record.
    """
    dic = json_parser.parse(line)
    values = tuple([dic[attribute] for attribute in projection])
    del dic
    return values

def _json_to_dicts(line, projection) -> dict:
    """
    Parse each line in the file to a dictionary.

    This is slower than converting to Tuples because we're going to do more work even
    though this routine has almost no code in it.
    """
    dict_parser = simdjson.Parser()
    dic = dict_parser.parse(line)
    return dic

def zstd_decoder(stream, projection):
    """
    Read zstandard compressed JSONL files
    """
    import zstandard

    with zstandard.open(stream, "rb") as file:
        yield from jsonl_decoder(file, projection)


def parquet_decoder(stream, projection):
    """
    Read parquet formatted files
    """
    try:
        import pyarrow.parquet as pq
    except ImportError:  # pragma: no cover
        raise MissingDependencyError(
            "`pyarrow` is missing, please install or include in requirements.txt"
        )
    table = pq.read_table(stream, columns=projection)
    return table


def orc_decoder(stream, projection):
    """
    Read orc formatted files
    """
    try:
        import pyarrow.orc as orc
    except ImportError:  # pragma: no cover
        raise MissingDependencyError(
            "`pyarrow` is missing, please install or include in requirements.txt"
        )

    orc_file = orc.ORCFile(stream)
    table = orc_file.read(columns=projection)
    return table


def jsonl_decoder(stream, projection):
    """
    The if we have a key
    """
    import pyarrow.json

    table = pyarrow.json.read_json(stream)
    return table