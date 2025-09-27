import time
from pathlib import Path
from typing import Optional, Dict, Any, Union
import requests
from dataclasses import dataclass

from .exceptions import PwnoAPIError, PwnoTimeoutError, PwnoFileNotFoundError, PwnoValidationError


@dataclass
class AnalyzeResponse:
    """Response from the analyze endpoint"""
    mcp_url: str
    expires_at: str
    status: str
    binaro_id: str
    task_id: str
    message: str
    fileinfo: Optional[Dict[str, Any]] = None


class PwnoMCPClient:
    """
    Synchronous MCP Client.

    Usage:
        client = PwnoMCPClient(api_key="sk-pwno-...")
        client.set_binary("path/to/binary")
        client.set_libc("path/to/libc")  # optional
        mcp_link = client.analyze()

    Or:
        mcp_link = client.analyze(binary="path/to/binary", libc="path/to/libc")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://backend.pwno.io",
        timeout: int = 300
    ):
        """
        Initialize the MCP client.

        Args:
            api_key: API key for authentication (format: sk-pwno-...)
            base_url: Base URL for the API
            timeout: Timeout in seconds for requests
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Builder pattern state
        self._binary_path: Optional[str] = None
        self._libc_path: Optional[str] = None

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "pwnoio-sdk/1.1.0"
        })

    def set_binary(self, binary_path: Union[str, Path]) -> 'PwnoMCPClient':
        """
        Set the binary file path for analysis.
        """
        self._binary_path = str(binary_path)
        return self

    def set_libc(self, libc_path: Union[str, Path]) -> 'PwnoMCPClient':
        """
        Set the libc file path for analysis.
        """
        self._libc_path = str(libc_path)
        return self

    def analyze(
        self,
        binary: Optional[Union[str, Path]] = None,
        libc: Optional[Union[str, Path]] = None
    ) -> AnalyzeResponse:
        """
        Analyze the binary with the /v1/analyze endpoint.

        This method handles the complete flow:
        1. Upload binary and libc files to storage
        2. Create binaro record
        3. Create and provision analysis machine
        4. Wait for machine to be ready
        5. Return MCP URL for interaction

        Args:
            binary: Path to binary file (overrides set_binary if provided)
            libc: Path to libc file (overrides set_libc if provided)

        Returns:
            AnalyzeResponse containing MCP URL and analysis information

        Raises:
            ValueError: If binary path is not provided
            FileNotFoundError: If binary or libc file doesn't exist
            requests.HTTPError: If API request fails
        """
        # Use provided paths or fall back to builder pattern paths
        binary_path = str(binary) if binary else self._binary_path
        libc_path = str(libc) if libc else self._libc_path

        if not binary_path:
            raise PwnoValidationError("Binary path must be provided either via set_binary() or analyze(binary=...)")

        # Validate file existence
        binary_file = Path(binary_path)
        if not binary_file.exists():
            raise PwnoFileNotFoundError(f"Binary file not found: {binary_path}")

        if libc_path:
            libc_file = Path(libc_path)
            if not libc_file.exists():
                raise PwnoFileNotFoundError(f"Libc file not found: {libc_path}")

        # Prepare multipart form data
        files = {
            'binary': ('binary', open(binary_file, 'rb'), 'application/octet-stream')
        }

        if libc_path:
            files['libc'] = ('libc', open(libc_file, 'rb'), 'application/octet-stream')

        try:
            # Make the analyze request
            response = self.session.post(
                f"{self.base_url}/v1/analyze",
                files=files,
                timeout=self.timeout
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    message = error_data.get("detail", f"API error: {response.status_code}")
                except:
                    message = f"HTTP {response.status_code}: {response.text}"
                raise PwnoAPIError(message, response.status_code, error_data if 'error_data' in locals() else None)

            response.raise_for_status()

            # Parse response
            data = response.json()

            return AnalyzeResponse(
                mcp_url=data["mcp_url"],
                expires_at=data["expires_at"],
                status=data["status"],
                binaro_id=data["binaro_id"],
                task_id=data["task_id"],
                message=data["message"],
                fileinfo=data.get("fileinfo")
            )

        except requests.exceptions.Timeout:
            raise PwnoTimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            if "timeout" in str(e).lower():
                raise PwnoTimeoutError(f"Request timed out: {e}")
            raise PwnoAPIError(f"Request failed: {e}")

        finally:
            # Close file handles
            for file_tuple in files.values():
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.
        """
        response = self.session.get(f"{self.base_url}/v1/health")
        response.raise_for_status()
        return response.json()

    # Additional convenience methods for direct API access

    def upload_binary(self, binary_path: Union[str, Path], mcp_only: bool = False) -> Dict[str, Any]:
        """
        Upload a binary file directly.
        """
        binary_file = Path(binary_path)
        if not binary_file.exists():
            raise FileNotFoundError(f"Binary file not found: {binary_path}")

        files = {
            'file': ('binary', open(binary_file, 'rb'), 'application/octet-stream')
        }
        data = {
            'mcpOnly': mcp_only
        }

        try:
            response = self.session.post(
                f"{self.base_url}/v1/binaro/",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        finally:
            files['file'][1].close()

    def list_binarios(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """
        List all binario records.
        """
        params = {
            'limit': min(limit, 100),
            'offset': max(offset, 0)
        }

        response = self.session.get(
            f"{self.base_url}/v1/binaro/",
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_binario(self, binaro_id: str) -> Dict[str, Any]:
        """
        Get details of a specific binario record.
        """
        response = self.session.get(
            f"{self.base_url}/v1/binaro/{binaro_id}",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def upload_libc_for_binario(self, binaro_id: str, libc_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Upload a libc file for an existing binario record.
        """
        libc_file = Path(libc_path)
        if not libc_file.exists():
            raise FileNotFoundError(f"Libc file not found: {libc_path}")

        files = {
            'file': ('libc', open(libc_file, 'rb'), 'application/octet-stream')
        }

        try:
            response = self.session.post(
                f"{self.base_url}/v1/binaro/{binaro_id}/libc",
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        finally:
            files['file'][1].close()

    def create_machine(self, binaro_id: str) -> Dict[str, Any]:
        """
        Create a machine for a binario record.
        """
        response = self.session.post(
            f"{self.base_url}/v1/binaro/{binaro_id}/machine",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_machine_status(self, binaro_id: str) -> Dict[str, Any]:
        """
        Get machine status for a binario record.
        """
        response = self.session.get(
            f"{self.base_url}/v1/binaro/{binaro_id}/machine/status",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def terminate_machine(self, binaro_id: str) -> Dict[str, Any]:
        """
        Terminate a machine for a binario record.
        """
        response = self.session.delete(
            f"{self.base_url}/v1/binaro/{binaro_id}/machine",
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup session"""
        self.session.close()
