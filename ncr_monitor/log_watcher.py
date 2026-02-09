import time
from typing import Generator, Optional

from .log_parser import LogParser
from .models import LogEvent

class LogWatcher:
    """
    Monitors a log file for new entries, similar to `tail -f`.
    Yields parsed LogEvent objects as they are added to the file.
    """
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.parser = LogParser() # Initialize LogParser

    def stream(self) -> Generator[LogEvent, None, None]:
        """
        Generator that continuously yields new LogEvent objects from the log file.
        It starts reading from the end of the file when initialized.
        """
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to the end of the file initially
                f.seek(0, 2)

                while True:
                    line = f.readline()
                    if not line:
                        # No new line, wait a bit and try again
                        time.sleep(0.1)
                        continue

                    event = self.parser.parse_log_line(line)
                    if event:
                        yield event
        except FileNotFoundError:
            print(f"Error: Log file not found at {self.log_file}")
            return
        except KeyboardInterrupt:
            print(f"Monitoring of {self.log_file} stopped by user.")
            return
