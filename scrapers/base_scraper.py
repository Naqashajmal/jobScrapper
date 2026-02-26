import time
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from models import JobPost

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]


class BaseScraper(ABC):

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = self._create_session()
        self.logger = logging.getLogger(self.__class__.__name__)

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(BROWSER_HEADERS)
        session.headers["User-Agent"] = random.choice(USER_AGENTS)
        return session

    def _rotate_user_agent(self):
        self.session.headers["User-Agent"] = random.choice(USER_AGENTS)

    # ── HTTP ──────────────────────────────────────────────────────────────────

    def _wait(self):
        wait_time = self.delay + random.uniform(0, 1.5)
        time.sleep(wait_time)

    def _fetch(self, url: str, params: dict = None) -> Optional[requests.Response]:
        self._wait()
        self.logger.info(f"GET {url}")

        try:
            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 429:
                self.logger.warning("Rate limited. Waiting 60s...")
                time.sleep(60)
                response = self.session.get(url, params=params, timeout=15)

            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"No connection: {url}")
        except requests.exceptions.Timeout:
            self.logger.error(f"Timed out: {url}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")

        return None

    # ── Abstract ──────────────────────────────────────────────────────────────

    @property
    @abstractmethod
    def site_name(self) -> str:
        pass

    @abstractmethod
    def scrape(self, search_term: str, location: str, results_wanted: int = 20) -> List[JobPost]:
        pass