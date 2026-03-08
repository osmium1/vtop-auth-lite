import logging
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .exceptions import NetworkConnectivityError

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

class VTOPSessionManager:
    """
    A unified, silent manager for web requests to VTOP that includes
    retry logic, user-agent rotation, and session clearing tools.
    """
    
    BASE_URL = "https://vtop.vitbhopal.ac.in"

    def __init__(self):
        self.session = None
        self.current_user_agent = None
        self.reset_session()
        
    def reset_session(self):
        """Initializes a fresh requests session with a random User-Agent."""
        if self.session:
            self.session.close()
            
        self.session = requests.Session()
        self.current_user_agent = random.choice(USER_AGENTS)
        
        self.session.headers.update({
            "User-Agent": self.current_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        logger.debug(f"Session initialized with identity: {self.current_user_agent}")

    @retry(
        stop=stop_after_attempt(4), 
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, NetworkConnectivityError)),
        reraise=True
    )
    def fetch(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        A robust fetch wrapper with automated retries and error mapping.
        """
        url = endpoint if endpoint.startswith('http') else f"{self.BASE_URL}{endpoint}"
        kwargs.setdefault('timeout', 15)
        
        try:
            logger.debug(f"{method} {url}")
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code >= 500 or response.status_code == 404:
                logger.warning(f"Server error {response.status_code} at {url}")
                raise NetworkConnectivityError(f"HTTP {response.status_code} from {url}")
                
            response.raise_for_status()
            return response
            
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.warning(f"Transport error fetching {url}")
            raise
        except Exception as e:
            if not isinstance(e, NetworkConnectivityError):
                logger.error(f"Unexpected fetch error: {e}")
            raise
