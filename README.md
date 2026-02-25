# 🔍 JobScraper — Build Your Own Job Scraper

A Python job scraper that works like JobSpy, built from scratch so you can
**understand every line**. Scrapes jobs from Indeed, LinkedIn, and RemoteOK.

---

## 📁 Project Structure

```
jobscraper/
├── main.py               ← CLI entry point (run this)
├── scraper.py            ← Main orchestrator (like JobSpy's scrape_jobs())
├── models.py             ← Data structures (what a "job" looks like)
├── requirements.txt      ← Python dependencies
└── scrapers/
    ├── __init__.py       ← Makes this a Python package
    ├── base_scraper.py   ← Shared utilities all scrapers inherit
    ├── indeed_scraper.py ← Indeed.com scraper (HTML parsing)
    ├── linkedin_scraper.py ← LinkedIn scraper (API sniffing)
    └── remoteok_scraper.py ← RemoteOK scraper (JSON API — easiest!)
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

---

## 🧠 Key Concepts — What You're Learning

### 1. Object-Oriented Programming (OOP)
The project uses **inheritance**. `BaseScraper` is the parent class with shared code.
`IndeedScraper`, `LinkedInScraper`, and `RemoteOKScraper` are child classes that
**inherit** all that shared code and only implement their own specific logic.

```
BaseScraper (parent)
├── _get()              ← All scrapers use this to make HTTP requests
├── _rotate_user_agent() ← All scrapers use this
└── scrape()            ← Abstract — each child MUST implement this

IndeedScraper (child)   ← Has its own scrape() for Indeed's HTML structure
LinkedInScraper (child) ← Has its own scrape() for LinkedIn's structure
RemoteOKScraper (child) ← Has its own scrape() for RemoteOK's JSON API
```

### 2. Three Types of Scraping (from easy to hard)

| Type | Site | Technique | Difficulty |
|------|------|-----------|------------|
| **JSON API** | RemoteOK | `response.json()` | ⭐ Easy |
| **HTML + known API** | LinkedIn | BeautifulSoup on their internal API | ⭐⭐ Medium |
| **HTML parsing** | Indeed | BeautifulSoup on full page HTML | ⭐⭐⭐ Hard |

**Start with RemoteOK** to understand the basics, then move to Indeed.

### 3. How HTML Parsing Works
```python
from bs4 import BeautifulSoup

# Pretend this is what Indeed's HTML looks like:
html = """
<div class="job_seen_beacon">
  <h2 class="jobTitle"><a href="/viewjob?jk=abc123">Python Developer</a></h2>
  <span data-testid="company-name">Acme Corp</span>
  <div data-testid="text-location">New York, NY</div>
</div>
"""

soup = BeautifulSoup(html, "html.parser")

# Find elements by class or attribute:
title = soup.find("h2", class_="jobTitle").get_text(strip=True)
company = soup.find("span", {"data-testid": "company-name"}).get_text()
location = soup.find("div", {"data-testid": "text-location"}).get_text()

print(title)    # "Python Developer"
print(company)  # "Acme Corp"
print(location) # "New York, NY"
```

### 4. Why We Add Delays
Job boards detect bots by looking for:
- Requests that come too fast (humans can't click that quickly)
- Identical request headers every time
- Too many requests from one IP

Our scraper handles this by:
- Sleeping 2-3 seconds between requests (+ random extra time)
- Rotating User-Agent headers
- Using session cookies (looks more like a browser)

### 5. Rate Limiting & Getting Blocked
If you get HTTP 429 errors, the site has rate-limited you. Solutions:
- Increase the delay: `IndeedScraper(delay_between_requests=5.0)`
- Use proxy IPs (for advanced use)
- Reduce results_wanted

---

## ⚙️ Configuration

### Custom delays
```python
from scrapers.indeed_scraper import IndeedScraper

# Use 5 second delays for Indeed (safer)
scraper = IndeedScraper(delay_between_requests=5.0)
jobs = scraper.scrape("software engineer", "Remote", results_wanted=20)
```

### Parallel scraping (faster but riskier)
```python
jobs = scrape_jobs(
    search_term="developer",
    site_name=["indeed", "remoteok"],
    run_parallel=True,   # Both scrapers run at the same time
)
```

---

## 🔧 Adding a New Site

1. Create `scrapers/newsite_scraper.py`
2. Inherit from `BaseScraper`
3. Implement `site_name` and `scrape()`
4. Register it in `scraper.py`'s `SCRAPERS` dict

```python
# scrapers/newsite_scraper.py
from scrapers.base_scraper import BaseScraper
from models import JobPost

class NewSiteScraper(BaseScraper):
    @property
    def site_name(self):
        return "newsite"
    
    def scrape(self, search_term, location, results_wanted=20):
        # Your scraping logic here
        response = self._get("https://newsite.com/jobs", params={"q": search_term})
        # ... parse response ...
        return []  # Return list of JobPost objects
```

```python
# In scraper.py, add to SCRAPERS dict:
SCRAPERS = {
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
    "remoteok": RemoteOKScraper,
    "newsite": NewSiteScraper,  # ← add this
}
```

---

## ⚠️ Tips & Common Issues

**Problem: Getting 0 results from Indeed/LinkedIn**
- Their HTML structure changes frequently. Open the site in your browser,
  right-click → "Inspect Element" on a job card, find the new class names,
  and update the selectors in the scraper.

**Problem: Getting blocked (403/429 errors)**
- Increase the delay
- Add a proxy: `session.proxies = {"https": "http://user:pass@host:port"}`

**Problem: LinkedIn returning empty results**
- LinkedIn requires the `X-Requested-With` header (already set in our scraper)
- Try increasing the delay to 5+ seconds

---

## 📚 Next Steps to Learn More

1. **Add more sites**: Try scraping Glassdoor, ZipRecruiter, or local job boards
2. **Add a database**: Store jobs in SQLite instead of CSV using Python's built-in `sqlite3`
3. **Build a web UI**: Use Flask or FastAPI to make a web app around this scraper
4. **Add email alerts**: Email yourself when new matching jobs appear
5. **Learn Selenium/Playwright**: For JavaScript-heavy sites that don't work with requests

---

## 📄 License
MIT — use this for anything, learn from it, build on it!
