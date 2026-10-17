from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TalentAI Resume Screener")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend dashboard at the root URL
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # Check multiple possible locations for index.html depending on Render's build structure
    possible_paths = [
        os.path.join(os.getcwd(), "index.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    ]
    
    html_path = None
    for path in possible_paths:
        normalized_path = os.path.normpath(path)
        logger.info(f"Checking path for index.html: {normalized_path}")
        if os.path.exists(normalized_path):
            html_path = normalized_path
            break

    if html_path and os.path.exists(html_path):
        logger.info(f"Serving index.html from: {html_path}")
        return FileResponse(html_path)
    
    logger.error("index.html not found in any expected location.")
    raise HTTPException(status_code=404, detail="Frontend index.html not found on server.")

# Include your API router from endpoints.py
try:
    from app.api.endpoints import router as screening_router
    app.include_router(screening_router)
    logger.info("Successfully loaded screening_router.")
except Exception as e:
    logger.error(f"Failed to load screening_router: {e}")