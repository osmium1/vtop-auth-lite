import sys
import logging
import argparse
from core.session import VTOPSessionManager
from core.auth import VTOPAuth
from core.exceptions import VTOPHandshakeError

def setup_silent_logging():
    """Configures logging for production: silent console, detailed file log."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Silence third-party noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # Console: Only Warnings/Errors
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("[!] %(levelname)s: %(message)s"))
    logger.addHandler(ch)
    
    # File: Full diagnostics
    fh = logging.FileHandler('handshake.log', mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s - [%(levelname)s] - %(message)s"))
    logger.addHandler(fh)

def main():
    setup_silent_logging()
    
    parser = argparse.ArgumentParser(description="VTOP Handshake Utility")
    parser.add_argument("username", help="VTOP Username")
    parser.add_argument("password", help="VTOP Password")
    args = parser.parse_args()
    
    try:
        session_manager = VTOPSessionManager()
        auth_handler = VTOPAuth(session_manager)
        
        # Perform silent login
        if auth_handler.login(args.username, args.password):
            # Fetch final authenticated CSRF
            dashboard_res = session_manager.fetch('GET', '/vtop/content')
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(dashboard_res.text, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf'})
            
            if csrf_input:
                print(csrf_input.get('value'))
            else:
                print("CSRF_NOT_FOUND")
                sys.exit(1)
                
    except VTOPHandshakeError as e:
        print(f"ERROR: {type(e).__name__}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: UnexpectedError")
        sys.exit(1)

if __name__ == "__main__":
    main()
