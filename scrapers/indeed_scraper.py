import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from typing import List, Optional
from models import JobPost
from scrapers.base_scraper import BaseScraper
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
API_URL = "https://jsearch.p.rapidapi.com/search"
API_HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "jsearch.p.rapidapi.com",
}
JOB_TYPE_MAP = {
    "fulltime":   "fulltime",
    "full_time":  "fulltime",
    "parttime":   "parttime",
    "part_time":  "parttime",
    "contractor": "contract",
    "intern":     "internship",
}


class IndeedScraper(BaseScraper):

    @property
    def site_name(self) -> str:
        return "indeed"

    # ── Main entry point ──────────────────────────────────────────────────────

    def scrape(self, search_term: str, location: str, results_wanted: int = 20) -> List[JobPost]:
        self.logger.info(f"Searching Indeed for '{search_term}' in '{location}'")

        jobs = []
        page = 1

        while len(jobs) < results_wanted:
            page_jobs = self._fetch_page(search_term, location, page)
            if not page_jobs:
                break
            jobs.extend(page_jobs)
            page += 1

        self.logger.info(f"Found {len(jobs)} Indeed jobs")
        return jobs[:results_wanted]

    # ── Fetching ──────────────────────────────────────────────────────────────

    def _fetch_page(self, search_term: str, location: str, page: int) -> List[JobPost]:
        params = {
            "query": f"{search_term} {location}",
            "page": str(page),
            "num_pages": "1",
            "date_posted": "all",
        }

        try:
            response = requests.get(API_URL, headers=API_HEADERS, params=params, timeout=20)
            response.raise_for_status()
            results = response.json().get("data", [])
            self.logger.info(f"Page {page}: got {len(results)} results")
            return self._parse_all(results)

        except Exception as e:
            self.logger.error(f"Failed to fetch page {page}: {e}")
            return []

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_all(self, results: list) -> List[JobPost]:
        jobs = []
        for item in results:
            job = self._parse_one(item)
            if job:
                jobs.append(job)
        return jobs

    def _parse_one(self, data: dict) -> Optional[JobPost]:
        try:
            return JobPost(
                title=data.get("job_title", "Unknown"),
                company=data.get("employer_name", "Unknown"),
                location=self._build_location(data),
                job_url=data.get("job_apply_link") or data.get("job_url") or "https://www.indeed.com",
                source=self.site_name,
                is_remote=data.get("job_is_remote", False),
                date_posted=data.get("job_posted_at_datetime_utc"),
                description=(data.get("job_description") or "")[:500],
                job_type=self._get_job_type(data),
                salary_min=float(data["job_min_salary"]) if data.get("job_min_salary") else None,
                salary_max=float(data["job_max_salary"]) if data.get("job_max_salary") else None,
                salary_interval=(data.get("job_salary_period") or "").lower() or None,
            )
        except Exception as e:
            self.logger.debug(f"Skipped a job: {e}")
            return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _build_location(self, data: dict) -> str:
        parts = [data.get("job_city"), data.get("job_state"), data.get("job_country")]
        return ", ".join(filter(None, parts)) or "Unknown"

    def _get_job_type(self, data: dict) -> Optional[str]:
        raw = (data.get("job_employment_type") or "").lower()
        return JOB_TYPE_MAP.get(raw, raw or None)