import os
import sys
from pathlib import Path
from pwnoio_sdk import PwnoMCPClient, PwnoError


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: quickstart_analyze.py /path/to/binary [/path/to/libc]")
        sys.exit(1)

    binary_path = Path(sys.argv[1])
    libc_path = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    api_key = os.getenv("PWNO_API_KEY")
    if not api_key:
        print("PWNO_API_KEY environment variable is required")
        sys.exit(1)

    try:
        client = PwnoMCPClient(api_key=api_key)

        if libc_path:
            result = client.analyze(binary=binary_path, libc=libc_path)
        else:
            result = client.analyze(binary=binary_path)

        print("Analysis complete")
        print(f"MCP URL:   {result.mcp_url}")
        print(f"Binaro ID: {result.binaro_id}")
        print(f"Status:    {result.status}")
        print(f"Message:   {result.message}")
        print(f"Expires:   {result.expires_at}")

        if result.fileinfo:
            print(f"Fileinfo:  {result.fileinfo}")

    except PwnoError as e:
        print(f"Pwno SDK Error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()

