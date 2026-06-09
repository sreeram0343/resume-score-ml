# 📄 Resume Score Checker ML

An enterprise-grade, machine-learning-powered **Resume Score Checker & ATS Optimizer**. This application uses a multi-faceted feature extraction pipeline, a trained **XGBoost regressor**, and **SHAP (SHapley Additive exPlanations)** to score resumes against target roles or job descriptions and provide explainable, actionable recommendations to candidates. The backend test suite is verified 100% passing.

---

## 🚀 Badges & Tech Stack
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1572B6?style=for-the-badge&logo=python&logoColor=white)](https://xgboost.readthedocs.io/)
[![SHAP](https://img.shields.io/badge/SHAP_Explainers-FF6F00?style=for-the-badge&logo=googleanalytics&logoColor=white)](https://github.com/shap/shap)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

---

## 🏗️ System Architecture

The following diagram illustrates the interaction between the frontend client, FastAPI backend, database, cache, parser dispatcher, and the Machine Learning evaluation engine (XGBoost + SHAP).

```mermaid
graph TD
    User([Candidate Client]) <-->|Next.js 14 Frontend| Frontend[Frontend Service: Port 3000]
    Frontend <-->|REST API JSON / Files| Backend[FastAPI API: Port 8000]
    
    subgraph FastAPI Core
        Backend -->|1. Dispatch Parser| Parser[Parser Dispatcher]
        Parser -->|Extract Sections & Metadata| Extractor[Section Extractor]
        
        Extractor -->|2. Multi-Faceted Pipeline| FE[Feature Extractors]
        subgraph Feature Extractors
            FE1[ATS Compliance]
            FE2[Content Quality]
            FE3[Keyword Match]
            FE4[Semantic Similarity]
        end
        
        FE1 & FE2 & FE3 & FE4 -->|3. Assemble| Assembler[Feature Assembler]
        Assembler -->|Feature Vector| ML[XGBoost Scorer]
        ML -->|Predict Score| Explainer[SHAP Explainer]
        Explainer -->|Feature Contributions| Suggestion[Suggestion Engine]
    end

    Backend <-->|Alembic / SQLAlchemy| DB[(PostgreSQL Resume DB)]
    Backend <-->|Session Caching| Cache[(Redis Cache)]
    
    classDef primary fill:#2563EB,stroke:#1D4ED8,color:#FFFFFF;
    classDef secondary fill:#4B5563,stroke:#374151,color:#FFFFFF;
    classDef db fill:#059669,stroke:#047857,color:#FFFFFF;
    classDef ml fill:#7C3AED,stroke:#6D28D9,color:#FFFFFF;
    
    class Frontend,Backend primary;
    class Parser,Extractor,Assembler secondary;
    class DB,Cache db;
    class FE,FE1,FE2,FE3,FE4,ML,Explainer,Suggestion ml;
```

---

## ✨ Key Features

- 📑 **Advanced Document Parsing**: Supports uploading resumes in multiple formats. Automatically analyzes structural components (headers, footer, sections, layout) and flags issues like scanning artifacts (unreadable text), complex column formats, nested tables, images, and special character ratios.
- 🧪 **Multi-Stage Feature Extraction**:
  - **ATS Compliance**: Evaluates file type, page and word count constraints, and compatibility issues.
  - **Content Quality**: Examines key section completeness (Education, Experience, Skills, Projects) and validates item distributions.
  - **Keyword Matching**: Uses direct token/frequency mapping to spot missing critical skills and keywords from a Job Description.
  - **Semantic Relevance**: Leverages NLP techniques (including spaCy) to match semantic contexts of work history and skills against target role descriptions.
- 🤖 **Explainable AI with XGBoost & SHAP**:
  - Scoring is handled via a trained **XGBoost Regressor** that generates a normalized score between 0 and 100.
  - Predictions are parsed through a **SHAP (SHapley Additive exPlanations)** engine, returning the exact waterfall data representing the positive or negative contribution of each feature towards the final grade.
- 💡 **Actionable Suggestion Engine**: Dynamically analyzes the SHAP waterfall data and ATS/Content check failures to generate tailored recommendations (e.g. *"Your experience density has a strong negative contribution (-8.5 pts). Expand your project descriptions."*).
- 📊 **Interactive SHAP Visualizer**: A custom-engineered, lightweight CSS/SVG chart rendering pipeline that maps raw game-theoretic SHAP contribution values into a responsive waterfall graph. Candidates can instantly trace how specific aspects (e.g., keyword match, layout) pushed their score up or down from the baseline.
- 🧹 **Automatic Data Maintenance**: Auto-cleans expired resume records in the database based on lifespan rules.


---

## 🛠️ Technological Stack

| Category | Component | Details |
| :--- | :--- | :--- |
| **Backend** | FastAPI | Async routing, Pydantic data validation, modular routers, dependency injection. |
| **Frontend** | Next.js 14 & TypeScript | Built on React 18, App Router, metadata SEO optimization, fully responsive glassmorphism styles with zero third-party visual framework dependencies. |
| **Database** | PostgreSQL | Persistent relational database storage for parsed resumes, scores, feature vectors, and recommendations. Managed via **SQLAlchemy (Async)** and versioned using **Alembic**. |
| **Caching / Broker** | Redis | Caching layer & session key management for high-speed score caching. |
| **Machine Learning**| XGBoost | High-performance gradient boosted tree regression model. |
| **Interpretability**| SHAP | Explains model output using game-theoretic Shapley values to pinpoint score impacts. |
| **NLP** | spaCy | Named Entity Recognition (NER), linguistic matching, and phrase mapping. |
| **Containerization**| Docker Compose | Multi-container setups for seamless local deployment. |

### 🗄️ Database Schema & Cache Management
The database relies on an asynchronous **SQLAlchemy** pipeline to persist the raw resume documents and calculated SHAP values:
* **Resume Table**: Holds base metadata, parsed raw text, page count, word count, and JSON-serialized ATS flags.
* **Score Table**: Stores target role/job description, feature importance maps, full Shapley waterfall values list, and overall numeric grading metrics.
* **Redis Caching**: Controls session lifetimes, caching temporary scoring operations, and preventing duplicate processing on identical payloads within active windows.

---


## 🧠 Machine Learning Pipeline

```
Raw Resume Content & JD
  │
  ▼
[Section Extractor] ──► Parse sections (Skills, Work History, Education, etc.)
  │
  ▼
[Feature Extraction Pipeline]
  ├── ATS Features: word count, layout checks, scanned PDF flag
  ├── Content Features: section density, formatting completeness
  ├── Keyword Features: token match ratio with Job Description
  └── Semantic Features: contextual text similarity with target role
  │
  ▼
[Feature Assembler] ──► Flattens vectors into a 1D NumPy array
  │
  ▼
[XGBoost Scorer] ──► Infers overall score (0 - 100)
  │
  ▼
[SHAP Explainer] ──► Derives feature contributions (Waterfall & Scatter plot)
  │
  ▼
[Suggestion Engine] ──► Recommends optimizations based on SHAP importances
```

> [!NOTE]
> The model can be trained or re-evaluated locally with custom datasets by executing the training pipeline script.

### 🧠 Feature Assembler Architecture
The flattener transforms modular feature groups into a unified numerical vector:
1. **ATS Compliance Features**: Scanned PDF flag (binary), page/word count ratios, special character density.
2. **Section Content Quality Features**: Integrity check scores for Education, Skills, and Experience.
3. **Keyword Matching Features**: Token match frequency and tf-idf overlap with target requirements.
4. **Semantic Similarity Features**: Embedding distance score using spaCy NLP models to verify contextual role similarity.


---

## 🔌 API Reference (FastAPI)

The API is fully documented with OpenAPI spec. Access the interactive Swagger UI at [http://localhost:8000/api/docs](http://localhost:8000/api/docs) or ReDoc at [http://localhost:8000/api/redoc](http://localhost:8000/api/redoc).

### 1. Upload Resume
* **Endpoint**: `POST /api/v1/resume/upload_resume`
* **Content-Type**: `multipart/form-data`
* **Response**:
```json
{
  "resume_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "filename": "john_doe_resume.pdf",
  "word_count": 482,
  "page_count": 1,
  "ats_flags": {
    "tables_detected": false,
    "columns_detected": true,
    "images_detected": false,
    "special_chars_ratio": 0.04,
    "is_scanned_pdf": false
  },
  "preview_text": "Experienced Software Engineer with a passion for building high-performance systems...",
  "warnings": []
}
```

### 2. Score & Analyze Resume
* **Endpoint**: `POST /api/v1/resume/score_resume/{resume_id}`
* **Payload**:
```json
{
  "job_description": "Seeking a Backend Engineer proficient in Python, FastAPI, and Postgres. Knowledge of XGBoost is a plus.",
  "target_role": "Backend Engineer"
}
```
* **Response**:
```json
{
  "resume_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "score_id": "d38d0112-70b1-4566-ae9d-92736e4f3a3f",
  "overall_score": 83.5,
  "ats_score": 90.0,
  "content_score": 85.0,
  "keyword_score": 75.0,
  "semantic_score": 82.0,
  "grade": "B+",
  "explanation_text": "Your resume shows strong semantic alignment with the role, but has keyword gaps.",
  "suggestions": [
    {
      "category": "keyword",
      "impact": -8.5,
      "message": "Add key terms: 'XGBoost', 'Postgres' to match the job description."
    }
  ],
  "keyword_gaps": ["XGBoost", "Postgres"],
  "waterfall_data": {
    "base_value": 70.0,
    "values": [10.0, 5.0, -5.0, 3.5],
    "feature_names": ["ats_score", "content_score", "keyword_score", "semantic_score"]
  },
  "processing_time_ms": 142
}
```

---

## 🏃 Getting Started

### 📋 Prerequisites
- Python 3.10+ (Fully compatible and tested on Python 3.14+)
- Node.js 18+ (tested on Node 20+) & npm
- Docker & Docker Compose (optional, for containerized run)

### Local Configuration
1. Clone this repository.
2. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Customize configuration values in `.env` (database connection URLs, file limits, environment).
4. Navigate to the frontend directory, install npm packages, and verify compilation:
   ```bash
   cd frontend
   npm install
   npm run build
   ```


### Setup and Running with Makefile

This project provides a `Makefile` to simplify local setup, training, and execution:

| Command | Action |
| :--- | :--- |
| `make install` | Installs local python backend requirements and npm packages for frontend. |
| `make dev` | Launches the multi-container Docker Compose cluster. |
| `make test` | Executes backend tests using `pytest`. |
| `make lint` | Performs backend linting and type-checking (`flake8`, `mypy`, `black`). |
| `make build` | Builds docker container images. |
| `make migrate` | Applies database migrations using Alembic. |
| `make train` | Runs the machine learning training pipeline to export the XGBoost scorer. |
| `make demo` | Runs the simulation demo script. |

> [!TIP]
> Run `make train` before starting the application locally to generate the XGBoost Scorer model binary (`scorer.pkl`).

### 💻 Manual CLI Commands (Fallback)
If `make` is not supported on your operating system (e.g. Windows without MSYS2/MinGW), execute the CLI commands manually:
* **Train XGBoost model**: `cd backend && python -m ml_pipeline.train` (Exports the trained model binary)
* **Run test suite**: `cd backend && pytest`
* **Apply DB migration**: `cd backend && alembic upgrade head`
* **Generate Alembic revision**: `cd backend && alembic revision --autogenerate -m "migration_name"`

### 🧪 Testing & Verification Coverage
The backend uses a modular testing configuration with `pytest`:
* **Model Explainability tests**: Validates SHAP fallback explanation generations under missing scorer parameters.
* **Layout and Parser tests**: Verifies PDF/DOCX contact extracting and section categorization consistency.
* **NLP Pipeline tests**: Checks spacy named entity extraction accuracy and phrase matching score ranges.

---



## 🐳 Docker Deployment

To launch the full ecosystem (FastAPI, Next.js, PostgreSQL, Redis) with a single command:

```bash
make dev
```

This will bootstrap:
- **FastAPI Backend API Server**: [http://localhost:8000](http://localhost:8000)
- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
- **PostgreSQL**: Port `5432`
- **Redis**: Port `6379`

---

## 🔧 Troubleshooting

### 1. TypeScript compilation issues with CSS
If you run into `Cannot find module or type declarations for side-effect import of './globals.css'` during the compilation step, verify that the declaration file `frontend/src/global.d.ts` contains:
```typescript
declare module '*.css' {
  const content: { [className: string]: string };
  export default content;
}
```

### 2. Next.js Hydration mismatch issues
If you see hydration mismatch warnings in your browser console during development, check that your browser extensions (e.g. adblockers, dark mode toggles) are not injecting content that alters the DOM structure.

### 3. CORS Errors in local dev
Ensure the FastAPI backend environment variables allow connection from the frontend. In `backend/.env` (or via docker-compose), ensure:
```env
ALLOWED_ORIGINS=http://localhost:3000
```

### 4. SpaCy Model Downloading Failure
If the `en_core_web_sm` model fails to load or download automatically, manually run:
```bash
python -m spacy download en_core_web_sm
```

---

## 🔮 Future Roadmap & Core Enhancements
Planned future feature developments include:
* **Interactive PDF Exporting**: Export detailed score breakdowns and optimization suggestions in a professionally formatted PDF.
* **Resume Comparison Dashboard**: Side-by-side comparison score grid for comparing multiple resume versions against the same role.
* **Historical Tracker**: Account profile page showing historical resume iterations and grade improvements over time.
* **AI-Powered Cover Letter Generator**: Generate a matching cover letter optimized for the target job description.


