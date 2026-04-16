from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.db.supabase import supabase

router = APIRouter()

class UserCreate(BaseModel):
    email       : str
    password    : str
    display_name: str
    group_id    : str = Field(..., description="The UUID of the EquityCircle group")

class UserLogin(BaseModel):
    email   : str
    password: str

@router.post("/signup")
def sign_up(user_data: UserCreate):
    """
    Register a new user and pass metadata to trigger the supabase function
    """
    try:
        response = supabase.auth.sign_up({
            "email"   : user_data.email,
            "password": user_data.password,
            "options" : {
                "data": {
                    "display_name": user_data.display_name,
                    "group_id"    : user_data.group_id
                }
            }
        })

        return {
            "message": "User created successfully",
            "user_id": response.user.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(user_data: UserLogin):
    """
    Authenticate and return the session JWT token.
    """
    try:
        response = supabase.auth.sign_in_with_password({
            "email"   : user_data.email,
            "password": user_data.password
        })

        return {
            "access_token": response.session.access_token,
            "token_type"  : "bearer",
            "user"        : response.user
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or user")
    