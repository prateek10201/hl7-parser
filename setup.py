#!/usr/bin/env python3
"""
Setup script for HL7 SIU Parser.
"""

from setuptools import setup, find_packages

setup(
    name="hl7-siu-parser",
    version="1.0.0",
    description="HL7 SIU Parser for Appointments",
    author="",
    author_email="",
    packages=find_packages(),
    py_modules=["hl7_parser"],
    install_requires=[
        "jsonschema>=3.2.0;python_version>='3.8'",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "hl7-parser=hl7_parser:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
)