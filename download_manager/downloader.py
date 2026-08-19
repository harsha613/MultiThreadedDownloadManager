from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
import threading

from download_manager.utils import FileInfo
from download_manager.progress import ProgressTracker
from download_manager.chunk import create_chunks
from download_manager.worker import download_chunk
from download_manager.merger import merge_chunks

class Downloader:

    CHUNK_SIZE = 8192

    def __init__(
        self,
        url: str,
        output_path: Path,
        num_threads: int = 4,
        ):
        self.url = url
        self.output_path = output_path
        self.num_threads = num_threads

    def download(self) -> None:
        """
        Download the file to specified output path,
        using multiple threads if the server supports range requests.
        """
        file_info = self.get_file_info()

        if not file_info.supports_ranges:
            self.download_single()
            return

        tracker = ProgressTracker(file_info.file_size)

        stop_event = threading.Event()

        print(f"File: {file_info.filename}")
        print(f"Size: {file_info.file_size} bytes")

        chunks = create_chunks(
            file_info.file_size,
            self.num_threads,
        )

        print(f"Created {len(chunks)} chunks for download.")

        chunk_paths = [
            self.output_path.with_suffix(
                f"{self.output_path.suffix}.part{chunk.index}"
            )
            for chunk in chunks
        ]

        with ThreadPoolExecutor(
            max_workers=self.num_threads
        ) as executor:

            futures = []

            for chunk, chunk_path in zip(chunks, chunk_paths):
                future = executor.submit(
                    download_chunk,
                    self.url,
                    chunk,
                    str(chunk_path),
                    tracker.update,
                    stop_event,
                )
                futures.append(future)

            for future in futures:
                try:
                    future.result()  # wait for the download or throw an exception if it failed
                except Exception as e:
                    print(f"Error downloading chunk: {e}")

                    for f in futures:
                        f.cancel()  # Cancel all other futures if one fails

                    for chunk_path in chunk_paths:
                        if Path(chunk_path).exists():
                            Path(chunk_path).unlink()  # Clean up any partially downloaded chunks
                    return  # Exit if any chunk fails to download

        tracker.finish()

        merge_chunks(chunk_paths, self.output_path,)
        print(f"Download completed and merged into {self.output_path}")

    def download_single(self) -> None:
        """Download the entire file using single HTTP request."""

        response = requests.get(self.url, stream=True)
        response.raise_for_status()

        with self.output_path.open("wb") as output_file:
            for data in response.iter_content(chunk_size=8192):
                if data:
                    output_file.write(data)
        print(f"Download completed: {self.output_path}")

    def get_file_info(self) -> FileInfo:
        """
        Retrieve file metadata without downloading the entire file.
        """
        response = requests.head(self.url, allow_redirects=True)
        response.raise_for_status()

        headers = response.headers

        content_length = headers.get("Content-Length")

        if content_length is None:
            raise ValueError("Server did not provide Content-Length")

        file_size = int(content_length)

        content_type = headers.get(
            "Content-Type",
            "application/octet-stream"
        )

        supports_ranges = (
            headers.get("Accept-Ranges", "").lower() == "bytes"
        )

        filename = self.output_path.name

        return FileInfo(
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            supports_ranges=supports_ranges
        )