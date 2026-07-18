import json
from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database import courses_collection
from auth import get_current_user_id
from chroma_utils import get_or_create_collection
from groq_utils import call_llm

router = APIRouter(prefix="/courses", tags=["courses"])

COURSE_GEN_SYSTEM_PROMPT = """You are an expert instructional designer. Given raw text extracted from a document, generate a structured learning course.

Output ONLY valid JSON matching this exact schema, no other text:
{
  "title": "string",
  "description": "string",
  "estimated_time": "string, e.g. '3 hours'",
  "difficulty": "Beginner|Intermediate|Advanced",
  "prerequisites": ["string"],
  "learning_objectives": ["string"],
  "chapters": [
    {
      "title": "string",
      "lessons": [
        {
          "title": "string",
          "content": "detailed explanation, 200-400 words",
          "key_takeaways": ["string"],
          "important_notes": "string or null",
          "examples": "string or null",
          "summary": "string"
        }
      ]
    }
  ]
}

Create 2-5 chapters, each with 2-4 lessons, based on the natural topic breaks in the content provided. Be thorough but concise."""

@router.post("/{course_id}/generate")
async def generate_course(course_id: str, user_id: str = Depends(get_current_user_id)):
    course = await courses_collection.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Pull all chunks back from ChromaDB to feed the generation prompt
    collection = get_or_create_collection(course_id)
    all_chunks = collection.get()["documents"]
    full_text = "\n\n".join(all_chunks)

    # Guard against exceeding context — cap input size for the prompt
    max_chars = 15000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]

    raw_response = call_llm(
        system_prompt=COURSE_GEN_SYSTEM_PROMPT,
        user_prompt=f"Generate a course from this content:\n\n{full_text}",
        json_mode=True
    )

    try:
        course_data = json.loads(raw_response)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM returned invalid JSON, retry generation")

    # Attach IDs to chapters/lessons for reference later (progress tracking, quizzes)
    for c_idx, chapter in enumerate(course_data.get("chapters", [])):
        chapter["chapter_id"] = str(ObjectId())
        chapter["order_index"] = c_idx
        for l_idx, lesson in enumerate(chapter.get("lessons", [])):
            lesson["lesson_id"] = str(ObjectId())
            lesson["order_index"] = l_idx

    update_fields = {
        "title": course_data.get("title", course["title"]),
        "description": course_data.get("description"),
        "estimated_time": course_data.get("estimated_time"),
        "difficulty": course_data.get("difficulty"),
        "prerequisites": course_data.get("prerequisites", []),
        "learning_objectives": course_data.get("learning_objectives", []),
        "chapters": course_data.get("chapters", []),
        "status": "ready"
    }

    await courses_collection.update_one({"_id": ObjectId(course_id)}, {"$set": update_fields})

    return {"course_id": course_id, "status": "ready", "chapters_count": len(update_fields["chapters"])}

@router.get("/{course_id}")
async def get_course(course_id: str, user_id: str = Depends(get_current_user_id)):
    course = await courses_collection.find_one({"_id": ObjectId(course_id), "user_id": user_id})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course["_id"] = str(course["_id"])
    return course

@router.get("")
async def list_courses(user_id: str = Depends(get_current_user_id)):
    cursor = courses_collection.find({"user_id": user_id})
    courses = []
    async for c in cursor:
        c["_id"] = str(c["_id"])
        courses.append(c)
    return courses