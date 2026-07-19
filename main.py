from pathlib import Path

from download_manager.downloader import Downloader

def main() -> None:
    url = input("Enter the download URL: ").strip()

    filename = url.split("/")[-1]

    output_directory = Path("downloads")
    output_directory.mkdir(parents=True, exist_ok=True)

    output_path = output_directory / filename

    downloader = Downloader(url, output_path)
    downloader.download()

if __name__ == "__main__":
    main()