#!/usr/bin/env python3
"""
Setup script for Hansard Tales Python Functions
"""

from setuptools import setup, find_packages

setup(
    name="hansard-tales-python-functions",
    version="0.1.0",
    description="Python functions for Hansard Tales data processing and AI analysis",
    author="Hansard Tales Team",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "google-cloud-aiplatform>=1.38.0",
        "google-cloud-storage>=2.10.0",
        "spacy>=3.7.0",
        "pandas>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.0.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
