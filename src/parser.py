import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Generator
from .models import LogEvent, EventType


class LogParser:
    # Regex to match the start of a log line: [YYYY-MM-DD HH:MM:SS:MS][INFO]:
    # Example:
    # [2026-01-30 18:43:08:538][INFO]: TID(...) [ScoAdapter] CONTENT [
    LOG_START_PATTERN = re.compile(
        r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}:\d{3})\]\[INFO\]:.*?"
        r"\[ScoAdapter\] CONTENT \[(.*)",
        re.DOTALL
    )

    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> List[LogEvent]:
        events = []
        raw_blocks = self._read_log_blocks()

        for timestamp, content in raw_blocks:
            event = self._process_content(timestamp, content)
            if event:
                events.append(event)

        return events

    def follow(self) -> Generator[LogEvent, None, None]:
        """
        Follows the log file for new entries (tail -f style).
        Yields events as they are parsed.
        """
        import time
        f = None
        try:
            f = open(self.file_path, 'r', encoding='utf-8')
            f.seek(0, 2)  # Seek to end of file

            buffer = []
            current_timestamp = None

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                match = self.LOG_START_PATTERN.match(line)
                if match:
                    # Found a new log entry start.
                    # If we were buffering a previous one, it implies it's done
                    # (or failed/malformed if it wasn't yielded yet).
                    # We simply reset for the new block.
                    current_timestamp = match.group(1)
                    buffer = [match.group(2)]
                else:
                    if current_timestamp:
                        buffer.append(line)

                # Attempt to process if it looks complete
                if current_timestamp and buffer:
                    # Optimization: Check specifically for the closing bracket
                    # which is characteristic of the log format CONTENT [...]
                    combined_content = "".join(buffer).strip()
                    if combined_content.endswith(']'):
                        # Try to parse
                        event = self._process_content(
                            current_timestamp, combined_content
                        )
                        if event:
                            yield event
                            # Reset buffer to avoid re-parsing
                            current_timestamp = None
                            buffer = []

        except FileNotFoundError:
            print(f"Error: File {self.file_path} not found.")
            return
        except KeyboardInterrupt:
            if f:
                f.close()
            return

    def _read_log_blocks(self) -> Generator[tuple[str, str], None, None]:
        """
        Reads the file and yields tuples of (timestamp, content_string).
        Handles multiline log entries.
        """
        current_timestamp = None
        buffer = []

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    match = self.LOG_START_PATTERN.match(line)
                    if match:
                        # If we have a previous block, yield it
                        if current_timestamp:
                            yield current_timestamp, "".join(buffer)

                        # Start new block
                        current_timestamp = match.group(1)
                        # The regex group 2 captures the start of the content
                        buffer = [match.group(2)]
                    else:
                        # Continuation of previous block
                        if current_timestamp:
                            buffer.append(line)

                # Yield the last block
                if current_timestamp and buffer:
                    yield current_timestamp, "".join(buffer)
        except FileNotFoundError:
            print(f"Error: File {self.file_path} not found.")
            return

    def _process_content(
        self, timestamp: str, content: str
    ) -> Optional[LogEvent]:
        """
        Parses the XML content inside the log block and maps it to an Event.
        The content is expected to end with a closing ']',
        which needs to be stripped.
        """
        stripped_content = content.strip()
        if stripped_content.endswith(']'):
            xml_string = stripped_content[:-1]
        else:
            # Fallback or malformed
            xml_string = stripped_content

        try:
            # Clean up potential leading/trailing whitespace around XML
            xml_string = xml_string.strip()
            if not xml_string:
                return None

            root = ET.fromstring(xml_string)

            message_id = root.get('id')
            message_name = root.get('name')

            # Extract fields
            details = {}
            fields_node = root.find('fields')
            if fields_node is not None:
                for field in fields_node.findall('field'):
                    key = field.get('name')
                    # Handle types if needed
                    ftype = field.get('ftype')
                    value = field.text

                    if ftype == 'int':
                        try:
                            value = int(value)
                        except (ValueError, TypeError):
                            pass
                    elif ftype == 'boolean':
                        value = True if value == '1' else False

                    if key:
                        details[key] = value

            # Determine Event Type
            event_type = None

            if message_id == "StartTransaction":
                event_type = EventType.TRANSACTION_START
            elif message_id == "ItemSold":
                event_type = EventType.ITEM_PICKED
            elif message_id == "DataNeeded":
                # Check for EnterAssistMode
                if details.get("EnterAssistMode") == 1:
                    event_type = EventType.INTERVENTION_START
            elif message_name == "DataNeededReply":
                event_type = EventType.INTERVENTION_FINISH
            elif message_name == "EnterTenderMode":
                event_type = EventType.PAYMENT_START
            elif message_id == "EndTransaction":
                event_type = EventType.PAYMENT_FINISH

            if event_type:
                return LogEvent(
                    timestamp=timestamp,
                    event_type=event_type,
                    details=details
                )

        except ET.ParseError:
            # print(f"Warning: XML Parse error at {timestamp}")
            pass

        return None
