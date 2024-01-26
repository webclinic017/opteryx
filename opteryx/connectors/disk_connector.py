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
The 'direct disk' connector provides the reader for when a dataset is
given as a folder on local disk
"""

import os
from typing import Dict
from typing import List

import pyarrow
from orso.schema import RelationSchema
from orso.tools import single_item_cache
from orso.types import OrsoTypes

from opteryx.connectors.base.base_connector import BaseConnector
from opteryx.connectors.capabilities import Cacheable
from opteryx.connectors.capabilities import Partitionable
from opteryx.connectors.capabilities import PredicatePushable
from opteryx.exceptions import DatasetNotFoundError
from opteryx.exceptions import EmptyDatasetError
from opteryx.exceptions import UnsupportedFileTypeError
from opteryx.utils.file_decoders import VALID_EXTENSIONS
from opteryx.utils.file_decoders import get_decoder


class DiskConnector(BaseConnector, Cacheable, Partitionable, PredicatePushable):
    __mode__ = "Blob"

    PUSHABLE_OPS: Dict[str, bool] = {
        "Eq": True,
        "NotEq": True,
        "Gt": True,
        "GtEq": True,
        "Lt": True,
        "LtEq": True,
    }

    PUSHABLE_TYPES = {OrsoTypes.BOOLEAN, OrsoTypes.DOUBLE, OrsoTypes.INTEGER, OrsoTypes.VARCHAR}

    def __init__(self, **kwargs):
        """
        Initialize the DiskConnector, which reads datasets directly from disk.

        Parameters:
            kwargs: Dict
                Arbitrary keyword arguments.
        """
        BaseConnector.__init__(self, **kwargs)
        Partitionable.__init__(self, **kwargs)
        Cacheable.__init__(self, **kwargs)
        PredicatePushable.__init__(self, **kwargs)

        self.dataset = self.dataset.replace(".", "/")
        self.cached_first_blob = None  # Cache for the first blob in the dataset

    def read_blob(self, *, blob_name, **kwargs) -> bytes:
        """
        Read a blob (binary large object) from disk.

        We're using the low-level read, on the whole it's about 5% faster - not
        much faster considering the effort to bench-mark different disk access
        methods, but as one of the slowest parts of the system we wanted to find
        if there was a faster way.

        Parameters:
            blob_name: str
                The name of the blob file to read.
            kwargs: Dict
                Arbitrary keyword arguments.

        Returns:
            The blob as bytes.
        """
        file_descriptor = os.open(blob_name, os.O_RDONLY)
        try:
            return os.read(file_descriptor, os.path.getsize(blob_name))
        finally:
            os.close(file_descriptor)

    @single_item_cache
    def get_list_of_blob_names(self, *, prefix: str) -> List[str]:
        """
        List all blob files in the given directory path.

        Parameters:
            prefix: str
                The directory path.

        Returns:
            A list of blob filenames.
        """
        return [
            os.path.join(root, file)
            for root, _, files in os.walk(prefix)
            for file in files
            if os.path.splitext(file)[1] in VALID_EXTENSIONS
        ]

    def read_dataset(
        self, columns: list = None, predicates: list = None, just_schema: bool = False, **kwargs
    ) -> pyarrow.Table:
        """
        Read the entire dataset from disk.

        Yields:
            Each blob's content as a PyArrow Table.
        """
        blob_names = self.partition_scheme.get_blobs_in_partition(
            start_date=self.start_date,
            end_date=self.end_date,
            blob_list_getter=self.get_list_of_blob_names,
            prefix=self.dataset,
        )

        for blob_name in blob_names:
            try:
                decoder = get_decoder(blob_name)
                blob_bytes = self.read_blob(blob_name=blob_name, statistics=self.statistics)
                yield decoder(
                    blob_bytes, projection=columns, selection=predicates, just_schema=just_schema
                )
            except UnsupportedFileTypeError:
                pass  # Skip unsupported file types
            except pyarrow.ArrowInvalid:
                self.statistics.unreadable_data_blobs += 1

    def get_dataset_schema(self) -> RelationSchema:
        """
        Retrieve the schema of the dataset either from the metastore or infer it from the first blob.

        Returns:
            The schema of the dataset.
        """
        self.schema = self.read_schema_from_metastore()
        if self.schema:
            return self.schema

        self.schema = next(self.read_dataset(just_schema=True), None)

        if self.schema is None:
            if os.path.isdir(self.dataset):
                raise EmptyDatasetError(dataset=self.dataset.replace("/", "."))
            raise DatasetNotFoundError(dataset=self.dataset)

        return self.schema
