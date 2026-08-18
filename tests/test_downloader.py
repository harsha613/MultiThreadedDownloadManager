from pathlib import Path
from unittest.mock import Mock, patch

from download_manager.downloader import Downloader
from download_manager.utils import FileInfo

def test_downloader_success(tmp_path: Path):
    output_path = tmp_path / "test.bin"

    file_info = FileInfo(
        filename="test.bin",
        file_size=10,
        content_type="application/octet-stream",
        supports_ranges=True,
    )

    with patch.object(
        Downloader,
        "get_file_info",
        return_value=file_info,
    ), patch(
        "download_manager.downloader.download_chunk"
    ) as mock_download_chunk, patch(
        "download_manager.downloader.merge_chunks"
    ) as mock_merge_chunks:

        downloader = Downloader(
            "https://example.com/test.bin",
            output_path,
            num_threads=2,
        )

        downloader.download()

    assert mock_download_chunk.call_count == 2
    mock_merge_chunks.assert_called_once()

def test_downloader_failure_cleanup(tmp_path: Path):
    output_path = tmp_path / "test.bin"

    file_info = FileInfo(
        filename="test.bin",
        file_size=10,
        content_type="application/octet-stream",
        supports_ranges=True,
    )

    def fake_download_chunk(
        url,
        chunk,
        chunk_path,
        progress_callback,
        stop_event,
    ):
        Path(chunk_path).write_bytes(b"partial")

        if chunk.index == 0:
            raise RuntimeError("Download failed")

    with patch.object(
        Downloader,
        "get_file_info",
        return_value=file_info,
    ), patch(
        "download_manager.downloader.download_chunk",
        side_effect=fake_download_chunk,
    ):
        downloader = Downloader(
            "https://example.com/test.bin",
            output_path,
            num_threads=2,
        )

        downloader.download()

    assert not output_path.exists()

    assert not (tmp_path / "test.bin.part0").exists()
    assert not (tmp_path / "test.bin.part1").exists()
        