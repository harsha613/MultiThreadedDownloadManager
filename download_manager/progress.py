import time
import threading

class ProgressTracker:
    "Tracks and displays the progress of a download."

    def __init__(self, total_size: int):
        self.total_size = total_size
        self.downloaded = 0
        self.start_time = time.time()

        self.last_display_time = 0
        self.last_downloaded = 0
        self.last_speed_time = time.time()

        self.lock = threading.Lock()

    def update(self, bytes_downloaded: int) -> None:
        with self.lock:
            self.downloaded += bytes_downloaded

            current_time = time.time()
            if current_time - self.last_display_time >= 1:  # Update every second
                self.last_display_time = current_time
                self._display()

    def _format_speed(self, bytes_per_second: float) -> str:
        """Convert bytes per second to a human-readable format."""
        if bytes_per_second < 1024 :
            return f"{bytes_per_second:.0f} B/s"

        if bytes_per_second < 1024 ** 2:
            return f"{bytes_per_second / 1024:.2f} KB/s"

        return f"{bytes_per_second / (1024 ** 2):.2f} MB/s"

    def _display(self) -> None:

        current_time = time.time()

        elapsed = current_time - self.last_speed_time
        bytes_downloaded = self.downloaded - self.last_downloaded

        if elapsed > 0:
            speed = bytes_downloaded / elapsed
        else:
            speed = 0

        self.last_speed_time = current_time
        self.last_downloaded = self.downloaded

        if self.total_size > 0:
            percentage = (self.downloaded / self.total_size) * 100
        else:
            percentage = 0

        speed_text = self._format_speed(speed)

        print(
            f"\033[2K\rDownloaded: "
            f"{self.downloaded:,} / {self.total_size:,} bytes "
            f"({percentage:.2f}%) "
            f"| Speed: {speed_text}",
            end="",
            flush=True,
        )

    def finish(self) -> None:
        with self.lock:
            self._display()
            print()  # Move to the next line after finishing