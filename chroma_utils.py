import chromadb
from sentence_transformers import SentenceTransformer

chroma_client = chromadb.PersistentClient(path="./chroma_store")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def get_or_create_collection(course_id: str):
    return chroma_client.get_or_create_collection(name=f"course_{course_id}")

def embed_and_store(course_id: str, chunks: list[str]):
    collection = get_or_create_collection(course_id)
    embeddings = embedder.encode(chunks).tolist()
    ids = [f"{course_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, embeddings=embeddings, ids=ids)

def retrieve_relevant_chunks(course_id: str, query: str, top_k: int = 4):
    collection = get_or_create_collection(course_id)
    query_embedding = embedder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results["documents"][0] if results["documents"] else []