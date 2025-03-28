import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from typing import Callable, List, Set

from cannonball.document import Document


class MarkdownWatcher(FileSystemEventHandler):
    def __init__(self, file_paths: List[Path], callback: Callable[["MarkdownWatcher", Path], None]):
        self.callback = callback
        self.watched_files = set(map(lambda p: p.resolve(), file_paths))
        self.paused_files: Set[Path] = set()
        self.directories = {p.resolve().parent for p in file_paths}
        self.observer = Observer()

    def on_modified(self, event):
        path = Path(event.src_path).resolve()
        if path in self.watched_files and path not in self.paused_files:
            self.callback(self, path)

    def start(self):
        for directory in self.directories:
            self.observer.schedule(self, str(directory), recursive=False)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def pause(self, path: Path):
        self.paused_files.add(path.resolve())

    def resume(self, path: Path):
        self.paused_files.discard(path.resolve())

    def resume_later(self, path: Path, delay: float = 0.1):
        def _resume():
            time.sleep(delay)
            self.resume(path)

        threading.Thread(target=_resume).start()


if __name__ == "__main__":
    import argparse
    import glob

    def on_change(watcher: MarkdownWatcher, path: Path):
        print(f"File changed: {path}")
        document = Document(path.read_text())

        watcher.pause(path)
        with open(path, "w") as f:
            f.write(document.to_markdown(indent="\t"))
        watcher.resume_later(path)

    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="Markdown files to watch (supporting glob patterns)")
    args = parser.parse_args()

    files = []
    for pattern in args.paths:
        files.extend(map(Path, glob.glob(pattern)))

    watcher = MarkdownWatcher(files, on_change)
    try:
        watcher.start()
        print("Watching for file changes... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
