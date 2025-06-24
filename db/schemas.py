# db/schemas.py

from pydantic import BaseModel

class UserRegisterRequest(BaseModel):
    in_game_name: str
