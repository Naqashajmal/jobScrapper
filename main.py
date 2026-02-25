"""
main.py - Run the job scraper from the command line

This is the entry point. Run it like:
    python main.py
    python main.py --search "data analyst" --location "Remote" --sites indeed remoteok
    python main.py --search "backend developer" --location "London" --results 30

Uses argparse to handle command-line arguments — the standard Python way to build CLIs.
"""

import argparse
import sys
import os

# Make sure Python can find our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_jobs, save_to_csv, save_to_json, SCRAPERS


def print_jobs(jobs):
    """Print jobs in a readable format to the terminal."""
    print("\n" + "="*70)
    print(f"  📋 FOUND {len(jobs)} JOBS")
    print("="*70)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{'─'*60}")
        print(f"  #{i} [{job.source.upper()}]")
        print(f"  🏷️  Title:    {job.title}")
        print(f"  🏢  Company:  {job.company}")
        print(f"  📍  Location: {job.location}", end="")
        print(" 🌐 REMOTE" if job.is_remote else "")
        
        if job.salary_min:
            salary_str = f"${job.salary_min:,.0f}"
            if job.salary_max:
                salary_str += f" - ${job.salary_max:,.0f}"
            if job.salary_interval:
                salary_str += f" / {job.salary_interval}"
            print(f"  💰  Salary:   {salary_str}")
        
        if job.job_type:
            print(f"  📄  Type:     {job.job_type}")
        
        if job.date_posted:
            print(f"  📅  Posted:   {job.date_posted}")
        
        print(f"  🔗  URL:      {job.job_url}")
    
    print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="🔍 Job Scraper — Scrape jobs from Indeed, LinkedIn, RemoteOK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --search "python developer" --location "Remote" --sites remoteok
  python main.py --search "data scientist" --location "New York" --results 30 --output csv
        """
    )
    
    parser.add_argument(
        "--search", "-s",
        default="software engineer",
        help="Job title or keywords to search for (default: 'software engineer')"
    )
    parser.add_argument(
        "--location", "-l",
        default="Remote",
        help="Location to search in (default: 'Remote')"
    )
    parser.add_argument(
        "--sites",
        nargs="+",  # Accept one or more values
        choices=list(SCRAPERS.keys()),
        default=["remoteok"],  # Default to remoteok since it's most reliable
        help=f"Sites to scrape. Options: {list(SCRAPERS.keys())}. Default: remoteok"
    )
    parser.add_argument(
        "--results", "-r",
        type=int,
        default=10,
        help="Number of results to fetch per site (default: 10)"
    )
    parser.add_argument(
        "--output", "-o",
        choices=["csv", "json", "both", "none"],
        default="csv",
        help="Output format (default: csv)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",  # Flag — True if --parallel is passed, False otherwise
        help="Run scrapers in parallel (faster but may trigger rate limits)"
    )
    
    args = parser.parse_args()
    
    print(f"\n🔍 Searching for: '{args.search}'")
    print(f"📍 Location: {args.location}")
    print(f"🌐 Sites: {', '.join(args.sites)}")
    print(f"📊 Results per site: {args.results}")
    print(f"⚡ Parallel: {args.parallel}")
    print()
    
    # Run the scraper
    jobs = scrape_jobs(
        search_term=args.search,
        location=args.location,
        site_name=args.sites,
        results_wanted=args.results,
        run_parallel=args.parallel,
    )
    
    if not jobs:
        print("❌ No jobs found. Try different search terms or check your internet connection.")
        return
    
    # Print results to terminal
    print_jobs(jobs)
    
    # Save to file
    if args.output in ("csv", "both"):
        save_to_csv(jobs, "jobs.csv")
    if args.output in ("json", "both"):
        save_to_json(jobs, "jobs.json")


if __name__ == "__main__":
    main()
