import csv
import re
import json
import logging
import pandas as pd
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from models import JobPost
from scrapers.indeed_scraper import IndeedScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.remoteok_scraper import RemoteOKScraper

logger = logging.getLogger(__name__)

SCRAPERS = {
    "indeed":   IndeedScraper,
    "linkedin":  LinkedInScraper,
    "remoteok":  RemoteOKScraper,
}

# Columns we want in the CSV and in what order
CSV_COLUMNS = [
    "title",
    "company",
    "location",
    "is_remote",
    "job_type",
    "salary_min",
    "salary_max",
    "salary_interval",
    "date_posted",
    "source",
    "job_url",
    "description",
]


# ── Main function ─────────────────────────────────────────────────────────────

def scrape_jobs(
    search_term: str,
    location: str = "Remote",
    site_name: Optional[List[str]] = None,
    results_wanted: int = 20,
    run_parallel: bool = False,
) -> List[JobPost]:

    sites = site_name or list(SCRAPERS.keys())

    invalid = [s for s in sites if s not in SCRAPERS]
    if invalid:
        raise ValueError(f"Unknown sites: {invalid}. Valid: {list(SCRAPERS.keys())}")

    logger.info(f"Searching '{search_term}' in '{location}' across {sites}")

    all_jobs = _run_parallel(sites, search_term, location, results_wanted) \
               if run_parallel else \
               _run_sequential(sites, search_term, location, results_wanted)

    unique_jobs = _deduplicate(all_jobs)
    logger.info(f"Total unique jobs found: {len(unique_jobs)}")
    return unique_jobs


# ── Running scrapers ──────────────────────────────────────────────────────────

def _run_sequential(sites, search_term, location, results_wanted) -> List[JobPost]:
    all_jobs = []
    for site in sites:
        try:
            jobs = _run_one(site, search_term, location, results_wanted)
            all_jobs.extend(jobs)
            logger.info(f"[{site}] Collected {len(jobs)} jobs")
        except Exception as e:
            logger.error(f"[{site}] Failed: {e}")
    return all_jobs


def _run_parallel(sites, search_term, location, results_wanted) -> List[JobPost]:
    all_jobs = []
    with ThreadPoolExecutor(max_workers=len(sites)) as executor:
        futures = {
            executor.submit(_run_one, site, search_term, location, results_wanted): site
            for site in sites
        }
        for future in as_completed(futures):
            site = futures[future]
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
                logger.info(f"[{site}] Collected {len(jobs)} jobs")
            except Exception as e:
                logger.error(f"[{site}] Failed: {e}")
    return all_jobs


def _run_one(site: str, search_term: str, location: str, results_wanted: int) -> List[JobPost]:
    scraper = SCRAPERS[site]()
    return scraper.scrape(search_term, location, results_wanted)


# ── Deduplication ─────────────────────────────────────────────────────────────

def _deduplicate(jobs: List[JobPost]) -> List[JobPost]:
    seen = set()
    unique = []
    for job in jobs:
        key = (job.title.lower(), job.company.lower())
        if key not in seen:
            seen.add(key)
            unique.append(job)
    removed = len(jobs) - len(unique)
    if removed:
        logger.info(f"Removed {removed} duplicates")
    return unique


# ── Export ────────────────────────────────────────────────────────────────────
def _clean_description(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = " ".join(text.split())
    return text[:200] + "..." if len(text) > 200 else text

def save_to_csv(jobs: List[JobPost], filename: str = "jobs.csv"):
    if not jobs:
        print("No jobs to save.")
        return

    # Convert all jobs to a list of dicts
    data = [job.to_dict() for job in jobs]

    # Create a pandas DataFrame — like a table in Python
    df = pd.DataFrame(data)

    # Keep only the columns we want, in the right order
    df = df[CSV_COLUMNS]

    # Clean up the data
    df["title"]     = df["title"].str.title()        # Title Case for job titles
    df["company"]   = df["company"].str.title()      # Title Case for company names
    df["source"]    = df["source"].str.upper()       # UPPERCASE for source
    df["is_remote"] = df["is_remote"].map({True: "Yes", False: "No", None: "Unknown"})
    df["job_type"]  = df["job_type"].fillna("Not specified")
    df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce").dt.strftime("%d %b %Y")

    # Format salary as readable string e.g. "$80,000"
    df["salary_min"] = df["salary_min"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "")
    df["salary_max"] = df["salary_max"].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "")

    df["description"] = df["description"].apply(_clean_description)

    # Rename columns to be human readable
    df.columns = [col.replace("_", " ").title() for col in df.columns]

    # Save to CSV
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ Saved {len(jobs)} jobs to {filename}")


def save_to_json(jobs: List[JobPost], filename: str = "jobs.json"):
    if not jobs:
        return
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([job.to_dict() for job in jobs], f, indent=2, default=str)
    print(f"✅ Saved {len(jobs)} jobs to {filename}")