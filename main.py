import argparse
from pathlib import Path

from download_manager.downloader import Downloader

def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-threaded file downloader.")
    parser.add_argument(
        "url",
        type=str,
        help="The URL of the file to download.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        choices=range(1, 33),
        help="Number of threads to use for downloading (1-32, default: 4).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("downloads"),
        help="Directory to save the downloaded file (default: downloads).",
    )

    args = parser.parse_args()
    url = args.url
    num_threads = args.threads

    filename = url.split("/")[-1]

    output_directory = args.output
    output_directory.mkdir(parents=True, exist_ok=True)

    output_path = output_directory / filename

    downloader = Downloader(url, output_path, num_threads)
    downloader.download()

if __name__ == "__main__":
    main()