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
MinIo Reader - also works with AWS
"""
import io
import os
from typing import List

import pyarrow
from orso.schema import FlatColumn
from orso.schema import RelationSchema
from orso.tools import single_item_cache

from opteryx.connectors.base.base_connector import BaseConnector
from opteryx.connectors.capabilities import Cacheable
from opteryx.connectors.capabilities import Partitionable
from opteryx.exceptions import DatasetNotFoundError
from opteryx.exceptions import MissingDependencyError
from opteryx.exceptions import UnmetRequirementError
from opteryx.exceptions import UnsupportedFileTypeError
from opteryx.utils import paths
from opteryx.utils.file_decoders import VALID_EXTENSIONS
from opteryx.utils.file_decoders import get_decoder


class AwsS3Connector(BaseConnector, Cacheable, Partitionable):
    __mode__ = "Blob"

    def __init__(self, credentials=None, **kwargs):
        try:
            from minio import Minio  # type:ignore
        except ImportError as err:  # pragma: no cover
            raise MissingDependencyError(err.name) from err

        BaseConnector.__init__(self, **kwargs)
        Partitionable.__init__(self, **kwargs)
        Cacheable.__init__(self, **kwargs)

        end_point = os.environ.get("MINIO_END_POINT")
        access_key = os.environ.get("MINIO_ACCESS_KEY")
        secret_key = os.environ.get("MINIO_SECRET_KEY")
        secure = str(os.environ.get("MINIO_SECURE", "TRUE")).lower() == "true"

        if end_point is None:  # pragma: no cover
            raise UnmetRequirementError(
                "MinIo (S3) adapter requires MINIO_END_POINT, MINIO_ACCESS_KEY and MINIO_SECRET_KEY set in environment variables."
            )

        self.minio = Minio(end_point, access_key, secret_key, secure=secure)
        self.dataset = self.dataset.replace(".", "/")

    @single_item_cache
    def get_list_of_blob_names(self, *, prefix: str) -> List[str]:
        bucket, object_path, _, _ = paths.get_parts(prefix)
        blobs = self.minio.list_objects(bucket_name=bucket, prefix=object_path, recursive=True)
        blobs = (
            bucket + "/" + blob.object_name for blob in blobs if not blob.object_name.endswith("/")
        )

        return [blob for blob in blobs if ("." + blob.split(".")[-1].lower()) in VALID_EXTENSIONS]

    def read_dataset(self) -> pyarrow.Table:
        blob_names = self.partition_scheme.get_blobs_in_partition(
            start_date=self.start_date,
            end_date=self.end_date,
            blob_list_getter=self.get_list_of_blob_names,
            prefix=self.dataset,
        )

        for blob_name in blob_names:
            try:
                decoder = get_decoder(blob_name)
                blob_bytes = self.read_blob(blob_name=blob_name)
                yield decoder(blob_bytes)
            except UnsupportedFileTypeError:
                pass

    def get_dataset_schema(self) -> RelationSchema:
        # Try to read the schema from the metastore
        self.schema = self.read_schema_from_metastore()
        if self.schema:
            return self.schema

        record = next(self.read_dataset(), None)

        if record is None:
            raise DatasetNotFoundError(dataset=self.dataset)

        arrow_schema = record.schema

        self.schema = RelationSchema(
            name=self.dataset,
            columns=[FlatColumn.from_arrow(field) for field in arrow_schema],
        )

        return self.schema

    @Cacheable().read_thru()
    def read_blob(self, *, blob_name):
        try:
            bucket, object_path, name, extension = paths.get_parts(blob_name)
            stream = self.minio.get_object(bucket, object_path + "/" + name + extension)
            return io.BytesIO(stream.read())
        finally:
            stream.close()
