from .base_plan_node import BasePlanNode

from .distinct_node import DistinctNode # remove duplicate records
from .limit_node import LimitNode # select the first N records
from .projection_node import ProjectionNode # remove unwanted columns including renames



# ANALYZE
#- PartitionReaderNode (read a partition)
#- SelectionNode (find records matching a predicate)
#- JoinNode (currently only INNER JOIN)
#- SortNode (order a relation by given keys)
#- GroupNode (put a relation into groups - GROUP BY)
#- AggregateNode (group by MIN/MAX/AVG etc
#- CombineNode (combine sketches and aggregations)
#- Merge - append sets to each other
#- Evaluate ()
#- Index (create an index, can be temporary or persisted)
