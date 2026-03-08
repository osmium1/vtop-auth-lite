# VTOP Session Handshake Utility

A lightweight, high-reliability automation utility for bypassing
CAPTCHA-protected authentication on the VTOP portal.

## Technical Overview

This utility performs an automated "handshake" with the **VTOP VIT Bhopal**
(https://vtop.vitbhopal.ac.in/vtop/) server to acquire an authenticated session.

> [!NOTE]
> This utility is designed and tested exclusively for the **Student Login**
> portal.

- Model and inference engine require only **~40-60MB of RAM**, making it ideal
  for low-cost VPS and server-side deployment.
- 5-stage retry loop. On any failure, a hard reset is performed—clearing
  cookies, rotating User-Agents, and re-fetching the login page.
- Typical handshake takes **2.5 to 4 seconds** depending on network latency.
- Designed as a library-first utility with a custom exception hierarchy for
  robust programmatic error handling.
- Since the ONNX model runs locally, the project has zero external API
  dependencies and requires **no API keys**.

## Installation

1. Install Python 3.12+.
2. Install the package locally:
   ```powershell
   pip install .
   ```

## Integration

### CLI Usage

Run the utility to acquire a session-active CSRF:

```powershell
python -m vtop_auth_lite <USERNAME> <PASSWORD>
```

### Programmatic Usage

```python
from vtop_auth_lite.session import VTOPSessionManager
from vtop_auth_lite.auth import VTOPAuth

session = VTOPSessionManager()
auth = VTOPAuth(session)
if auth.login("username", "password"):
    # session is now authenticated
    res = session.fetch("GET", "/vtop/content")
```

**Output**:

- **Success**: Prints the **64-character CSRF Token**.
- **Failure**: Prints a specific error code (e.g., `AuthenticationFailedError`)
  and exits with code 1.

## Errors & Troubleshooting

| Error                       | Cause                    | Solution                                         |
| :-------------------------- | :----------------------- | :----------------------------------------------- |
| `AuthenticationFailedError` | Invalid credentials.     | Verify your VTOP username and password.          |
| `CaptchaSolverError`        | AI inference failure.    | Ensure model is inside `vtop_auth_lite/models/`. |
| `NetworkConnectivityError`  | VTOP is down or blocked. | Check your internet; VTOP may be in maintenance. |
| `UnexpectedError`           | Unhandled system crash.  | Check `handshake.log` for a detailed traceback.  |

_If you encounter a persistent breaking error, please submit an issue with the
contents of `handshake.log`._

## Repository Structure

- `vtop_auth_lite/`: The core package (Auth, Session, OCR, and ONNX models).
- `pyproject.toml`: Package build configuration.

---

_Developed for research, development, and educational purposes._
