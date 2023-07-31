from functools import wraps

from opteryx.exceptions import InvalidConfigurationError


class Partitionable:
    partitioned = True

    def __init__(self, **kwargs):
        self.partition_scheme = kwargs.get("partition_scheme")

        from opteryx.managers.schemes import BasePartitionScheme
        from opteryx.managers.schemes import DefaultPartitionScheme

        if self.partition_scheme is None:
            self.partition_scheme = DefaultPartitionScheme

        if not isinstance(self.partition_scheme, type):
            raise InvalidConfigurationError(
                config_item="partition_scheme",
                provided_value=str(self.partition_scheme.__class__.__name__),
                valid_value_description="an uninitialized class.",
            )

        if not issubclass(self.partition_scheme, BasePartitionScheme):
            raise InvalidConfigurationError(
                config_item="partition_scheme", provided_value=str(self.partition_scheme.__name__)
            )

        self.start_date = None
        self.end_date = None

    def read_partitioned(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            base_path = "data/"
            partition_template = "year_{YYYY}/month_{MM}/day_{DD}"

            read_range = "yesterday to today"

            for partition_thing in read_range:
                partition_path = populate_partition_values(
                    base_path + partition_template, partition_thing
                )

                # Get the partition(s) to read
                partition_range = kwargs.get("partition_range", None)

                if partition_range is None:
                    # Read all partitions if no range is specified
                    partitions_to_read = all_partitions
                else:
                    start, end = partition_range
                    # Read a range of partitions if specified
                    partitions_to_read = all_partitions[start:end]

                # Read each partition
                for partition in partitions_to_read:
                    # Update kwargs with the partition directory
                    kwargs.update({"directory": os.path.join(self.base_directory, partition)})

                    # Read the partition
                    result = func(*args, **kwargs)

                    yield result

        return wrapper
