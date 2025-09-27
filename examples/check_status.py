#!/usr/bin/env python3
"""
Check machine status for a given binaro ID.

Usage:
    export PWNO_API_KEY="sk-pwno-..."
    python examples/check_status.py <binaro_id>
"""

import os
import sys
from pwnoio_sdk import PwnoMCPClient, PwnoError


def main():
    if len(sys.argv) != 2:
        print("Usage: check_status.py <binaro_id>")
        sys.exit(1)

    binaro_id = sys.argv[1]
    api_key = os.getenv("PWNO_API_KEY")
    if not api_key:
        print("PWNO_API_KEY environment variable is required")
        sys.exit(1)

    try:
        client = PwnoMCPClient(api_key=api_key)
        status = client.get_machine_status(binaro_id)
        print(status)
    except PwnoError as e:
        print(f"Pwno SDK Error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()

