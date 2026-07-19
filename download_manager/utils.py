from dataclasses import dataclass

@dataclass
class FileInfo:
    """Class for keeping track of a file's information."""
    filename: str
    file_size: int
    content_type: str
    supports_ranges: bool