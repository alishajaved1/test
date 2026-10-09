"""Supabase authentication and clearly labelled local demo sessions."""
import re
import streamlit as st
from edupredict.config import AppConfig, get_config

class AuthError(Exception):
    pass

def _client(config=None):
    config = config or get_config()
    if not config.supabase_configured:
        return None
    try:
        from supabase import create_client
        return create_client(config.supabase_url, config.supabase_anon_key)
    except Exception:
        return None

def validate_email(email: str) -> bool:
    email = email.strip()
    return len(email) <= 254 and bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))

def validate_password(password: str):
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        return False, "Password must contain at least one letter and one number."
    return True, ""

def get_current_user():
    user = st.session_state.get("auth_user")
    return user if isinstance(user, dict) and user.get("id") and user.get("email") else None

def is_authenticated():
    return get_current_user() is not None

def is_demo_session():
    return bool(st.session_state.get("auth_demo_mode", False))

def _set_user(user_id, email, name="", demo=False, token=None):
    user = {"id": str(user_id), "email": email.strip().lower(),
            "display_name": name.strip() or email.split("@")[0]}
    st.session_state["auth_user"] = user
    st.session_state["auth_demo_mode"] = bool(demo)
    if token:
        st.session_state["auth_access_token"] = token
    else:
        st.session_state.pop("auth_access_token", None)
    return user

def sign_up(email, password, display_name="", config=None):
    config = config or get_config()
    email = email.strip().lower()
    if not validate_email(email):
        raise AuthError("Enter a valid email address.")
    valid, msg = validate_password(password)
    if not valid:
        raise AuthError(msg)
    if not config.supabase_configured:
        raise AuthError("Signup requires Supabase. Configure SUPABASE_URL and SUPABASE_ANON_KEY.")
    try:
        response = _client(config).auth.sign_up({"email": email, "password": password,
            "options": {"data": {"display_name": display_name.strip()}}})
        user = getattr(response, "user", None)
        session = getattr(response, "session", None)
        if not user:
            raise AuthError("Signup was not completed. Check Supabase Auth settings.")
        if session:
            _set_user(user.id, email, display_name, token=getattr(session, "access_token", None))
        else:
            st.session_state["pending_signup_email"] = email
        return {"user_id": str(user.id), "email": email, "authenticated": session is not None,
                "confirmation_required": session is None,
                "message": "Account created. Check email to confirm, then sign in." if not session else "Account created."}
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError("Signup failed. Check email and Supabase Auth configuration.") from exc

def sign_in(email, password, config=None):
    config = config or get_config()
    email = email.strip().lower()
    if not validate_email(email):
        raise AuthError("Enter a valid email address.")
    if not password:
        raise AuthError("Enter your password.")
    if not config.supabase_configured:
        raise AuthError("Online login requires Supabase configuration. You can use demo mode for preview.")
    try:
        response = _client(config).auth.sign_in_with_password({"email": email, "password": password})
        user, session = getattr(response, "user", None), getattr(response, "session", None)
        if not user or not session:
            raise AuthError("Login not completed. Confirm your email if required.")
        metadata = getattr(user, "user_metadata", {}) or {}
        return _set_user(user.id, email, metadata.get("display_name", ""),
                         token=getattr(session, "access_token", None))
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError("Incorrect credentials or authentication provider error.") from exc

def sign_in_demo(display_name="Demo Student", email="demo@edupredict.local"):
    return _set_user("local-demo-user", email, display_name, demo=True)

def sign_out(config=None):
    config = config or get_config()
    if not is_demo_session():
        client = _client(config)
        if client:
            try:
                client.auth.sign_out()
            except Exception:
                pass
    for key in ("auth_user", "auth_demo_mode", "auth_access_token", "pending_signup_email"):
        st.session_state.pop(key, None)

def request_password_reset(email, config=None, redirect_to=None):
    config = config or get_config()
    email = email.strip().lower()
    if not validate_email(email):
        raise AuthError("Enter a valid email address.")
    client = _client(config)
    if not client:
        raise AuthError("Password reset requires configured Supabase Auth.")
    try:
        options = {"redirect_to": redirect_to} if redirect_to else None
        if options:
            client.auth.reset_password_for_email(email, options=options)
        else:
            client.auth.reset_password_for_email(email)
        return "If an account exists for that email, a reset message will be sent."
    except Exception as exc:
        raise AuthError("Could not request password reset. Check Supabase Auth settings.") from exc
