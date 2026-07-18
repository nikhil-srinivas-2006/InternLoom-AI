import os
import json
import time
from groq import Groq
from dotenv import load_dotenv
from schema.resume_schema import CandidateData
from utils.helpers import normalize_cgpa

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an expert data extractor. Extract the candidate's details from the provided resume text. 
1. If a field is missing, you MUST return null. Do not guess or assume.
2. SKILL EXTRACTION (CRITICAL): Do not just look for a 'Skills' header. You must extract skills from the ENTIRE document. Read through project descriptions, work experience bullets, and certifications. If a candidate mentions building a "MERN stack application" in a project, you must extract "MongoDB", "Express", "React", and "Node.js" into the skills array.
3. For projects, strictly provide the title and summarize the description into a single line.


You MUST return strictly valid JSON matching this exact structure:
{
    "full_name": "string or null",
    "email_address": "string or null",
    "phone_number": "string or null",
    "college_name": "string or null",
    "degree_and_branch": "string or null",
    "graduation_year": 2024, 
    "raw_cgpa_or_percentage": "string or null",
    "normalized_cgpa": null,
    "skills": ["string"],
    "projects": [
        {
            "title": "string or null",
            "description": "string or null"
        }
    ],
    "experience": [
        {
            "company": "string or null",
            "role": "string or null",
            "duration": "string or null"
        }
    ],
    "certifications": ["string"]
}
"""

def extract_structured_data(raw_pdf_text: str) -> CandidateData:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", # Upgraded to 70B for flawless JSON
                response_format={"type": "json_object"},
                temperature=0.0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"RESUME TEXT:\n{raw_pdf_text}"}
                ]
            )
            
            extracted_dict = json.loads(response.choices[0].message.content)
            
            raw_cgpa = extracted_dict.get("raw_cgpa_or_percentage")
            cgpa_data = normalize_cgpa(raw_cgpa) 
            extracted_dict["normalized_cgpa"] = cgpa_data["value"]
            extracted_dict["cgpa_assumption"] = cgpa_data["assumption"] 
            
            return CandidateData(**extracted_dict)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg:
                print(f"    ⚠️ Groq Rate Limit Hit! Sleeping for 60 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(60)
            else:
                print(f"    ❌ Extraction Error: {e}")
                return None
                
    print("Failed to extract data: Rate limit max retries exceeded.")
    return None