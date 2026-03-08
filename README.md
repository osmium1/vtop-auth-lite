# VTOP Session Handshake Utility

A lightweight, high-reliability automation utility for bypassing
CAPTCHA-protected authentication on the VTOP portal.

## Technical Overview

This utility performs an automated "handshake" with the **VTOP VIT Bhopal**
(https://vtop.vitbhopal.ac.in/vtop/) server to acquire an authenticated session.

> NOTE: This utility is designed and tested exclusively for **student login
> only**.

- The model and inference engine require only **~40-60MB of RAM**, making it
  ideal for low-cost VPS and server-side deployment.
- A 5-stage retry loop. On each failure, a hard reset is performed at any
  failure—clearing cookies, rotating User-Agents, and re-fetching the login page
  to ensure a synchronized session.
- Typical handshake takes **2.5 to 4 seconds** depending on network latency.
- Designed as a library-first utility with custom exception hierarchy for
  programmatic error handling.

## Installation

1. Install Python 3.12+.
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Integration

Run the utility to acquire a session-active CSRF:

```powershell
python main.py <USERNAME> <PASSWORD>
```

**Output**:

- **Success**: Prints the **64-character CSRF Token**.
- **Failure**: Prints a specific error code (e.g., `AuthenticationFailedError`)
  and exits with code 1.

## Errors & Troubleshooting

| Error                       | Cause                    | Solution                                         |
| :-------------------------- | :----------------------- | :----------------------------------------------- |
| `AuthenticationFailedError` | Invalid credentials.     | Verify your VTOP username and password.          |
| `CaptchaSolverError`        | AI inference failure.    | Ensure `models/captcha_crnn.onnx` is present.    |
| `NetworkConnectivityError`  | VTOP is down or blocked. | Check your internet; VTOP may be in maintenance. |
| `UnexpectedError`           | Unhandled system crash.  | Check `handshake.log` for a detailed traceback.  |

_If you encounter a persistent breaking error, please submit an issue with the
contents of `handshake.log`._

## Repository Structure

- `core/`: Handshake, Session, and OCR logic.
- `models/`: Optimized ONNX model weights.

---

_Developed for research and development purposes._
