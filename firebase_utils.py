# firebase_utils.py
from firebase_admin import auth
from firebase_admin import exceptions as firebase_exceptions

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
