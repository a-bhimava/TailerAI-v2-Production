# PRD: Master Dataset & Intelligent Selection Engine

**Document Status:** **Final** | **Version:** 2.0 | **Date:** June 26, 2025
**Author:** TailerAI Product Team
**Stakeholders:** Development, UX/UI, Business

---

## 1. Introduction

### 1.1. The Problem
In today's competitive job market, a generic resume is ineffective. Job seekers, especially those with extensive experience, face a recurring, high-stakes problem: manually tailoring their resume for every single application. This process is tedious, subjective, and error-prone. They struggle to identify which of their many accomplishments are most relevant to a specific role and how to fit this curated content onto a single, perfectly formatted page that can pass both automated (ATS) and human reviews.

### 1.2. The Strategic Pivot: Authenticity over Fabrication
Initial market analysis and user feedback have revealed a critical insight: **users value their authentic experience above all else.** They do not want an AI to invent achievements for them. They want a powerful tool to help them **curate, optimize, and present their own career story** with maximum impact.

This PRD outlines the development of the **Master Dataset & Intelligent Selection Engine**, a paradigm shift for TailerAI. We are moving from a content *generation* tool to a career *curation* platform. The system's core will be a comprehensive, user-owned database of their entire professional history, which the AI will use to construct the optimal resume for any given job.

### 1.3. Product Goals
- **For the User:** To drastically reduce the time and effort required to create a highly effective, tailored resume, leading to more interview opportunities.
- **For the Business:** To establish TailerAI as the market leader in authentic resume optimization, driving user retention by creating an indispensable, evolving career asset for our users.

---

## 2. User Personas & Scenarios

- **Persona 1: Sarah, the Senior Product Manager**
  - **Background:** 10+ years in tech, has worked at 4 companies with dozens of major projects.
  - **Pain Point:** Her "master" resume is 4 pages long. She spends hours deleting and re-writing bullet points for each application, trying to guess what a specific hiring manager wants to see.
  - **Scenario:** Sarah is applying for a "Head of Mobile Product" role. She uploads her 4-page resume to TailerAI to create her Master Dataset. She then pastes the job description. The engine analyzes it, prioritizes her achievements related to mobile app growth and team leadership, and selects the best content to create a powerful, one-page resume, leaving out less relevant (but still valid) experience from her early career.

- **Persona 2: David, the Career Switcher**
  - **Background:** 8 years in marketing, now transitioning to a Data Analyst role after completing a certification.
  - **Pain Point:** His marketing-focused resume gets ignored for data roles. He knows he has relevant analytical skills but struggles to highlight them effectively.
  - **Scenario:** David builds his Master Dataset, including his marketing roles and his new data analysis projects. When applying for a Data Analyst position, the AI de-prioritizes his campaign management achievements and instead selects and highlights bullet points that demonstrate analytical skills, such as "Analyzed campaign data for 15 A/B tests, leading to a 10% increase in conversion" and his capstone project from his certification.

---

## 3. Feature Epics & Detailed User Stories

### EPIC 1: The Master Dataset - A Career Source of Truth

- **USER STORY 1.1:** As a user, I want a guided, step-by-step interface to manually build my Master Dataset.
  - **Acceptance Criteria:**
    - 1. The UI presents a clear, multi-step form for adding Education, Work Experience, Projects, and Skills.
    - 2. Each work experience entry allows for an unlimited number of granular achievements (bullet points).
    - 3. The system auto-saves progress every 60 seconds to prevent data loss.
    - 4. The interface is fully responsive and usable on mobile devices.

- **USER STORY 1.2:** As a user, I want to accelerate dataset creation by uploading my existing comprehensive resume.
  - **Acceptance Criteria:**
    - 1. The system accepts PDF and DOCX file uploads.
    - 2. A parsing service extracts all sections, roles, and individual bullet points.
    - 3. **Crucially**, the user is then guided through a mandatory verification UI to confirm, edit, or delete every piece of extracted data to ensure 100% accuracy.
    - 4. The system should be able to merge content from multiple uploaded resumes, flagging potential duplicates for user review.

- **USER STORY 1.3:** As a user, I want to easily manage my Master Dataset over time.
  - **Acceptance Criteria:**
    - 1. A central dashboard allows me to view, edit, and delete any entry in my dataset.
    - 2. I can add new achievements to past jobs at any time.
    - 3. I can duplicate an experience or achievement to use as a template for a new entry.

### EPIC 2: The Intelligent Selection Engine - AI as Expert Curator

- **USER STORY 2.1:** As a user, I want the AI to perform a deep analysis of a target job description.
  - **Acceptance Criteria:**
    - 1. The system accepts pasted text or a URL for a job description.
    - 2. The AI identifies and extracts: Hard Skills, Soft Skills, Years of Experience, Key Responsibilities, and ATS Keywords.
    - 3. The analysis results are displayed to the user in a clean, readable format.
    - 4. The entire analysis process completes in under 20 seconds.

- **USER STORY 2.2:** As a user, I want the AI to score my achievements and select the optimal set for a one-page resume.
  - **Acceptance Criteria:**
    - 1. The engine scores every achievement in the Master Dataset based on its relevance to the job analysis (keyword match, semantic similarity, impact).
    - 2. The engine uses a constrained optimization algorithm (e.g., 0/1 Knapsack) to select the combination of achievements with the highest total score that fits within a defined character limit (approximating one page).
    - 3. The system provides a "transparency view" explaining *why* top achievements were selected (e.g., "Matches 'data analysis' keyword") and why others were not (e.g., "Lower relevance score," "Excluded due to space constraints").
    - 4. The user can manually override the AI's choices, forcing an item to be included or excluded, which triggers the optimization to re-run with the new constraints.

---

## 4. Technical Architecture & Design

### 4.1. System Diagram
```
+-------------+      +-----------------+      +---------------------------+
|             |----->|                 |----->|                           |
|  Frontend   |      |  Backend API    |      |  Intelligent Selection    |
| (React/JS)  |      |  (FastAPI)      |      |  Engine (AI Service)      |
|             |<-----|                 |<-----|                           |
+-------------+      +-------+---------+      +-------------+-------------+
                             |                      |
                             |                      |
           +-----------------v-----------------+    |
           |                                   |    |
           |  Database (PostgreSQL / SQLite)   |    |
           |  (Master Dataset Storage)         |    |
           |                                   |    |
           +-----------------------------------+    |
                             |                      |
           +-----------------v-----------------+    |
           |                                   |    |
           |  Job Queue (Celery & Redis)       |<---+
           |  (For AI & LaTeX Processing)      |
           |                                   |
           +-----------------v-----------------+
                             |
           +-----------------v-----------------+
           |                                   |
           |  LaTeX Generation Service        |
           |  (Dockerized TeX Live)           |
           |                                   |
           +-----------------------------------+
```

### 4.2. Technology Stack
- **Backend:** Python 3.11+, FastAPI
- **Database:** PostgreSQL (for Cloud), SQLite (for Local)
- **AI Integration:** Google Gemini API
- **Job Queue:** Celery with Redis as the broker
- **LaTeX Engine:** TeX Live (full distribution), run inside a Docker container.
- **Containerization:** Docker & Docker Compose

### 4.3. Dual Deployment Strategy (Local & Cloud)
The system will be architected to run seamlessly in both a local development environment and on a cloud provider (Google Cloud Run is the recommended target per `hosting-analysis-v2.md`).

- **Configuration Management:** A single `app/config/settings.py` file will use environment variables to manage settings. A `.env` file will control local configuration.
- **Database Connection:** The application will connect to a local SQLite database when `ENVIRONMENT=local` and a PostgreSQL instance (e.g., Cloud SQL) when `ENVIRONMENT=production`.
- **Unified Dockerfile:** A multi-stage `Dockerfile` will define the complete environment, including the TeX Live installation, ensuring parity between local and cloud.
- **Local Development:** `docker-compose.yml` will orchestrate the FastAPI app, a local Redis instance, and a Celery worker for a complete local testing environment.

---

## 5. Detailed API Specification

Base URL: `/api/v2`

- **Master Dataset Management:**
  - `POST /master-dataset/experiences`: Create a new work experience.
    - **Request Body:** `{ "profile_id": "uuid", "company_name": "str", "position_title": "str", ... }`
    - **Response:** `{ "id": "uuid", ... }` (201 Created)
  - `POST /master-dataset/achievements`: Add an achievement to an experience.
    - **Request Body:** `{ "experience_id": "uuid", "achievement_text": "str", ... }`
    - **Response:** `{ "id": "uuid", ... }` (201 Created)
  - `GET /master-dataset/{profile_id}`: Get the entire master dataset for a user.
    - **Response:** A nested JSON object of the user's full career history.

- **Optimization Workflow:**
  - `POST /optimize/jobs`: Submit a job description for analysis.
    - **Request Body:** `{ "profile_id": "uuid", "job_description": "str" }`
    - **Response:** `{ "job_analysis_id": "uuid", "status": "pending" }` (202 Accepted)
  - `GET /optimize/jobs/{job_analysis_id}`: Check the status and get the results of the analysis and selection.
    - **Response:** `{ "status": "completed", "selected_content": [...], "transparency_report": {...} }`
  - `POST /optimize/overrides`: Allow the user to override the AI selection.
    - **Request Body:** `{ "job_analysis_id": "uuid", "include_ids": ["uuid"], "exclude_ids": ["uuid"] }`
    - **Response:** Returns the newly re-optimized selection.

---

## 6. Database Schema
The database will implement the schema detailed in **`ENHANCED_MASTER_DATASET_SCHEMA.md`**. Key tables include:
- `user_profiles`: Stores user account and profile information.
- `work_experiences`: Stores details of each job role.
- `achievements`: Stores every individual achievement, linked to a work experience. This is the core table for the selection engine.
- `job_applications` & `application_content_selections`: Tracks which achievements were selected for which jobs, enabling future performance analysis.

---

## 7. Non-Functional Requirements (NFRs)

- **Performance:**
  - P95 latency for all API endpoints must be < 500ms, excluding the asynchronous `/optimize` endpoint.
  - The end-to-end optimization and LaTeX generation workflow should complete in < 60 seconds for 95% of users.
- **Scalability:**
  - The system on Google Cloud Run must be configured to handle up to 100 concurrent users with auto-scaling.
- **Reliability:**
  - Target 99.9% uptime.
  - Implement robust service-level fallbacks: if the Gemini API is down, the system should revert to a simpler, keyword-based scoring model. If LaTeX fails, it should offer a clean HTML-to-PDF fallback.
- **Security:**
  - All user data must be encrypted at rest (AES-256).
  - All data in transit must use TLS 1.2+.
  - Implement standard protections against SQL Injection, XSS, and CSRF.

---

## 8. Phased Development Plan

- **Phase 1: Backend Foundation (2 Weeks)**
  - Implement the full database schema using SQLAlchemy and Alembic for migrations.
  - Build the CRUD APIs for managing the Master Dataset.
  - Set up the Docker and Docker Compose local environment.
- **Phase 2: Core Engine Development (3 Weeks)**
  - Implement the Job Description Analysis service.
  - Develop the multi-dimensional Relevance Scoring algorithm.
  - Build the one-page Knapsack optimization solver.
  - Integrate the core engine with the asynchronous job queue (Celery).
- **Phase 3: Frontend Integration (3 Weeks)**
  - Develop the UI for the manual Master Dataset builder.
  - Implement the file upload and verification workflow.
  - Build the UI for submitting a job description and viewing the selection results and transparency report.
- **Phase 4: Finalization & Deployment (2 Weeks)**
  - Implement the manual override functionality.
  - Connect the final selected content to the LaTeX generation pipeline.
  - Perform end-to-end testing.
  - Configure and deploy to Google Cloud Run.

---

## 9. Success Metrics

- **Primary Metric:** **Manual Override Rate.** The percentage of optimization runs where a user manually changes the AI's selection. A low rate signifies high trust and accuracy. **Target: < 15%**.
- **Secondary Metrics:**
  - **Task Completion Rate:** % of users who successfully generate a resume after starting the process. **Target: > 85%**.
  - **Time-to-Value:** The median time it takes a new user to generate their first tailored resume. **Target: < 25 minutes**.
  - **User Retention:** % of users who return to generate a resume for a second job application. **Target: > 40%**.

---

## 10. Risks & Mitigation

- **Risk 1 (High Impact):** The initial data entry for the Master Dataset is too cumbersome, leading to high user drop-off.
  - **Mitigation:**
    - 1. Prioritize the development of a highly accurate and user-friendly resume parser to minimize manual entry.
    - 2. Use UI/UX techniques like progress bars and gamification to encourage completion.
    - 3. Allow users to save their progress and return at any time.
- **Risk 2 (Medium Impact):** The AI selection quality is perceived as poor or misses critical context.
  - **Mitigation:**
    - 1. The "Transparency Report" is non-negotiable; users must understand the AI's reasoning.
    - 2. The manual override feature is a critical safety valve that ensures the user is always in control.
    - 3. Implement a feedback loop where user overrides are logged and used to fine-tune the selection models over time.

---

## 📋 **DOCUMENT REFERENCE**

**Strategic Role**: This document provides the **HIGH-LEVEL STRATEGIC VISION** for TailerAI v2.0  
**Detailed Implementation**: See `Tailer_v2_PRDs.md` for complete technical specifications  
**Current Progress**: See `DEVELOPMENT_STATUS.md` for implementation tracking  

**Implementation follows**: `DEVELOPMENT_STATUS.md` + `Tailer_v2_PRDs.md` combination  
**Last Updated**: December 28, 2024
