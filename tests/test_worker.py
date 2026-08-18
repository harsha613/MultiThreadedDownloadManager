import requests
import pytest
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