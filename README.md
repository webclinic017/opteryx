<img align="centre" alt="archaeopteryx" height="104" src="opteryx.png" />

## Query your data, no database required

[Documentation](https://mabel-dev.github.io/opteryx/) |
[Examples](notebooks) |
[Contributing](https://mabel-dev.github.io/opteryx/Contributing%20Guide/CONTRIBUTING/)

> **NOTE**  
> Opteryx is an beta product. Beta means different things to different people, to us, being beta means:
>
> - Functionality is stable and any updates should be to address bugs and performance
> - Core functionality has test cases to ensure stability
> - Some edge cases may have undetected bugs
> - Performance tuning may be incomplete

[![Status](https://img.shields.io/badge/status-beta-blue)](https://github.com/mabel-dev/opteryx)
[![Regression Suite](https://github.com/mabel-dev/opteryx/actions/workflows/regression_suite.yaml/badge.svg)](https://github.com/mabel-dev/opteryx/actions/workflows/regression_suite.yaml)
[![Static Analysis](https://github.com/mabel-dev/opteryx/actions/workflows/static_analysis.yml/badge.svg)](https://github.com/mabel-dev/opteryx/actions/workflows/static_analysis.yml)
[![PyPI Latest Release](https://img.shields.io/pypi/v/opteryx.svg)](https://pypi.org/project/opteryx/)
[![opteryx](https://snyk.io/advisor/python/opteryx/badge.svg?style=flat-square)](https://snyk.io/advisor/python/opteryx)
[![Downloads](https://pepy.tech/badge/opteryx)](https://pepy.tech/project/opteryx)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![commit_freq](https://img.shields.io/github/commit-activity/m/mabel-dev/opteryx)](https://github.com/mabel-dev/opteryx/commits)
[![last_commit](https://img.shields.io/github/last-commit/mabel-dev/opteryx)](https://github.com/mabel-dev/opteryx/commits)
[![codecov](https://codecov.io/gh/mabel-dev/opteryx/branch/main/graph/badge.svg?token=sIgKpzzd95)](https://codecov.io/gh/mabel-dev/opteryx)

## What is Opteryx

Opteryx is a distributed SQL Engine designed for cloud-native environments.

**Scalable**

Designed to run in Knative and similar environments like Google Cloud Run, Opteryx can scale down to zero, or scale up to respond to thousands of concurrent queries within seconds.

**High Availability**

Each query can run in a separate container instance, meaning it's nearly impossible for a rogue query to affect any other users.

No matter if a cluster, region or datacentre goes down, Opteryx can keep responding to queries.  
_(inflight queries may not be recovered)_

**Bring your own Files**

Opteryx supports many popular data formats, including Parquet and JSONL, stored on local disk or on Cloud Storage. You can mix and match formats, one dataset can be Parquet and another JSONL, and Opteryx will be able to JOIN across these datasets.

**Consumption-Based Billing**

Opteryx is designed for deployments to environments which are pay-as-you-use, like Google Cloud Run. Great for situations where you low-volume usage, or many environments, where the costs of a traditional database deployment would quickly compound.

**Python Native**

Opteryx is an Open Source Python library, it quickly and easily integrates into Python code, you can start querying your data within a few minutes.

**Time Travel**

Designed for data analytics in environments where decisions need to be replayable, Opteryx allows you to query data as at a point in time in the past to replay decision algorithms against facts as they were known in the past.  
_(data must be structured to enable temporal queries)_

## How Can I Contribute?

All contributions, [bug reports](https://github.com/mabel-dev/opteryx/issues/new/choose), bug fixes, documentation improvements, enhancements, and [ideas](https://github.com/mabel-dev/opteryx/issues/new/choose) are welcome.

If you have a suggestion for an improvement or a bug, [raise a ticket](https://github.com/mabel-dev/opteryx/issues/new/choose) or start a [discussion](https://github.com/mabel-dev/opteryx/discussions).

Want to help build Opteryx? See the [Contribution Guide](https://mabel-dev.github.io/opteryx/Contributing%20Guide/CONTRIBUTING/).

## Security

See the project [security policy](SECURITY.md) for information about reporting vulnerabilities.

## License

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/mabel-dev/opteryx/blob/master/LICENSE)
