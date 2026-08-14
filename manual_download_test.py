from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from download_manager.merger import merge_chunks
from download_manager.chunk import create_chunks
from download_manager.worker import download_chunk

url = "https://proof.ovh.net/files/10Mb.dat"

file_size = 10 * 1024 * 1024  # 10 MB
number_of_chunks = 4

chunks = create_chunks(file_size, number_of_chunks)

with ThreadPoolExecutor(max_workers=number_of_chunks) as executor:
    for chunk in chunks:
        output_path = f"downloads/10Mb.dat.part{chunk.index}"

        future = executor.submit(
            download_chunk,
            url,
            chunk,
            output_path,
        )

        future.result()  # retrieves the result or raises an exception if the download failed

print("All chunks downloaded successfully.")

chunks_path = [
    Path(f"downloads/10Mb.dat.part{i}")
    for i in range(number_of_chunks)
]

output_path = Path("downloads/10Mb.dat")
merge_chunks(chunks_path, output_path)

print(f"File merged successfully into {output_path}")