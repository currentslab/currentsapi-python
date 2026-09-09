#!/usr/bin/env python

import re
from pathlib import Path

from setuptools import setup, find_packages

ROOT = Path(__file__).parent

with (ROOT / "README.md").open(encoding="utf-8") as fh:
    long_description = fh.read()

with (ROOT / "currentsapi" / "__init__.py").open(encoding="utf-8") as fh:
    version = re.search(r'^__version__ = "(.*?)"$', fh.read(), re.MULTILINE).group(1)

extras_require = {
    "dev": [
        "pytest",
    ],
}

install_requires = [
    "requests>=2.25.0",
    "python-dateutil>=2.8.0",
]

setup(
    name="currentsapi",
    version=version,
    author="Currents Dev",
    author_email="ray@currentsapi.services",
    license="MIT",
    url="https://github.com/currentslab/currentsapi-python",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    extras_require=extras_require,
    description="Official Python client for the Currents API",
    keywords=["currentsapi", "news", "wrapper", "currents", "api"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Information Technology",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)
