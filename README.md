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
