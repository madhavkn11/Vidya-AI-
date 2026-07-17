import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends
from bson import ObjectId
from database import courses_collection
from auth import get_current_user_id
from pdf_utils import extract_text_from_pdf, chunk_text
from chroma_utils import embed_and_store

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)

    course_doc = {
        "user_id": user_id,
        "title": file.filename.replace(".pdf", ""),
        "pdf_filename": file.filename,
        "chapters": [],
        "status": "processing"
    }
    result = await courses_collection.insert_one(course_doc)
    course_id = str(result.inserted_id)

    embed_and_store(course_id, chunks)

    await courses_collection.update_one(
        {"_id": ObjectId(course_id)},
        {"$set": {"status": "ready_for_generation", "raw_text_length": len(text)}}
    )

    return {"course_id": course_id, "chunks_created": len(chunks), "status": "ready_for_generation"}