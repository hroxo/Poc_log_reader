# test_parser.py
import os
import json
from ncr_monitor.log_parser import LogParser
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run_parser_test():
    log_file_path = "logSelfcheckout.log"
    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at '{log_file_path}'")
        return

    parser = LogParser()
    # print(f"Parsing log file: {log_file_path}")

    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            event = parser.parse_log_line(line)
            if event:
                print(event.to_json())

if __name__ == "__main__":
    run_parser_test()
