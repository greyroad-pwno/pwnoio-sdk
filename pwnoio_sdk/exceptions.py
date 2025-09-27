class PwnoError(Exception):
    """Base exception for all Pwno.io SDK errors"""
    pass


class PwnoAPIError(PwnoError):
    """Exception raised when API returns an error response"""

    def __init__(self, message: str, status_code: int = None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PwnoTimeoutError(PwnoError):
    """Exception raised when operations timeout"""
    pass


class PwnoAuthenticationError(PwnoAPIError):
    """Exception raised when authentication fails"""
    pass


class PwnoValidationError(PwnoError):
    """Exception raised when input validation fails"""
    pass


class PwnoFileNotFoundError(PwnoError, FileNotFoundError):
    """Exception raised when required files are not found"""
    pass