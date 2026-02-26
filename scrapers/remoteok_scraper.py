import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import random
import requests
from typing import List, Optional
from models import JobPost
from scrapers.base_scraper import BaseScraper


class RemoteOKScraper(BaseScraper):

    API_URL = "https://remoteok.com/api"

    def __init__(self):
        super().__init__(delay=2.0)

    @property
    def site_name(self) -> str:
        return "remoteok"

    # ── Main entry point ──────────────────────────────────────────────────────

    def scrape(self, search_term: str, location: str = "remote", results_wanted: int = 20) -> List[JobPost]:
        self.logger.info(f"Searching RemoteOK for '{search_term}'")

        all_jobs = self._fetch_jobs()
        if not all_jobs:
            return []

        matched = self._filter_jobs(all_jobs, search_term, results_wanted)
        return self._parse_all(matched)

    # ── Fetching ──────────────────────────────────────────────────────────────

    def _fetch_jobs(self) -> Optional[list]:
        self._visit_homepage()
        time.sleep(random.uniform(2, 4))
        return self._call_api()

    def _visit_homepage(self):
        try:
            requests.get(
                "https://remoteok.com/",
                timeout=10,
                headers={
                    "User-Agent": self.session.headers["User-Agent"],
                    "Accept-Encoding": "gzip, deflate",
                }
            )
            self.logger.info("Homepage visited")
        except Exception:
            self.logger.warning("Homepage visit failed, continuing anyway")

    def _call_api(self) -> Optional[list]:
        try:
            response = self.session.get(
                self.API_URL,
                timeout=15,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                    "Referer": "https://remoteok.com/",
                }
            )

            data = json.loads(response.text)
            self.logger.info(f"Got {len(data)} items from API")
            return data

        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            return None

    # ── Filtering ─────────────────────────────────────────────────────────────

    def _filter_jobs(self, all_jobs: list, search_term: str, limit: int) -> list:
        search_words = search_term.lower().split()
        matched = []

        for job in all_jobs[1:]:  # skip first item, it's metadata not a job
            title = str(job.get("position", "")).lower()
            tags = " ".join(job.get("tags", [])).lower()

            if any(word in title or word in tags for word in search_words):
                matched.append(job)

            if len(matched) >= limit:
                break

        self.logger.info(f"Matched {len(matched)} jobs")
        return matched

    # ── Parsing ───────────────────────────────────────────────────────────────

    def _parse_all(self, jobs_data: list) -> List[JobPost]:
        jobs = []
        for job_data in jobs_data:
            job = self._parse_one(job_data)
            if job:
                jobs.append(job)
        self.logger.info(f"Parsed {len(jobs)} jobs")
        return jobs

    def _parse_one(self, data: dict) -> Optional[JobPost]:
        try:
            if not data.get("position"):
                return None

            return JobPost(
                title=data.get("position", "Unknown"),
                company=data.get("company", "Unknown"),
                location="Remote",
                job_url=data.get("url", self.API_URL),
                source=self.site_name,
                is_remote=True,
                salary_min=float(data["salary_min"]) if data.get("salary_min") else None,
                salary_max=float(data["salary_max"]) if data.get("salary_max") else None,
                salary_interval="yearly" if data.get("salary_min") else None,
                date_posted=data.get("date"),
                description=data.get("description", "")[:500] if data.get("description") else None,
            )

        except Exception as e:
            self.logger.debug(f"Skipped a job: {e}")
            return None