#!/usr/bin/env python3
"""
Setup script for ferias-cli package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ferias-cli",
    version="1.0.0",
    author="mementomorri",
    description="CLI toolkit for scraping municipal feria data and generating interactive maps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mementomorri/ferias-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "scrape-ferias=scrape_ferias_json:main",
            "generate-ferias-map=generate_ferias_map:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 