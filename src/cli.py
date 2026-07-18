import argparse
import os
import time
import csv
import json
import gdown
import shutil
import webbrowser

from extractor.parser import extract_text
from extractor.engine import extract_structured_data
from matcher.evaluator import score_candidate

def determine_parse_quality(candidate_data):
    if not candidate_data:
        return "Failed", ["all"]

    missing_fields = []
    if not candidate_data.full_name: missing_fields.append("full_name")
    if not candidate_data.skills: missing_fields.append("skills")
    if not candidate_data.college_name or not candidate_data.degree_and_branch: 
        missing_fields.append("education_details")
    
    if missing_fields:
        return "Partial", missing_fields
    return "Clean", []

def main():
    parser = argparse.ArgumentParser(description="InternLoom Resume Shortlisting Engine")
    parser.add_argument("--data_source", required=True, help="Drive folder URL OR local path to resumes")
    parser.add_argument("--jds_dir", required=True, help="Path to the folder containing all JD JSON files") # <-- CHANGED
    
    args = parser.parse_args()

    # ==========================================
    # PREPARATION: Handle Files & Drive Links
    # ==========================================
    working_dir = args.data_source
    is_temp_dir = False

    if "drive.google.com" in args.data_source:
        print("📥 Google Drive link detected. Downloading files...")
        working_dir = "temp_drive_downloads"
        is_temp_dir = True
        if os.path.exists(working_dir): shutil.rmtree(working_dir)
        os.makedirs(working_dir, exist_ok=True)
        try:
            gdown.download_folder(args.data_source, output=working_dir, quiet=False, use_cookies=False)
        except Exception as e:
            print(f"❌ Failed to download from Google Drive: {e}")
            return
    elif not os.path.exists(working_dir):
        print(f"❌ Local path {working_dir} does not exist.")
        return

    # Load ALL Job Descriptions from the folder
    jds = []
    for jd_file in os.listdir(args.jds_dir):
        if jd_file.endswith('.json'):
            with open(os.path.join(args.jds_dir, jd_file), 'r', encoding='utf-8') as f:
                jds.append({"filename": jd_file, "data": json.load(f)})
                
    if not jds:
        print("❌ No Job Descriptions found in the specified folder.")
        return

    # ==========================================
    # PHASE 1: EXTRACTION (Run Once Per Resume)
    # ==========================================
    allowed_extensions = ('.pdf', '.docx', '.txt', '.xml')
    resume_files = [f for f in os.listdir(working_dir) if f.lower().endswith(allowed_extensions)]
    resume_files = resume_files[:3]
    print(f"\n🚀 PHASE 1: Extracting {len(resume_files)} resumes...")
    
    parse_report = []
    parsed_candidates = [] # Store them in memory so we don't re-extract them!

    for filename in resume_files:
        filepath = os.path.join(working_dir, filename)
        raw_text = extract_text(filepath)
        
        if not raw_text.strip():
            parse_report.append({"file": filename, "status": "Failed", "failed_what": "No text extracted"})
            parsed_candidates.append({"file": filename, "status": "Failed", "data": None})
            continue

        candidate_data = extract_structured_data(raw_text)
        status, missing_fields = determine_parse_quality(candidate_data)
        
        parse_report.append({
            "file": filename, 
            "status": status, 
            "failed_what": ", ".join(missing_fields) if missing_fields else "N/A"
        })
        
        parsed_candidates.append({
            "file": filename, 
            "status": status, 
            "data": candidate_data
        })
        
        print(f"✅ Extracted {filename}. Resting 4s for API limits...")
        time.sleep(2)

    # ==========================================
    # PHASE 2: SCORING (Against ALL JDs)
    # ==========================================
    print(f"\n🚀 PHASE 2: Scoring candidates against {len(jds)} Job Descriptions...")
    master_output = {}

    for jd in jds:
        role_name = jd["data"].get("role", jd["filename"])
        print(f"\n--- Evaluating for: {role_name} ---")
        
        AVAILABLE_SLOTS = jd["data"].get("slots", 0)
        scored_candidates = []
        failed_reviews = []
        
        for candidate in parsed_candidates:
            if candidate["status"] == "Failed":
                failed_reviews.append({
                    "file": candidate["file"],
                    "score": None,
                    "flag": "FAILED_PARSE",
                    "reasoning": "RECOMMENDATION FOR HUMAN REVIEW"
                })
                continue
                
            evaluation = score_candidate(candidate["data"], jd["data"], candidate["status"])
            
            scored_candidates.append({
                "candidate_name": candidate["data"].full_name or candidate["file"],
                "file": candidate["file"],
                "score": evaluation["score"],
                "reasoning": evaluation["reasoning"],
                "parse_status": candidate["status"]
            })
            
            print(f"Scored {candidate['file']} for {role_name}. Resting 4s...")
            time.sleep(2)
            
        # Apply Slot Awareness per JD
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        master_output[role_name] = {
            "available_slots": AVAILABLE_SLOTS,
            "shortlist": scored_candidates[:AVAILABLE_SLOTS],
            "reserve": scored_candidates[AVAILABLE_SLOTS:],
            "human_review_required": failed_reviews
        }

    # ==========================================
    # OUTPUT GENERATION
    # ==========================================
    os.makedirs("output", exist_ok=True)
    os.makedirs("documents", exist_ok=True)

    # 1. Save the Master Dashboard Output
    with open("output/sample_output.json", 'w', encoding='utf-8') as f:
        json.dump(master_output, f, indent=4)
        
    # 2. Save the Parse Quality CSV
    with open("documents/parse_quality_report.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["file", "status", "failed_what"])
        writer.writeheader()
        writer.writerows(parse_report)

    # 3. NEW: Save the Extracted Student Details (Candidate Database)
    extracted_export = []
    for candidate in parsed_candidates:
        if candidate["data"]:
            # Convert the Pydantic object to a standard dictionary
            record = candidate["data"].model_dump() 
            # Attach the system metadata so you know which file it came from
            record["source_file"] = candidate["file"]
            record["parse_status"] = candidate["status"]
            extracted_export.append(record)
            
    with open("output/extracted_student_details.json", 'w', encoding='utf-8') as f:
        json.dump(extracted_export, f, indent=4)

    # Clean up temporary drive folder if used
    if is_temp_dir: shutil.rmtree(working_dir)
    print("\n✅ Pipeline complete! Master JSON, CSV, and Student Details generated.")
    
    # ==========================================
    # LAUNCH DASHBOARD
    # ==========================================
    dashboard_path = os.path.abspath("dashboard.html")
    if os.path.exists(dashboard_path):
        print("🌐 Opening Master Dashboard in your browser...")
        # The 'file://' prefix ensures the browser knows it's a local file
        webbrowser.open(f"file://{dashboard_path}")
    else:
        print("⚠️ dashboard.html not found. Make sure it is in the same folder as your script.")


if __name__ == "__main__":
    main()