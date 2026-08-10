from dataclasses import dataclass

@dataclass
class Chunk:
    """Represents a byte range of a file to be downloaded."""

    index: int
    start: int
    end: int

    @property
    def size(self) -> int:
        """Return the size of the chunk in bytes."""
        return self.end - self.start + 1

def create_chunks(file_size: int, number_of_chunks: int) -> list[Chunk]:
    """Divide the file into chunks based on the specified number of chunks."""

    chunks = []
    chunk_size = file_size // number_of_chunks

    for i in range(number_of_chunks):
        start = i * chunk_size

        if i == number_of_chunks - 1:
            end = file_size - 1
        else:
            end = start + chunk_size - 1

        chunks.append(Chunk(index=i, start=start, end=end))

    return chunks