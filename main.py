import argparse
from datetime import datetime

from scraper import scrape_jobs, save_to_csv, save_to_json, SCRAPERS


def print_jobs(jobs):
    print(f"\n{'='*60}")
    print(f"  📋 FOUND {len(jobs)} JOBS")
    print(f"{'='*60}")

    for i, job in enumerate(jobs, 1):
        print(f"\n  #{i} [{job.source.upper()}]")
        print(f"  {job.title} @ {job.company}")
        print(f"  {job.location}" + (" 🌐 REMOTE" if job.is_remote else ""))

        if job.salary_display:
            print(f"    {job.salary_display}")
        if job.job_type:
            print(f"    {job.job_type}")
        if job.date_posted:
            print(f"    {job.date_posted}")

        print(f"  🔗  {job.job_url}")

    print(f"\n{'='*60}\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description="🔍 Job Scraper — Indeed, LinkedIn, RemoteOK",
    )
    parser.add_argument("--search",   "-s", default="software engineer")
    parser.add_argument("--location", "-l", default="Remote")
    parser.add_argument("--sites",    nargs="+", choices=list(SCRAPERS.keys()), default=["remoteok"])
    parser.add_argument("--results",  "-r", type=int, default=10)
    parser.add_argument("--output",   "-o", choices=["csv", "json", "both", "none"], default="csv")
    parser.add_argument("--parallel", action="store_true")
    return parser


def main():
    args = build_parser().parse_args()

    print(f"\n🔍 '{args.search}' | 📍 {args.location} | 🌐 {', '.join(args.sites)} | 📊 {args.results} results\n")

    jobs = scrape_jobs(
        search_term=args.search,
        location=args.location,
        site_name=args.sites,
        results_wanted=args.results,
        run_parallel=args.parallel,
    )

    if not jobs:
        print("❌ No jobs found. Try different search terms.")
        return

    print_jobs(jobs)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.output in ("csv", "both"):
        save_to_csv(jobs, f"jobs_{timestamp}.csv")
    if args.output in ("json", "both"):
        save_to_json(jobs, f"jobs_{timestamp}.json")


if __name__ == "__main__":
    main()