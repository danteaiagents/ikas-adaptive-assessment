from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SessionStart(BaseModel):
    topic_id: str
    preset: str = 'standard'
    total_questions: Optional[int] = None
    time_limit_minutes: Optional[int] = None

class AnswerSubmit(BaseModel):
    question_id: str
    selected_options: List[str]
    time_taken_seconds: int

class OptionOut(BaseModel):
    id: str
    text: str

class QuestionOut(BaseModel):
    id: str
    stem: str
    level: str
    options: List[OptionOut]
    concept_id: str
    concept_name: str = ''
    prerequisites: List[Dict[str, Any]] = []
    resources: List[Any] = []

class SessionReport(BaseModel):
    session_id: str
    total_questions: int
    correct_count: int
    score: float
    theta: float
    theta_se: float
    level_breakdown: Dict[str, Any]
    concept_mastery: Dict[str, float]
    recommendations: List[str]

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any]
