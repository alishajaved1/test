# EduPredict AI

A Streamlit hackathon prototype for student performance analysis, baseline grade prediction, and optional Gemini-powered study recommendations.

## Features

- Public landing page and responsive dashboard
- Supabase Auth signup, sign-in, and password-reset request
- Local demo session for previewing the UI
- CSV upload, validation, filtering, and download
- Dataset KPIs and interactive Plotly charts
- Ridge regression with leave-one-out cross-validation
- Experimental grade estimation and risk bands
- Optional Google Gemini study-plan generation
- Prediction history in Supabase or local SQLite
- Theme, reduced-motion support, and SVG illustrations

## Project layout

```text
EduPredict_AI/
├── app.py
├── edupredict/
│   ├── __init__.py
│   ├── ai.py
│   ├── auth.py
│   ├── config.py
│   ├── data.py
│   ├── model.py
│   ├── store.py
│   └── ui.py
├── data/student_performance.csv
├── assets/
├── tests/test_core.py
├── supabase_schema.sql
├── requirements.txt
├── .env.example
└── .streamlit/config.toml
```

## Run locally on Windows

1. Install Python 3.10 or newer.
2. Extract the ZIP.
3. Open PowerShell in the extracted `EduPredict_AI` folder.
4. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

5. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Create your environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

7. Open `.env` and add credentials if you want cloud authentication or Gemini features. The demo session works without cloud credentials.
8. Start the app:

   ```powershell
   streamlit run app.py
   ```

## Supabase setup

1. Create a Supabase project.
2. In **Project Settings → API**, copy the project URL and the anon/public key.
3. Put them in `.env` as `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
4. In the Supabase SQL Editor, run `supabase_schema.sql`.
5. Configure email confirmation and redirect URLs in Supabase Auth.
6. Do not use a service-role key in the browser-facing app or commit any secret.

Cloud history is enabled only when Supabase is configured. The local SQLite history is intended for demo/testing, not multi-user production hosting.

## Gemini setup

1. Create an API key in Google AI Studio.
2. Set `GEMINI_API_KEY` in `.env`.
3. Keep `GEMINI_MODEL` set to a model supported by your account and approved in `edupredict/ai.py`.
4. Use the app's **Test Gemini connection** button.

The app does not display API keys. Gemini requests should contain only anonymized academic fields; do not submit student names, IDs, email addresses, or other personal data. Model names and API access can change; verify availability in your Google AI Studio account.

## Images and video

This ZIP includes original SVG illustrations under `assets/`. If you want to use your own supplied photos, save copies as:

- `assets/study_desk.jpg`
- `assets/academic_performance.jpg`

The current app uses the bundled SVG illustrations by default. To use a video hero, save a suitable video as `assets/hero.mp4` and add `st.video("assets/hero.mp4")` where appropriate in `app.py`.

## Dataset

A small synthetic sample dataset is included at `data/student_performance.csv`. Replace it with an authorized dataset using the required column names. Validate data consent and remove personal identifiers before using real student data.

Required fields:
`StudentID, Name, Gender, AttendanceRate, StudyHoursPerWeek, PreviousGrade, ExtracurricularActivities, ParentalSupport, FinalGrade`

The model excludes `StudentID`, `Name`, and `FinalGrade` from predictors. It uses a Ridge regression pipeline with imputation, scaling, and one-hot encoding. LOOCV metrics on tiny samples are unstable and should not be presented as validated predictive performance.

## Run tests

```powershell
pytest -q
```

## Deployment

For Streamlit Community Cloud, push the project to a GitHub repository, choose `app.py` as the entry point, and enter secrets in the app's **Settings → Secrets**. Do not upload `.env` or `.streamlit/secrets.toml`.

## Important limitations

- This is a hackathon prototype, not a production student information system.
- Real Supabase and Gemini credentials are required to test those integrations end to end.
- No model can guarantee a student's final grade.
- Do not use outputs as the sole basis for high-stakes academic decisions.
