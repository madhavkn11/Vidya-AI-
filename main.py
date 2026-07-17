from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth_routes, upload_routes

app = FastAPI(title="AI Course Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before final submission
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(upload_routes.router)

@app.get("/")
def root():
    return {"status": "running"}