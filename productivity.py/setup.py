#!/bin/env python3
# noqa: D100

import setuptools  # type: ignore

with open("../README.md", "r", encoding="utf-8") as readme:
    long_description = readme.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.readlines()

__version__ = "0.1.1"

setuptools.setup(
    name="pyaoi",
    version=__version__,
    author="Jonas Muehlmann",
    author_email="jonasmuehlmann@protonmail.com",
    description="My personal, library/CLI/Neovim based, all-in-one productivity system including components like bookmarks, notes, todos, projects, etc.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JonasMuehlmann/productivity.nvim",
    packages=setuptools.find_packages("productivity.py"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
)
