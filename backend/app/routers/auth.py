from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.database import MissingSupabaseConfigurationError, get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    data: dict = {}


def _get_auth_client():
    try:
        return get_supabase()
    except MissingSupabaseConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

@router.post("/signup")
async def signup(user: UserSignup):
    try:
        supabase = _get_auth_client()
        # Create user with auto-confirmation using Admin API
        response = supabase.auth.admin.create_user({
            "email": user.email,
            "password": user.password,
            "email_confirm": True,
            "user_metadata": user.data
        })
        
        return {"message": "User created successfully", "user_id": response.user.id}
        
    except Exception as e:
        error_msg = str(e)
        if "User already registered" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {error_msg}"
        )
