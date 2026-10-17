import json
from openai import OpenAI
from app.config import settings
from app.schemas.models import ScreeningResponse

# Initialize the OpenAI client with your API key from config
client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def analyze_resume_with_ai(resume_text: str, job_description: str) -> ScreeningResponse:
    """
    Sends the resume text and job description to OpenAI to evaluate,
    score, and extract structured data.
    """
    prompt = f"""
    You are an expert HR recruiter and technical talent screener. 
    Evaluate the following candidate resume against the provided job description.
    
    JOB DESCRIPTION:
    {job_description}
    
    CANDIDATE RESUME:
    {resume_text}
    
    Analyze the candidate thoroughly and provide:
    1. candidate_name: The name of the candidate if found, otherwise null.
    2. match_score: An integer score from 0 to 100 representing how well the candidate fits the job description.
    3. matching_skills: A list of skills the candidate has that match the requirements.
    4. missing_skills: Important skills required by the job description that are missing from the resume.
    5. summary_reasoning: A professional summary explaining the score and evaluation.
    6. recommendation: One of ["Strong Hire", "Interview", "Keep on File", "Reject"].
    
    Return your response strictly as a JSON object matching these exact fields.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Cost-effective and highly accurate for text analysis
            messages=[
                {"role": "system", "content": "You are a precise HR automation assistant that outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Validate and return via our Pydantic model
        return ScreeningResponse(**data)
        
    except Exception as e:
        raise RuntimeError(f"Error communicating with OpenAI API: {str(e)}")