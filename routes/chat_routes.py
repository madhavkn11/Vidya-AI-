from fastapi import APIRouter, Depends
from bson import ObjectId
from database import chat_collection, courses_collection
from auth import get_current_user_id
from chroma_utils import retrieve_relevant_chunks
from groq_utils import call_llm
from models import ChatMessage

router = APIRouter(prefix="/chat", tags=["chat"])

CHAT_SYSTEM_PROMPT = """You are a helpful AI learning companion. Answer the user's question using ONLY the provided context from their course material. If the context doesn't contain the answer, say so honestly rather than making something up. Be clear, concise, and encouraging."""

@router.post("/{course_id}")
async def chat_with_course(course_id: str, message: dict, user_id: str = Depends(get_current_user_id)):
    user_question = message["content"]

    # Retrieve relevant chunks from this course's ChromaDB collection
    relevant_chunks = retrieve_relevant_chunks(course_id, user_question, top_k=4)
    context = "\n\n".join(relevant_chunks)

    prompt = f"Context from the course material:\n{context}\n\nQuestion: {user_question}"

    answer = call_llm(system_prompt=CHAT_SYSTEM_PROMPT, user_prompt=prompt)

    # Persist both sides of the conversation
    await chat_collection.insert_one({
        "user_id": user_id, "course_id": course_id, "role": "user", "content": user_question
    })
    await chat_collection.insert_one({
        "user_id": user_id, "course_id": course_id, "role": "assistant", "content": answer
    })

    return {"answer": answer, "sources_used": len(relevant_chunks)}

@router.get("/{course_id}/history")
async def get_chat_history(course_id: str, user_id: str = Depends(get_current_user_id)):
    cursor = chat_collection.find({"user_id": user_id, "course_id": course_id}).sort("_id", 1)
    history = []
    async for msg in cursor:
        msg["_id"] = str(msg["_id"])
        history.append(msg)
    return history