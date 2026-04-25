#!/usr/bin/env python

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = [
    "requests>=2.25.0",
    "python-dateutil>=2.8.0",
]

tests_require = [
    "pytest",
]

setup(
    name="currentsapi",
    version="0.1.0",
    author="Currents Dev",
    author_email="ray@currentsapi.services",
    license="MIT",
    url="https://github.com/currentslab/currentsapi-python",
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    tests_require=tests_require,
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
