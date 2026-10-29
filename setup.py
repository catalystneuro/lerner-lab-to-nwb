# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="lerner-lab-to-nwb",
    version="0.2.0",
    description="NWB conversion scripts, functions, and classes for Lerner conversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="CatalystNeuro",
    author_email="ben.dichter@catalystneuro.com",
    url="https://github.com/catalystneuro/lerner-lab-to-nwb",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.8",
)
