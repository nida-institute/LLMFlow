#!/usr/bin/env python3
"""Extract Windows install script verification failure logs from GitHub Actions."""

import subprocess
import sys

def main():
    run_id = "24001499387"

    print(f"Fetching logs for run {run_id}...")

    try:
        # Get the full log output for failed jobs
        result = subprocess.run(
            ["/usr/local/bin/gh", "run", "view", run_id, "--log-failed"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            print(f"Error getting logs: {result.stderr}")
            sys.exit(1)

        logs = result.stdout

        # Find the Windows verification section
        in_windows_verify = False
        windows_logs = []

        for line in logs.splitlines():
            if "Verify install script on windows-latest" in line:
                in_windows_verify = True
            elif in_windows_verify:
                # Collect logs until we hit another job section
                if line.strip() and not line.startswith(" ") and ":" in line and line.split(":")[0].isupper():
                    # New section started
                    break
                windows_logs.append(line)

        if not windows_logs:
            print("\nNo Windows verification logs found. Showing all failed job logs:\n")
            print(logs)
        else:
            print("\n=== Windows Install Script Verification Failure ===\n")
            print("\n".join(windows_logs[:100]))  # First 100 lines

            if len(windows_logs) > 100:
                print(f"\n... ({len(windows_logs) - 100} more lines)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
