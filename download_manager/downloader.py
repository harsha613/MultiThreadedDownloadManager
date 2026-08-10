from pathlib import Path
import requests

from download_manager.utils import FileInfo

class Downloader:

    CHUNK_SIZE = 8192

    def __init__(self, url: str, output_path: Path):
        self.url = url
        self.output_path = output_path

    def download(self) -> None:

        response = requests.get(self.url, stream=True)

        response.raise_for_status()

        with self.output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

        print(f"Downloaded completed: {self.output_path}")

    def get_file_info(self) -> FileInfo:
        """
        Retrieve file metadata without downloading the entire file.
        """
        response = requests.head(self.url, allow_redirects=True)
        response.raise_for_status()
        headers = response.headers

        file_size = int(headers.get("Content-Length", 0))

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