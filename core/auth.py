import logging
from bs4 import BeautifulSoup
from core.session import VTOPSessionManager
from core.exceptions import AuthenticationFailedError, CaptchaSolverError, NetworkConnectivityError

logger = logging.getLogger(__name__)

class VTOPAuth:
    """
    Silent authentication handler for VTOP.
    Encapsulates the complex multi-step login handshake.
    """
    
    def __init__(self, session_manager: VTOPSessionManager):
        self.session_manager = session_manager
        from core.ocr import CaptchaSolver
        self.solver = CaptchaSolver()
        
    def _extract_csrf(self, html_content: str) -> str:
        """Parses the HTML to find the _csrf input field."""
        soup = BeautifulSoup(html_content, 'html.parser')
        csrf_input = soup.find('input', {'name': '_csrf'})
        if csrf_input:
            return csrf_input.get('value')
        
        logger.error("CSRF token missing from response.")
        raise NetworkConnectivityError("CSRF token missing from VTOP response.")

    def _solve_captcha(self) -> str:
        """Fetches and solves a fresh CAPTCHA image."""
        logger.debug("Generating fresh CAPTCHA...")
        captcha_frag_res = self.session_manager.fetch('GET', '/vtop/get/new/captcha')
        soup = BeautifulSoup(captcha_frag_res.text, 'html.parser')
        
        img_tag = soup.find('img', src=lambda s: s and s.startswith('data:image'))
        if not img_tag:
            img_tag = soup.find('img', {'id': 'captchaRefresh'})
            
        if not img_tag:
            raise NetworkConnectivityError("Failed to locate CAPTCHA image tag.")
            
        captcha_url = img_tag.get('src')
        
        if captcha_url.startswith('data:image'):
            import base64
            b64_data = captcha_url.split(',')[1]
            img_bytes = base64.b64decode(b64_data)
        else:
            if not captcha_url.startswith('/'):
                captcha_url = '/' + captcha_url
            captcha_res = self.session_manager.fetch('GET', captcha_url)
            img_bytes = captcha_res.content
        
        captcha_text = self.solver.solve(img_bytes)
        
        if "ERROR" in captcha_text:
            raise CaptchaSolverError(f"AI Model failed to solve CAPTCHA: {captcha_text}")
            
        logger.debug(f"CAPTCHA solved: {captcha_text}")
        return captcha_text

    def login(self, username, password):
        """
        Executes the VTOP login handshake.
        Raises specific exceptions on failure.
        """
        max_attempts = 5
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"Handshake attempt {attempt}/{max_attempts}")
                
                # Step 1: Initial Session Binding
                initial_res = self.session_manager.fetch('GET', '/vtop/')
                initial_csrf = self._extract_csrf(initial_res.text)
                
                # Step 2: Mandatory Prelogin Setup
                setup_payload = {'_csrf': initial_csrf, 'flag': 'VTOP'}
                self.session_manager.fetch(
                    'POST', 
                    '/vtop/prelogin/setup', 
                    data=setup_payload,
                    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                )

                # Step 3: Page Binding
                login_page_res = self.session_manager.fetch('GET', '/vtop/login')
                current_csrf = self._extract_csrf(login_page_res.text)
                
                # Step 4: AI Solver
                captcha_str = self._solve_captcha()
                
                # Step 5: Submission
                login_payload = {
                    '_csrf': current_csrf,
                    'username': username,
                    'password': password,
                    'captchaStr': captcha_str
                }
                
                login_res = self.session_manager.fetch(
                    'POST',
                    '/vtop/login',
                    data=login_payload,
                    headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
                )

                response_text = login_res.text.lower()
                
                # Failure Case: Wrong Captcha (Internal Retry)
                if "invalid captcha" in response_text or "captcha is invalid" in response_text:
                    logger.warning(f"Attempt {attempt}: Captcha rejected. Retrying with fresh session...")
                    continue
                    
                # Failure Case: Bad Credentials (Immediate Error)
                if "invalid username or password" in response_text or "bad credentials" in response_text:
                    raise AuthenticationFailedError("VTOP: Invalid Username or Password.")
                    
                # Success Case
                if any(x in response_text for x in ["logout", "/vtop/logout", "dashboard"]) or login_res.url.endswith('dashboard'):
                    logger.debug("Authentication Handshake successful.")
                    return True
                
                logger.warning(f"Unexpected handshake response state. Status: {login_res.status_code}")
                
            except Exception as e:
                if isinstance(e, (AuthenticationFailedError, CaptchaSolverError)):
                    raise
                logger.debug(f"Retryable error during handshake: {e}")
                
            self.session_manager.reset_session()
            
        raise NetworkConnectivityError("Handshake failed after multiple automated retries.")
