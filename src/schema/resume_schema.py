from pydantic import BaseModel
from typing import List, Optional

class Project(BaseModel):
    title: Optional[str]
    description: Optional[str]

class Experience(BaseModel):
    company: Optional[str]
    role: Optional[str]
    duration: Optional[str]

class CandidateData(BaseModel):
    full_name: Optional[str]
    email_address: Optional[str]
    phone_number: Optional[str]
    
    college_name: Optional[str]
    degree_and_branch: Optional[str]
    graduation_year: Optional[int]
    
    raw_cgpa_or_percentage: Optional[str] 
    normalized_cgpa: Optional[float]
    cgpa_assumption: Optional[str]
    
    skills: Optional[List[str]]
    projects: Optional[List[Project]]
    experience: Optional[List[Experience]]
    certifications: Optional[List[str]]