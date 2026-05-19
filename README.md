# GradeOps

GradeOps is an AI-assisted exam grading platform built for professors and teaching assistants who need a faster way to process handwritten or scanned answer sheets. The project connects a web dashboard with a FastAPI backend and a model pipeline that can convert exam PDFs into images, run OCR, extract question-wise answers, compare them with an answer key, and generate marks with justification.

The goal is not to fully replace manual evaluation. GradeOps is designed as a grading assistant: the AI proposes scores, shows reasoning, and keeps a review flow where a TA or professor can approve, override, or flag the result.

## Collaborators

- Parth Parmar
- Dhwanit Gajjar
- Pathikrit
- Himanshu

## What the project does

GradeOps currently supports the complete basic flow for checking one exam paper at a time:

1. Upload a student answer sheet PDF.
2. Upload the answer key or marking scheme PDF.
3. Convert PDF pages into images.
4. Run OCR on the student answer sheet.
5. Split the OCR output into question-wise JSON.
6. Extract the answer key into structured JSON.
7. Run the grading model against the answer key and rubric.
8. Return marks, rubric-wise breakdown, confidence, missing points, and explanation.
9. Send outputs to a review-style dashboard where the evaluator can take the final decision.

## Features

### Instructor side

- Login screen with role selection.
- Dashboard overview for total papers, AI-graded papers, pending reviews, approved answers, and flagged answers.
- PDF upload interface for scanned exam papers.
- Rubric builder for creating question-wise marking criteria.
- Exam library UI to view exams, grading status, progress, and flagged papers.

### Teaching assistant side

- Review queue for answers that need manual checking.
- Side-by-side review layout with OCR text, AI score, rubric breakdown, and justification.
- Approve, override, and flag actions.
- Completed review history for the current session.

### Backend and model pipeline

- FastAPI backend with modular routers for auth, exams, rubrics, reviews, results, and model endpoints.
- MongoDB integration using Motor.
- PDF-to-image conversion using PyMuPDF.
- OCR pipeline using `JackChew/Qwen2-VL-2B-OCR`.
- Answer-key extraction with direct PDF text extraction first and OCR fallback for scanned files.
- Grading pipeline using a Qwen2.5 Instruct text model.
- JSON-based intermediate outputs for OCR, answer key, and grading results.
- GPU memory cleanup between OCR and grading to make the pipeline more usable on limited VRAM systems.

## Tech stack

### Frontend

- React
- Vite
- Plain CSS
- Fetch-based API services

### Backend

- Python
- FastAPI
- MongoDB
- Motor
- PyMuPDF
- Transformers
- PyTorch
- Qwen-VL utilities

### Models used

- OCR model: `JackChew/Qwen2-VL-2B-OCR`
- Grading model: `Qwen/Qwen2.5-3B-Instruct`

Both model IDs can be changed from the backend environment variables.

## Project structure

```text
gradeops-final-merged/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI routes
│   │   ├── core/                # Config and app settings
│   │   ├── pipelines/           # End-to-end grading pipelines
│   │   ├── services/            # OCR, PDF, grading, answer key and helper services
│   │   └── database.py          # MongoDB connection helpers
│   ├── main.py                  # FastAPI entry point
│   ├── requirements.txt
│   └── requirements-models.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Shared UI components
│   │   ├── pages/               # Login, instructor dashboard, TA dashboard
│   │   ├── services/            # API service functions
│   │   ├── styles/              # Global CSS
│   │   └── main.jsx
│   ├── package.json
│   └── index.html
│
└── README.md
```

## Backend setup

Go to the backend folder:

```bash
cd backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

For Windows PowerShell:

```bash
.\venv\Scripts\Activate.ps1
```

For Command Prompt:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file inside the `backend` folder:

```env
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB_NAME=gradeops
UPLOAD_DIR=uploads

OCR_MODEL_ID=JackChew/Qwen2-VL-2B-OCR
GRADING_MODEL_ID=Qwen/Qwen2.5-3B-Instruct
PDF_DPI=140
OCR_MAX_TOKENS=700
ANSWER_KEY_OCR_MAX_TOKENS=1200
GRADING_MAX_TOKENS=650
UNLOAD_OCR_BEFORE_GRADING=true
```

Do not commit the real `.env` file to GitHub.

Run the backend:

```bash
uvicorn main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

FastAPI docs will be available at:

```text
http://localhost:8000/docs
```

## Frontend setup

Open a new terminal and go to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create a `.env` file inside the `frontend` folder:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Run the frontend:

```bash
npm run dev
```

The frontend will usually run at:

```text
http://localhost:5173
```

## Main API endpoints

### Basic app endpoints

```text
POST /auth/login
GET  /exams
POST /exams/upload
GET  /rubrics
POST /rubrics
POST /rubrics/upload-json
GET  /reviews/queue
GET  /reviews/completed
POST /reviews/{paper_id}/approve
POST /reviews/{paper_id}/override
POST /reviews/{paper_id}/flag
GET  /results/dashboard
```

### Model pipeline endpoints

```text
POST /model/pdf-to-images
POST /model/ocr-image
POST /model/student-ocr
POST /model/answer-key-json
POST /model/grade-json
POST /model/full-pipeline
```

The most important endpoint for the complete flow is:

```text
POST /model/full-pipeline
```

It takes a student PDF and an answer-key PDF, then returns OCR output, extracted answer-key JSON, and grading output.

## Current limitations

- The login system is currently a prototype and returns a development token.
- Some dashboard data is still demo data until the complete database flow is connected everywhere.
- The plagiarism service is present as an integration point, but the actual similarity logic is not fully implemented yet.
- The grading quality depends heavily on OCR quality, answer-key formatting, and the marking rubric.
- Running the model pipeline locally may require a good GPU. CPU execution can be very slow.

## Notes for GitHub submission

Before pushing this project to GitHub:

- Remove any real MongoDB URL or private key from `.env` and `.env.example`.
- Add `.env`, `venv/`, `__pycache__/`, `uploads/`, `storage/`, and generated output files to `.gitignore`.
- Do not commit uploaded student answer sheets, answer keys, or generated model outputs.
- Keep only sample/demo files if they are safe to share.

A suitable `.gitignore` should include:

```gitignore
.env
venv/
__pycache__/
*.pyc
uploads/
storage/
backend/uploads/
backend/storage/
node_modules/
dist/
.DS_Store
```

## Future improvements

- Add proper JWT authentication and role-based access control.
- Store full grading outputs and review decisions in MongoDB.
- Add real plagiarism or similarity detection.
- Add support for batch processing multiple students.
- Add export options for CSV/PDF reports.
- Improve OCR post-processing for messy handwriting.
- Add deployment configuration for frontend and backend.

## Status

GradeOps is a working prototype of an AI-assisted grading system. The main pipeline is in place, and the project is ready to be extended into a more complete production-style application.
