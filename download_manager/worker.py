from pathlib import Path

import requests
import time

from download_manager.chunk import Chunk

MAX_RETRIES = 3

def download_chunk(
        url: str,
        chunk: Chunk,
        output_path: str,
        progress_callback=None,
        stop_event=None,
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
        if stop_event and stop_event.is_set():
            return  # Exit if the stop event is set

        try:
            output_file = Path(output_path)
            if output_file.exists():
                existing_size = output_file.stat().st_size

                if existing_size > expected_size:
                    raise ValueError(
                        f"Existing chunk size {existing_size} exceeds "
                        f"expected size {expected_size}"
                    )

                if existing_size == expected_size:
                    return
            else:
                existing_size = 0

            resume_from = chunk.start + existing_size
            headers = {
                "Range": f"bytes={resume_from}-{chunk.end}"
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
            with output_file.open("ab") as file:
                for data in response.iter_content(chunk_size=8192):
                    if stop_event and stop_event.is_set():
                        return  # Exit if the stop event is set

                    if data:
                        file.write(data)
                        downloaded_size += len(data)

                        if progress_callback:
                            progress_callback(len(data))  # Update progress with the number of bytes downloaded

            if existing_size + downloaded_size != expected_size:
                raise requests.RequestException(
                    f"Downloaded size {downloaded_size} does not match expected size {expected_size}"
                )

            return  # Exit the function if download is successful

        except requests.RequestException as e:
            print(f"\nAttempt {attempt + 1} failed for chunk {chunk.index}: {e}")

            if attempt == MAX_RETRIES - 1:
                if stop_event:
                    stop_event.set()  # Signal to stop other threads if this is the last attempt
                raise  # Re-raise the exception if it's the last attempt

            time.sleep(1)  # Wait for a second before retrying
