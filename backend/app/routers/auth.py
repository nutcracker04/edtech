from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize Supabase Admin Client
print(f"Initializing Supabase Client with URL: {settings.supabase_url}")
print(f"Service Key (first 10 chars): {settings.supabase_service_key[:10]}...")

try:
    supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)
except Exception as e:
    print(f"Failed to initialize Supabase client: {e}")
    raise e

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    data: dict = {}

@router.post("/signup")
async def signup(user: UserSignup):
    try:
        print(f"Attempting signup for {user.email}")
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
        print(f"FULL ERROR: {error_msg}")
        if "User already registered" in error_msg:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered"
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {error_msg}"
        )
