from pathlib import Path
from download_manager.merger import merge_chunks

def test_merge_chunks(tmp_path: Path) -> None:
    chunk1 = tmp_path / "chunk1"
    chunk2 = tmp_path / "chunk2"
    chunk3 = tmp_path / "chunk3"

    chunk1.write_bytes(b"Hello ")
    chunk2.write_bytes(b"World")
    chunk3.write_bytes(b"!")

    output = tmp_path / "output.txt"

    merge_chunks(
        [chunk1, chunk2, chunk3],
        output,
    )

    assert output.read_bytes() == b"Hello World!"

    assert not chunk1.exists()
    assert not chunk2.exists()
    assert not chunk3.exists()