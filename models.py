from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class JobPost:

    title: str
    company: str
    location: str
    job_url: str
    source: str

    description: Optional[str] = None
    job_type: Optional[str] = None
    is_remote: Optional[bool] = None
    date_posted: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_interval: Optional[str] = None

    def __post_init__(self):
        self.title = self.title.strip()
        self.company = self.company.strip()
        self.location = self.location.strip()
        self.source = self.source.lower().strip()

        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.company:
            raise ValueError("company cannot be empty")
        if not self.job_url:
            raise ValueError("job_url cannot be empty")

    @property
    def salary_display(self) -> Optional[str]:
        if not self.salary_min and not self.salary_max:
            return None
        interval = f" / {self.salary_interval}" if self.salary_interval else ""
        if self.salary_min and self.salary_max:
            return f"${self.salary_min:,.0f} - ${self.salary_max:,.0f}{interval}"
        return f"${self.salary_min:,.0f}{interval}" if self.salary_min else None

    def to_dict(self) -> dict:
        return asdict(self)

    def __str__(self) -> str:
        location = self.location + (" | REMOTE" if self.is_remote else "")
        salary = f" | {self.salary_display}" if self.salary_display else ""
        return f"[{self.source.upper()}] {self.title} @ {self.company} — {location}{salary}"