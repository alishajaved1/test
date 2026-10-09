"""Shared styling and reusable UI helpers."""
import html
import streamlit as st
from edupredict.auth import get_current_user, is_demo_session, sign_out
from edupredict.config import AppConfig, get_config

COLORS = {"background":"#F1F0EC","surface":"#FFFFFF","sidebar":"#252622",
          "text":"#292A26","muted":"#77786F","accent":"#A28D39","border":"#E1E0D9"}

def inject_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html,body,[class*="css"]{font-family:Inter,Arial,sans-serif}
    .stApp{background:#F1F0EC;color:#292A26}
    .block-container{max-width:1440px;padding-top:1.6rem;padding-bottom:3rem}
    h1,h2,h3{letter-spacing:-.035em}
    [data-testid="stSidebar"]{background:#252622;border-right:1px solid #393A34}
    [data-testid="stSidebar"] *{color:#F5F3EA}
    [data-testid="stSidebar"] .stButton>button{background:transparent;color:#EAE9E1;border:1px solid transparent;text-align:left}
    [data-testid="stSidebar"] .stButton>button:hover{background:#34352F;border-color:#494A40;transform:translateX(2px)}
    .stButton>button{border-radius:10px;min-height:42px;font-weight:600;transition:all 180ms ease}
    .stButton>button:hover{transform:translateY(-1px);box-shadow:0 5px 14px #292a2612}
    .stButton>button[kind="primary"]{background:#A28D39;border-color:#A28D39;color:white}
    [data-testid="stMetric"]{padding:17px;border:1px solid #E1E0D9;border-radius:15px;background:white;transition:transform 180ms ease}
    [data-testid="stMetric"]:hover{transform:translateY(-2px)}
    [data-testid="stPlotlyChart"]{border:1px solid #E1E0D9;border-radius:15px;background:white;padding:8px}
    .ep-brand{display:flex;align-items:center;gap:10px;padding:7px 2px 20px}
    .ep-brand-mark{width:40px;height:40px;display:flex;align-items:center;justify-content:center;border-radius:12px;background:#A28D39;color:white;font-size:1.12rem;font-weight:800}
    .ep-brand-name{color:white;font-size:1.05rem;font-weight:800}
    .ep-brand-tagline{color:#B8B9AD;font-size:.72rem}
    .ep-sidebar-section{color:#999B8D;font-size:.69rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin:17px 0 7px 4px}
    .ep-sidebar-note{border:1px solid #414238;background:#2E2F29;border-radius:11px;padding:12px;color:#D9D9CF;font-size:.77rem;line-height:1.65;margin:14px 0}
    .ep-page-header{margin:0 0 22px;animation:epfade .4s ease both}
    .ep-eyebrow{color:#A28D39;font-size:.74rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;margin-bottom:7px}
    .ep-page-title{font-size:clamp(1.75rem,3vw,2.35rem);font-weight:800;letter-spacing:-.045em;line-height:1.2;margin:0 0 8px}
    .ep-page-subtitle{color:#77786F;font-size:.94rem;line-height:1.7;margin:0}
    .ep-hero{background:linear-gradient(125deg,#292A25,#39382D 65%,#50472B);color:white;border-radius:20px;padding:clamp(25px,4vw,43px);margin-bottom:23px;animation:epfade .5s ease both}
    .ep-hero-kicker{color:#D7C47E;font-size:.76rem;letter-spacing:.13em;text-transform:uppercase;font-weight:800;margin-bottom:13px}
    .ep-hero-title{color:white;font-size:clamp(2rem,4.5vw,3.1rem);line-height:1.12;letter-spacing:-.05em;font-weight:800;margin-bottom:15px}
    .ep-hero-description{color:#D6D5CC;line-height:1.8;font-size:.95rem}
    .ep-auth-wrap{max-width:480px;margin:0 auto;padding-top:14px;animation:epfade .45s ease both}
    .ep-auth-heading{font-size:clamp(1.8rem,4vw,2.4rem);font-weight:800;letter-spacing:-.045em;margin:10px 0 8px}
    .ep-auth-subtitle{color:#77786F;line-height:1.75;margin-bottom:24px}
    .ep-feature-item{display:flex;align-items:flex-start;gap:12px;margin:14px 0}
    .ep-feature-icon{width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:10px;color:#8D792D;background:#F1EBD4;font-weight:800;flex-shrink:0}
    .ep-feature-title{font-weight:700;margin-bottom:3px}
    .ep-feature-description{color:#77786F;font-size:.82rem;line-height:1.65}
    .ep-empty{text-align:center;padding:34px 18px;border:1px dashed #D2D0C7;border-radius:14px;background:#ffffffa6}
    .ep-footer{border-top:1px solid #E1E0D9;padding-top:17px;margin-top:35px;color:#77786F;font-size:.76rem;line-height:1.7}
    @keyframes epfade{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
    @media(max-width:768px){.block-container{padding:1rem}.ep-hero{border-radius:15px;padding:25px 20px}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}}
    </style>""", unsafe_allow_html=True)

def render_page_header(title, subtitle="", eyebrow="EDUPREDICT AI"):
    st.markdown(f'<div class="ep-page-header"><div class="ep-eyebrow">{html.escape(eyebrow)}</div><div class="ep-page-title">{html.escape(title)}</div><p class="ep-page-subtitle">{html.escape(subtitle)}</p></div>', unsafe_allow_html=True)

def render_brand():
    st.markdown('<div class="ep-brand"><div class="ep-brand-mark">E</div><div><div class="ep-brand-name">EduPredict AI</div><div class="ep-brand-tagline">Student success intelligence</div></div></div>', unsafe_allow_html=True)

NAVIGATION = {"Overview":[("Dashboard","◫"),("Dataset Explorer","▤"),("Grade Prediction","◎"),("Model Performance","⌁")],
              "AI TOOLS":[("AI Study Advisor","✧"),("Prediction History","◷")],
              "PREFERENCES":[("Settings","⚙"),("About","ⓘ")]}

def render_sidebar(config: AppConfig | None = None):
    config = config or get_config()
    user = get_current_user()
    if not user: return "Home"
    if "current_page" not in st.session_state: st.session_state["current_page"] = "Dashboard"
    with st.sidebar:
        render_brand()
        st.markdown("---")
        for group, items in NAVIGATION.items():
            st.markdown(f'<div class="ep-sidebar-section">{html.escape(group)}</div>', unsafe_allow_html=True)
            for page, icon in items:
                selected = st.session_state.get("current_page") == page
                if st.button(f"{'●' if selected else icon}  {page}", key=f"nav_{page}", use_container_width=True, type="primary" if selected else "secondary"):
                    st.session_state["current_page"] = page
                    st.rerun()
        st.markdown("---")
        if is_demo_session():
            st.markdown('<div class="ep-sidebar-note"><b>Demo mode</b><br>Local preview session; not a verified account.</div>', unsafe_allow_html=True)
        st.caption(f"{user.get('display_name','Student')} · {user.get('email','')}")
        if st.button("↪ Sign out", use_container_width=True):
            sign_out(config)
            st.session_state["current_page"] = "Home"
            st.rerun()
    return st.session_state.get("current_page","Dashboard")

def render_public_brand():
    st.markdown('<div class="ep-brand" style="padding-bottom:14px"><div class="ep-brand-mark">E</div><div><div style="font-size:1.15rem;font-weight:800;color:#292A26">EduPredict AI</div><div style="font-size:.76rem;color:#77786F">Student success intelligence</div></div></div>', unsafe_allow_html=True)

def render_auth_heading(title, subtitle):
    st.markdown(f'<div class="ep-auth-heading">{html.escape(title)}</div><div class="ep-auth-subtitle">{html.escape(subtitle)}</div>', unsafe_allow_html=True)

def render_feature(icon_text,title,description):
    st.markdown(f'<div class="ep-feature-item"><div class="ep-feature-icon">{html.escape(icon_text)}</div><div><div class="ep-feature-title">{html.escape(title)}</div><div class="ep-feature-description">{html.escape(description)}</div></div></div>', unsafe_allow_html=True)

def render_empty_state(title, description, icon="📊"):
    st.markdown(f'<div class="ep-empty"><div style="font-size:2rem">{html.escape(icon)}</div><b>{html.escape(title)}</b><div style="color:#77786F;font-size:.87rem">{html.escape(description)}</div></div>', unsafe_allow_html=True)

def render_footer():
    st.markdown('<div class="ep-footer"><b>EduPredict AI</b> · Predictions are estimates, not guarantees. Do not use this prototype as the sole basis for high-stakes decisions.</div>', unsafe_allow_html=True)

def render_connection_status(config=None):
    config = config or get_config()
    st.write("Supabase:", "Configured" if config.supabase_configured else "Not configured")
    st.write("Gemini:", "Configured" if config.gemini_configured else "Not configured")
