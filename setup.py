"""
setup.py: Package configuration for Webook Platform.
Enables absolute package imports across Google Colab, Docker, and local environments.
Run `pip install -e .` to register all packages into the environment.
"""
from setuptools import setup, find_packages
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name="webook-platform",
    version="2.0.0",
    description="Webook Platform & Ingestion Automation",
    author="Webook Platform Team",
    packages=find_packages(),
    py_modules=["main", "bot_runner"],
    package_dir={"": "."},
    python_requires=">=3.8",
    install_requires=[
        # Core runtime requirements
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
