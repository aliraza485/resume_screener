from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Union, Dict, Any
import json
import csv
import io
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.services.parser import extract_text_from_file
from app.services.screener import analyze_resume_with_ai
from app.schemas.models import ScreeningResponse, ScreeningRecord
from app.database import SessionLocal, EvaluationDB

# ==========================================
# 1. INITIALIZE ROUTER FIRST (Crucial Step)
# ==========================================
router = APIRouter()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/screen", response_model=ScreeningResponse)
async def screen_single_resume(
    file: UploadFile = File(..., description="Upload candidate resume (PDF or DOCX)"),
    job_description: str = Form(..., description="Paste the target job description here"),
    db: Session = Depends(get_db)
):
    """
    Screens a single resume against a job description, saves to DB, and returns the evaluation.
    """
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
        
    resume_text = await extract_text_from_file(file)
    result = await analyze_resume_with_ai(resume_text, job_description)
    
    # Save to SQLite Database
    db_item = EvaluationDB(
        filename=file.filename,
        candidate_name=result.candidate_name,
        match_score=result.match_score,
        matching_skills=json.dumps(result.matching_skills),
        missing_skills=json.dumps(result.missing_skills),
        summary_reasoning=result.summary_reasoning,
        recommendation=result.recommendation
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    response_data = result.model_dump() if hasattr(result, "model_dump") else result.dict()
    response_data["id"] = db_item.id
    return response_data

@router.post("/screen/batch", response_model=List[dict])
async def screen_batch_resumes(
    files: List[UploadFile] = File(..., description="Upload multiple candidate resumes (PDF or DOCX)"),
    job_description: str = Form(..., description="Paste the target job description here"),
    db: Session = Depends(get_db)
):
    """
    Screens multiple resumes concurrently, ranks them in descending order by match score, and saves to DB.
    """
    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    
    if not files:
        raise HTTPException(status_code=400, detail="Please upload at least one resume file.")

    results = []

    for file in files:
        try:
            resume_text = await extract_text_from_file(file)
            result = await analyze_resume_with_ai(resume_text, job_description)
            
            db_item = EvaluationDB(
                filename=file.filename,
                candidate_name=result.candidate_name,
                match_score=result.match_score,
                matching_skills=json.dumps(result.matching_skills),
                missing_skills=json.dumps(result.missing_skills),
                summary_reasoning=result.summary_reasoning,
                recommendation=result.recommendation
            )
            db.add(db_item)
            db.commit()
            db.refresh(db_item) 

            results.append({
                "id": db_item.id,
                "filename": file.filename,
                "candidate_name": result.candidate_name,
                "match_score": result.match_score,
                "matching_skills": result.matching_skills,
                "missing_skills": result.missing_skills,
                "summary_reasoning": result.summary_reasoning,
                "recommendation": result.recommendation
            })
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            continue

    sorted_results = sorted(results, key=lambda x: x["match_score"], reverse=True)
    return sorted_results

@router.get("/history", response_model=List[dict])
async def get_screening_history(db: Session = Depends(get_db)):
    """
    Retrieves all past resume evaluations from the database.
    """
    records = db.query(EvaluationDB).order_by(EvaluationDB.created_at.desc()).all()
    
    history_list = []
    for rec in records:
        history_list.append({
            "id": rec.id,
            "filename": rec.filename,
            "candidate_name": rec.candidate_name,
            "match_score": rec.match_score,
            "matching_skills": json.loads(rec.matching_skills) if rec.matching_skills else [],
            "missing_skills": json.loads(rec.missing_skills) if rec.missing_skills else [],
            "summary_reasoning": rec.summary_reasoning,
            "recommendation": rec.recommendation,
            "created_at": rec.created_at.isoformat()
        })
        
    return history_list

@router.delete("/admin/reset-database")
async def reset_database(db: Session = Depends(get_db)):
    """
    Clears all past candidate evaluation history from the database.
    """
    try:
        num_deleted = db.query(EvaluationDB).delete()
        db.commit()
        return {
            "success": True,
            "message": f"Database successfully cleared! Deleted {num_deleted} past evaluation records."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset database: {str(e)}"
        )

@router.get("/export/csv")
async def export_evaluations_csv(db: Session = Depends(get_db)):
    """
    Exports all past candidate evaluations from the database as a downloadable CSV file.
    """
    records = db.query(EvaluationDB).order_by(EvaluationDB.created_at.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "Filename", "Candidate Name", "Match Score (%)", "Recommendation", "Matching Skills", "Missing Skills", "Evaluated At"])
    
    for rec in records:
        matching = ", ".join(json.loads(rec.matching_skills)) if rec.matching_skills else ""
        missing = ", ".join(json.loads(rec.missing_skills)) if rec.missing_skills else ""
        writer.writerow([
            rec.id,
            rec.filename,
            rec.candidate_name or "N/A",
            rec.match_score,
            rec.recommendation,
            matching,
            missing,
            rec.created_at.isoformat()
        ])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidate_evaluations.csv"}
    )

@router.get("/export/pdf/{evaluation_id}")
async def export_single_evaluation_pdf(evaluation_id: int, db: Session = Depends(get_db)):
    """
    Generates and downloads a clean PDF report with a professional candidate and role-based filename.
    """
    record = db.query(EvaluationDB).filter(EvaluationDB.id == evaluation_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#4f46e5'), spaceAfter=15)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1e293b'), spaceBefore=10, spaceAfter=5)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#475569'), leading=14)

    story.append(Paragraph("TalentAI - Candidate Evaluation Report", title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f"<b>Candidate Name:</b> {record.candidate_name or 'N/A'}", body_style))
    story.append(Paragraph(f"<b>Source File:</b> {record.filename}", body_style))
    story.append(Paragraph(f"<b>Match Score:</b> {record.match_score}%", body_style))
    story.append(Paragraph(f"<b>Recommendation:</b> {record.recommendation}", body_style))
    story.append(Paragraph(f"<b>Date Evaluated:</b> {record.created_at.strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 15))

    matching_str = ", ".join(json.loads(record.matching_skills)) if record.matching_skills else "None"
    missing_str = ", ".join(json.loads(record.missing_skills)) if record.missing_skills else "None"

    story.append(Paragraph("Matching Skills", heading_style))
    story.append(Paragraph(matching_str, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Missing Skills", heading_style))
    story.append(Paragraph(missing_str, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("AI Evaluation Reasoning", heading_style))
    story.append(Paragraph(record.summary_reasoning or "No reasoning provided.", body_style))

    doc.build(story)
    pdf_buffer.seek(0)
    
    safe_candidate = (record.candidate_name or "Candidate").replace(" ", "_")
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Evaluation_{safe_candidate}_Report.pdf"}
    )

# ==========================================
# Candidate Comparison Endpoint
# ==========================================
@router.post("/compare")
async def compare_candidates(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Compares multiple selected candidates side-by-side using AI analysis.
    """
    raw_ids = payload.get("evaluation_ids") or payload.get("ids") or payload.get("candidate_ids") or []
    
    clean_ids = []
    for uid in raw_ids:
        try:
            clean_ids.append(int(uid))
        except (ValueError, TypeError):
            continue

    if not clean_ids:
        raise HTTPException(status_code=400, detail="No valid candidate IDs provided for comparison.")

    records = db.query(EvaluationDB).filter(EvaluationDB.id.in_(clean_ids)).all()
    if not records:
        raise HTTPException(status_code=404, detail="Selected candidates not found in database.")

    candidates_data = []
    for r in records:
        candidates_data.append({
            "name": r.candidate_name,
            "score": r.match_score,
            "recommendation": r.recommendation,
            "matching_skills": json.loads(r.matching_skills) if r.matching_skills else [],
            "missing_skills": json.loads(r.missing_skills) if r.missing_skills else [],
            "reasoning": r.summary_reasoning
        })

    from openai import OpenAI
    import os
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing on the server.")

    client = OpenAI(api_key=api_key)

    prompt = f"""
    You are an expert technical recruiter. Compare the following candidate profiles side-by-side based on their evaluations:
    {json.dumps(candidates_data, indent=2)}

    Provide a professional, structured comparison highlighting:
    1. Key differentiators between them (who is stronger in what area).
    2. Which candidate is the overall best fit and why.
    Keep the tone objective, analytical, and concise (within 3-4 paragraphs).
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        comparison_text = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")
    
    return {"candidates": candidates_data, "comparison_analysis": comparison_text}

# ==========================================
# Comparison PDF Export Endpoint
# ==========================================
@router.post("/export/compare/pdf")
async def export_comparison_pdf(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Generates and downloads a professionally formatted, easy-to-read side-by-side comparison PDF report.
    """
    raw_ids = payload.get("evaluation_ids") or payload.get("ids") or payload.get("candidate_ids") or []
    
    clean_ids = []
    for uid in raw_ids:
        try:
            clean_ids.append(int(uid))
        except (ValueError, TypeError):
            continue

    if not clean_ids:
        raise HTTPException(status_code=400, detail="No valid candidate IDs provided for comparison.")

    records = db.query(EvaluationDB).filter(EvaluationDB.id.in_(clean_ids)).all()
    if not records:
        raise HTTPException(status_code=404, detail="Selected candidates not found in database.")

    candidates_data = []
    for r in records:
        candidates_data.append({
            "name": r.candidate_name,
            "score": r.match_score,
            "recommendation": r.recommendation,
            "matching_skills": json.loads(r.matching_skills) if r.matching_skills else [],
            "missing_skills": json.loads(r.missing_skills) if r.missing_skills else [],
            "reasoning": r.summary_reasoning
        })

    from openai import OpenAI
    import os
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY environment variable is missing on the server.")

    client = OpenAI(api_key=api_key)

    prompt = f"""
    You are an expert technical recruiter. Compare the following candidate profiles side-by-side based on their evaluations:
    {json.dumps(candidates_data, indent=2)}

    Provide a professional, structured comparison highlighting:
    1. Key differentiators between them (who is stronger in what area).
    2. Which candidate is the overall best fit and why.
    Keep the tone objective, analytical, and concise. Format your response cleanly in 2 clear sections:
    Section 1 heading: "Key Differentiators"
    Section 2 heading: "Overall Best Fit & Recommendation"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        comparison_text = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")

    # Clean up any markdown symbols from AI response for clean ReportLab rendering
    cleaned_text = comparison_text.replace("###", "").replace("**", "").strip()
    
    # Split analysis into sections if possible, or handle gracefully
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Professional typography styles
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#4f46e5'), spaceAfter=4)
    subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#64748b'), spaceAfter=15)
    
    section_heading = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1e293b'), spaceBefore=12, spaceAfter=6, keepWithNext=True)
    
    card_header = ParagraphStyle('CardHead', parent=styles['Heading3'], fontSize=10, textColor=colors.HexColor('#0f172a'), spaceBefore=6, spaceAfter=2)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#334155'), leading=12, spaceAfter=4)
    analysis_style = ParagraphStyle('Analysis', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#334155'), leading=13, spaceAfter=8)

    # Document Header
    story.append(Paragraph("TalentAI &bull; Candidate Comparison Report", title_style))
    story.append(Paragraph("Side-by-side evaluation summary generated by AI recruitment engine", subtitle_style))
    story.append(Spacer(1, 5))

    # Candidate Summary Blocks
    story.append(Paragraph("Candidate Profiles Overview", section_heading))
    
    for c in candidates_data:
        matching_str = ", ".join(c['matching_skills']) if c['matching_skills'] else "None"
        missing_str = ", ".join(c['missing_skills']) if c['missing_skills'] else "None"
        
        candidate_card_text = f"""
        <b>Name:</b> {c['name']} &nbsp;|&nbsp; <b>Match Score:</b> {c['score']}% &nbsp;|&nbsp; <b>Recommendation:</b> {c['recommendation']}<br/>
        <b>Matching Skills:</b> <font color="#059669">{matching_str}</font><br/>
        <b>Missing Skills:</b> <font color="#e11d48">{missing_str}</font>
        """
        story.append(Paragraph(candidate_card_text, body_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(Paragraph("AI Comparative Analysis & Insights", section_heading))
    
    # Render analysis paragraphs cleanly with spacing
    paragraphs = cleaned_text.split("\n\n")
    for p in paragraphs:
        if p.strip():
            story.append(Paragraph(p.strip(), analysis_style))

    doc.build(story)
    pdf_buffer.seek(0)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Candidate_Comparison_Report.pdf"}
    )