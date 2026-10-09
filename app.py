from __future__ import annotations

import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

from edupredict.config import get_config
from edupredict.auth import (
    AuthError, get_current_user, is_authenticated, is_demo_session,
    request_password_reset, sign_in, sign_in_demo, sign_out, sign_up,
)
from edupredict.data import (
    DataValidationError, add_risk_column, dataframe_to_csv_bytes,
    get_dataset_statistics, load_dataset, validate_upload,
)
from edupredict.model import train_and_evaluate, predict_grade
from edupredict.store import HistoryStore
from edupredict.ai import (
    GeminiError, generate_study_recommendations, answer_study_question,
    test_gemini_connection,
)
from edupredict.ui import (
    COLORS, inject_global_css, render_page_header, render_sidebar,
    render_public_brand, render_auth_heading, render_feature, render_footer,
    render_empty_state, render_connection_status,
)

st.set_page_config(
    page_title="EduPredict AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()
config = get_config()

@st.cache_data(show_spinner=False)
def get_default_dataset():
    return load_dataset(config.data_path)

def _dataset():
    uploaded = st.session_state.get("active_uploaded_dataset")
    if isinstance(uploaded, pd.DataFrame):
        return uploaded.copy()
    try:
        return get_default_dataset().copy()
    except Exception:
        return pd.DataFrame()

def _store():
    return HistoryStore(config=config)

def _set_page(name):
    st.session_state["current_page"] = name
    st.rerun()

def _auth_page():
    st.markdown('<div class="ep-auth-wrap">', unsafe_allow_html=True)
    render_public_brand()
    mode = st.session_state.get("auth_view", "Login")
    if mode == "Forgot Password":
        render_auth_heading("Reset your password", "Enter your email and we’ll send a reset link if the account exists.")
        email = st.text_input("Email address", key="forgot_email", placeholder="you@example.com")
        if st.button("Send reset link", type="primary", use_container_width=True):
            try:
                st.success(request_password_reset(email, config))
            except AuthError as e:
                st.error(str(e))
        if st.button("Back to login", use_container_width=True):
            st.session_state["auth_view"] = "Login"
            st.rerun()
    elif mode == "Signup":
        render_auth_heading("Create your account", "Start exploring academic performance insights.")
        with st.form("signup_form"):
            name = st.text_input("Full name", placeholder="Your name")
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password", help="At least 8 characters, including a letter and number.")
            confirm = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            if password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    result = sign_up(email, password, name, config)
                    if result["authenticated"]:
                        st.success("Account created. Welcome!")
                        _set_page("Dashboard")
                    else:
                        st.success(result["message"])
                except AuthError as e:
                    st.error(str(e))
        if st.button("Already have an account? Sign in", use_container_width=True):
            st.session_state["auth_view"] = "Login"
            st.rerun()
    else:
        render_auth_heading("Welcome back", "Sign in to continue to your student success workspace.")
        with st.form("login_form"):
            email = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if submitted:
            try:
                sign_in(email, password, config)
                st.success("Signed in successfully.")
                _set_page("Dashboard")
            except AuthError as e:
                st.error(str(e))
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Create account", use_container_width=True):
                st.session_state["auth_view"] = "Signup"
                st.rerun()
        with c2:
            if st.button("Forgot password?", use_container_width=True):
                st.session_state["auth_view"] = "Forgot Password"
                st.rerun()
        st.markdown("---")
        st.caption("Preview the interface without cloud credentials.")
        if st.button("Continue in demo mode", use_container_width=True):
            sign_in_demo()
            _set_page("Dashboard")
    st.markdown("</div>", unsafe_allow_html=True)

def _home():
    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        st.markdown("""
        <div class="ep-hero">
          <div class="ep-hero-kicker">Student success intelligence</div>
          <div class="ep-hero-title">Turn academic data into meaningful progress.</div>
          <div class="ep-hero-description">Explore performance patterns, estimate grades, and create practical study plans with responsible AI-powered insights.</div>
        </div>
        """, unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("Analytics", "Interactive")
        b.metric("Prediction", "ML-powered")
        c.metric("Study support", "AI-assisted")
        if st.button("Get started →", type="primary"):
            st.session_state["auth_view"] = "Login"
            st.rerun()
    with right:
        image_path = Path("assets/academic_performance.svg")
        if image_path.exists():
            st.image(str(image_path), use_container_width=True)
        st.markdown("### Designed for better decisions")
        render_feature("↗", "Understand patterns", "Explore attendance, study hours, and academic outcomes.")
        render_feature("◎", "Estimate outcomes", "Use a baseline machine-learning model to explore possible grades.")
        render_feature("✧", "Build a study plan", "Get structured suggestions when Gemini is configured.")
    render_footer()

def _dashboard(df):
    render_page_header("Dashboard", "A quick overview of academic performance across the current dataset.", "OVERVIEW")
    if df.empty:
        render_empty_state("No dataset available", "Add data/student_performance.csv or upload a valid CSV in Dataset Explorer.")
        return
    stats = get_dataset_statistics(df)
    k = st.columns(4)
    k[0].metric("Students", f"{stats.get('rows', 0):,}")
    k[1].metric("Average grade", f"{stats.get('average_grade', 0):.1f}")
    k[2].metric("Average attendance", f"{stats.get('average_attendance', 0):.1f}%")
    k[3].metric("Avg. study hours", f"{stats.get('average_study_hours', 0):.1f}")
    dfr = add_risk_column(df)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Grade distribution")
        if "FinalGrade" in dfr:
            fig = px.histogram(dfr, x="FinalGrade", nbins=12, color_discrete_sequence=[COLORS["accent"]])
            fig.update_layout(template="plotly_white", margin=dict(l=10,r=10,t=10,b=10), height=330)
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Risk overview")
        if "RiskLevel" in dfr:
            risk = dfr["RiskLevel"].value_counts().rename_axis("Risk level").reset_index(name="Students")
            fig = px.pie(risk, names="Risk level", values="Students", hole=.58,
                         color_discrete_sequence=["#387A58", "#A28D39", "#B84C43"])
            fig.update_layout(template="plotly_white", margin=dict(l=10,r=10,t=10,b=10), height=330)
            st.plotly_chart(fig, use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Attendance vs. final grade")
        if {"AttendanceRate", "FinalGrade"}.issubset(df.columns):
            fig = px.scatter(df, x="AttendanceRate", y="FinalGrade", color="Gender" if "Gender" in df else None,
                             hover_data=[c for c in ["StudyHoursPerWeek", "PreviousGrade"] if c in df])
            fig.update_layout(template="plotly_white", height=330, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("#### Recent dataset rows")
        st.dataframe(df.head(8), use_container_width=True, hide_index=True)
    st.caption("Dataset-level patterns are descriptive and do not establish cause and effect.")

def _dataset_explorer(df):
    render_page_header("Dataset Explorer", "Inspect, filter, validate, and download your academic data.", "DATA")
    upload = st.file_uploader("Upload a CSV dataset", type=["csv"], help="Required fields: AttendanceRate, StudyHoursPerWeek, PreviousGrade, FinalGrade.")
    if upload is not None:
        try:
            frame, report = validate_upload(upload, config.max_upload_size_mb)
            st.session_state["active_uploaded_dataset"] = frame
            st.success("Dataset loaded into this session.")
            for warning in report.get("warnings", []):
                st.warning(warning)
            df = frame
        except DataValidationError as e:
            st.error(str(e))
    if df.empty:
        render_empty_state("No dataset to explore", "Upload a CSV file or add the sample CSV to data/student_performance.csv.")
        return
    st.write(f"**{len(df):,} rows** · **{len(df.columns)} columns**")
    cols = st.multiselect("Columns to display", options=list(df.columns), default=list(df.columns))
    shown = df[cols] if cols else df
    st.dataframe(shown, use_container_width=True, hide_index=True)
    with st.expander("Filter rows"):
        filter_col = st.selectbox("Column", options=list(df.columns))
        values = df[filter_col].dropna().unique().tolist()
        if len(values) <= 40:
            chosen = st.multiselect("Keep values", values, default=values)
            filtered = df[df[filter_col].isin(chosen)]
        else:
            st.caption("This column has many unique values; showing the full dataset.")
            filtered = df
        st.write(f"{len(filtered)} rows after filtering.")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("Download current dataset as CSV", dataframe_to_csv_bytes(df), "student_performance.csv", "text/csv")

def _prediction(df):
    render_page_header("Grade Prediction", "Estimate a final grade using academic features. Results are experimental, especially on small datasets.", "PREDICTION")
    if df.empty:
        render_empty_state("Dataset required", "Load a dataset containing academic features before training the model.")
        return
    with st.expander("Train and evaluate the baseline model", expanded=True):
        if st.button("Train model and evaluate", type="primary"):
            try:
                with st.spinner("Training and validating model…"):
                    result = train_and_evaluate(df)
                st.session_state["model_result"] = result
                st.success("Model training and leave-one-out evaluation completed.")
            except Exception as e:
                st.error(str(e))
    result = st.session_state.get("model_result")
    if result:
        c = st.columns(3)
        c[0].metric("MAE", f"{result['mae']:.2f}")
        c[1].metric("R²", "N/A" if result["r2"] is None else f"{result['r2']:.3f}")
        c[2].metric("Validation", "LOOCV")
        st.caption("Leave-one-out cross-validation is used due to the small sample size. Metrics may be unstable.")
    st.markdown("#### Predict for a student")
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        with col1:
            attendance = st.number_input("Attendance rate (%)", min_value=0.0, max_value=100.0, value=85.0)
            hours = st.number_input("Study hours per week", min_value=0.0, max_value=100.0, value=10.0)
        with col2:
            previous = st.number_input("Previous grade", min_value=0.0, max_value=100.0, value=75.0)
            gender = st.selectbox("Gender (optional)", ["Not specified", "Female", "Male", "Other"])
        submit = st.form_submit_button("Estimate final grade", type="primary")
    if submit:
        try:
            pred = predict_grade(df, {
                "AttendanceRate": attendance,
                "StudyHoursPerWeek": hours,
                "PreviousGrade": previous,
                **({"Gender": gender} if gender != "Not specified" else {}),
            })
            st.session_state["latest_prediction"] = pred
            st.session_state["latest_prediction_inputs"] = {
                "AttendanceRate": attendance, "StudyHoursPerWeek": hours, "PreviousGrade": previous,
                **({"Gender": gender} if gender != "Not specified" else {}),
            }
            st.success(f"Estimated final grade: **{pred['predicted_grade']:.1f}/100** · {pred['risk_level']}")
            _store().save_prediction(
                user_id=get_current_user()["id"], student_label="Manual prediction",
                predicted_grade=pred["predicted_grade"], risk_level=pred["risk_level"],
                inputs=st.session_state["latest_prediction_inputs"], model_method=pred.get("model_method", "Ridge regression"),
                event_id=f"prediction-{st.session_state.get('prediction_event_id', 0)}-{pred['predicted_grade']:.2f}",
            )
            st.session_state["prediction_event_id"] = st.session_state.get("prediction_event_id", 0) + 1
        except Exception as e:
            st.error(str(e))

def _model_performance(df):
    render_page_header("Model Performance", "Understand how the baseline regression model performs on held-out samples.", "MODEL")
    result = st.session_state.get("model_result")
    if not result:
        st.info("Train the model in Grade Prediction to see evaluation metrics.")
        if st.button("Go to Grade Prediction"):
            _set_page("Grade Prediction")
        return
    a,b,c = st.columns(3)
    a.metric("Mean absolute error", f"{result['mae']:.2f}")
    b.metric("R² score", "N/A" if result["r2"] is None else f"{result['r2']:.3f}")
    c.metric("Rows evaluated", len(result.get("predictions", [])))
    st.markdown("#### Actual vs. predicted")
    pred_df = result.get("predictions")
    if isinstance(pred_df, pd.DataFrame) and not pred_df.empty:
        fig = px.scatter(pred_df, x="ActualGrade", y="PredictedGrade", hover_data=["Error"] if "Error" in pred_df else None)
        fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(dash="dash", color="#A28D39"))
        fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
    st.warning("This is a baseline educational model, not a validated high-stakes assessment tool.")

def _ai_advisor(df):
    render_page_header("AI Study Advisor", "Generate a structured study plan using anonymized academic information.", "AI TOOLS")
    st.caption("AI responses can be inaccurate. Do not enter names, emails, student IDs, or other identifying details.")
    if df.empty:
        st.info("Load a dataset to calculate context for study recommendations.")
        return
    if not config.gemini_configured:
        st.warning("Gemini is not configured. Add GEMINI_API_KEY to your .env file or Streamlit secrets.")
    if st.button("Test Gemini connection"):
        try:
            with st.spinner("Checking Gemini…"):
                st.success(test_gemini_connection(config))
        except GeminiError as e:
            st.error(str(e))
    st.markdown("#### Create a study plan")
    with st.form("advisor_form"):
        attendance = st.slider("Attendance rate", 0, 100, 80)
        hours = st.slider("Study hours per week", 0, 40, 8)
        previous = st.slider("Previous grade", 0, 100, 70)
        goals = st.text_area("Learning goals (avoid personal information)", placeholder="e.g. Improve algebra and prepare for weekly quizzes")
        submit = st.form_submit_button("Generate study recommendations", type="primary")
    if submit:
        try:
            with st.spinner("Preparing recommendations…"):
                result = generate_study_recommendations({
                    "AttendanceRate": attendance,
                    "StudyHoursPerWeek": hours,
                    "PreviousGrade": previous,
                    "LearningGoals": goals[:500],
                }, config=config)
            st.session_state["last_ai_recommendation"] = result
        except GeminiError as e:
            st.error(str(e))
    result = st.session_state.get("last_ai_recommendation")
    if result:
        st.markdown("### Your study plan")
        st.write(result.get("summary", ""))
        for item in result.get("strengths", []):
            st.success(str(item))
        for item in result.get("focus_areas", []):
            st.warning(str(item))
        plan = result.get("weekly_plan", [])
        if isinstance(plan, list):
            for item in plan:
                st.markdown(f"- {item}")
        st.info(result.get("encouragement", "Build consistency through small, repeatable steps."))
        st.caption("AI-generated advice · Verify important academic decisions with an educator.")
    st.markdown("---")
    st.markdown("#### Ask a study question")
    question = st.text_area("Question", key="study_question", placeholder="How can I make a realistic weekly revision schedule?")
    if st.button("Ask Gemini", type="primary"):
        try:
            with st.spinner("Generating answer…"):
                answer = answer_study_question(question, config=config)
            st.session_state["last_study_answer"] = answer
        except GeminiError as e:
            st.error(str(e))
    if st.session_state.get("last_study_answer"):
        st.markdown(st.session_state["last_study_answer"])

def _history():
    render_page_header("Prediction History", "Review estimates saved for the current account or local demo session.", "AI TOOLS")
    user = get_current_user()
    records = _store().get_predictions(user_id=user["id"], limit=200)
    if not records:
        render_empty_state("No prediction history yet", "Run a grade prediction and it will appear here.", "◷")
        return
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button("Export history CSV", df.to_csv(index=False).encode("utf-8"), "prediction_history.csv", "text/csv")
    if st.button("Clear my prediction history"):
        _store().clear_predictions(user_id=user["id"])
        st.success("History cleared.")
        st.rerun()

def _settings():
    render_page_header("Settings", "Review configuration and connection status.", "PREFERENCES")
    st.markdown("### Connections")
    render_connection_status(config)
    st.markdown("### Current configuration")
    st.write({
        "Application": config.app_name,
        "Version": config.app_version,
        "Dataset path": config.data_path,
        "Gemini model": config.gemini_model,
        "Supabase configured": config.supabase_configured,
        "Gemini configured": config.gemini_configured,
    })
    st.caption("Secret values are never displayed. Configure secrets through .env locally or Streamlit Community Cloud settings.")

def _about():
    render_page_header("About EduPredict AI", "An academic analytics prototype built for a university hackathon.", "INFORMATION")
    st.markdown("""
    ### Purpose
    EduPredict AI combines descriptive data analysis, an interpretable baseline prediction workflow, and optional AI-generated study guidance.

    ### Technology
    - Python, Streamlit, Pandas, NumPy
    - Plotly interactive charts
    - scikit-learn Ridge regression with leave-one-out evaluation
    - Google Gemini through the official `google-genai` SDK
    - Supabase Auth and PostgreSQL-backed history, with local SQLite demo history

    ### Responsible use
    Predictions are estimates, not guarantees. Small datasets can produce unstable metrics. Do not use this prototype as the sole basis for admissions, discipline, grading, or other high-stakes decisions.
    """)

def main():
    if not is_authenticated():
        page = st.query_params.get("page", "home")
        if page == "login":
            _auth_page()
        else:
            _home()
            with st.expander("Sign in or create an account"):
                _auth_page()
        return
    df = _dataset()
    selected = render_sidebar(config)
    routes = {
        "Dashboard": _dashboard,
        "Dataset Explorer": _dataset_explorer,
        "Grade Prediction": _prediction,
        "Model Performance": _model_performance,
        "AI Study Advisor": _ai_advisor,
        "Prediction History": lambda data: _history(),
        "Settings": lambda data: _settings(),
        "About": lambda data: _about(),
    }
    routes.get(selected, _dashboard)(df)
    render_footer()

if __name__ == "__main__":
    main()
