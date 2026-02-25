from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from unittest import result


@dataclass
class JobPost:
    #Each field corresponds to a piece of info we scrape from the job board.
    #@dataclass automatically generates __init__, __repr__, etc. for us.
    
    # Required fields
    title: str                     
    company: str              
    location: str                 
    job_url: str                   
    source: str                    
    
    #Optional[str] means the field can be a string or none
    description: Optional[str] = None       
    job_type: Optional[str] = None          
    is_remote: Optional[bool] = None        
    date_posted: Optional[str] = None      
    salary_min: Optional[float] = None      
    salary_max: Optional[float] = None    
    salary_interval: Optional[str] = None   
    
    def to_dict(self) -> dict:
        #Convert this job post into a plain dictionary 
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "job_url": self.job_url,
            "source": self.source,
            "description": self.description,
            "job_type": self.job_type,
            "is_remote": self.is_remote,
            "date_posted": self.date_posted,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_interval": self.salary_interval,
        }
    
    def __str__(self):

        # Build the salary text
        if self.salary_min and self.salary_max:
            salary_text = " | $" + str(self.salary_min) + " - $" + str(self.salary_max)
        else:
            salary_text = ""

        # Build the remote text
        if self.is_remote:
            remote_text = " | REMOTE"
        else:
            remote_text = ""

        # Join everything and return
        result = "[" + self.source.upper() + "] " + self.title + " @ " + self.company + " — " + self.location + remote_text + salary_text
        return result
