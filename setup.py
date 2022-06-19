import numpy as np
from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup

with open("opteryx/version.py", "r") as v:
    vers = v.read()
exec(vers)  # nosec

with open("README.md", "r") as rm:
    long_description = rm.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

extensions = [
    Extension(
        name="cjoin",
        sources=["opteryx/third_party/pyarrow_ops/cjoin.pyx"],
        include_dirs=[np.get_include()],
    ),
    Extension(
        name="counting_tree",
        sources=["opteryx/sketches/counting_tree.pyx"],
        include_dirs=["opteryx/sketches"],
    ),
]

setup(
    name="opteryx",
    version=__version__,
    description="Python SQL Query Engine for Serverless Environments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    maintainer="Joocer",
    author="joocer",
    author_email="justin.joyce@joocer.com",
    packages=find_packages(include=["opteryx", "opteryx.*"]),
    package_data={"opteryx.sketches": ["counting_tree.pyx"]},
    url="https://github.com/mabel-dev/opteryx/",
    install_requires=required,
    ext_modules=cythonize(extensions),
)
