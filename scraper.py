"""
scraper.py - The main orchestrator (your version of JobSpy's scrape_jobs())

This is the "public API" of our scraper — the function users call.
It coordinates multiple scrapers to run in parallel (or sequentially),
deduplicates results, and returns them in a clean format.

This teaches you:
1. How to design a clean public API
2. Concurrent execution with ThreadPoolExecutor
3. Deduplication strategies
4. Data export (CSV, JSON)
"""

import csv
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed  # For parallel scraping

from models import JobPost
from scrapers.indeed_scraper import IndeedScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.remoteok_scraper import RemoteOKScraper

logger = logging.getLogger(__name__)


# Map site names → scraper classes
# This makes it easy to add new scrapers later — just add an entry here
SCRAPERS = {
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
    "remoteok": RemoteOKScraper,
}


def scrape_jobs(
    search_term: str,
    location: str = "Remote",
    site_name: Optional[List[str]] = None,
    results_wanted: int = 20,
    run_parallel: bool = False,  # Run scrapers at the same time (faster but riskier)
) -> List[JobPost]:
    """
    Main function — scrape jobs from multiple sites.
    This is your version of JobSpy's scrape_jobs().
    
    Args:
        search_term:     What to search for, e.g. "python developer"
        location:        Where to search, e.g. "New York, NY" or "Remote"
        site_name:       List of sites to scrape. None = all sites.
                         Options: ["indeed", "linkedin", "remoteok"]
        results_wanted:  How many results per site
        run_parallel:    If True, scrape all sites simultaneously (faster)
    
    Returns:
        List of JobPost objects, deduplicated and sorted by date
    
    Example:
        jobs = scrape_jobs(
            search_term="python developer",
            location="Remote",
            site_name=["indeed", "remoteok"],
            results_wanted=10
        )
    """
    
    # Default to all available scrapers
    if site_name is None:
        site_name = list(SCRAPERS.keys())
    
    # Validate site names
    invalid_sites = [s for s in site_name if s not in SCRAPERS]
    if invalid_sites:
        raise ValueError(f"Unknown sites: {invalid_sites}. Valid options: {list(SCRAPERS.keys())}")
    
    logger.info(f"Starting job search: '{search_term}' in '{location}' across {site_name}")
    
    all_jobs = []
    
    if run_parallel:
        # ── PARALLEL MODE ─────────────────────────────────────────────────────
        # Run multiple scrapers at the same time using threads.
        # ThreadPoolExecutor manages a pool of threads for us.
        # Each thread runs one scraper independently.
        # This is faster but may increase rate-limiting risk.
        
        with ThreadPoolExecutor(max_workers=len(site_name)) as executor:
            # Submit all scraping tasks
            future_to_site = {
                executor.submit(
                    _run_scraper, site, search_term, location, results_wanted
                ): site
                for site in site_name
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    logger.info(f"[{site}] Collected {len(jobs)} jobs")
                except Exception as e:
                    logger.error(f"[{site}] Scraper failed: {e}")
    
    else:
        # ── SEQUENTIAL MODE ───────────────────────────────────────────────────
        # Run scrapers one after another. Slower but safer and easier to debug.
        
        for site in site_name:
            try:
                jobs = _run_scraper(site, search_term, location, results_wanted)
                all_jobs.extend(jobs)
                logger.info(f"[{site}] Collected {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"[{site}] Scraper failed: {e}")
    
    # Remove duplicate jobs (same title + company)
    all_jobs = _deduplicate(all_jobs)
    
    logger.info(f"Total unique jobs found: {len(all_jobs)}")
    return all_jobs


def _run_scraper(site: str, search_term: str, location: str, results_wanted: int) -> List[JobPost]:
    """Helper to instantiate and run a single scraper."""
    ScraperClass = SCRAPERS[site]
    scraper = ScraperClass()
    return scraper.scrape(search_term, location, results_wanted)


def _deduplicate(jobs: List[JobPost]) -> List[JobPost]:
    """
    Remove duplicate job postings.
    
    We consider a job a duplicate if it has the same title AND company.
    This catches jobs that appear on multiple boards (e.g., same job on both Indeed and LinkedIn).
    
    We use a set to track what we've seen. Sets have O(1) lookup — very fast.
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        # Create a "fingerprint" for this job using title + company (lowercased for comparison)
        fingerprint = (job.title.lower().strip(), job.company.lower().strip())
        
        if fingerprint not in seen:
            seen.add(fingerprint)
            unique_jobs.append(job)
    
    duplicates_removed = len(jobs) - len(unique_jobs)
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate jobs")
    
    return unique_jobs


# ── Export Functions ───────────────────────────────────────────────────────────

def save_to_csv(jobs: List[JobPost], filename: str = "jobs.csv"):
    """
    Save job results to a CSV file.
    CSV (Comma-Separated Values) is a simple format that Excel and Google Sheets can open.
    """
    if not jobs:
        logger.warning("No jobs to save.")
        return
    
    # Get column names from the first job's dict keys
    fieldnames = list(jobs[0].to_dict().keys())
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()          # Write the column names row
        for job in jobs:
            writer.writerow(job.to_dict())
    
    logger.info(f"Saved {len(jobs)} jobs to {filename}")
    print(f"✅ Saved {len(jobs)} jobs to {filename}")


def save_to_json(jobs: List[JobPost], filename: str = "jobs.json"):
    """
    Save job results to a JSON file.
    JSON is great for web apps and APIs.
    """
    if not jobs:
        logger.warning("No jobs to save.")
        return
    
    data = [job.to_dict() for job in jobs]
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Saved {len(jobs)} jobs to {filename}")
    print(f"✅ Saved {len(jobs)} jobs to {filename}")
