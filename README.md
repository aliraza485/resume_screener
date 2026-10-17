# 🚀 TalentAI - AI-Powered Resume Screener & Candidate Comparison Engine

TalentAI is a full-stack, intelligent recruitment platform designed to automate resume screening, evaluate candidate competency scores against job descriptions using Large Language Models, and generate professional PDF comparison reports.

---

## ✨ Key Features

* **AI-Powered Candidate Scoring**: Automatically parses resumes and evaluates match percentages with detailed reasoning.
* **Side-by-Side Candidate Comparison**: Compares multiple candidates simultaneously using LLMs to highlight key differentiators and identify the overall best fit.
* **Automated PDF Export**: Leverages ReportLab to export clean, structured individual evaluation summaries and comparative reports.
* **Interactive UI**: Clean, responsive frontend styled with Tailwind CSS, backed by a robust FastAPI asynchronous backend.
* **Vector & RAG Capabilities**: Built with modern AI architectures utilizing embeddings and similarity search foundations.

---

## 🛠️ Tech Stack

* **Backend**: Python, FastAPI, Uvicorn, SQLAlchemy
* **AI & LLM Integration**: OpenAI API, LangChain framework, FAISS vector database
* **Document Processing & Reporting**: ReportLab, PyPDF, Python-Docx
* **Frontend**: HTML5, Tailwind CSS, JavaScript

## ⚙️ Local Installation & Setup

Follow these steps to set up and run the project locally on your machine:

### Prerequisites
Make sure you have **Python 3.10 or higher** installed on your system.

### 1. Clone the Repository

git clone [https://github.com/aliraza485/resume_screener.git](https://github.com/aliraza485/resume_screener.git)
cd resume_screener

### 2. Create and Activate Virtual Environment
Create a virtual environment named 'myenv'
python -m venv myenv

Activate on Windows (PowerShell / Command Prompt):
myenv\Scripts\activate

Activate on macOS / Linux:
source myenv/bin/activate

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Configure Environment Variables
OPENAI_API_KEY=your_actual_openai_api_key_here

### 5. Run the Application
uvicorn app.main:app --reload

### 6. Access the Application
Open your web browser and go to:
👉 http://127.0.0.1:8000

---

## 📂 Project Architecture

```text
resume_screener/
│
├── app/
│   ├── api/
│   │   └── endpoints.py     # Core API logic, evaluation & PDF export routes
│   └── main.py              # FastAPI app initialization & static frontend routing
│
├── index.html               # Tailwind CSS frontend dashboard
├── requirements.txt         # Project Python dependencies
└── README.md
