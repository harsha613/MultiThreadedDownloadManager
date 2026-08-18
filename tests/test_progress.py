from download_manager.progress import ProgressTracker

def test_progress_tracker_initial_state():
    tracker = ProgressTracker(1000)

    assert tracker.total_size == 1000
    assert tracker.downloaded == 0

def test_progress_tracker_update():
    tracker = ProgressTracker(1000)

    tracker.update(250)

    assert tracker.downloaded == 250

    tracker.update(300)

    assert tracker.downloaded == 550

def test_format_speed():
    tracker = ProgressTracker(1000)

    assert tracker._format_speed(500) == "500 B/s"
    assert tracker._format_speed(2048) == "2.00 KB/s"
    assert tracker._format_speed(2 * 1024 ** 2) == "2.00 MB/s"