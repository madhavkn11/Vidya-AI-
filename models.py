from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Lesson(BaseModel):
    lesson_id: str
    title: str
    order_index: int
    content: str
    key_takeaways: List[str] = []
    important_notes: Optional[str] = None
    examples: Optional[str] = None
    summary: Optional[str] = None

class Chapter(BaseModel):
    chapter_id: str
    title: str
    order_index: int
    lessons: List[Lesson] = []

class Course(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = None
    estimated_time: Optional[str] = None
    difficulty: Optional[str] = None
    prerequisites: List[str] = []
    learning_objectives: List[str] = []
    pdf_filename: Optional[str] = None
    chapters: List[Chapter] = []
    created_at: datetime = datetime.utcnow()

class ChatMessage(BaseModel):
    course_id: str
    role: str  # 'user' or 'assistant'
    content: str

class ProgressUpdate(BaseModel):
    course_id: str
    lesson_id: str
    completed: bool

class QuizAttempt(BaseModel):
    chapter_id: str
    score: int
    total: int
    answers: List[dict]