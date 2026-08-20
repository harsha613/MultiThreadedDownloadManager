# Multi-Threaded Download Manager

A Python-based HTTP download manager that downloads files concurrently using multiple threads and HTTP byte-range requests.

The downloader divides a file into independent byte ranges, downloads those ranges concurrently, supports resuming partially downloaded chunks, retries failed requests, tracks download progress, and merges the chunks into the final file.

## Features

* Multi-threaded file downloads using `ThreadPoolExecutor`
* HTTP `Range` request support
* Automatic division of files into multiple byte ranges
* Resume support for partially downloaded chunks
* Automatic retry mechanism for failed chunk downloads
* Cooperative cancellation using `threading.Event`
* Real-time download progress and speed display
* Automatic fallback to a single HTTP request when range requests are not supported
* Automatic cleanup of temporary `.part` files after successful merging
* Unit tests using `pytest`
* Command-line interface using `argparse`

## How It Works

The downloader first sends an HTTP `HEAD` request to obtain file metadata such as:

* File size
* Content type
* Whether the server supports byte-range requests

If the server supports range requests, the file is divided into multiple chunks.

For example, a 1000-byte file with four threads is divided into:

```text
Chunk 0: bytes 0-249
Chunk 1: bytes 250-499
Chunk 2: bytes 500-749
Chunk 3: bytes 750-999
```

Each chunk is downloaded concurrently:

```text
                    File
                     │
                     ▼
              create_chunks()
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Chunk 0      Chunk 1      Chunk 2 ... Chunk N
        │            │            │
        ▼            ▼            ▼
      .part0       .part1       .part2
        │            │            │
        └────────────┼────────────┘
                     ▼
               merge_chunks()
                     │
                     ▼
                Final file
```

Each worker sends an HTTP request containing a `Range` header such as:

```text
Range: bytes=250-499
```

The server responds with `206 Partial Content`, and the worker stores the received bytes in a temporary `.part` file.

## Resume Support

If a `.part` file already exists, the downloader checks how many bytes have already been downloaded.

For example:

```text
Requested chunk: 1000-1999
Existing data:    500 bytes
```

The worker resumes from:

```text
bytes=1500-1999
```

instead of downloading the entire chunk again.

If a chunk is already complete, it is skipped.

## Retry and Failure Handling

Each chunk has a maximum of three download attempts.

If a request fails temporarily, the worker waits briefly and retries.

If all attempts fail:

1. The worker signals the shared stop event.
2. Other workers are asked to stop.
3. The downloader cancels pending futures.
4. Partially downloaded chunk files are removed.
5. The download operation terminates without producing an incomplete final file.

## Range Request Fallback

Not every HTTP server supports byte-range requests.

If the server does not advertise:

```text
Accept-Ranges: bytes
```

the downloader falls back to a normal single-request download using streaming:

```text
GET request
   │
   ▼
stream response
   │
   ├── 8192 bytes
   ├── 8192 bytes
   ├── 8192 bytes
   └── ...
   │
   ▼
final file
```

This avoids loading the entire file into memory at once.

## Progress Tracking

The `ProgressTracker` is shared by the worker threads.

It tracks:

* Total bytes
* Downloaded bytes
* Percentage completed
* Current download speed

A `threading.Lock` protects shared progress information because multiple worker threads update it concurrently.

Example:

```text
Downloaded: 10,485,760 / 10,485,760 bytes (100.00%) | Speed: 568.10 KB/s
```

## Project Structure

```text
MultiThreadedDownloadManager/
├── download_manager/
│   ├── __init__.py
│   ├── chunk.py
│   ├── downloader.py
│   ├── merger.py
│   ├── progress.py
│   ├── utils.py
│   └── worker.py
├── tests/
│   ├── test_chunk.py
│   ├── test_downloader.py
│   ├── test_merger.py
│   ├── test_progress.py
│   └── test_worker.py
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

### Module Responsibilities

| Module          | Responsibility                        |
| --------------- | ------------------------------------- |
| `main.py`       | Command-line interface                |
| `downloader.py` | Coordinates the complete download     |
| `chunk.py`      | Creates and validates byte ranges     |
| `worker.py`     | Downloads individual chunks           |
| `progress.py`   | Tracks and displays download progress |
| `merger.py`     | Combines temporary chunks             |
| `utils.py`      | Stores file metadata                  |
| `tests/`        | Automated test suite                  |

## Requirements

* Python 3.10+
* `requests`
* `pytest` for running tests

## Installation

Clone the repository and enter the project directory:

```bash
git clone <your-repository-url>
cd MultiThreadedDownloadManager
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic download:

```bash
python main.py <URL>
```

Example:

```bash
python main.py https://example.com/file.zip
```

Specify the number of threads:

```bash
python main.py https://example.com/file.zip --threads 8
```

Specify an output directory:

```bash
python main.py https://example.com/file.zip --output downloads
```

The number of download threads can be set between 1 and 32.

## Running Tests

Run the complete test suite:

```bash
python -m pytest
```

The project currently contains **30 automated tests** covering chunk creation, downloading, retries, resume behavior, progress tracking, merging, failure handling, and downloader coordination.

## Integration Test

The downloader was also tested against a real 10 MiB file using four concurrent download threads.

Verified output:

```text
File size: 10,485,760 bytes
Download: 100%
Chunks: 4
Merge: successful
```

The resulting file was verified using SHA-256:

```text
7d04fde0818e71734edc44c306e1227e564f3e6d9b129df577066d677e5898a3
```

## Technologies Used

* Python
* `requests`
* `concurrent.futures`
* `threading`
* `dataclasses`
* `pathlib`
* `argparse`
* `pytest`

## Design Considerations

The project uses streaming I/O so that large files do not need to be loaded completely into memory.

Concurrent workers operate on independent byte ranges, while a shared progress tracker provides synchronized download statistics.

The downloader also separates responsibilities across modules, making individual components easier to test and maintain.

## Future Improvements

Possible future enhancements include:

* Download pause and resume from the command line
* Persistent download state
* Bandwidth limiting
* Configurable retry delays
* Concurrent download queues for multiple files
* Checksum verification against a user-provided hash
* More robust filename extraction from HTTP headers
* Packaging as an installable Python application
