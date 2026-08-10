from download_manager.chunk import create_chunks


file_size = 10485760
number_of_chunks = 4

chunks = create_chunks(file_size, number_of_chunks)

for chunk in chunks:
    print(
        f"Chunk {chunk.index}: "
        f"{chunk.start} → {chunk.end} "
        f"({chunk.size} bytes)"
    )