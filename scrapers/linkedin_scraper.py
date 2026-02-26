import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from bs4 import BeautifulSoup
from models import JobPost
from scrapers.base_scraper import BaseScraper

API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
REMOTE_KEYWORDS = ["remote", "anywhere", "distributed"]


class LinkedInScraper(BaseScraper):

    def __init__(self):
        super().__init__(delay=3.0)
        self.session.headers.update({
            "Referer": "https://www.linkedin.com/jobs/search/",
            "X-Requested-With": "XMLHttpRequest",
        })

    @property
    def site_name(self) -> str:
        return "linkedin"

    # ── Main entry point ──────────────────────────────────────────────────────

    def scrape(self, search_term: str, location: str, results_wanted: int = 20) -> List[JobPost]:
        self.logger.info(f"Searching LinkedIn for '{search_term}' in '{location}'")

        jobs = []
        start = 0

        while len(jobs) < results_wanted:
            page_jobs = self._fetch_page(search_term, location, start)
            if not page_jobs:
                break
            jobs.extend(page_jobs)
            start += 25

        self.logger.info(f"Found {len(jobs)} LinkedIn jobs")
        return jobs[:results_wanted]

    # ── Fetching ──────────────────────────────────────────────────────────────

    def _fetch_page(self, search_term: str, location: str, start: int) -> List[JobPost]:
        params = {
            "keywords": search_term,
            "location": location,
            "start": start,
            "sortBy": "DD",
            "f_TPR": "r604800",
        }

        response = self._fetch(API_URL, params=params)
        if not response:
            return []

        cards = BeautifulSoup(response.text, "html.parser").find_all("li")
        self.logger.info(f"Found {len(cards)} LinkedIn jobs so far...")
        return self._parse_all(cards)

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_all(self, cards: list) -> List[JobPost]:
        jobs = []
        for card in cards:
            job = self._parse_one(card)
            if job:
                jobs.append(job)
        return jobs

    def _parse_one(self, card) -> Optional[JobPost]:
        try:
            title_elem = card.find("h3", class_="base-search-card__title")
            if not title_elem:
                return None

            title    = title_elem.get_text(strip=True)
            company  = self._get_text(card, "h4", "base-search-card__subtitle")
            location = self._get_text(card, "span", "job-search-card__location")
            job_url  = self._get_url(card)
            date     = self._get_date(card)

            return JobPost(
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                source=self.site_name,
                is_remote=self._is_remote(location),
                date_posted=date,
            )

        except Exception as e:
            self.logger.debug(f"Skipped a card: {e}")
            return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_text(self, card, tag: str, css_class: str) -> str:
        elem = card.find(tag, class_=css_class)
        return elem.get_text(strip=True) if elem else "Unknown"

    def _get_url(self, card) -> str:
        link = card.find("a", class_="base-card__full-link")
        return link["href"].split("?")[0] if link else ""

    def _get_date(self, card) -> Optional[str]:
        date_elem = card.find("time")
        return date_elem.get("datetime") if date_elem else None

    def _is_remote(self, location: str) -> bool:
        return any(word in location.lower() for word in REMOTE_KEYWORDS)