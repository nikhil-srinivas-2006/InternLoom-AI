import fitz  # PyMuPDF
import docx  # python-docx
import os

def extract_text(filepath: str) -> str:
    """Extracts raw text from PDF, DOCX, or TXT files."""
    text = ""
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.pdf':
            doc = fitz.open(filepath)
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text += page_text + "\n"
            doc.close()
            
        elif ext == '.docx':
            doc = docx.Document(filepath)
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"
                    
        elif ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
        else:
            print(f"⚠️ Unsupported file type ignored: {filepath}")
            
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
    
    return text