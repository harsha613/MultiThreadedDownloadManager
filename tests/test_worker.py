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