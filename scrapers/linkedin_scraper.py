"""
linkedin_scraper.py - Scraper for LinkedIn Jobs

LinkedIn is MORE restrictive than Indeed:
- It rate-limits aggressively (blocks after ~10 pages per IP)
- It uses JavaScript to load some content
- It requires more sophisticated headers

STRATEGY:
LinkedIn has a "lite" jobs page that returns cleaner HTML than the main site.
We target: https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search

This is the API endpoint their own frontend uses to load more jobs — it's public
and returns cleaner HTML than the main page. This is called "API sniffing" — 
watching what requests a website makes and calling those directly.
"""

import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
from bs4 import BeautifulSoup
from models import JobPost
from scrapers.base_scraper import BaseScraper


class LinkedInScraper(BaseScraper):
    """
    Scraper for LinkedIn job listings.
    Uses LinkedIn's internal job search API endpoint.
    """

    # This is the URL LinkedIn's own frontend uses to fetch job cards
    JOBS_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    def __init__(self, delay_between_requests: float = 3.0):
        # LinkedIn is strict — use longer delays than Indeed
        super().__init__(delay_between_requests)
        # LinkedIn-specific headers — we need to look like we're coming from their own site
        self.session.headers.update({
            "Referer": "https://www.linkedin.com/jobs/search/",
            "X-Requested-With": "XMLHttpRequest",  # Tells the server this is an AJAX request
        })

    @property
    def site_name(self) -> str:
        return "linkedin"

    def scrape(self, search_term: str, location: str, results_wanted: int = 20) -> List[JobPost]:
        """
        Scrape LinkedIn jobs using their internal API endpoint.
        
        LinkedIn paginates with 'start' just like Indeed, but in chunks of 25.
        """
        jobs = []
        start = 0
        jobs_per_page = 25
        
        self.logger.info(f"Searching LinkedIn for '{search_term}' in '{location}'")
        
        while len(jobs) < results_wanted:
            page_jobs = self._scrape_page(search_term, location, start)
            
            if not page_jobs:
                self.logger.info("No more LinkedIn results, stopping.")
                break
            
            jobs.extend(page_jobs)
            self.logger.info(f"Found {len(jobs)} LinkedIn jobs so far...")
            start += jobs_per_page
        
        return jobs[:results_wanted]

    def _scrape_page(self, search_term: str, location: str, start: int) -> List[JobPost]:
        """Fetch one page of LinkedIn job results."""
        
        params = {
            "keywords": search_term,  # LinkedIn uses 'keywords' not 'q'
            "location": location,
            "start": start,
            "sortBy": "DD",           # DD = Date Descending (most recent first)
            "f_TPR": "r604800",       # Time posted: last 7 days (604800 seconds)
        }
        
        response = self._get(self.JOBS_API_URL, params=params)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # LinkedIn job cards are in <li> elements inside the response
        job_cards = soup.find_all("li")
        
        if not job_cards:
            self.logger.debug("No job cards found in LinkedIn response")
            return []
        
        self.logger.debug(f"Found {len(job_cards)} LinkedIn cards (start={start})")
        
        jobs = []
        for card in job_cards:
            job = self._parse_job_card(card)
            if job:
                jobs.append(job)
        
        return jobs

    def _parse_job_card(self, card) -> Optional[JobPost]:
        """Parse a single LinkedIn job card."""
        try:
            # ── Job Title ─────────────────────────────────────────────────────
            title_elem = card.find("h3", class_="base-search-card__title")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)
            
            # ── Company ───────────────────────────────────────────────────────
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # ── Location ──────────────────────────────────────────────────────
            location_elem = card.find("span", class_="job-search-card__location")
            location = location_elem.get_text(strip=True) if location_elem else "Unknown"
            
            # ── Job URL ───────────────────────────────────────────────────────
            link_elem = card.find("a", class_="base-card__full-link")
            job_url = link_elem["href"].split("?")[0] if link_elem else ""  # Remove tracking params
            
            # ── Date Posted ───────────────────────────────────────────────────
            date_elem = card.find("time")
            date_posted = date_elem.get("datetime") if date_elem else None  # ISO date from <time datetime="...">
            
            # ── Remote detection ─────────────────────────────────────────────
            is_remote = any(word in location.lower() for word in ["remote", "anywhere", "distributed"])
            
            return JobPost(
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                source=self.site_name,
                is_remote=is_remote,
                date_posted=date_posted,
            )
            
        except Exception as e:
            self.logger.debug(f"Failed to parse LinkedIn card: {e}")
            return None
