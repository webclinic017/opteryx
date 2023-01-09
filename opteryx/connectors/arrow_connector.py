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
Arrow Reader

Used to read datasets registered using the register_arrow or register_df functions.
"""

import pyarrow

from opteryx.connectors import BaseDocumentStorageAdapter
from opteryx.shared import MaterializedDatasets

BATCH_SIZE = 500


class ArrowConnector(BaseDocumentStorageAdapter):
    def __init__(self):
        self._datasets = MaterializedDatasets()

    def get_document_count(self, collection) -> int:
        dataset = self._datasets[collection]
        return dataset.num_rows

    def read_documents(self, collection, page_size: int = BATCH_SIZE):
        dataset = self._datasets[collection]
        for batch in dataset.to_batches(max_chunksize=BATCH_SIZE):
            page = pyarrow.Table.from_batches([batch], schema=dataset.schema)
            yield page
