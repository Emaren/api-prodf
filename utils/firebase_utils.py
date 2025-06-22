"""
Centralised Firebase-Admin initialisation + a *synchronous* helper
to verify ID-tokens.  Call `verify_firebase_token()` from your FastAPI
dependencies – no `await` needed.
"""

from __future__ import annotations

import os
import firebase_admin
from firebase_admin import credentials, auth

# 🔒 Resolve credential path
firebase_cert_path = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "/var/www/api-prod/secrets/serviceAccountKey.json",
)

# 🔒 Safe one-time initialization
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_cert_path)
    firebase_admin.initialize_app(cred)

# 🔑 Public token verification helper
def verify_firebase_token(id_token: str) -> tuple[str, bool, str | None]:
    """
    Verify a Firebase ID token.

    Returns
    -------
    (uid, is_anonymous, email)

    Raises
    ------
    Any exception produced by `firebase_admin.auth.verify_id_token`
    – caller should handle & translate to HTTP 401.
    """
    decoded = auth.verify_id_token(id_token)

    uid = decoded["uid"]
    provider = decoded.get("firebase", {}).get("sign_in_provider", "")
    is_anonymous = provider == "anonymous"
    email = decoded.get("email")  # may be None for anonymous users

    return uid, is_anonymous, email
