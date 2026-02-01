import sys
from src.parser import LogParser


def main():
    log_file = "logSelfcheckout.log"

    # Allow overriding log file via command line argument
    if len(sys.argv) > 1:
        log_file = sys.argv[1]

    print(f"Monitoring {log_file} for new events...")
    print("Press Ctrl+C to stop.")

    parser = LogParser(log_file)
    output_file = "logParcer.json"

    try:
        with open(output_file, "a", encoding="utf-8") as f_out:
            # Use follow() to tail the file
            for event in parser.follow():
                json_str = event.to_json()
                
                # Print to console
                print(json_str)
                sys.stdout.flush()

                # Write to file
                f_out.write(json_str + "\n")
                f_out.flush()

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
