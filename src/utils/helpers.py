import re

def normalize_cgpa(raw_score: str) -> dict:
    """
    Normalizes CGPA based on hackathon rules and flags ambiguous scales.
    Returns: {"value": float or None, "assumption": str or None}
    """
    if not raw_score:
        return {"value": None, "assumption": None}
        
    # Extract the first valid number
    match = re.search(r'\d+(\.\d+)?', raw_score)
    if not match:
        return {"value": None, "assumption": None}
        
    score = float(match.group())
    raw_upper = raw_score.upper()
    
    # 1. Percentage (e.g., 79% -> 8.3)
    if '%' in raw_score or score > 10.0:
        return {"value": round(score / 9.5, 2), "assumption": None}
        
    # 2. 4-point scale explicitly stated (e.g., 3.6/4 -> 9.0)
    if '/4' in raw_score or '4.0' in raw_score or 'GPA' in raw_upper:
        return {"value": round(score * 2.5, 2), "assumption": None}
        
    # 3. 10-point scale explicitly stated (e.g., 8.4/10 -> 8.4)
    if '/10' in raw_score or '10.0' in raw_score or 'CGPA' in raw_upper:
        if score <= 10.0:
            return {"value": round(score, 2), "assumption": None}
            
    # 4. AMBIGUOUS SCALE (No %, /10, /4, GPA, or CGPA context provided)
    if score <= 4.0:
        # Assume it is a 4-point scale
        return {
            "value": round(score * 2.5, 2), 
            "assumption": f"Ambiguous scale '{raw_score}'. Assumed 4-point scale, multiplied by 2.5."
        }
    elif score <= 10.0:
        # Assume it is a 10-point scale
        return {
            "value": round(score, 2), 
            "assumption": f"Ambiguous scale '{raw_score}'. Assumed 10-point scale, used as-is."
        }
        
    return {"value": None, "assumption": None}