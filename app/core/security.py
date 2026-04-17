from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.supabase import supabase

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Extracts the JWT token from the header, verifies it with supabase,
    and returns the user object.
    """
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return response.user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_group_membership(user_id: str, group_id: str, require_admin: bool = False):
    """
    Checks the group_members junction table to ensure he user has access.
    """
    res = supabase.table("group_members").select("role").eq("user_id", user_id). eq("group_id", group_id).execute()

    if not res.data:
        raise HTTPException(status_code=403, detail="You do not have access to this group.")

    user_role = res.data[0]["role"]

    if require_admin and user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required.")

    return user_role

