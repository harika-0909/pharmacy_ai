"""
JWT Authentication Utilities
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "smart-pharmacy-secret-key-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password, hashed):
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_token(username, role):
    """Generate a JWT token for a user."""
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    """
    Decode and verify a JWT token.
    
    Returns:
        dict with 'username' and 'role' on success
        None on failure (expired, invalid, etc.)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "username": payload["username"],
            "role": payload["role"]
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def authenticate_user(username, password):
    """
    Authenticate a user and return a JWT token.
    
    Returns:
        (token, role) on success
        (None, None) on failure
    """
    from modules.utils.db import get_user

    user = get_user(username)
    if user and verify_password(password, user["password_hash"]):
        token = generate_token(username, user["role"])
        return token, user["role"]
    return None, None


def get_role_permissions(role):
    """Get permitted menu options for a role."""
    permissions = {
        "admin": [
            "🏥 Dashboard",
            "👨‍⚕️ Doctor Module",
            "👤 Patient Management",
            "📦 Orders",
            "💊 Pharmacy Verification",
            "🧑‍💻 Admin Panel",
            "🤖 AI Prediction",
            "🚨 Alerts",
            "📄 PDF Generator"
        ],
        "doctor": [
            "🏥 Dashboard",
            "👨‍⚕️ Doctor Module",
            "👤 Patient Management",
            "📦 Orders",
            "🤖 AI Prediction",
            "📄 PDF Generator"
        ],
        "pharmacy": [
            "🏥 Dashboard",
            "💊 Pharmacy Verification",
            "👤 Patient Management",
            "📦 Orders",
            "🚨 Alerts",
            "📄 PDF Generator"
        ],
        "caregiver": [
            "👨‍👩‍👦 Caregiver Dashboard"
        ]
    }
    return permissions.get(role, [])
