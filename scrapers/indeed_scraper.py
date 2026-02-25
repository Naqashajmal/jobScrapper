#Scraper for Indeed.com via JSearch API on RapidAPI

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
import requests
from models import JobPost
from scrapers.base_scraper import BaseScraper
from dotenv import load_dotenv
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY") # Your RapidAPI key

class IndeedScraper(BaseScraper):

    API_URL = "https://jsearch.p.rapidapi.com/search"

    @property
    def site_name(self) -> str:
        return "indeed"

    def scrape(self, search_term: str, location: str, results_wanted: int = 20) -> List[JobPost]:
        self.logger.info(f"Searching Indeed (via JSearch) for '{search_term}' in '{location}'")

        jobs = []
        page = 1

        while len(jobs) < results_wanted:
            page_jobs = self._scrape_page(search_term, location, page)
            if not page_jobs:
                break
            jobs.extend(page_jobs)
            self.logger.info(f"Found {len(jobs)} Indeed jobs so far...")
            page += 1

        return jobs[:results_wanted]

    def _scrape_page(self, search_term: str, location: str, page: int) -> List[JobPost]:
        # Build headers exactly as RapidAPI expects
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
            "Content-Type": "application/json",
        }

        params = {
            "query": f"{search_term} {location}",
            "page": str(page),
            "num_pages": "1",
            "country": "us",
            "date_posted": "all",
        }

        try:
            # Make request directly without using our base class
            # to have full control over headers
            response = requests.get(
                self.API_URL,
                headers=headers,
                params=params,
                timeout=20,
            )
            self.logger.info(f"JSearch status: {response.status_code}")

            if response.status_code == 403:
                self.logger.error("403 Forbidden — check your API key is correct and subscribed")
                self.logger.error(f"Response: {response.text[:300]}")
                return []

            response.raise_for_status()
            data = response.json()

        except Exception as e:
            self.logger.error(f"JSearch API error: {e}")
            return []

        results = data.get("data", [])
        self.logger.info(f"JSearch returned {len(results)} results for page {page}")

        jobs = []
        for item in results:
            job = self._parse_job(item)
            if job:
                jobs.append(job)

        return jobs

    def _parse_job(self, data: dict) -> Optional[JobPost]:
        try:
            title = data.get("job_title", "Unknown")
            company = data.get("employer_name", "Unknown")

            city = data.get("job_city", "")
            state = data.get("job_state", "")
            country = data.get("job_country", "")
            location = ", ".join(filter(None, [city, state, country])) or "Unknown"

            job_url = data.get("job_apply_link") or data.get("job_url") or "https://www.indeed.com"
            is_remote = data.get("job_is_remote", False)
            date_posted = data.get("job_posted_at_datetime_utc", None)
            description = (data.get("job_description") or "")[:500]

            salary_min = data.get("job_min_salary")
            salary_max = data.get("job_max_salary")
            salary_interval = (data.get("job_salary_period") or "").lower() or None

            job_type_raw = (data.get("job_employment_type") or "").lower()
            job_type_map = {
                "fulltime": "fulltime",
                "full_time": "fulltime",
                "parttime": "parttime",
                "part_time": "parttime",
                "contractor": "contract",
                "intern": "internship",
            }
            job_type = job_type_map.get(job_type_raw, job_type_raw or None)

            return JobPost(
                title=title,
                company=company,
                location=location,
                job_url=job_url,
                source=self.site_name,
                description=description,
                job_type=job_type,
                is_remote=is_remote,
                date_posted=date_posted,
                salary_min=float(salary_min) if salary_min else None,
                salary_max=float(salary_max) if salary_max else None,
                salary_interval=salary_interval,
            )

        except Exception as e:
            self.logger.debug(f"Failed to parse JSearch job: {e}")
            return None