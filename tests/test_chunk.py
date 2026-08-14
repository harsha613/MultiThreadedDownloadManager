import pytest
from download_manager.chunk import Chunk, create_chunks

def test_create_chunks_evenly():
    chunks = create_chunks(1000, 4)

    assert len(chunks) == 4

    assert chunks[0].start == 0
    assert chunks[0].end == 249

    assert chunks[1].start == 250
    assert chunks[1].end == 499

    assert chunks[2].start == 500
    assert chunks[2].end == 749

    assert chunks[3].start == 750
    assert chunks[3].end == 999

def test_create_chunks_uneven():
    chunks = create_chunks(1001, 4)

    assert len(chunks) == 4

    assert chunks[0].start == 0
    assert chunks[0].end == 249

    assert chunks[1].start == 250
    assert chunks[1].end == 499

    assert chunks[2].start == 500
    assert chunks[2].end == 749

    assert chunks[3].start == 750
    assert chunks[3].end == 1000

def test_chunks_are_continuous():
    file_size = 1001
    chunks = create_chunks(file_size, 4)

    assert len(chunks) == 4

    for previous, current in zip(chunks, chunks[1:]):
        assert current.start == previous.end + 1

    assert chunks[-1].end == file_size - 1

def test_create_chunks_invalid_file_size():
    with pytest.raises(ValueError):
        create_chunks(0, 4)

    with pytest.raises(ValueError):
        create_chunks(-100, 4)

def test_create_chunks_invalid_number_of_chunks():
    with pytest.raises(ValueError):
        create_chunks(1000, 0)

    with pytest.raises(ValueError):
        create_chunks(1000, -5)

def test_create_chunks_more_chunks_than_file_size():
    with pytest.raises(ValueError):
        create_chunks(3, 4)

def test_chunk_size():
    chunk = Chunk(
        index=0,
        start=100,
        end=199,
    )
    assert chunk.size == 100