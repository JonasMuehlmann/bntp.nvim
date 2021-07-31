#!/usr/bin/env python3


from pathlib import Path


def create_test_file(_self: object, function_name: str, ext: str) -> Path:
    """Create a unique file for a test function.

    The file is composed of the fully qualified function identifier
    (made up of the class hierarchy and function name)

    Args:
        _self: The class the function belongs to
        function_name: The name of the function to create the file for
        ext: The extension of the created file

    Returns:
        Path: A relative path to the newly created file
    """
    Path("tests/data/").mkdir(exist_ok=True)
    file_path: Path = (
        f"tests/data/{_self.__repr__().split(' ')[0][1:]}.{function_name}.{ext}"
    )
    print(file_path)
    with open(file_path, "w+") as f:
        f.write("")

    return file_path
