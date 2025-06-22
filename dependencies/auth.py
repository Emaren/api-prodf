from fastapi import Request, HTTPException, status
from firebase_utils import verify_firebase_token

async def get_firebase_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Authorization header missing or malformed"
        )

    id_token = auth_header.split("Bearer ")[1]

    firebase_user = verify_firebase_token(id_token)
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Firebase token"
        )

    return firebase_user  # Dict with 'uid' and 'email'
