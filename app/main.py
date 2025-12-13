from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GenAI CRUD API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "GenAI CRUD Backend is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "genai-user-mgmt-backend"}


from .routes import router as user_router
app.include_router(user_router, tags=["Users"], prefix="/users")

from pydantic import BaseModel
class ChatRequest(BaseModel):
    question: str

from .rag import ask_question

@app.post("/chat", tags=["AI"])
async def chat_endpoint(request: ChatRequest):
    response = await ask_question(request.question)
    return {"answer": response}
