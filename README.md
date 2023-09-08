<div align="center">

![Opteryx](https://raw.githubusercontent.com/mabel-dev/opteryx/main/opteryx-word-small.png)
## Query your data, where it lives.

_One interface, endless possibilities - effortless cross-platform data analytics._
</div>

<h3 align="center">
Unlock your ability to discover insights across your diverse data sources, like Postgres and S3, all via a single, unified SQL interface.
</h3>

<div align="center">

[**Documentation**](https://opteryx.dev/latest) |
[**Install**](#install) |
[**Examples**](#examples) |
[**Contributing**](https://opteryx.dev/latest/contributing/contributing/)

[![PyPI Latest Release](https://img.shields.io/pypi/v/opteryx.svg)](https://pypi.org/project/opteryx/)
[![opteryx](https://snyk.io/advisor/python/opteryx/badge.svg?style=flat-square)](https://snyk.io/advisor/python/opteryx)
[![Downloads](https://static.pepy.tech/badge/opteryx)](https://pepy.tech/project/opteryx)
[![last_commit](https://img.shields.io/github/last-commit/mabel-dev/opteryx)](https://github.com/mabel-dev/opteryx/commits)
[![codecov](https://codecov.io/gh/mabel-dev/opteryx/branch/main/graph/badge.svg?token=sIgKpzzd95)](https://codecov.io/gh/mabel-dev/opteryx)
[![PyPI Latest Release](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue?logo=python)](https://pypi.org/project/opteryx/)

[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Easily%20query%20your%data%20with%20Opteryx&url=https://mabel-dev.github.io/opteryx/&hashtags=python,sql)
</div>

## What is Opteryx?

Opteryx simplifies cross-platform data analytics by federating SQL queries across multiple data sources, such as Postgres databases and Parquet files. The goal is to enhance your data analytics process by offering a unified way to access and manage different types of data.

Opteryx is a Python library that combines elements of in-process database engines like SQLite and DuckDB with federative features found in systems like Presto and Trino. The result is a versatile tool for querying data across multiple data sources in a seamless fashion.

Opteryx offers the following features:

- SQL queries on data files generated by other processes, such as logs
- A command-line tool for filtering, transforming, and combining files
- Integration with familiar tools like pandas and Polars
- Embeddable as a low-cost engine, enabling portability and allowing for hundreds of analysts to leverage ad hoc databases with ease
- Unified and federated access to data on disk, in the cloud, and in on-premises databases, not only through the same interface but in the same query

## Why Use Opteryx?

### __Familiar Interface__

Opteryx supports key parts of the [Python DBAPI](https://peps.python.org/pep-0249/) and [SQL92 standard](https://opteryx.dev/latest/get-started/external-standards/sql92/) standards which many analysts and engineers will already know how to use.

### __Consistent Syntax__

Opteryx creates a common SQL-layer over multiple data platforms, allowing backend systems to be upgraded, migrated or consolidated without changing any Opteryx code.

Where possible, errors and warnings returned by Opteryx help the user to understand how to fix their statement to reduce time-to-success for even novice SQL users.

### __Bring your own Data__

![Opteryx](https://github.com/mabel-dev/opteryx.dev/raw/main/assets/data-stores.png)

Opteryx supports multiple query engines, dataframe APIs and storage formats. You can mix-and-match sources in a single query. Opteryx can even `JOIN` datasets stored in different formats and different platforms in the same query, such as Parquet and MySQL.

Opteryx allows you to query your data directly in the systems where they are stored, eliminating the need to duplicate data into a common store for analytics. This saves you the cost and effort of maintaining duplicates.

Opteryx can push parts of your query to the source query engine, allowing queries to run at the speed of the backend, rather than your local computer.

And if there's not a connector in the box for your data platform; bespoke connectors can be added.

### __Consumption-Based Billing Friendly__

Opteryx is well-suited for deployments to environments which are pay-as-you-use, like Google Cloud Run. Great for situations where you have low-volume usage, or multiple environments, where the costs of many traditional database deployment can quickly add up.

### __Python Ecosystem__

Opteryx is Open Source Python, it quickly and easily integrates into Python code, including Jupyter Notebooks, so you can start querying your data within a few minutes. Opteryx integrates with many of your favorite Python data tools, you can use Opteryx to run SQL against pandas and Polars DataFrames, and even execute a `JOIN` on an in-memory DataFrame and a remote SQL dataset.

### __Time Travel__

Designed for data analytics in environments where decisions need to be replayable, Opteryx allows you to query data as at a point in time in the past to replay decision algorithms against facts as they were known in the past. You can even self-join tables historic data, great for finding deltas in datasets over time. _(data must be structured to enable temporal queries)_

### __Fast__

Benchmarks on M1 Pro Mac running an ad hoc `GROUP BY` over a 1Gb parquet file via the CLI in ~1/5th of a second, from a cold start. _(different systems will have different performance characteristics)_

Rows    | Columns | File Size | Query Time
------- | ------- | --------- | ----------
561225  |      81 |       1Gb | 0.22sec
1064539 |      81 |       2Gb | 0.27sec

### __Instant Elasticity__

Designed to run in Knative and similar environments like Google Cloud Run, Opteryx can scale down to zero, and scale up to respond to thousands of concurrent queries within seconds.

## Install

Installing from PyPI is recommended.

~~~bash
pip install opteryx
~~~

To build Opteryx from source, refer to the [contribution guides](https://opteryx.dev/latest/contributing/contributing/).

Opteryx installs with a small set of libraries it uses, such as [Numpy](https://numpy.org/doc/stable/index.html), [PyArrow](https://arrow.apache.org/), and [orjson](https://github.com/ijl/orjson). Some features require additional libraries to be installed, you are notified of tese libraries as they are required.

## Examples

[Filter a Dataset on the Command Line](#filter-a-dataset-on-the-command-line)  
[Execute a Simple Query in Python](#execute-a-simple-query-in-python)   
[Execute SQL on a pandas DataFrame](#execute-sql-on-a-pandas-dataframe)   
[Query Data on Local Disk](#query-data-on-local-disk)    
[Query Data on GCS](#query-data-on-gcs)  
[Query Data in SQLite](#query-data-in-sqlite)  
<!---[Further Examples](#further-examples)--->

#### Filter a Dataset on the Command Line

In this example, we are running Opteryx from the command line to filter one of the internal example datasets and display the results on the console.

~~~bash
python -m opteryx "SELECT * FROM \$astronauts WHERE 'Apollo 11' IN UNNEST(missions);"
~~~

![Opteryx](https://github.com/mabel-dev/opteryx.dev/raw/main/assets/cli.png)
_this example is complete and should run as-is_

#### Execute a Simple Query in Python  

In this example, we are showing the basic usage of the Python API by executing a simple query that makes no references to any datasets.

~~~python
# Import the Opteryx SQL query engine library.
import opteryx

# Execute a SQL query to evaluate the expression 4 * 7.
# The result is stored in the 'result' variable.
result = opteryx.query("SELECT 4 * 7;")

# Display the first row(s) of the result to verify the query executed correctly.
result.head()
~~~

ID |  4 * 7  
-- | -------
 1 |     28 

_this example is complete and should run as-is_

#### Execute SQL on a pandas DataFrame

In this example, we are running a SQL statement on a pandas DataFrame and returning the result as a new pandas DataFrame.

~~~python
# Required imports
import opteryx
import pandas

# Read data from the exoplanets.csv file hosted on Google Cloud Storage
# The resulting DataFrame is stored in the variable `pandas_df`.
pandas_df = pandas.read_csv("https://storage.googleapis.com/opteryx/exoplanets/exoplanets.csv")

# Register the pandas DataFrame with Opteryx under the alias "exoplanets"
# This makes the DataFrame available for SQL-like queries.
opteryx.register_df("exoplanets", pandas_df)

# Perform an SQL query to group the data by `koi_disposition` and count the number
# of occurrences of each distinct `koi_disposition`.
# The result is stored in `aggregated_df`.
aggregated_df = opteryx.query("SELECT koi_disposition, COUNT(*) FROM exoplanets GROUP BY koi_disposition;").pandas()

# Display the aggregated DataFrame to get a preview of the result.
aggregated_df.head()
~~~
~~~
  koi_disposition  COUNT(*)
0       CONFIRMED      2293
1  FALSE POSITIVE      5023
2       CANDIDATE      2248 
~~~
_this example is complete and should run as-is_

#### Query Data on Local Disk

In this example, we are querying and filtering a file directly. This example will not run as written because the file being queried does not exist.

~~~python
# Import the Opteryx query engine.
import opteryx

# Execute a SQL query to select the first 5 rows from the 'space_missions.parquet' table.
# The result will be stored in the 'result' variable.
result = opteryx.query("SELECT * FROM 'space_missions.parquet' LIMIT 5;")

# Display the result.
# This is useful for quick inspection of the data.
result.head()

~~~

 ID | Company   | Location                       | Price | Launched_at         | Rocket         | Rocket_Status | Mission        | Mission_Status 
--- | --------- | ------------------------------ | ----- | ------------------- | -------------- | ------------- | -------------- | --------------- 
  0 | RVSN USSR | Site 1/5, Baikonur Cosmodrome, |  null | 1957-10-04 19:28:00 | Sputnik 8K71PS | Retired       | Sputnik-1      | Success        
  1 | RVSN USSR | Site 1/5, Baikonur Cosmodrome, |  null | 1957-11-03 02:30:00 | Sputnik 8K71PS | Retired       | Sputnik-2      | Success        
  2 | US Navy   | LC-18A, Cape Canaveral AFS, Fl |  null | 1957-12-06 16:44:00 | Vanguard       | Retired       | Vanguard TV3   | Failure        
  3 | AMBA      | LC-26A, Cape Canaveral AFS, Fl |  null | 1958-02-01 03:48:00 | Juno I         | Retired       | Explorer 1     | Success        
  4 | US Navy   | LC-18A, Cape Canaveral AFS, Fl |  null | 1958-02-05 07:33:00 | Vanguard       | Retired       | Vanguard TV3BU | Failure        


_this example requires a data file, [space_missions.parquet](https://storage.googleapis.com/opteryx/space_missions/space_missions.parquet)._

#### Query Data in SQLite

In this example, we are querying a SQLite database via Opteryx. This example will not run as written because the file being queried does not exist.

~~~python
# Import the Opteryx query engine and the SqlConnector from its connectors module.
import opteryx
from opteryx.connectors import SqlConnector

# Register a new data store with the prefix "sql", specifying the SQL Connector to handle it.
# This allows queries with the 'sql' prefix to be routed to the appropriate SQL database.
opteryx.register_store(
   prefix="sql",  # Prefix for distinguishing this particular store
   connector=SqlConnector,  # Specify the connector to handle queries for this store
   remove_prefix=True,  # Remove the prefix from the table name when querying SQLite
   connection="sqlite:///database.db"  # SQLAlchemy connection string for the SQLite database
)

# Execute a SQL query to select specified columns from the 'planets' table in the SQL store,
# limiting the output to 5 rows. The result is stored in the 'result' variable.
result = opteryx.query("SELECT name, mass, diameter, density FROM sql.planets LIMIT 5;")

# Display the result.
# This is useful for quickly verifying that the query executed correctly.
result.head()

~~~

ID | name    |   mass | diameter | density 
-- | ------- | ------ | -------- | -------
 1 | Mercury |   0.33 |     4879 |    5427 
 2 | Venus   |   4.87 |    12104 |    5243 
 3 | Earth   |   5.97 |    12756 |    5514 
 4 | Mars    |  0.642 |     6792 |    3933 
 5 | Jupiter | 1898.0 |   142984 |    1326 


_this example requires a data file, [database.db](https://storage.googleapis.com/opteryx/planets/database.db)._

#### Query Data on GCS  

In this example, we are to querying a dataset on GCS in a public bucket called 'opteryx'.

~~~python
# Import the Opteryx query engine and the GcpCloudStorageConnector from its connectors module.
import opteryx
from opteryx.connectors import GcpCloudStorageConnector

# Register a new data store named 'opteryx', specifying the GcpCloudStorageConnector to handle it.
# This allows queries for this particular store to be routed to the appropriate GCP Cloud Storage bucket.
opteryx.register_store(
    "opteryx",  # Name of the store to register
    GcpCloudStorageConnector  # Connector to handle queries for this store
)

# Execute a SQL query to select all columns from the 'space_missions' table located in the 'opteryx' store,
# and limit the output to 5 rows. The result is stored in the 'result' variable.
result = opteryx.query("SELECT * FROM opteryx.space_missions LIMIT 5;")

# Display the result.
# This is useful for quickly verifying that the query executed correctly.
result.head()

~~~

 ID | Company   | Location                       | Price | Launched_at         | Rocket         | Rocket_Status | Mission        | Mission_Status 
--- | --------- | ------------------------------ | ----- | ------------------- | -------------- | ------------- | -------------- | --------------- 
  0 | RVSN USSR | Site 1/5, Baikonur Cosmodrome, |  null | 1957-10-04 19:28:00 | Sputnik 8K71PS | Retired       | Sputnik-1      | Success        
  1 | RVSN USSR | Site 1/5, Baikonur Cosmodrome, |  null | 1957-11-03 02:30:00 | Sputnik 8K71PS | Retired       | Sputnik-2      | Success        
  2 | US Navy   | LC-18A, Cape Canaveral AFS, Fl |  null | 1957-12-06 16:44:00 | Vanguard       | Retired       | Vanguard TV3   | Failure        
  3 | AMBA      | LC-26A, Cape Canaveral AFS, Fl |  null | 1958-02-01 03:48:00 | Juno I         | Retired       | Explorer 1     | Success        
  4 | US Navy   | LC-18A, Cape Canaveral AFS, Fl |  null | 1958-02-05 07:33:00 | Vanguard       | Retired       | Vanguard TV3BU | Failure            

_this example is complete and should run as-is_

## Community

[![Discord](https://img.shields.io/badge/discuss%20on-discord-5865F2.svg?logo=discord)](https://discord.gg/PHqKAb9Y)
[![X Follow](https://img.shields.io/badge/follow%20on-x-1DA1F2.svg?logo=X)](https://twitter.com/OpteryxSQL)

**How do I get Support?**

For support ask our [Discord Server](https://discord.gg/PHqKAb9Y).

**How Can I Contribute?**

We are looking for volunteers to help build and direct Opteryx. If you are interested please use the Issues to let use know.

All contributions, [bug reports](https://github.com/mabel-dev/opteryx/issues/new/choose), documentation improvements, enhancements, and [ideas](https://github.com/mabel-dev/opteryx/discussions) are welcome.

Want to help build Opteryx? See the [Contribution](https://opteryx.dev/latest/contributing/contributing/) and [Set Up](https://opteryx.dev/latest/contributing/set-up-guides/debian/) Guides.

## Security

[![Static Analysis](https://github.com/mabel-dev/opteryx/actions/workflows/static_analysis.yaml/badge.svg)](https://github.com/mabel-dev/opteryx/actions/workflows/static_analysis.yml)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=mabel-dev_opteryx&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=mabel-dev_opteryx)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=mabel-dev_opteryx&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=mabel-dev_opteryx)

See the project [Security Policy](SECURITY.md) for information about reporting vulnerabilities.

## License

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/mabel-dev/opteryx/blob/master/LICENSE)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fmabel-dev%2Fopteryx.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fmabel-dev%2Fopteryx?ref=badge_shield)

Opteryx is licensed under [Apache 2.0](https://github.com/mabel-dev/opteryx/blob/master/LICENSE) except where specific module note otherwise.

## Status

[![Status](https://img.shields.io/badge/status-beta-orange)](https://github.com/mabel-dev/opteryx)

Opteryx is in beta. Beta means different things to different people, to us, being beta means:

- Core functionality has good regression test coverage to help ensure stability
- Some edge cases may have undetected bugs
- Performance tuning is incomplete
- Changes are focused on feature completion, bugs, performance, reducing debt, and security
- Code structure and APIs are not stable and may change

## Related Projects

- **[orso](https://github.com/mabel-dev/orso)** DataFrame library
- **[mabel](https://github.com/mabel-dev/mabel)** Streaming data APIs
- **[mesos](https://github.com/mabel-dev/mesos)** MySQL connector for Opteryx