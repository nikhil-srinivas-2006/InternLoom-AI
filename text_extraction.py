import os
from src.extractor.parser import extract_text
from src.extractor.engine import extract_structured_data

def test_single_resume(pdf_path: str):
    print(f"--- Testing Extraction for: {pdf_path} ---")
    
    # 1. Extract raw text
    print("1. Extracting raw text with pdfplumber...")
    raw_text = extract_text(pdf_path)
    
    if not raw_text.strip():
        print("❌ FAILED: No text extracted. (Might be a scanned image requiring OCR)")
        return

    print(f"✅ Extracted {len(raw_text)} characters of raw text.")
    
    # 2. Extract structured data with Gemini
    print("2. Sending to Gemini for structuring (this takes a few seconds)...")
    candidate_data = extract_structured_data(raw_text)
    
    if candidate_data:
        print("\n✅ Structuring Successful! Here is the JSON output:\n")
        # model_dump_json is a Pydantic method that converts the object to a JSON string
        print(candidate_data.model_dump_json(indent=4))
    else:
        print("❌ Structuring Failed. Engine returned None.")

if __name__ == "__main__":
    # Update this filename to match one of the PDFs in your folder!
    target_resume = "data/dummy_resumes/SDE_Resume_2_Meera_Pillai.pdf" 
    
    if os.path.exists(target_resume):
        test_single_resume(target_resume)
    else:
        print(f"File not found: {target_resume}")
        print("Please check the filename and try again.")