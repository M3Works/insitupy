
def yaml_file_in_list(filename: str, file_paths: str) -> bool:
    """
    Checks whether a file name is present in the path

    Args:
        filename (str): File name
        file_paths (str): List of absolute file path

    Returns:
        Boolean - File is present in the path
    """
    return any(
        [filename in str(file_path) for file_path in file_paths]
    )
