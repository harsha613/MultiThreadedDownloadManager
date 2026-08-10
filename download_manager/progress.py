import time

class ProgressTracker:
    "Tracks and displays the progress of a download."

    def __init__(self, total_size: int):
        self.total_size = total_size
        self.downloaded = 0
        self.start_time = time.time()

    def update(self, bytes_downloaded: int) -> None:
        self.downloaded += bytes_downloaded
        self._display()

    def _format_speed(self, bytes_per_second: float) -> str:
        """Convert bytes per second to a human-readable format."""
        if bytes_per_second < 1024 :
            return f"{bytes_per_second:.0f} B/s"

        if bytes_per_second < 1024 ** 2:
            return f"{bytes_per_second / 1024:.2f} KB/s"

        return f"{bytes_per_second / (1024 ** 2):.2f} MB/s"

    def _display(self) -> None:
        elapsed = time.time() - self.start_time

        if elapsed > 0:
            speed = self.downloaded / elapsed
        else:
            speed = 0

        if self.total_size > 0:
            percentage = (self.downloaded / self.total_size) * 100
        else:
            percentage = 0

        speed_text = self._format_speed(speed)

        print(
            f"\rDownloaded: "
            f"{self.downloaded:,} / {self.total_size:,} bytes "
            f"({percentage:.2f}%) "
            f"| Speed: {speed_text}",
            end="",
            flush=True,
        )

    def finish(self) -> None:
        print()