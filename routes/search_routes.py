from fastapi import APIRouter, Depends
from database import courses_collection
from auth import get_current_user_id

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
async def search_courses(q: str, user_id: str = Depends(get_current_user_id)):
    query = q.lower()
    results = []

    cursor = courses_collection.find({"user_id": user_id})
    async for course in cursor:
        for chapter in course.get("chapters", []):
            if query in chapter.get("title", "").lower():
                results.append({
                    "type": "chapter", "course_id": str(course["_id"]),
                    "course_title": course.get("title"), "match": chapter["title"]
                })
            for lesson in chapter.get("lessons", []):
                searchable = f"{lesson.get('title', '')} {lesson.get('content', '')}".lower()
                if query in searchable:
                    results.append({
                        "type": "lesson", "course_id": str(course["_id"]),
                        "course_title": course.get("title"),
                        "chapter_title": chapter["title"], "match": lesson["title"]
                    })

    return {"query": q, "results": results, "count": len(results)}