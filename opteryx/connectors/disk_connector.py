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
The 'direct disk' connector provides the reader for when a dataset file is
given directly in a query.

As such it assumes 
"""
import io
import os

import pyarrow
from orso.schema import RelationSchema

from opteryx.connectors.base.base_connector import BaseConnector
from opteryx.connectors.capabilities import Cacheable
from opteryx.connectors.capabilities import Partitionable
from opteryx.exceptions import UnsupportedFileTypeError
from opteryx.utils.file_decoders import get_decoder


class DiskConnector(BaseConnector, Cacheable, Partitionable):
    __mode__ = "Blob"

    def __init__(self, **kwargs):
        BaseConnector.__init__(self, **kwargs)
        Partitionable.__init__(self, **kwargs)
        Cacheable.__init__(self, **kwargs)

        self.dataset = self.dataset.replace(".", "/")

    @Cacheable().read_thru()
    def read_blob(self, blob_name):
        with open(blob_name, mode="br") as file:
            file_stream = file.read()
        return io.BytesIO(file_stream)

    def read_partition(self, base_folder):
        # get the list of files in the folder
        # pass them to the partitionable function to filter in/out blobs
        # use read_blob to read over the blobs
        pass

    def read_dataset(self) -> pyarrow.Table:
        import glob

        for g in glob.iglob(self.dataset + "/**", recursive=True):
            if not os.path.isfile(g):
                continue
            try:
                decoder = get_decoder(g)
                contents = self.read_blob(g)
                yield decoder(contents)
            except UnsupportedFileTypeError:
                pass

    def get_dataset_schema(self) -> RelationSchema:
        import glob

        for g in glob.iglob(self.dataset + "/**", recursive=True):
            if not os.path.isfile(g):
                continue
            try:
                decoder = get_decoder(g)
                contents = self.read_blob(g)
                return decoder(contents, just_schema=True)
            except UnsupportedFileTypeError:
                pass
