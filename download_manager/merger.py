from pathlib import Path

def merge_chunks(
        chunk_paths: list[Path],
        output_path: Path,
) -> None:
    """
    Merge multiple chunk files into a single output file.

    Args:
        chunk_paths (list[Path]): List of paths to the chunk files.
        output_path (Path): Path to the final merged output file.

    Returns:
        None
    """
    with output_path.open("wb") as output_file:
        for chunk_path in chunk_paths:
            with chunk_path.open("rb") as chunk_file:
                while True:
                    data = chunk_file.read(8192)
                    if not data:
                        break
                    output_file.write(data)

    print(f"Merged {len(chunk_paths)} chunks into {output_path}")

    for chunk_path in chunk_paths:
        chunk_path.unlink()  # Delete the chunk file after merging