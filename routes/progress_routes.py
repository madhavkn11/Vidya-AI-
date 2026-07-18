from fastapi import APIRouter, Depends
from database import progress_collection, courses_collection
from auth import get_current_user_id
from bson import ObjectId

router = APIRouter(prefix="/progress", tags=["progress"])

@router.post("/{course_id}/lesson/{lesson_id}")
async def mark_lesson_complete(course_id: str, lesson_id: str, completed: bool, user_id: str = Depends(get_current_user_id)):
    await progress_collection.update_one(
        {"user_id": user_id, "course_id": course_id, "lesson_id": lesson_id},
        {"$set": {"completed": completed}},
        upsert=True
    )
    return {"status": "updated"}

@router.get("/{course_id}")
async def get_course_progress(course_id: str, user_id: str = Depends(get_current_user_id)):
    course = await courses_collection.find_one({"_id": ObjectId(course_id)})
    total_lessons = sum(len(ch.get("lessons", [])) for ch in course.get("chapters", []))

    completed_cursor = progress_collection.find({"user_id": user_id, "course_id": course_id, "completed": True})
    completed_count = 0
    async for _ in completed_cursor:
        completed_count += 1

    percentage = round((completed_count / total_lessons) * 100, 1) if total_lessons > 0 else 0

    return {"completed": completed_count, "total": total_lessons, "percentage": percentage}