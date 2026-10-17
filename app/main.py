from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="TalentAI Resume Screener")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (restrict to your domain in production if needed)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend dashboard at the root URL
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Adjust path if index.html is in the project root directory (one level up from app/)
    # If index.html is in the same folder as main.py, use "index.html" directly.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, "..", "index.html") # Change to os.path.join(base_dir, "index.html") if index.html is inside app/
    
    if not os.path.exists(html_path):
        # Fallback to current working directory check
        html_path = "index.html"

    if os.path.exists(html_path):
        return FileResponse(html_path)
    
    return "<h1>Frontend index.html not found</h1>"

# Include your API router from endpoints.py
from app.api.endpoints import router as screening_router
app.include_router(screening_router)