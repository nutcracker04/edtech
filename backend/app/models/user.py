from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    grade: str  # '9', '10', '11', '12'
    syllabus: str  # 'cbse', 'icse', 'state'
    target_exam: str
    created_at: datetime
    updated_at: datetime


class UserPreferences(BaseModel):
    id: str
    user_id: str
    daily_goal: int = 20
    focus_subjects: List[str] = []
    difficulty_level: str = "adaptive"
    notifications_enabled: bool = True
    daily_reminders: bool = True
    dark_mode: bool = False
    created_at: datetime
    updated_at: datetime
