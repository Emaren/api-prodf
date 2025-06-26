import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin import exceptions as firebase_exceptions

# Initialize Firebase Admin SDK
def initialize_firebase():
    if firebase_admin._apps:
        return  # Already initialized

    json_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if json_key:
        cred = credentials.Certificate(json.loads(json_key))
    else:
        cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(cred)

# Verify ID token coming from frontend
def verify_firebase_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        return {"uid": uid, "email": email}
    except firebase_exceptions.FirebaseError as e:
        print(f"❌ Firebase verification error: {e}")
        return None
    except Exception as e:
        print(f"❌ General token verification error: {e}")
        return None

# Optional: fetch user details by UID
def get_user_by_uid(uid: str):
    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
        }
    except Exception as e:
        print(f"❌ Firebase get_user_by_uid error: {e}")
        return None

def get_user_from_token(token: str):
    # TODO: replace with real Firebase validation
    return {"uid": "test-uid", "email": "test@example.com"}
