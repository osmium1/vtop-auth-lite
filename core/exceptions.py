class VTOPHandshakeError(Exception):
    """Base exception for all VTOP Handshake related errors."""
    pass

class AuthenticationFailedError(VTOPHandshakeError):
    """Raised when VTOP rejects the provided username or password."""
    pass

class CaptchaSolverError(VTOPHandshakeError):
    """Raised when the AI model fails to process or solve a CAPTCHA."""
    pass

class NetworkConnectivityError(VTOPHandshakeError):
    """Raised when the VTOP server is unreachable or returns unexpected 4xx/5xx errors."""
    pass

class SessionExpiredError(VTOPHandshakeError):
    """Raised when an authenticated session is no longer valid."""
    pass
