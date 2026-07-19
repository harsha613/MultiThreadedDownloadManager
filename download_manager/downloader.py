from pathlib import Path
import requests

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
