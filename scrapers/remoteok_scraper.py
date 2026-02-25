"""
remoteok_scraper.py - Scraper for RemoteOK.com
"""

import sys
import os
import json
import zlib
import time
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Optional
import requests
from models import JobPost
from scrapers.base_scraper import BaseScraper


class RemoteOKScraper(BaseScraper):
    
    API_URL = "https://remoteok.com/api"

    def __init__(self):
        super().__init__(delay_between_requests=2.0)

    def _decompress(self, content: bytes) -> Optional[str]:
        """Try every possible decompression method."""
        
        # Method 1: brotli (br) — most likely what RemoteOK uses
        try:
            import brotli
            return brotli.decompress(content).decode("utf-8")
        except Exception:
            pass

        # Method 2: gzip
        try:
            return zlib.decompress(content, zlib.MAX_WBITS | 16).decode("utf-8")
        except Exception:
            pass

        # Method 3: zlib
        try:
            return zlib.decompress(content).decode("utf-8")
        except Exception:
            pass

        # Method 4: deflate
        try:
            return zlib.decompress(content, -zlib.MAX_WBITS).decode("utf-8")
        except Exception:
            pass

        # Method 5: raw utf-8
        try:
            return content.decode("utf-8")
        except Exception:
            pass

        return None

    def _fetch_all_jobs(self) -> Optional[list]:
        session = requests.Session()

        # Step 1: Visit homepage first like a real browser
        try:
            session.get("https://remoteok.com/", timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",  # No brotli for homepage
            })
            self.logger.info("Homepage visited successfully")
        except Exception as e:
            self.logger.warning(f"Homepage visit failed (continuing anyway): {e}")

        time.sleep(random.uniform(2, 4))

        # Step 2: Fetch the API — explicitly say we DON'T want brotli
        # so we get gzip which we can handle with zlib
        try:
            response = session.get(
                self.API_URL,
                timeout=15,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate",  # No brotli — we can't handle it without extra lib
                    "Referer": "https://remoteok.com/",
                    "Connection": "keep-alive",
                },
                # Tell requests NOT to auto-decompress so we can do it manually
                stream=False,
            )

            self.logger.info(f"Status: {response.status_code} | Encoding: {response.headers.get('Content-Encoding', 'none')} | Type: {response.headers.get('Content-Type', '?')}")

            # Let requests handle decompression automatically first
            # (it does gzip automatically when you access response.text)
            text = response.text
            self.logger.info(f"Response text preview: {text[:100]}")

            if text.strip().startswith("[") or text.strip().startswith("{"):
                # Looks like valid JSON!
                data = json.loads(text)
                self.logger.info(f"Got {len(data)} items from API")
                return data
            else:
                # Not JSON — try manual decompression on raw bytes
                self.logger.warning("response.text not JSON, trying manual decompression...")
                decoded = self._decompress(response.content)
                if decoded:
                    self.logger.info(f"Manual decompress preview: {decoded[:100]}")
                    data = json.loads(decoded)
                    self.logger.info(f"Got {len(data)} items after manual decompress")
                    return data
                else:
                    self.logger.error("All decompression methods failed")
                    self.logger.error(f"Raw content (hex): {response.content[:50].hex()}")
                    return None

        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None

    @property
    def site_name(self) -> str:
        return "remoteok"

    def scrape(self, search_term: str, location: str = "remote", results_wanted: int = 20) -> List[JobPost]:
        self.logger.info(f"Searching RemoteOK for '{search_term}'")

        data = self._fetch_all_jobs()
        if not data:
            return []

        jobs_data = data[1:] if data else []
        self.logger.info(f"Total jobs available: {len(jobs_data)}")

        # Filter by search term locally
        search_lower = search_term.lower()
        matched = []
        for job_data in jobs_data:
            title = str(job_data.get("position", "")).lower()
            tags = " ".join(job_data.get("tags", [])).lower()

            if any(word in title or word in tags for word in search_lower.split()):
                matched.append(job_data)

            if len(matched) >= results_wanted:
                break

        self.logger.info(f"Matched {len(matched)} jobs for '{search_term}'")

        jobs = []
        for job_data in matched:
            job = self._parse_job(job_data)
            if job:
                jobs.append(job)

        self.logger.info(f"Found {len(jobs)} RemoteOK jobs")
        return jobs

    def _parse_job(self, data: dict) -> Optional[JobPost]:
        try:
            if not data.get("position"):
                return None

            title = data.get("position", "Unknown")
            company = data.get("company", "Unknown")
            job_url = data.get("url", "https://remoteok.com")

            salary_min = data.get("salary_min")
            salary_max = data.get("salary_max")

            if salary_min:
                salary_min = float(salary_min)
            if salary_max:
                salary_max = float(salary_max)

            return JobPost(
                title=title,
                company=company,
                location="Remote",
                job_url=job_url,
                source=self.site_name,
                is_remote=True,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_interval="yearly" if salary_min else None,
                date_posted=data.get("date"),
                description=data.get("description", "")[:500] if data.get("description") else None,
            )

        except Exception as e:
            self.logger.debug(f"Failed to parse RemoteOK job: {e}")
            return None