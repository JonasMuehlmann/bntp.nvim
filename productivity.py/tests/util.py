#!/usr/bin/env python3


from pathlib import Path


def create_test_file(_self, name: str, ext: str) -> Path:
    """Create an empty file with the specified extension, based on the methods name and in ./data/ and return it's relative path"""
    file_path: Path = f"tests/data/{_self.__repr__().split(' ')[0][1:]}.{name}.{ext}"
    print(file_path)
    with open(file_path, "w+") as f:
        f.write("")

    return file_path
