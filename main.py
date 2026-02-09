from ncr_monitor import LogWatcher
import os
import json

def main():
    log_file_path = "logSelfcheckout.log" # Assuming log file is in the root directory

    if not os.path.exists(log_file_path):
        print(f"Error: Log file not found at '{log_file_path}'")
        print("Please ensure 'logSelfcheckout.log' is in the same directory as main.py")
        return

    watcher = LogWatcher(log_file=log_file_path)
    print(f"Monitoring log file: {log_file_path}")
    print("Press Ctrl+C to stop.")

    try:
        for event in watcher.stream():
            print(event.to_json())
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()