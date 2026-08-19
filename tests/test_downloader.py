import pytest
import requests
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

def test_downloader_without_range_support(tmp_path: Path):
    output_path = tmp_path / "test.bin"

    file_info = FileInfo(
        filename="test.bin",
        file_size=10,
        content_type="application/octet-stream",
        supports_ranges=False,
    )

    with patch.object(
        Downloader,
        "get_file_info",
        return_value=file_info,
    ), patch.object(
        Downloader,
        "download_single",
    ) as mock_download_single, patch(
        "download_manager.downloader.create_chunks",
    ) as mock_create_chunks:

        downloader = Downloader(
            "https://example.com/test.bin",
            output_path,
            num_threads=4,
        )

        downloader.download()

    mock_download_single.assert_called_once()
    mock_create_chunks.assert_not_called()

def test_download_single(tmp_path: Path):
    output_path = tmp_path / "test.bin"

    response = Mock()
    response.iter_content.return_value = [
        b"Hello",
        b"World",
    ]

    with patch(
        "download_manager.downloader.requests.get",
        return_value=response,
    ) as mock_get:

        download = Downloader(
            "https://example.com/test.bin",
            output_path,
        )

        download.download_single()

    response.raise_for_status.assert_called_once()

    mock_get.assert_called_once_with(
        "https://example.com/test.bin",
        stream=True,
    )

    assert output_path.read_bytes() == b"HelloWorld"

def test_get_file_info_http_error():
    response = Mock()

    error = requests.HTTPError("404 Not Found")
    response.raise_for_status.side_effect = error

    with patch(
        "download_manager.downloader.requests.head",
        return_value=response,
    ) as mock_head:

        downloader = Downloader(
            "https://example.com/missing.bin",
            Path("downloads/missing.bin"),
        )

        with pytest.raises(requests.HTTPError):
            downloader.get_file_info()

    mock_head.assert_called_once_with(
        "https://example.com/missing.bin",
        allow_redirects=True,
    )

def test_get_file_info_missing_content_length():
    response = Mock()

    response.headers = {
        "Content-Type": "application/octet-stream",
        "Accept-Ranges": "bytes",
    }

    with patch(
        "download_manager.downloader.requests.head",
        return_value=response,
    ):

        downloader = Downloader(
            "https://example.com/file.bin",
            Path("downloads/file.bin"),
        )

        with pytest.raises(
            ValueError,
            match="did not provide Content-Length",
        ):
            downloader.get_file_info()

def test_get_file_info_invalid_content_length():
    response = Mock()

    response.headers = {
        "Content-Length": "abc",
        "Content-Type": "application/octet-stream",
        "Accept-Ranges": "bytes",
    }

    with patch(
        "download_manager.downloader.requests.head",
        return_value=response,
    ):
        downloader = Downloader(
            "https://example.com/file.bin",
            Path("downloads/file.bin"),
        )

        with pytest.raises(ValueError):
            downloader.get_file_info()

@pytest.mark.parametrize(
    "accept_ranges, expected",
    [
        ("bytes", True),
        ("none", False),
        (None, False),
    ],
)
def test_get_file_info_supports_ranges(accept_ranges, expected):
    response = Mock()

    headers = {
        "Content-Length": "1000",
        "Content-Type": "application/octet-stream",
    }

    if accept_ranges is not None:
        headers["Accept-Ranges"] = accept_ranges

    response.headers = headers

    with patch(
        "download_manager.downloader.requests.head",
        return_value=response,
    ):
        downloader = Downloader(
            "https://example.com/file.bin",
            Path("downloads/file.bin"),
        )

        file_info = downloader.get_file_info()

    assert file_info.supports_ranges is expected