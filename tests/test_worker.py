import requests
import pytest
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from download_manager.chunk import Chunk
from download_manager.worker import download_chunk

def test_download_chunk_success(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=9,
    )

    response = Mock()
    response.status_code = 206
    response.iter_content.return_value = [b"Hello", b"World"]

    progress_callback = Mock()

    with patch("download_manager.worker.requests.get",return_value=response) as mock_get:
        download_chunk(
            "https://example.com/file",
            chunk,
            output_path,
            progress_callback,
        )

    assert output_path.read_bytes() == b"HelloWorld"

    mock_get.assert_called_once_with(
        "https://example.com/file",
        headers={"Range": "bytes=0-9"},
        stream=True,
    )

    assert progress_callback.call_count == 2
    assert progress_callback.call_args_list[0].args == (5,)
    assert progress_callback.call_args_list[1].args == (5,)

def test_download_chunk_resume(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=9,
    )

    #simulate that the first 5 bytes were already downloaded.
    output_path.write_bytes(b"Hello")

    response = Mock()
    response.status_code = 206
    response.iter_content.return_value = [b"World"]

    with patch(
        "download_manager.worker.requests.get",
        return_value=response,
    )as mock_get:
        download_chunk(
            "https://example.com/file",
            chunk,
            str(output_path),
        )

    assert output_path.read_bytes() == b"HelloWorld"

    mock_get.assert_called_once_with(
        "https://example.com/file",
        headers={"Range": "bytes=5-9"},
        stream=True,
    )

def test_download_chunk_retry(tmp_path: Path):
    output_path = tmp_path/"chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=4,
    )

    response = Mock()
    response.status_code = 206
    response.iter_content.return_value = [b"Hello"]

    with patch(
        "download_manager.worker.requests.get",
        side_effect=[
            requests.RequestException("Temporary failure"),
            response,
        ]
    ) as mock_get:
        download_chunk(
            "https://example.com/file",
            chunk,
            str(output_path),
        )

    assert output_path.read_bytes() == b"Hello"
    assert mock_get.call_count == 2

def test_download_chunk_max_retries(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=4,
    )

    with patch(
        "download_manager.worker.requests.get",
        side_effect=requests.RequestException("Permanent failure"),
    ) as mock_get:

        with pytest.raises(requests.RequestException, match="Permanent failure"):
            download_chunk(
                "https://example.com/files",
                chunk,
                str(output_path),
            )

    assert mock_get.call_count == 3

def test_download_chunk_already_complete(tmp_path: Path):
    output_file = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=4,
    )

    #The complete 5-bytes chunk already exists.
    output_file.write_bytes(b"Hello")

    with patch(
        "download_manager.worker.requests.get"
    ) as mock_get:
        download_chunk(
            "https://example.com/file",
            chunk,
            str(output_file),
        )

    mock_get.assert_not_called()

    assert output_file.read_bytes() == b"Hello"

def test_download_chunk_resumes_partial_file(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=100,
        end=109,
    )

    # First 5 bytes of the chunk already exist.
    output_path.write_bytes(b"12345")

    response = Mock()
    response.status_code = 206
    response.iter_content.return_value = [b"67890"]

    with patch(
        "download_manager.worker.requests.get",
        return_value=response,
    ) as mock_get:

        download_chunk(
            "https://example.com/file",
            chunk,
            output_path,
        )

    mock_get.assert_called_once_with(
        "https://example.com/file",
        headers={"Range": "bytes=105-109"},
        stream=True,
    )

    assert output_path.read_bytes() == b"1234567890"

def test_download_chunk_rejects_oversized_file(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=4,
    )

    # Expected size = 5 bytes, but existing file is 6 bytes.
    output_path.write_bytes(b"123456")

    with patch(
        "download_manager.worker.requests.get"
    ) as mock_get:

        with pytest.raises(
            ValueError,
            match="exceeds expected size",
        ):
            download_chunk(
                "https://example.com/file",
                chunk,
                str(output_path),
            )

    mock_get.assert_not_called()

def test_download_chunk_stop_before_download(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=9,
    )

    stop_event = threading.Event()
    stop_event.set()

    with patch(
        "download_manager.worker.requests.get",
    ) as mock_get:

        download_chunk(
            "https://example.com/file",
            chunk,
            str(output_path),
            stop_event=stop_event,
        )

    mock_get.assert_not_called()
    assert not output_path.exists()

def test_download_chunk_stops_during_download(tmp_path: Path):
    output_path = tmp_path / "chunk.part"

    chunk = Chunk(
        index=0,
        start=0,
        end=9,
    )

    stop_event = threading.Event()

    response = Mock()
    response.status_code = 206

    def generate_data():
        yield b"12345"
        stop_event.set()
        yield b"67890"

    response.iter_content.return_value = generate_data()

    with patch(
        "download_manager.worker.requests.get",
        return_value=response,
    ):

        download_chunk(
            "https://example.com/file",
            chunk,
            str(output_path),
            stop_event=stop_event,
        )

    assert output_path.read_bytes() == b"12345"