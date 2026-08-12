import requests
import time

from download_manager.chunk import Chunk

MAX_RETRIES = 3

def download_chunk(
        url: str,
        chunk: Chunk,
        output_path: str,
        progress_callback=None,
        ) -> None:
    """
    Download a specific chunk of a file from the given URL.

    Args:
        url (str): The URL of the file to download.
        chunk (Chunk): The chunk to download.
        output_path (str): The path where the downloaded chunk will be saved.
        progress_callback (callable, optional): A function to call with download progress updates.

    Returns:
        None
    """
    expected_size = chunk.end - chunk.start + 1

    for attempt in range(MAX_RETRIES):
        try:
            headers = {
                "Range": f"bytes={chunk.start}-{chunk.end}"
            }

            response = requests.get(
                url,
                headers=headers,
                stream=True,
            )

            response.raise_for_status()

            if response.status_code != 206:
                raise requests.RequestException(
                    f"Server did not return partial content: {response.status_code}"
                )

            downloaded_size = 0
            with open(output_path, "wb") as file:
                for data in response.iter_content(chunk_size=8192):
                    if data:
                        file.write(data)
                        downloaded_size += len(data)

                        if progress_callback:
                            progress_callback(len(data))  # Update progress with the number of bytes downloaded

            if downloaded_size != expected_size:
                raise requests.RequestException(
                    f"Downloaded size {downloaded_size} does not match expected size {expected_size}"
                )

            return  # Exit the function if download is successful

        except requests.RequestException as e:
            print(f"Attempt {attempt + 1} failed for chunk {chunk.index}: {e}")

            if attempt == MAX_RETRIES - 1:
                raise  # Re-raise the exception if it's the last attempt

            time.sleep(1)  # Wait for a second before retrying
