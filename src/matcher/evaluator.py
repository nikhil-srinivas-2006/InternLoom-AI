import os
import json
from groq import Groq
import time
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an expert technical recruiter AI. Evaluate the candidate's structured resume data against the Job Description.

SCORING WEIGHTS & LOGIC:
1. Skill Matching (0-60 points): 
   - Exact and Synonym matches get full credit.
   - Partial matches get partial credit.
   - Implicit matches (implied by projects) get credit but note Low confidence.

2. Signal Conflict Resolution (0-40 points) - YOU MUST RESOLVE THESE SPECIFICALLY:
   - High CGPA, zero projects: Strong academic, weak practical. Penalize the final score for developer roles.
   - Low CGPA, multiple deployed projects: Weak academic, strong practical. Forgive the CGPA deficit and grant high points.
   - Perfect skill match, non-CS degree: Role fit overrides educational background. Do NOT penalize the candidate if their skills perfectly match the JD.

You MUST return strictly valid JSON matching this exact structure:
{
    "raw_score": <int between 0 and 100>,
    "reasoning": "<A strict 2-3 sentence explanation addressing skill match types and how you resolved any signal conflicts.>"
}
"""


def score_candidate(candidate_data, jd_data, parse_status: str) -> dict:
    resume_json = candidate_data.model_dump_json(exclude_none=True)
    jd_json = json.dumps(jd_data)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"JOB DESCRIPTION:\n{jd_json}\n\nCANDIDATE RESUME DATA:\n{resume_json}"}
                ]
            )
            
            evaluation = json.loads(response.choices[0].message.content)
            final_score = evaluation.get("raw_score", 0)
            reasoning = evaluation.get("reasoning", "No reasoning provided.")
            
            if parse_status == "Partial":
                final_score = min(final_score, 50)
                reasoning = f"[PARTIAL PARSE PENALTY APPLIED] {reasoning}"
                
            if candidate_data.cgpa_assumption:
                final_score = min(final_score, 40)
                reasoning = f"[LOW CONFIDENCE: {candidate_data.cgpa_assumption}] {reasoning}"
                
            return {"score": final_score, "reasoning": reasoning}
            
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg:
                print(f"    ⚠️ Groq Rate Limit Hit! Sleeping for 60 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(60)
            else:
                print(f"    ❌ Scoring Error: {e}")
                return {"score": 0, "reasoning": "Scoring failed due to AI error."}
                
    return {"score": 0, "reasoning": "Scoring failed: Rate limit max retries exceeded."}