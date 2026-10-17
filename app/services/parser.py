import io
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Extracts text from an uploaded PDF or DOCX resume file.
    """
    filename = file.filename.lower()
    contents = await file.read()
    
    text = ""
    
    try:
        if filename.endswith(".pdf"):
            # Read PDF using pypdf
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        elif filename.endswith(".docx"):
            # Read Word Document using python-docx
            doc_file = io.BytesIO(contents)
            doc = Document(doc_file)
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file format. Please upload a PDF or DOCX file."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error reading file: {str(e)}"
        )
        
    if not text.strip():
        raise HTTPException(
            status_code=400, 
            detail="The uploaded file appears to be empty or unreadable."
        )
        
    return text.strip()