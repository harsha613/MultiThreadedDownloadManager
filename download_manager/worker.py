import requests

from download_manager.chunk import Chunk

def download_chunk(url: str, chunk: Chunk, output_path: str) -> None:
    """
    Download a specific chunk of a file from the given URL.

    Args:
        url (str): The URL of the file to download.
        chunk (Chunk): The chunk to download.
        output_path (str): The path where the downloaded chunk will be saved.

    Returns:
        None
    """
    headers = {
        "Range": f"bytes={chunk.start}-{chunk.end}"
    }

    response = requests.get(
        url,
        headers=headers,
    )

    response.raise_for_status()

    with open(output_path, "wb") as file:
        file.write(response.content)

    return None
