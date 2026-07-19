import json
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database import courses_collection, quiz_collection
from auth import get_current_user_id
from groq_utils import call_llm
from models import QuizAttempt

router = APIRouter(prefix="/quiz", tags=["quiz"])

QUIZ_GEN_SYSTEM_PROMPT = """You are an expert quiz creator. Given lesson content from a chapter, generate a quiz to test understanding.

Output ONLY valid JSON matching this exact schema, no other text:
{
  "questions": [
    {
      "question_id": "q1",
      "type": "mcq",
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_answer": "string (must exactly match one option)",
      "explanation": "string, why this is correct"
    },
    {
      "question_id": "q2",
      "type": "true_false",
      "question": "string",
      "correct_answer": "True or False",
      "explanation": "string"
    }
  ]
}

Generate 5 questions total: 3 MCQ and 2 True/False, based on the content provided. Vary difficulty across the questions."""

@router.post("/generate/{course_id}/{chapter_id}")
async def generate_quiz(course_id: str, chapter_id: str, user_id: str = Depends(get_current_user_id)):
    course = await courses_collection.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    chapter = next((c for c in course.get("chapters", []) if c.get("chapter_id") == chapter_id), None)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Combine all lesson content in this chapter to feed the quiz prompt
    chapter_content = "\n\n".join(
        f"{lesson['title']}: {lesson['content']}" for lesson in chapter.get("lessons", [])
    )

    raw_response = call_llm(
        system_prompt=QUIZ_GEN_SYSTEM_PROMPT,
        user_prompt=f"Generate a quiz from this chapter content:\n\n{chapter_content}",
        json_mode=True
    )

    try:
        quiz_data = json.loads(raw_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned invalid JSON, retry generation")

    return {"chapter_id": chapter_id, "quiz": quiz_data}

@router.post("/submit/{chapter_id}")
async def submit_quiz(chapter_id: str, attempt: QuizAttempt, user_id: str = Depends(get_current_user_id)):
    await quiz_collection.insert_one({
        "user_id": user_id,
        "chapter_id": chapter_id,
        "score": attempt.score,
        "total": attempt.total,
        "answers": attempt.answers
    })
    return {"status": "recorded", "score": attempt.score, "total": attempt.total}

@router.get("/history/{chapter_id}")
async def get_quiz_history(chapter_id: str, user_id: str = Depends(get_current_user_id)):
    cursor = quiz_collection.find({"user_id": user_id, "chapter_id": chapter_id}).sort("_id", -1)
    attempts = []
    async for a in cursor:
        a["_id"] = str(a["_id"])
        attempts.append(a)
    return attempts