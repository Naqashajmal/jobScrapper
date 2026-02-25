import time
import random
import logging
from abc import ABC, abstractmethod  #Abstract Base Class
from typing import List, Optional
import requests
from models import JobPost

# Set up logging so we can see what's happening while the scraper runs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)


class BaseScraper(ABC):
    #rotate through multiple user agents so we don't look repetitive.
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    ]

    def __init__(self, delay_between_requests: float = 2.0):
      
        self.delay = delay_between_requests
        self.session = self._create_session()  
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_session(self) -> requests.Session:
        session = requests.Session() # website remembers your cookies,headers,identity
        session.headers.update({
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",    # Do Not Track, header looks like a real browser
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        return session

    def _get(self, url: str, params: dict = None, **kwargs) -> Optional[requests.Response]:
        #**kwargs keyword arguments, accept any extra arguments someone passes in
        #This wraps requests.get() with automatic delays, Error handling, Logging 
        sleep_time = self.delay + random.uniform(0, 1.5)  # Add randomness so it looks human
        self.logger.debug(f"Sleeping {sleep_time:.1f}s before request...")
        time.sleep(sleep_time)

        try:
            self.logger.info(f"GET {url}")
            response = self.session.get(url, params=params, timeout=15, **kwargs)

        # 200 = Success, here's your page
        # 403 = Forbidden, you're blocked
        # 404 = Not Found, page doesn't exist
        # 429 = Too Many Requests, slow down bot!
        # 500 = Server Error, website is broken 

            
            # HTTP 429 Too Many Requests ,rate limited
            if response.status_code == 429:
                self.logger.warning("Rate limited (429). Waiting 60s before retrying...")
                time.sleep(60)
                response = self.session.get(url, params=params, timeout=15, **kwargs)
            
            # HTTP 200 success. Anything else is a problem.
            response.raise_for_status()  # Raises an exception for 4xx/5xx errors
            return response
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timed out: {url}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        
        return None  # Return None on any failure

    def _rotate_user_agent(self):
        self.session.headers["User-Agent"] = random.choice(self.USER_AGENTS)

    @abstractmethod
    def scrape(self, search_term: str, location: str, results_wanted: int = 20) -> List[JobPost]:
        pass  # Subclasses fill this in
    
    @property
    @abstractmethod
    def site_name(self) -> str:
        pass
