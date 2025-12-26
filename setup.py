#!/usr/bin/env python3
from setuptools import setup

setup(
    name="web-noise",
    version="2.0.0",
    description="Generate realistic web traffic noise for privacy",
    author="AcidDemon",
    py_modules=["noise_generator"],
    install_requires=[
        "requests",
        "urllib3",
    ],
    entry_points={
        "console_scripts": [
            "web-noise=noise_generator:main",
        ],
    },
    python_requires=">=3.6",
)
