# 🔍 JobScraper — Job Board Scraper

A Python job scraper, built from scratch so you can
Scrapes jobs from Indeed, LinkedIn, and RemoteOK.


## 📁 Project Structure

```
jobscraper/
├── main.py               ← CLI entry point (run this)
├── scraper.py            ← Main orchestrator 
├── models.py             ← Data structures (what a "job" looks like)
├── requirements.txt      ← Python dependencies
└── scrapers/
    ├── __init__.py       ← Makes this a Python package
    ├── base_scraper.py   ← Shared utilities all scrapers inherit
    ├── indeed_scraper.py ← Indeed.com scraper 
    ├── linkedin_scraper.py ← LinkedIn scraper 
    └── remoteok_scraper.py ← RemoteOK scraper
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run it
```bash
# Basic usage (RemoteOK — most reliable to start)
python main.py --search "python developer" --sites remoteok

# Search Indeed
python main.py --search "data analyst" --location "New York" --sites indeed

# Multiple sites, save as JSON
python main.py --search "backend developer" --sites indeed remoteok --output json

# Get more results
python main.py --search "machine learning" --sites remoteok --results 30
```

### 3. Use it as a library in your own scripts
```python
from scraper import scrape_jobs, save_to_csv

jobs = scrape_jobs(
    search_term="python developer",
    location="Remote",
    site_name=["indeed", "remoteok"],
    results_wanted=20,
)

for job in jobs:
    print(job)

save_to_csv(jobs, "my_jobs.csv")
```



